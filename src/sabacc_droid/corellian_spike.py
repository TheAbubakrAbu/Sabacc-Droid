# corellian_spike.py

import random
import logging
from urllib.parse import quote
import discord
from discord import Embed, ButtonStyle, ui, Interaction
import requests
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from rules import get_corellian_spike_rules_embed, corellian_thumbnail, corellian_footer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_card_image_urls(cards: list[int]) -> list[str]:
    '''
    Generate image URLs for the given card values.
    Positive cards are prefixed with '+', negative as-is, and zero as '0'.
    '''

    base_url = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/corellian_spike/triangle/'

    return [f'''{base_url}{quote(f'+{card}' if card > 0 else str(card))}.png''' for card in cards]

def download_and_process_image(url: str, resize_width: int, resize_height: int) -> Image.Image:
    '''
    Download and resize an image, converting it to RGBA format.
    Returns the processed Image object or None on failure.
    '''

    try:
        response = requests.get(url, stream=True, timeout=5)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content)).convert('RGBA')
        img = img.resize((resize_width, resize_height), Image.LANCZOS)
        return img
    except Exception as e:
        logger.error(f'Error processing image from {url}: {e}')
        return None

def combine_card_images(card_image_urls: list[str], resize_width: int = 80, resize_height: int = 120, padding: int = 10) -> BytesIO:
    '''
    Combine multiple card images into a single horizontal image.
    Returns a BytesIO containing the combined PNG image.
    '''

    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [(i, executor.submit(download_and_process_image, url, resize_width, resize_height)) for i, url in enumerate(card_image_urls)]
        results = []
        for idx, future in futures:
            img = future.result()
            results.append((idx, img))
    results.sort()
    card_images = [img for idx, img in results if img is not None]
    if not card_images:
        raise ValueError('No valid images were provided to combine.')

    total_width = sum(img.width for img in card_images) + padding * (len(card_images) - 1)
    max_height = max(img.height for img in card_images)
    combined_image = Image.new('RGBA', (total_width, max_height), (255, 255, 255, 0))

    x_offset = 0
    for img in card_images:
        combined_image.paste(img, (x_offset, 0))
        x_offset += img.width + padding

    image_bytes = BytesIO()
    combined_image.save(image_bytes, format='PNG')
    image_bytes.seek(0)
    return image_bytes

async def create_embed_with_cards(title: str, description: str, cards: list[int]) -> tuple[Embed, discord.File]:
    '''
    Create an embed showing card images for the given hand.
    Returns an Embed and a File if images are available, else just an Embed.
    '''

    card_image_urls = get_card_image_urls(cards)
    image_bytes = None
    try:
        image_bytes = combine_card_images(card_image_urls)
    except Exception as e:
        logger.error(f'Failed to combine card images: {e}')

    embed = Embed(title=title, description=description, color=0xCBB7A0)
    embed.set_thumbnail(url=corellian_thumbnail)
    embed.set_footer(text=corellian_footer)

    if image_bytes:
        embed.set_image(url='attachment://combined_cards.png')
        file = discord.File(fp=image_bytes, filename='combined_cards.png')
        return embed, file
    else:
        return embed, None

class Player:
    '''
    Represents a player with a Discord user and a hand of cards.
    '''

    def __init__(self, user):
        self.user = user
        self.cards = []

    def draw_card(self, deck: list[int]) -> None:
        '''
        Draw one card from the deck and add it to the player's hand.
        Raises ValueError if the deck is empty.
        '''

        if not deck:
            raise ValueError('The deck is empty. Cannot draw more cards.')
        card = deck.pop()
        self.cards.append(card)

    def get_cards_string(self) -> str:
        '''
        Return a formatted string of the player's cards with separators.
        '''

        return ' | ' + ' | '.join(f'''{('+' if c > 0 else '')}{c}''' for c in self.cards) + ' |'

    def get_total(self) -> int:
        '''
        Return the sum of the player's card values.
        '''

        return sum(self.cards)

