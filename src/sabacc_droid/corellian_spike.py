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
from rules import get_corellian_spike_rules_embed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Utility functions
def get_card_image_urls(cards: list[int]) -> list[str]:
    '''Generate card image URLs based on card values.'''
    base_url = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/corellian_spike/'
    return [f'{base_url}{quote(f"+{card}" if card > 0 else str(card))}.png' for card in cards]

def download_and_process_image(url: str, resize_width: int, resize_height: int) -> Image.Image:
    '''Download an image and resize it.'''
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
    '''Combine multiple card images horizontally into a single image while preserving order.'''
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

async def create_embed_with_cards(title: str, description: str, cards: list[int], thumbnail_url: str, color: int = 0x964B00) -> tuple[Embed, discord.File]:
    '''Create an embed with combined card images.'''
    card_image_urls = get_card_image_urls(cards)
    image_bytes = None
    try:
        image_bytes = combine_card_images(card_image_urls)
    except Exception as e:
        logger.error(f'Failed to combine card images: {e}')
    
    embed = Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=thumbnail_url)
    
    if image_bytes:
        embed.set_image(url='attachment://combined_cards.png')
        file = discord.File(fp=image_bytes, filename='combined_cards.png')
        return embed, file
    else:
        return embed, None

class Player:
    '''Represents a player in the game.'''

    def __init__(self, user):
        '''Initialize a player with a Discord user.'''
        self.user = user
        self.cards: list[int] = []

    def draw_card(self, deck: list[int]) -> None:
        '''Draw a card from the deck and add it to the player's hand.'''
        if not deck:
            raise ValueError('The deck is empty. Cannot draw more cards.')
        card = deck.pop()
        self.cards.append(card)

    def get_cards_string(self) -> str:
        '''Return a string representation of the player's hand.'''
        return ' | ' + ' | '.join(f'{"+ " if c > 0 else ""}{c}' for c in self.cards) + ' |'

    def get_total(self) -> int:
        '''Calculate the total value of the player's hand.'''
        return sum(self.cards)