class CorelliaGameView(ui.View):
    '''
    Represents a Corellian Spike Sabacc game instance, managing players,
    deck, turns, and interactions.
    '''

    def __init__(self, rounds: int = 3, num_cards: int = 2, active_games=None, channel=None):
        super().__init__(timeout=None)
        self.players = []
        self.game_started = False
        self.current_player_index = -1
        self.deck = []
        self.rounds = rounds
        self.total_rounds = rounds
        self.rounds_completed = 0
        self.first_turn = True
        self.num_cards = num_cards
        self.current_message = None
        self.active_games = active_games if active_games is not None else []
        self.solo_game = False
        self.channel = channel

        self.view_rules_button = ViewRulesButton()
        self.add_item(self.view_rules_button)

        self.allow_discard = False
        self.discard_toggle_button = DiscardToggleButton(self)
        self.add_item(self.discard_toggle_button)

        self.game_ended = False
        self.message = None

    async def reset_lobby(self, interaction: Interaction) -> None:
        '''
        Reset the lobby to initial state and update the lobby message.
        '''

        self.game_started = False
        self.players.clear()
        self.current_player_index = -1
        self.deck.clear()
        self.solo_game = False
        self.rounds_completed = 0
        self.first_turn = True
        self.game_ended = False

        self.play_game_button.disabled = False
        self.leave_game_button.disabled = False
        self.start_game_button.disabled = True

        embed = Embed(
            title='Corellian Spike Sabacc Lobby',
            description=('Click **Join Game** to join the game!\n\n'
                         f'**Game Settings:**\n'
                         f'• {self.rounds} rounds\n'
                         f'• {self.num_cards} starting cards\n'
                         f'• Discarding cards is {"enabled" if self.allow_discard else "disabled"}\n\n'
                         'Once someone has joined, **Start Game** will be enabled.'),
            color=0xCBB7A0
        )
        embed.set_thumbnail(url=corellian_thumbnail)
        embed.set_footer(text=corellian_footer)

        await interaction.response.edit_message(embed=embed, view=self)

    async def update_game_embed(self) -> None:
        '''
        Send a message showing the current player's turn and card backs.
        '''

        if self.game_ended:
            return

        current_player = self.players[self.current_player_index]
        card_count = len(current_player.cards)

        description = f'**Players:**\n' + '\n'.join(
            player.user.mention for player in self.players) + '\n\n'
        description += f'**Round {self.rounds_completed}/{self.total_rounds}**\n'
        description += f'It\'s now {current_player.user.mention}\'s turn.\n'
        description += 'Click **Play Turn** to proceed.\n\n'
        description += f'**Target Number:** Always **0**'

        card_back_url = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/corellian_spike/card.png'
        card_image_urls = [card_back_url] * card_count

        image_bytes = None
        try:
            image_bytes = combine_card_images(card_image_urls)
        except Exception as e:
            logger.error(f'Failed to combine card images: {e}')

        embed = Embed(
            title='Corellian Spike Sabacc',
            description=description,
            color=0xCBB7A0
        )
        embed.set_thumbnail(url=corellian_thumbnail)
        embed.set_footer(text=corellian_footer)

        if image_bytes:
            embed.set_image(url='attachment://combined_cards.png')

        play_turn_view = PlayTurnView(self)

        if image_bytes:
            file = discord.File(fp=image_bytes, filename='combined_cards.png')
            await self.channel.send(
                content=f'{current_player.user.mention}',
                embed=embed,
                file=file,
                view=play_turn_view
            )
        else:
            await self.channel.send(
                content=f'{current_player.user.mention}',
                embed=embed,
                view=play_turn_view
            )

    async def update_lobby_embed(self, interaction=None) -> None:
        '''
        Update the lobby embed to show players, status, and start conditions.
        Reset if no players remain.
        '''

        if len(self.players) == 0:
            if interaction:
                await self.reset_lobby(interaction)
            return

        description = f'**Players Joined ({len(self.players)}/8):**\n' + '\n'.join(
            player.user.mention for player in self.players) + '\n\n'

        if len(self.players) >= 8:
            description += 'The game lobby is full.'

        description += (
            f'**Game Settings:**\n'
            f'• {self.rounds} rounds\n'
            f'• {self.num_cards} starting cards\n'
            f'• Discarding cards is {"enabled" if self.allow_discard else "disabled"}\n\n'
        )

        if len(self.players) < 2:
            description += 'Waiting for more players to join...\n'
            description += 'Click **Start Game** if you want to play with an AI.\n'
        else:
            description += 'Click **Start Game** to begin!\n'

        embed = Embed(
            title='Corellian Spike Sabacc Lobby',
            description=description,
            color=0xCBB7A0
        )
        embed.set_thumbnail(url=corellian_thumbnail)
        embed.set_footer(text=corellian_footer)

        self.start_game_button.disabled = len(self.players) < 1 or self.game_started
        self.play_game_button.disabled = len(self.players) >= 8 or self.game_started

        if interaction:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await self.message.edit(embed=embed, view=self)

    @ui.button(label='Join Game', style=ButtonStyle.primary)
    async def play_game_button(self, interaction: Interaction, button: ui.Button) -> None:
        '''
        Add the user who clicked to the game if possible.
        '''

        user = interaction.user
        if self.game_started:
            await interaction.response.send_message('The game has already started.', ephemeral=True)
            return
        if any(player.user.id == user.id for player in self.players):
            await interaction.response.send_message('You are already in the game.', ephemeral=True)
        elif len(self.players) >= 8:
            await interaction.response.send_message('The maximum number of players (8) has been reached.', ephemeral=True)
        else:
            self.players.append(Player(user))
            await self.update_lobby_embed(interaction)

    @ui.button(label='Leave Game', style=ButtonStyle.danger)
    async def leave_game_button(self, interaction: Interaction, button: ui.Button) -> None:
        '''
        Remove the user from the lobby if the game has not started yet.
        '''

        user = interaction.user
        if self.game_started:
            await interaction.response.send_message('You can\'t leave the game after it has started.', ephemeral=True)
            return
        player = next((p for p in self.players if p.user.id == user.id), None)
        if player:
            self.players.remove(player)
            await self.update_lobby_embed(interaction)
        else:
            await interaction.response.send_message('You are not in the game.', ephemeral=True)

    @ui.button(label='Start Game', style=ButtonStyle.success, disabled=True)
    async def start_game_button(self, interaction: Interaction, button: ui.Button) -> None:
        '''
        Start the game if conditions are met, deal cards, and proceed.
        '''

        if self.game_started:
            await interaction.response.send_message('The game has already started.', ephemeral=True)
            return
        if interaction.user.id not in [player.user.id for player in self.players]:
            await interaction.response.send_message('Only players in the game can start the game.', ephemeral=True)
            return
        if len(self.players) >= 1:
            self.game_started = True
            self.current_player_index = -1
            self.deck = []
            self.solo_game = False
            self.rounds_completed = 1
            self.first_turn = True
            self.game_ended = False

            self.play_game_button.disabled = True
            self.leave_game_button.disabled = True
            self.start_game_button.disabled = True

            if self.message:
                await self.message.edit(view=self)

            self.deck = self.generate_deck()
            random.shuffle(self.players)

            for player in self.players:
                player.cards.clear()
                for _ in range(self.num_cards):
                    player.draw_card(self.deck)

            await interaction.response.defer()
            await self.proceed_to_next_player()

            if len(self.players) == 1:
                self.solo_game = True
        else:
            await interaction.response.send_message('Not enough players to start the game.', ephemeral=True)

    def generate_deck(self) -> list[int]:
        '''
        Generate and return a shuffled deck of Corellian Spike Sabacc cards.
        '''

        deck = [i for i in range(1, 11) for _ in range(3)]
        deck += [-i for i in range(1, 11) for _ in range(3)]
        deck += [0, 0]
        second_deck = deck.copy()
        random.shuffle(deck)
        random.shuffle(second_deck)
        return deck + second_deck

    async def proceed_to_next_player(self) -> None:
        '''
        Move to the next player's turn, or end the game if the final round is completed.
        '''

        if self.game_ended:
            return

        self.current_player_index = (self.current_player_index + 1) % len(self.players)

        if self.current_player_index == 0 and not self.first_turn:
            self.rounds_completed += 1
            if self.rounds_completed > self.total_rounds:
                await self.end_game()
                return

        await self.update_game_embed()

        if self.first_turn:
            self.first_turn = False

    def evaluate_hand(self, player: Player) -> tuple:
        '''
        Evaluate a player's hand and return a tuple of sorting criteria, hand type, and total.
        Used for comparing final hands to determine the winner.
        '''

        cards = player.cards
        total = sum(cards)

        counts = {}
        for card in cards:
            counts[card] = counts.get(card, 0) + 1

        abs_counts = {}
        for card in cards:
            abs_card = abs(card)
            abs_counts[abs_card] = abs_counts.get(abs_card, 0) + 1

        def has_four_of_a_kind():
            return any(count >= 4 for count in abs_counts.values())

        def has_three_of_a_kind():
            return any(count >= 3 for count in abs_counts.values())

        def has_two_pairs():
            return len([v for v, c in abs_counts.items() if c >= 2]) >= 2

        zeros = counts.get(0, 0)
        positive_cards = [c for c in cards if c > 0]

        pairs = [v for v, c in abs_counts.items() if c >= 2]
        trips = [v for v, c in abs_counts.items() if c >= 3]
        quads = [v for v, c in abs_counts.items() if c >= 4]

        lowest_pair_value = min(pairs) if pairs else None
        lowest_trip_value = min(trips) if trips else None
        lowest_quad_value = min(quads) if quads else None

        hand_type = None
        hand_rank = None
        tie_breakers = []

        if total == 0:
            if zeros == 2 and len(cards) == 2:
                hand_type = 'Pure Sabacc'
                hand_rank = 1
                tie_breakers = []

            elif zeros >= 2:
                hand_type = 'Sarlacc Sabacc'
                hand_rank = 2
                tie_breakers = []

            elif sorted(cards) == [-10, -10, 0, 10, 10]:
                hand_type = 'Full Sabacc'
                hand_rank = 3
                tie_breakers = []

            elif zeros == 1 and has_four_of_a_kind():
                hand_type = 'Fleet'
                hand_rank = 4
                if lowest_quad_value is not None:
                    tie_breakers = [lowest_quad_value]
                else:
                    tie_breakers = [min(abs(c) for c in cards if c != 0)]

            elif zeros == 1 and has_two_pairs():
                hand_type = 'Twin Sun'
                hand_rank = 5
                if len(pairs) >= 2:
                    tie_breakers = [min(pairs)]
                else:
                    tie_breakers = [min(abs(c) for c in cards if c != 0)]

            elif zeros == 1 and len(cards) == 3 and any(c >= 2 for v, c in abs_counts.items() if v != 0):
                hand_type = 'Yee-Ha'
                hand_rank = 6
                if lowest_pair_value is not None:
                    tie_breakers = [lowest_pair_value]
                else:
                    tie_breakers = [min(abs(c) for c in cards if c != 0)]

            elif zeros == 1 and any(c >= 2 for v, c in abs_counts.items() if v != 0):
                hand_type = 'Kessel Run'
                hand_rank = 7
                if lowest_pair_value is not None:
                    tie_breakers = [lowest_pair_value]
                else:
                    tie_breakers = [min(abs(c) for c in cards if c != 0)]

            elif has_four_of_a_kind():
                hand_type = 'Squadron'
                hand_rank = 8
                if lowest_quad_value is not None:
                    tie_breakers = [lowest_quad_value]
                else:
                    tie_breakers = [min(abs(c) for c in cards)]

            elif has_three_of_a_kind():
                hand_type = 'Bantha\'s Wild'
                hand_rank = 9
                if lowest_trip_value is not None:
                    tie_breakers = [lowest_trip_value]
                else:
                    tie_breakers = [min(abs(c) for c in cards)]

            elif has_two_pairs():
                hand_type = 'Rule of Two'
                hand_rank = 10
                if len(pairs) >= 2:
                    tie_breakers = [min(pairs)]
                else:
                    tie_breakers = [min(abs(c) for c in cards)]

            elif any(count >= 2 for count in abs_counts.values()):
                hand_type = 'Sabacc Pair'
                hand_rank = 11
                if lowest_pair_value is not None:
                    tie_breakers = [lowest_pair_value]
                else:
                    tie_breakers = [min(abs(c) for c in cards)]

            else:
                hand_type = 'Sabacc'
                hand_rank = 12
                tie_breakers = [
                    min(abs(c) for c in cards),
                    -len(cards),
                    -sum(positive_cards),
                    -max(positive_cards) if positive_cards else float('-inf'),
                ]
        else:
            hand_type = 'Nulrhek'
            hand_rank = 13
            tie_breakers = [
                abs(total),
                0 if total > 0 else 1,
                -len(cards),
                -sum(positive_cards),
                -max(positive_cards) if positive_cards else float('-inf'),
            ]

        return (hand_rank, *tie_breakers), hand_type, total

    async def end_game(self) -> None:
        '''
        End the game, evaluate all hands, determine the winner(s), and show results.
        '''

        if self.game_ended:
            return

        self.game_ended = True

        if self.solo_game:
            if not any(player.user.name == 'Lando Calrissian AI' for player in self.players):
                lando_user = type('AIUser', (object,), {
                    'mention': 'Lando Calrissian AI',
                    'name': 'Lando Calrissian AI',
                    'id': -1
                })()
                lando = Player(user=lando_user)
                for _ in range(self.num_cards):
                    lando.draw_card(self.deck)
                self.players.append(lando)

        if not self.players:
            embed = Embed(
                title='Game Over',
                description='Nobody won because everyone junked!',
                color=0xCBB7A0
            )
            embed.set_thumbnail(url=corellian_thumbnail)
            embed.set_footer(text='Corellian Spike Sabacc')
            await self.channel.send(embed=embed, view=EndGameView(self.rounds, self.num_cards, self.active_games, self.channel))

            if self in self.active_games:
                self.active_games.remove(self)
            return

        evaluated_hands = []
        for player in self.players:
            hand_value, hand_type, total = self.evaluate_hand(player)
            evaluated_hands.append((hand_value, player, hand_type, total))

        evaluated_hands.sort(key=lambda x: x[0])

        results = '**Final Hands:**'
        for eh in evaluated_hands:
            _, player, hand_type, total = eh
            
            line1 = f'\n- {player.user.mention}: {player.get_cards_string()}'
            line2 = f'   - Total: {total}'
            line3 = f'   - Hand: {hand_type}'
            
            results += f'{line1}\n{line2}\n{line3}'

        best_hand_value = evaluated_hands[0][0]
        winners = [eh for eh in evaluated_hands if eh[0] == best_hand_value]

        if len(winners) == 1:
            winner = winners[0][1]
            hand_type = winners[0][2]
            results += f'\n\n🎉 {winner.user.mention} wins with a **{hand_type}**!'
        else:
            results += '\nIt\'s a tie between:'
            for eh in winners:
                player = eh[1]
                results += f' {player.user.mention}'
            results += '!'

        embed = Embed(
            title='Game Over',
            description=results,
            color=0xCBB7A0
        )
        embed.set_thumbnail(url=corellian_thumbnail)
        embed.set_footer(text='Corellian Spike Sabacc')
        mentions = ' '.join(
            player.user.mention
            for player in self.players
            if not (hasattr(player.user, 'name') and player.user.name == 'Lando Calrissian AI')
        )
        await self.channel.send(
            content=f'{mentions}',
            embed=embed,
            view=EndGameView(self.rounds, self.num_cards, self.active_games, self.channel)
        )

        if self in self.active_games:
            self.active_games.remove(self)

class EndGameView(ui.View):
    '''
    A view at the end of the game that allows starting a new game or viewing rules.
    '''

    def __init__(self, rounds: int, num_cards: int, active_games, channel):
        super().__init__(timeout=None)
        self.rounds = rounds
        self.num_cards = num_cards
        self.active_games = active_games
        self.channel = channel
        self.play_again_clicked = False

        self.play_again_button = ui.Button(label='Play Again', style=discord.ButtonStyle.success)
        self.play_again_button.callback = self.play_again_callback
        self.add_item(self.play_again_button)
        self.add_item(ViewRulesButton())

    async def play_again_callback(self, interaction: Interaction):
        '''
        Create a new lobby and add the player who clicked as the first player.
        '''

        if self.play_again_clicked:
            await interaction.response.send_message('Play Again has already been initiated.', ephemeral=True)
            return

        self.play_again_clicked = True
        self.play_again_button.disabled = True
        await interaction.response.edit_message(view=self)

        new_game_view = CorelliaGameView(
            rounds=self.rounds,
            num_cards=self.num_cards,
            active_games=self.active_games,
            channel=self.channel
        )
        new_game_view.message = await self.channel.send('New game lobby created!', view=new_game_view)
        new_player = Player(interaction.user)
        new_game_view.players.append(new_player)
        await new_game_view.update_lobby_embed()
        self.active_games.append(new_game_view)