class CorelliaGameView(ui.View):
    '''Manages the game state and user interactions for Corellian Spike Sabacc.'''

    def __init__(self, rounds: int = 3, num_cards: int = 2, active_games: list = None, channel=None):
        '''Initialize the game view with game settings.'''
        super().__init__(timeout=None)
        self.players: list[Player] = []
        self.game_started = False
        self.current_player_index = -1
        self.deck: list[int] = []
        self.rounds = rounds
        self.total_rounds = rounds
        self.rounds_completed = 0
        self.first_turn = True
        self.num_cards = num_cards
        self.current_message = None
        self.active_views: list[ui.View] = []
        self.active_games = active_games if active_games is not None else []
        self.solo_game = False
        self.channel = channel
        self.view_rules_button = ViewRulesButton()
        self.add_item(self.view_rules_button)
        self.game_ended = False  # New flag to indicate if the game has ended

    async def reset_lobby(self, interaction: Interaction) -> None:
        '''Reset the game lobby to its initial state.'''
        # Reset game state variables
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
            title='Sabacc Game Lobby',
            description='Click **Play Game** to join the game.\n\n'
                        f'**Game Settings:**\n{self.rounds} rounds\n{self.num_cards} starting cards\n\n'
                        'Once someone has joined, the **Start Game** button will be enabled.',
            color=0x964B00
        )
        embed.set_footer(text='Corellian Spike Sabacc')
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')

        await interaction.response.edit_message(embed=embed, view=self)

    async def update_game_embed(self) -> None:
        '''Update the game embed to reflect the current player's turn.'''
        if self.game_ended:
            return

        current_player = self.players[self.current_player_index]
        card_count = len(current_player.cards)

        description = f'**Players:**\n' + '\n'.join(
            player.user.mention for player in self.players) + '\n\n'
        description += f'**Round {self.rounds_completed}/{self.total_rounds}**\n'
        description += f'It\'s now {current_player.user.mention}\'s turn.\n'
        description += 'Click **Play Turn** to take your turn.\n\n'

        card_back_url = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/corellian_spike/card.png'
        card_image_urls = [card_back_url] * card_count

        image_bytes = None

        try:
            image_bytes = combine_card_images(card_image_urls)
        except Exception as e:
            logger.error(f'Failed to combine card images: {e}')

        embed = Embed(
            title='Sabacc Game',
            description=description,
            color=0x964B00
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')

        if image_bytes:
            embed.set_image(url='attachment://combined_cards.png')

        # Remove old PlayTurnViews from active_views
        self.active_views = [view for view in self.active_views if not isinstance(view, PlayTurnView)]

        play_turn_view = PlayTurnView(self)
        self.active_views.append(play_turn_view)

        if image_bytes:
            file = discord.File(fp=image_bytes, filename='combined_cards.png')
            play_turn_view.message = await self.channel.send(
                content=f'{current_player.user.mention}',
                embed=embed,
                file=file,
                view=play_turn_view
            )
        else:
            play_turn_view.message = await self.channel.send(
                content=f'{current_player.user.mention}',
                embed=embed,
                view=play_turn_view
            )

    async def update_lobby_embed(self, interaction=None) -> None:
        '''Update the lobby embed to reflect the current state of the lobby.'''
        if len(self.players) == 0:
            if interaction:
                await self.reset_lobby(interaction)
            return

        description = f'**Players Joined ({len(self.players)}/8):**\n' + '\n'.join(
            player.user.mention for player in self.players) + '\n\n'

        if self.game_started:
            description += 'The game has started!'
        elif len(self.players) >= 8:
            description += 'The game lobby is full.'

        description += f'**Game Settings:**\n{self.rounds} rounds\n{self.num_cards} starting cards\n\n'

        if len(self.players) < 2:
            description += 'Waiting for more players to join...\n'
            description += 'Click **Start Game** if you want to play with an AI.\n'
        else:
            description += 'Click **Start Game** to begin!\n'

        embed = Embed(
            title='Sabacc Game Lobby',
            description=description,
            color=0x964B00
        )
        embed.set_footer(text='Corellian Spike Sabacc')
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')

        self.start_game_button.disabled = len(self.players) < 1 or self.game_started
        self.play_game_button.disabled = len(self.players) >= 8 or self.game_started

        if interaction:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await self.message.edit(embed=embed, view=self)

    @ui.button(label='Play Game', style=ButtonStyle.primary)
    async def play_game_button(self, interaction: Interaction, button: ui.Button) -> None:
        '''Handle the Play Game button press to join the game.'''
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
        '''Handle the Leave Game button press to leave the game.'''
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
        '''Handle the Start Game button press to start the game.'''
        user = interaction.user
        if self.game_started:
            await interaction.response.send_message('The game has already started.', ephemeral=True)
            return
        if interaction.user.id not in [player.user.id for player in self.players]:
            await interaction.response.send_message('Only players in the game can start the game.', ephemeral=True)
            return
        if len(self.players) >= 1:
            # Reset game state variables when starting a new game
            self.game_started = True
            self.current_player_index = -1
            self.deck = []
            self.solo_game = False
            self.rounds_completed = 1
            self.first_turn = True
            self.game_ended = False

            # Disable lobby buttons after game starts
            self.play_game_button.disabled = True
            self.leave_game_button.disabled = True
            self.start_game_button.disabled = True
            await interaction.response.edit_message(view=self)

            # Initialize the game
            self.deck = self.generate_deck()
            random.shuffle(self.players)

            # Deal initial cards
            for player in self.players:
                player.cards.clear()  # Clear any previous cards
                for _ in range(self.num_cards):
                    player.draw_card(self.deck)

            # Start the first turn
            await self.proceed_to_next_player()

            if len(self.players) == 1:
                self.solo_game = True
        else:
            await interaction.response.send_message('Not enough players to start the game.', ephemeral=True)

    def generate_deck(self) -> list[int]:
        '''Generate and shuffle a new deck for the game.'''
        deck = [i for i in range(1, 11) for _ in range(3)]
        deck += [-i for i in range(1, 11) for _ in range(3)]
        deck += [0, 0]
        second_deck = deck.copy()
        random.shuffle(deck)
        random.shuffle(second_deck)
        return deck + second_deck

    async def proceed_to_next_player(self) -> None:
        '''Proceed to the next player's turn or end the game if rounds are completed.'''
        if self.game_ended:
            return

        # Remove any old PlayTurnViews from active_views
        self.active_views = [view for view in self.active_views if not isinstance(view, PlayTurnView)]

        # Check if there are still players in the game
        if len(self.players) < 1:
            await self.end_game()
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
        '''Evaluate a player's hand to determine its rank and type.'''
        cards = player.cards
        total = sum(cards)
        hand_type = None
        hand_rank = None
        tie_breakers = []
        counts = {}

        # Count occurrences of each card value
        for card in cards:
            counts[card] = counts.get(card, 0) + 1

        positive_cards = [c for c in cards if c > 0]
        zeros = counts.get(0, 0)

        # Count occurrences of absolute card values
        abs_counts = {}
        for card in cards:
            abs_card = abs(card)
            abs_counts[abs_card] = abs_counts.get(abs_card, 0) + 1

        # Helper functions
        def has_four_of_a_kind():
            return any(count >= 4 for count in abs_counts.values())

        def has_three_of_a_kind():
            return any(count >= 3 for count in abs_counts.values())

        def has_two_pairs():
            return len([count for count in abs_counts.values() if count >= 2]) >= 2

        if total == 0:
            if zeros == 2 and len(cards) == 2:
                hand_type = 'Pure Sabacc'
                hand_rank = 1
                tie_breakers = []
            elif sorted(cards) == [-10, -10, 0, +10, +10]:
                hand_type = 'Full Sabacc'
                hand_rank = 2
                tie_breakers = []
            elif zeros == 1 and has_four_of_a_kind():
                hand_type = 'Fleet'
                hand_rank = 3
                tie_breakers = [min(abs(c) for c in cards if c != 0)]
            elif zeros == 1 and any(count >= 2 for value, count in abs_counts.items() if value != 0):
                hand_type = 'Yee-Haa'
                hand_rank = 4
                tie_breakers = [min(abs(c) for c in cards if c != 0)]
            elif has_three_of_a_kind() and len(cards) > 3:
                hand_type = 'Rhylet'
                hand_rank = 5
                tie_breakers = [min(abs(c) for c in cards)]
            elif has_four_of_a_kind():
                hand_type = 'Squadron'
                hand_rank = 6
                tie_breakers = [min(abs(c) for c in cards)]
            elif has_three_of_a_kind():
                hand_type = 'Bantha\'s Wild'
                hand_rank = 7
                tie_breakers = [min(abs(c) for c in cards)]
            elif has_two_pairs():
                hand_type = 'Rule of Two'
                hand_rank = 8
                tie_breakers = [min(abs(c) for c in cards)]
            elif any(count >= 2 for count in abs_counts.values()):
                hand_type = 'Sabacc Pair'
                hand_rank = 9
                tie_breakers = [min(abs(c) for c in cards)]
            else:
                hand_type = 'Sabacc'
                hand_rank = 10
                tie_breakers = [
                    min(abs(c) for c in cards),
                    -len(cards),
                    -sum(positive_cards),
                    -max(positive_cards) if positive_cards else float('-inf'),
                ]
        else:
            hand_type = 'Nulrhek'
            hand_rank = 11
            tie_breakers = [
                abs(total),
                0 if total > 0 else 1,
                -len(cards),
                -sum(positive_cards),
                -max(positive_cards) if positive_cards else float('-inf'),
            ]

        return (hand_rank, *tie_breakers), hand_type, total

    async def end_game(self) -> None:
        '''Determine the winner and end the game.'''
        if self.game_ended:
            return

        self.game_ended = True

        if self.solo_game:
            # Check if Lando Calrissian AI is already in the game
            if not any(player.user.name == 'Lando Calrissian AI' for player in self.players):
                lando_user = type('AIUser', (object,), {
                    'mention': 'Lando Calrissian AI',
                    'name': 'Lando Calrissian AI',
                    'id': -1  # Assign a unique ID
                })()
                lando = Player(user=lando_user)
                for _ in range(self.num_cards):
                    lando.draw_card(self.deck)
                self.players.append(lando)

        if not self.players:
            embed = Embed(
                title='Game Over',
                description='Nobody won because everyone junked!',
                color=0x964B00
            )
            embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')
            await self.channel.send(embed=embed, view=EndGameView(self.rounds, self.num_cards, self.active_games, self.channel))

            if self in self.active_games:
                self.active_games.remove(self)
            return

        evaluated_hands = []
        for player in self.players:
            hand_value, hand_type, total = self.evaluate_hand(player)
            evaluated_hands.append((hand_value, player, hand_type, total))

        evaluated_hands.sort(key=lambda x: x[0])

        results = '**Final Hands:**\n'
        for eh in evaluated_hands:
            _, player, hand_type, total = eh
            results += f'{player.user.mention}: {player.get_cards_string()} (Total: {total}, Hand: {hand_type})\n'

        best_hand_value = evaluated_hands[0][0]
        winners = [eh for eh in evaluated_hands if eh[0] == best_hand_value]

        if len(winners) == 1:
            winner = winners[0][1]
            hand_type = winners[0][2]
            results += f'\n🎉 {winner.user.mention} wins with a **{hand_type}**!'
        else:
            results += '\nIt\'s a tie between:'
            for eh in winners:
                player = eh[1]
                results += f' {player.user.mention}'
            results += '!'

        embed = Embed(
            title='Game Over',
            description=results,
            color=0x964B00
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')
        mentions = ' '.join(player.user.mention for player in self.players if 'AIUser' not in type(player.user).__name__)
        await self.channel.send(
            content=f'{mentions}',
            embed=embed,
            view=EndGameView(self.rounds, self.num_cards, self.active_games, self.channel)
        )

        if self in self.active_games:
            self.active_games.remove(self)

    # Add the missing message attribute for the lobby
    message = None

class EndGameView(ui.View):
    '''View displayed at the end of the game with options to view rules and play again.'''

    def __init__(self, rounds: int, num_cards: int, active_games: list, channel):
        '''Initialize the end game view with Play Again and View Rules buttons.'''
        super().__init__(timeout=None)
        self.rounds = rounds
        self.num_cards = num_cards
        self.active_games = active_games
        self.channel = channel
        self.play_again_clicked = False

        # Add Play Again button
        self.play_again_button = ui.Button(label='Play Again', style=discord.ButtonStyle.success)
        self.play_again_button.callback = self.play_again_callback
        self.add_item(self.play_again_button)

        # Add View Rules button
        self.add_item(ViewRulesButton())

    async def play_again_callback(self, interaction: Interaction):
        '''Handle the Play Again button press.'''
        if self.play_again_clicked:
            await interaction.response.send_message('Play Again has already been initiated.', ephemeral=True)
            return

        self.play_again_clicked = True
        self.play_again_button.disabled = True
        await interaction.response.edit_message(view=self)

        # Create a new game lobby
        new_game_view = CorelliaGameView(
            rounds=self.rounds,
            num_cards=self.num_cards,
            active_games=self.active_games,
            channel=self.channel
        )
        new_game_view.message = await self.channel.send('New game lobby created!', view=new_game_view)
        # Add the user who clicked the button to the game
        new_player = Player(interaction.user)
        new_game_view.players.append(new_player)
        await new_game_view.update_lobby_embed()
        # Add the new game to active games
        self.active_games.append(new_game_view)

class PlayTurnView(ui.View):
    '''View for the player to start their turn.'''

    def __init__(self, game_view: CorelliaGameView):
        '''Initialize the play turn view with a timeout.'''
        super().__init__(timeout=60)
        self.game_view = game_view
        self.play_turn_button = PlayTurnButton(game_view)
        self.view_rules_button = ViewRulesButton()
        self.add_item(self.play_turn_button)
        self.add_item(self.view_rules_button)
        self.current_player_id = self.game_view.players[self.game_view.current_player_index].user.id
        self.message = None  # To store the message object

    async def on_timeout(self):
        '''Handle timeout when the player doesn't start their turn in time.'''
        if self.game_view.game_ended:
            return
        try:
            current_player = self.game_view.players[self.game_view.current_player_index]
            embed = Embed(
                title='Turn Skipped',
                description=f'{current_player.user.mention} took too long and their turn was skipped.',
                color=0xFF0000
            )
            await self.game_view.channel.send(embed=embed)
            self.clear_items()
            if self.message:
                await self.message.edit(view=self)
            await self.game_view.proceed_to_next_player()
        except Exception as e:
            logger.error(f'Error during timeout handling: {e}')

class PlayTurnButton(ui.Button):
    '''Button for the player to begin their turn.'''

    def __init__(self, game_view: CorelliaGameView):
        '''Initialize the play turn button.'''
        super().__init__(label='Play Turn', style=ButtonStyle.primary)
        self.game_view = game_view

    async def callback(self, interaction: Interaction) -> None:
        '''Handle the player clicking the Play Turn button.'''
        current_player = self.game_view.players[self.game_view.current_player_index]
        if interaction.user.id != current_player.user.id:
            await interaction.response.send_message('It\'s not your turn.', ephemeral=True)
            return

        # Check if the player already has an active TurnView
        existing_turn_view = None
        for view in self.game_view.active_views:
            if isinstance(view, TurnView) and view.player.user.id == interaction.user.id:
                existing_turn_view = view
                break

        title = f'Your Turn | Round {self.game_view.rounds_completed}/{self.game_view.total_rounds}'
        description = f'**Your Hand:** {current_player.get_cards_string()}\n**Total:** {current_player.get_total()}'

        embed, file = await create_embed_with_cards(
            title=title,
            description=description,
            cards=current_player.cards,
            thumbnail_url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png'
        )

        if existing_turn_view:
            # Resend the existing TurnView
            await interaction.response.send_message(
                embed=embed,
                view=existing_turn_view,
                file=file,
                ephemeral=True
            )
        else:
            # Start a new TurnView
            turn_view = TurnView(self.game_view, current_player)
            self.game_view.active_views.append(turn_view)
            await interaction.response.send_message(
                embed=embed,
                view=turn_view,
                file=file,
                ephemeral=True
            )

class TurnView(ui.View):
    '''View containing the actions a player can take on their turn.'''

    def __init__(self, game_view: CorelliaGameView, player: Player):
        '''Initialize the turn view for the current player.'''
        super().__init__(timeout=60)
        self.game_view = game_view
        self.player = player

    async def interaction_check(self, interaction: Interaction) -> bool:
        '''Ensure only the current player can interact with this view.'''
        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message('It\'s not your turn.', ephemeral=True)
            return False
        return True

    @ui.button(label='Draw Card', style=ButtonStyle.primary)
    async def draw_card_button(self, interaction: Interaction, button: ui.Button):
        '''Handle the Draw Card action.'''
        self.player.draw_card(self.game_view.deck)

        title = f'You Drew a Card | Round {self.game_view.rounds_completed}/{self.game_view.total_rounds}'
        description = f'**Your Hand:** {self.player.get_cards_string()}\n**Total:** {self.player.get_total()}'

        embed, file = await create_embed_with_cards(
            title=title,
            description=description,
            cards=self.player.cards,
            thumbnail_url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png'
        )

        if file:
            await interaction.response.edit_message(embed=embed, view=None, attachments=[file])
        else:
            await interaction.response.edit_message(embed=embed, view=None)

        await self.stop()
        await self.game_view.proceed_to_next_player()

    @ui.button(label='Discard Card', style=ButtonStyle.secondary)
    async def discard_card_button(self, interaction: Interaction, button: ui.Button):
        '''Handle the Discard Card action.'''
        if len(self.player.cards) <= 1:
            await interaction.response.send_message('You cannot discard when you have only one card.', ephemeral=True)
            return

        card_select_view = CardSelectView(self, action='discard')
        self.game_view.active_views.append(card_select_view)

        title = f'Discard a Card | Round {self.game_view.rounds_completed}/{self.game_view.total_rounds}'
        description = 'Click the button corresponding to the card you want to discard.'

        embed, file = await create_embed_with_cards(
            title=title,
            description=description,
            cards=self.player.cards,
            thumbnail_url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png'
        )

        if file:
            await interaction.response.edit_message(embed=embed, view=card_select_view, attachments=[file])
        else:
            await interaction.response.edit_message(embed=embed, view=card_select_view)

    @ui.button(label='Replace Card', style=ButtonStyle.secondary)
    async def replace_card_button(self, interaction: Interaction, button: ui.Button):
        '''Handle the Replace Card action.'''
        card_select_view = CardSelectView(self, action='replace')
        self.game_view.active_views.append(card_select_view)

        title = f'Replace a Card | Round {self.game_view.rounds_completed}/{self.game_view.total_rounds}'
        description = 'Click the button corresponding to the card you want to replace.'

        embed, file = await create_embed_with_cards(
            title=title,
            description=description,
            cards=self.player.cards,
            thumbnail_url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png'
        )

        if file:
            await interaction.response.edit_message(embed=embed, view=card_select_view, attachments=[file])
        else:
            await interaction.response.edit_message(embed=embed, view=card_select_view)

    @ui.button(label='Stand', style=ButtonStyle.success)
    async def stand_button(self, interaction: Interaction, button: ui.Button):
        '''Handle the Stand action.'''
        title = f'You Chose to Stand | Round {self.game_view.rounds_completed}/{self.game_view.total_rounds}'
        description = f'**Your Hand:** {self.player.get_cards_string()}\n**Total:** {self.player.get_total()}'

        embed, file = await create_embed_with_cards(
            title=title,
            description=description,
            cards=self.player.cards,
            thumbnail_url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png'
        )

        if file:
            await interaction.response.edit_message(embed=embed, view=None, attachments=[file])
        else:
            await interaction.response.edit_message(embed=embed, view=None)

        await self.stop()
        await self.game_view.proceed_to_next_player()

    @ui.button(label='Junk', style=ButtonStyle.danger)
    async def junk_button(self, interaction: Interaction, button: ui.Button):
        '''Handle the Junk action, removing the player from the game.'''
        title = f'You Chose to Junk | Round {self.game_view.rounds_completed}/{self.game_view.total_rounds}'
        description = 'You have given up and are out of the game.'

        embed, file = await create_embed_with_cards(
            title=title,
            description=description,
            cards=self.player.cards,
            thumbnail_url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png'
        )

        if file:
            await interaction.response.edit_message(embed=embed, view=None, attachments=[file])
        else:
            await interaction.response.edit_message(embed=embed, view=None)

        self.game_view.players.remove(self.player)
        await self.stop()

        if len(self.game_view.players) < 2:
            await self.game_view.end_game()
        else:
            await self.game_view.proceed_to_next_player()

    async def on_timeout(self) -> None:
        '''Handle timeout when the player doesn't make a move in time.'''
        if self.game_view.game_ended:
            return
        try:
            embed = Embed(
                title='Turn Skipped',
                description=f'{self.player.user.mention} took too long and their turn was skipped.',
                color=0xFF0000
            )
            await self.game_view.channel.send(embed=embed)
            await self.stop()
            await self.game_view.proceed_to_next_player()
        except Exception as e:
            logger.error(f'Error during timeout handling: {e}')

    async def stop(self) -> None:
        '''Stop the view and remove it from active views.'''
        super().stop()
        if self in self.game_view.active_views:
            self.game_view.active_views.remove(self)
        # Remove buttons from the associated PlayTurnView
        play_turn_view = None
        for view in self.game_view.active_views:
            if isinstance(view, PlayTurnView) and view.current_player_id == self.player.user.id:
                play_turn_view = view
                break
        if play_turn_view and play_turn_view.message:
            play_turn_view.clear_items()
            await play_turn_view.message.edit(view=play_turn_view)

class CardSelectView(ui.View):
    '''View for the player to select a card to discard or replace.'''

    def __init__(self, turn_view: TurnView, action: str):
        '''Initialize the card selection view.'''
        super().__init__(timeout=60)
        self.turn_view = turn_view
        self.game_view = turn_view.game_view
        self.player = turn_view.player
        self.action = action
        self.create_buttons()

    def create_buttons(self) -> None:
        '''Create buttons for each card in the player's hand.'''
        for idx, card in enumerate(self.player.cards):
            button_label = f'{"+ " if card > 0 else ""}{card}'
            button = ui.Button(label=button_label, style=ButtonStyle.primary)
            button.callback = self.make_callback(card, idx)
            self.add_item(button)
            if len(self.children) >= 25:
                break

        self.add_item(GoBackButton(self))

    def make_callback(self, card_value: int, card_index: int):
        '''Generate a callback function for each card button.'''
        async def callback(interaction: Interaction) -> None:
            if self.action == 'discard':
                if len(self.player.cards) <= 1:
                    await interaction.response.send_message('You cannot discard when you have only one card.', ephemeral=True)
                    return
                card_value = self.player.cards.pop(card_index)
                self.turn_view.game_view.deck.insert(0, card_value)
                title = f'You Discarded {card_value} | Round {self.turn_view.game_view.rounds_completed}/{self.turn_view.game_view.total_rounds}'
            elif self.action == 'replace':
                card_value = self.player.cards.pop(card_index)
                self.turn_view.game_view.deck.insert(0, card_value)
                self.player.draw_card(self.turn_view.game_view.deck)
                title = f'You Replaced {card_value} | Round {self.turn_view.game_view.rounds_completed}/{self.turn_view.game_view.total_rounds}'
            else:
                embed = Embed(title='Unknown Action', description='An error occurred.', color=0xFF0000)
                await interaction.response.edit_message(embed=embed, view=None)
                return

            description = f'**Your Hand:** {self.player.get_cards_string()}\n**Total:** {self.player.get_total()}'

            embed, file = await create_embed_with_cards(
                title=title,
                description=description,
                cards=self.player.cards,
                thumbnail_url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png'
            )

            if file:
                await interaction.response.edit_message(embed=embed, view=None, attachments=[file])
            else:
                await interaction.response.edit_message(embed=embed, view=None)

            await self.stop()
            await self.turn_view.stop()
            await self.turn_view.game_view.proceed_to_next_player()

        return callback

    async def interaction_check(self, interaction: Interaction) -> bool:
        '''Ensure only the current player can interact with this view.'''
        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message('This is not your card selection.', ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        '''Handle timeout when the player doesn't select a card in time.'''
        if self.game_view.game_ended:
            return
        try:
            embed = Embed(
                title='Turn Skipped',
                description=f'{self.player.user.mention} took too long and their turn was skipped.',
                color=0xFF0000
            )
            await self.game_view.channel.send(embed=embed)
            await self.stop()
            await self.turn_view.stop()
            await self.turn_view.game_view.proceed_to_next_player()
        except Exception as e:
            logger.error(f'Error during timeout handling: {e}')

    async def stop(self) -> None:
        '''Stop the view and remove it from active views.'''
        super().stop()
        if self in self.game_view.active_views:
            self.game_view.active_views.remove(self)

class GoBackButton(ui.Button):
    '''Button to go back to the previous view.'''

    def __init__(self, card_select_view: CardSelectView):
        '''Initialize the Go Back button.'''
        super().__init__(label='Go Back', style=ButtonStyle.secondary)
        self.card_select_view = card_select_view

    async def callback(self, interaction: Interaction) -> None:
        '''Handle the Go Back button press.'''
        turn_view = self.card_select_view.turn_view

        title = f'Your Turn | Round {turn_view.game_view.rounds_completed}/{turn_view.game_view.total_rounds}'
        description = f'**Your Hand:** {turn_view.player.get_cards_string()}\n**Total:** {turn_view.player.get_total()}'

        embed, file = await create_embed_with_cards(
            title=title,
            description=description,
            cards=turn_view.player.cards,
            thumbnail_url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png'
        )

        if file:
            await interaction.response.edit_message(embed=embed, view=turn_view, attachments=[file])
        else:
            await interaction.response.edit_message(embed=embed, view=turn_view)

        await self.card_select_view.stop()

class ViewRulesButton(ui.Button):
    '''Button to view the game rules.'''

    def __init__(self):
        '''Initialize the View Rules button.'''
        super().__init__(label='View Rules', style=ButtonStyle.secondary)

    async def callback(self, interaction: Interaction) -> None:
        '''Display the game rules when the button is pressed.'''
        rules_embed = get_corellian_spike_rules_embed()
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)