class PlayTurnView(ui.View):
    '''
    A view showing a button to take the current player's turn and one to view rules.
    '''

    def __init__(self, game_view: CorelliaGameView):
        super().__init__(timeout=None)
        self.game_view = game_view
        self.play_turn_button = PlayTurnButton(game_view)
        self.view_rules_button = ViewRulesButton()
        self.add_item(self.play_turn_button)
        self.add_item(self.view_rules_button)
        self.current_player_id = self.game_view.players[self.game_view.current_player_index].user.id
        self.message = None

class PlayTurnButton(ui.Button):
    '''
    A button that lets the current player start their turn and view their hand.
    '''

    def __init__(self, game_view: CorelliaGameView):
        super().__init__(label='Play Turn', style=ButtonStyle.primary)
        self.game_view = game_view

    async def callback(self, interaction: Interaction) -> None:
        '''
        Show the current player's hand when they choose to play their turn.
        '''

        current_player = self.game_view.players[self.game_view.current_player_index]
        if interaction.user.id != current_player.user.id:
            await interaction.response.send_message('It\'s not your turn.', ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        title = f'Your Turn | Round {self.game_view.rounds_completed}/{self.game_view.total_rounds}'
        description = f'**Your Hand:** {current_player.get_cards_string()}\n**Total:** {current_player.get_total()}'

        embed, file = await create_embed_with_cards(
            title=title,
            description=description,
            cards=current_player.cards,
        )

        turn_view = TurnView(self.game_view, current_player)
        if file:
            await interaction.followup.send(
                embed=embed,
                view=turn_view,
                file=file,
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                embed=embed,
                view=turn_view,
                ephemeral=True
            )

class TurnView(ui.View):
    '''
    A view with actions for the current player's turn: draw, discard, replace, stand, or junk.
    '''

    def __init__(self, game_view: CorelliaGameView, player: Player):
        super().__init__(timeout=None)
        self.game_view = game_view
        self.player = player

        if game_view.allow_discard:
            discard_button = ui.Button(label="Discard Card", style=ButtonStyle.secondary)
            discard_button.callback = self.discard_card_button_callback
            self.add_item(discard_button)

    async def interaction_check(self, interaction: Interaction) -> bool:
        '''
        Ensure only the current player interacts with these options.
        '''

        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message('It\'s not your turn.', ephemeral=True)
            return False
        return True

    @ui.button(label='Draw Card', style=ButtonStyle.primary)
    async def draw_card_button(self, interaction: Interaction, button: ui.Button):
        '''
        Draw a card from the deck and end the current player's turn.
        '''

        await interaction.response.defer()
        self.player.draw_card(self.game_view.deck)

        title = f'You Drew a Card | Round {self.game_view.rounds_completed}/{self.game_view.total_rounds}'
        description = f'**Your Hand:** {self.player.get_cards_string()}\n**Total:** {self.player.get_total()}'

        embed, file = await create_embed_with_cards(
            title=title,
            description=description,
            cards=self.player.cards,
        )

        if file:
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None, attachments=[file])
        else:
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)

        self.stop()
        await self.game_view.proceed_to_next_player()

    async def discard_card_button_callback(self, interaction: Interaction):
        '''
        Discard a card from the player's hand.
        '''

        if len(self.player.cards) <= 1:
            await interaction.response.send_message(
                "You cannot discard when you have only one card.", ephemeral=True
            )
            return

        await interaction.response.defer()

        card_select_view = CardSelectView(self, action="discard")

        title = (
            f"Discard a Card | Round {self.game_view.rounds_completed}/"
            f"{self.game_view.total_rounds}"
        )
        description = (
            f"**Your Hand:** {self.player.get_cards_string()}\n"
            f"**Total:** {self.player.get_total()}\n\n"
            "Click the button corresponding to the card you want to discard."
        )

        embed, file = await create_embed_with_cards(title, description, self.player.cards)

        if file:
            await interaction.followup.edit_message(
                interaction.message.id,
                embed=embed,
                view=card_select_view,
                attachments=[file],
            )
        else:
            await interaction.followup.edit_message(
                interaction.message.id, embed=embed, view=card_select_view
            )

    @ui.button(label='Replace Card', style=ButtonStyle.secondary)
    async def replace_card_button(self, interaction: Interaction, button: ui.Button):
        '''
        Replace one of the player's cards with a new draw.
        '''

        await interaction.response.defer()
        card_select_view = CardSelectView(self, action='replace')

        title = f'Replace a Card | Round {self.game_view.rounds_completed}/{self.game_view.total_rounds}'
        description = (f'**Your Hand:** {self.player.get_cards_string()}\n'
                       f'**Total:** {self.player.get_total()}\n\n'
                       'Click the button corresponding to the card you want to replace.')

        embed, file = await create_embed_with_cards(
            title=title,
            description=description,
            cards=self.player.cards,
        )

        if file:
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=card_select_view, attachments=[file])
        else:
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=card_select_view)

    @ui.button(label='Stand', style=ButtonStyle.success)
    async def stand_button(self, interaction: Interaction, button: ui.Button):
        '''
        Stand without taking additional actions.
        '''

        await interaction.response.defer()

        title = f'You Chose to Stand | Round {self.game_view.rounds_completed}/{self.game_view.total_rounds}'
        description = f'**Your Hand:** {self.player.get_cards_string()}\n**Total:** {self.player.get_total()}'

        embed, file = await create_embed_with_cards(
            title=title,
            description=description,
            cards=self.player.cards,
        )

        if file:
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None, attachments=[file])
        else:
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)

        self.stop()
        await self.game_view.proceed_to_next_player()

    @ui.button(label='Junk', style=ButtonStyle.danger)
    async def junk_button(self, interaction: Interaction, button: ui.Button):
        '''
        Junk your hand and leave the game.
        '''

        await interaction.response.defer()

        title = f'You Chose to Junk | Round {self.game_view.rounds_completed}/{self.game_view.total_rounds}'
        description = 'You have given up and are out of the game.'

        embed, file = await create_embed_with_cards(
            title=title,
            description=description,
            cards=self.player.cards,
        )

        if file:
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None, attachments=[file])
        else:
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)

        self.game_view.players.remove(self.player)
        self.stop()

        if len(self.game_view.players) < 2:
            await self.game_view.end_game()
        else:
            await self.game_view.proceed_to_next_player()

class CardSelectView(ui.View):
    '''
    A view for selecting a specific card from the player's hand for discard or replace.
    '''
    
    def __init__(self, turn_view: TurnView, action: str):
        super().__init__(timeout=None)
        self.turn_view = turn_view
        self.game_view = turn_view.game_view
        self.player = turn_view.player
        self.action = action
        self.create_buttons()

    def create_buttons(self) -> None:
        '''
        Create a button for each card to select for discard/replace, plus a Go Back button.
        '''

        for idx, card in enumerate(self.player.cards):
            button_label = f'''{('+' if card > 0 else '')}{card}'''
            button = ui.Button(label=button_label, style=ButtonStyle.primary)
            button.callback = self.make_callback(card, idx)
            self.add_item(button)
            if len(self.children) >= 25:
                break
        self.add_item(GoBackButton(self))

    def make_callback(self, card_value: int, card_index: int):
        '''
        Return a callback for the chosen card that handles the discard/replace action.
        '''

        async def callback(interaction: Interaction) -> None:
            await interaction.response.defer()
            if self.action == 'discard':
                if len(self.player.cards) <= 1:
                    await interaction.followup.send('You cannot discard when you have only one card.', ephemeral=True)
                    return
                card_value_discarded = self.player.cards.pop(card_index)
                self.game_view.deck.insert(0, card_value_discarded)
                title = f'You Discarded {card_value_discarded} | Round {self.game_view.rounds_completed}/{self.game_view.total_rounds}'
                description = f'**Your Hand:** {self.player.get_cards_string()}\n**Total:** {self.player.get_total()}'
            elif self.action == 'replace':
                card_value_replaced = self.player.cards.pop(card_index)
                self.game_view.deck.insert(0, card_value_replaced)
                self.player.draw_card(self.game_view.deck)
                new_card = self.player.cards[-1]
                title = f'You Replaced {card_value_replaced} with {new_card} | Round {self.game_view.rounds_completed}/{self.game_view.total_rounds}'
                description = f'**Your Hand:** {self.player.get_cards_string()}\n**Total:** {self.player.get_total()}'
            else:
                embed = Embed(title='Unknown Action', description='An error occurred.', color=0xFF0000)
                embed.set_thumbnail(url=corellian_thumbnail)
                embed.set_footer(text=corellian_footer)
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
                return

            embed, file = await create_embed_with_cards(
                title=title,
                description=description,
                cards=self.player.cards,
            )

            if file:
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None, attachments=[file])
            else:
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)

            self.stop()
            self.turn_view.stop()
            await self.turn_view.game_view.proceed_to_next_player()

        return callback

    async def interaction_check(self, interaction: Interaction) -> bool:
        '''
        Only the current player can select a card.
        '''

        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message('This is not your card selection.', ephemeral=True)
            return False
        return True

class GoBackButton(ui.Button):
    '''
    A button to return to the turn view without performing discard/replace.
    '''

    def __init__(self, card_select_view: CardSelectView):
        super().__init__(label='Go Back', style=ButtonStyle.secondary)
        self.card_select_view = card_select_view

    async def callback(self, interaction: Interaction) -> None:
        '''
        Return to the TurnView without discarding or replacing a card.
        '''

        await interaction.response.defer()
        turn_view = self.card_select_view.turn_view

        title = f'Your Turn | Round {turn_view.game_view.rounds_completed}/{turn_view.game_view.total_rounds}'
        description = f'**Your Hand:** {turn_view.player.get_cards_string()}\n**Total:** {turn_view.player.get_total()}'

        embed, file = await create_embed_with_cards(
            title=title,
            description=description,
            cards=turn_view.player.cards,
        )

        if file:
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=turn_view, attachments=[file])
        else:
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=turn_view)

        self.card_select_view.stop()

class ViewRulesButton(ui.Button):
    '''
    A button that displays the Corellian Spike Sabacc rules.
    '''

    def __init__(self):
        super().__init__(label='View Rules', style=ButtonStyle.secondary)

    async def callback(self, interaction: Interaction) -> None:
        '''
        Show the rules embed as an ephemeral message.
        '''
        
        rules_embed = get_corellian_spike_rules_embed()
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)

class DiscardToggleButton(ui.Button):
    '''
    A toggle button for enabling/disabling discarding in Corellian Spike.
    '''

    def __init__(self, game_view):
        self.game_view = game_view
        super().__init__(
            label='Discard Cards: Off',
            style=ButtonStyle.secondary
        )

    async def callback(self, interaction: Interaction) -> None:
        '''
        Toggle discard on/off and update the button + embed.
        '''
        
        self.game_view.allow_discard = not self.game_view.allow_discard
        self.label = 'Discard Cards: On' if self.game_view.allow_discard else 'Discard Cards: Off'

        await self.game_view.update_lobby_embed(interaction)