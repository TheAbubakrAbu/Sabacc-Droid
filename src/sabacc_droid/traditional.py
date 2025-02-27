# traditional.py

import random
import logging
from urllib.parse import quote
import discord
from discord import Embed, ButtonStyle, ui, Interaction
import requests
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from rules import get_traditional_rules_embed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_card_image_urls(cards: list[int]) -> list[str]:
    '''
    Generate image URLs for the given card values.
    For demonstration, this uses the same style of card naming as in corellian_spike.py.
    Adjust or replace with your actual image resources for Traditional Sabacc.
    '''
    base_url = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/traditional/'
    return [f"{base_url}{quote(f'+{card}' if card > 0 else str(card))}.png" for card in cards]

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
    results.sort(key=lambda x: x[0])
    card_images = [img for _, img in results if img is not None]
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

async def create_embed_with_cards(title: str, description: str, cards: list[int], thumbnail_url: str, color: int = 0xE8E8E8) -> tuple[Embed, discord.File]:
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

    embed = Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=thumbnail_url)

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
        return ' | ' + ' | '.join(f"{'+' if c > 0 else ''}{c}" for c in self.cards) + ' |'

    def get_total(self) -> int:
        '''
        Return the sum of the player's card values.
        '''
        return sum(self.cards)

class TraditionalGameView(ui.View):
    '''
    Represents a Traditional Sabacc game instance, managing players,
    deck, turns, and interactions. The game ends when a player calls Alderaan.
    '''
    def __init__(self, num_cards: int = 2, active_games=None, channel=None, max_players: int = 8):
        super().__init__(timeout=None)
        self.players = []
        self.game_started = False
        self.current_player_index = -1
        self.deck = []
        self.num_cards = num_cards
        self.game_ended = False
        self.active_games = active_games if active_games is not None else []
        self.channel = channel
        self.max_players = max_players

        self.view_rules_button = ViewRulesButton()
        self.add_item(self.view_rules_button)

        self.message = None

        self.round = 1
        self.turns_taken = 0

        self.alderaan_called = False
        self.alderaan_caller_index = None
        self.alderaan_caller_mention = ''

        self.solo_game = False

    async def reset_lobby(self, interaction: Interaction) -> None:
        '''
        Reset the lobby to initial state and update the lobby message.
        '''
        self.game_started = False
        self.players.clear()
        self.current_player_index = -1
        self.deck.clear()
        self.game_ended = False

        self.play_game_button.disabled = False
        self.leave_game_button.disabled = False
        self.start_game_button.disabled = True

        embed = Embed(
            title='Traditional Sabacc Lobby',
            description=(
                'Click **Play Game** to join the game!\n\n'
                '**Game Settings:**\n'
                '• No set number of rounds\n'
                '• Call Alderaan to end the game\n'
                f'• {self.num_cards} starting cards\n\n'
                'Once someone joins, **Start Game** will be enabled.'
            ),
            color=0xE8E8E8
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/Traditional.png')

        await interaction.response.edit_message(embed=embed, view=self)

    async def update_lobby_embed(self, interaction=None) -> None:
        '''
        Update the lobby embed to show players, status, and start conditions.
        Reset if no players remain.
        '''
        if len(self.players) == 0:
            if interaction:
                await self.reset_lobby(interaction)
            return

        description = f'**Players Joined ({len(self.players)}/{self.max_players}):**\n' + '\n'.join(
            player.user.mention for player in self.players
        ) + '\n\n'

        if len(self.players) >= self.max_players:
            description += 'The game lobby is full.'

        description += (
            '**Game Settings:**\n'
            '• No set number of rounds\n'
            '• Call Alderaan to end the game\n'
            f'• {self.num_cards} starting cards\n\n'
        )

        if len(self.players) < 2:
            description += ('Waiting for more players to join...\n'
                            'Click **Start Game** if you want to play with an AI.\n')
        else:
            description += 'Click **Start Game** to begin!\n'

        embed = Embed(
            title='Traditional Sabacc Lobby',
            description=description,
            color=0xE8E8E8
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/Traditional.png')

        self.start_game_button.disabled = (len(self.players) < 1 or self.game_started)
        self.play_game_button.disabled = (len(self.players) >= self.max_players or self.game_started)

        if interaction:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await self.message.edit(embed=embed, view=self)

    @ui.button(label='Play Game', style=ButtonStyle.primary)
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
        elif len(self.players) >= self.max_players:
            await interaction.response.send_message('The maximum number of players has been reached.', ephemeral=True)
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
            self.game_ended = False

            self.round = 1
            self.turns_taken = 0
            self.alderaan_called = False
            self.alderaan_caller_index = None
            self.alderaan_caller_mention = ''
            self.solo_game = (len(self.players) == 1)

            self.play_game_button.disabled = True
            self.leave_game_button.disabled = True
            self.start_game_button.disabled = True

            if self.message:
                await self.message.edit(view=self)

            self.deck = self.generate_deck()
            random.shuffle(self.deck)
            random.shuffle(self.players)

            for player in self.players:
                player.cards.clear()
                for _ in range(self.num_cards):
                    player.draw_card(self.deck)

            await interaction.response.defer()
            await self.proceed_to_next_player()
        else:
            await interaction.response.send_message('Not enough players to start the game.', ephemeral=True)

    def generate_deck(self) -> list[int]:
        '''
        Generate and return a shuffled deck of 76 Traditional Sabacc cards:
         - 4 suits, each with cards 1..15 (60 cards)
         - 16 special cards (2 copies each of the 8 specials)
        '''
        suited_cards = []
        for _suit in range(4):  # flasks, sabers, staves, coins
            for card in range(1, 16):
                suited_cards.append(card)

        special_values = [
            0,   # The Idiot
            -11, # Balance
            -8,  # Endurance
            -14, # Moderation
            -15, # The Evil One
            -2,  # The Queen of Air and Darkness
            -13, # Demise
            -17, # The Star
        ]
        special_cards = []
        for val in special_values:
            special_cards.extend([val, val])

        deck = suited_cards + special_cards
        return deck

    async def proceed_to_next_player(self) -> None:
        '''
        Move to the next player's turn. If Alderaan has been called,
        once the turn cycles back to the caller the game ends.
        Also, update the round count when a full cycle is completed.
        '''
        if self.game_ended:
            return

        self.turns_taken += 1
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        if self.current_player_index == 0 and self.turns_taken > len(self.players):
            self.round += 1

        if self.alderaan_called and self.current_player_index == self.alderaan_caller_index:
            await self.end_game()
            return

        await self.update_game_embed()

    async def update_game_embed(self) -> None:
        '''
        Send a message showing the current player's turn and card backs.
        '''
        if self.game_ended:
            return

        current_player = self.players[self.current_player_index]
        card_count = len(current_player.cards)

        description = f'**Players:**\n' + '\n'.join(player.user.mention for player in self.players) + '\n\n'
        description += f'**Round {self.round}**\n'
        description += f'It\'s now {current_player.user.mention}\'s turn.\n'
        description += 'Click **Play Turn** to proceed.\n\n'
        if self.alderaan_called:
            description += f'{self.alderaan_caller_mention} called Alderaan. This is your **final turn**.'

        card_back_url = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/traditional/card_back.png'
        card_image_urls = [card_back_url] * card_count

        image_bytes = None
        try:
            image_bytes = combine_card_images(card_image_urls)
        except Exception as e:
            logger.error(f'Failed to combine card images: {e}')

        embed = Embed(
            title='Traditional Sabacc',
            description=description,
            color=0xE8E8E8
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/Traditional.png')

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

    async def end_game(self) -> None:
        '''
        End the game, evaluate hands, determine the winner(s), and display results.
        Called when the final turn of the round has completed.
        If solo_game is True, a Lando Calrissian AI opponent is added.
        '''
        if self.game_ended:
            return
        self.game_ended = True

        if self.solo_game:
            if not any(hasattr(player.user, 'name') and player.user.name == 'Lando Calrissian AI' for player in self.players):
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
                description='No players remain. Nobody wins!',
                color=0xE8E8E8
            )
            embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/Traditional.png')
            await self.channel.send(embed=embed, view=EndGameView(self.active_games, self.channel))
            if self in self.active_games:
                self.active_games.remove(self)
            return

        evaluated_hands = []
        for player in self.players:
            rank_tuple, hand_name, total = self.evaluate_hand(player)
            evaluated_hands.append((rank_tuple, player, hand_name, total))

        evaluated_hands.sort(key=lambda x: x[0])

        results = '**Final Hands:**'
        for eh in evaluated_hands:
            _, pl, name, total = eh
            line1 = f'\n- {pl.user.mention}: {pl.get_cards_string()}'
            line2 = f'   - Total: {total}'
            line3 = f'   - Hand: {name}'
            results += f'{line1}\n{line2}\n{line3}'

        best_hand_val = evaluated_hands[0][0]
        winners = [x for x in evaluated_hands if x[0] == best_hand_val]

        if len(winners) == 1:
            winner_player = winners[0][1]
            winner_name = winners[0][2]
            results += f'\n\n🎉 {winner_player.user.mention} wins with a **{winner_name}**!'
        else:
            results += '\n\nIt\'s a tie between:'
            for w in winners:
                results += f' {w[1].user.mention}'
            results += '!'

        embed = Embed(
            title='Game Over',
            description=results,
            color=0xE8E8E8
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/Traditional.png')

        mentions = ' '.join(player.user.mention for player in self.players)
        await self.channel.send(
            content=f'{mentions}',
            embed=embed,
            view=EndGameView(self.active_games, self.channel)
        )

        if self in self.active_games:
            self.active_games.remove(self)

    def evaluate_hand(self, player: Player):
        '''
        Evaluate a player's hand according to Traditional Sabacc rules.
        Return: (rank_tuple, hand_name, total)
        rank_tuple is used for sorting (lower = better).
        '''
        cards = player.cards
        total = sum(cards)

        card_set = set(cards)
        if len(cards) == 3 and card_set == {0, 2, 3}:
            return ((1,), 'Idiot\'s Array', total)
        if total == 23 or total == -23:
            return ((2,), 'Sabacc', total)
        if len(cards) == 2 and cards.count(-2) == 2:
            return ((3,), 'Fairy Empress', total)

        distance = min(abs(23 - total), abs(-23 - total))
        neg_flag = 0 if total < 0 else 1
        card_count = -len(cards)
        abs_sum = -abs(total)
        max_card = -max(abs(c) for c in cards)

        return ((4, distance, neg_flag, card_count, abs_sum, max_card), 'Nulrhek', total)

class EndGameView(ui.View):
    '''
    A view at the end of the game that allows starting a new game or viewing rules.
    '''
    def __init__(self, active_games, channel):
        super().__init__(timeout=None)
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

        new_game_view = TraditionalGameView(
            active_games=self.active_games,
            channel=self.channel
        )
        new_game_view.message = await self.channel.send('New game lobby created!', view=new_game_view)
        new_game_view.players.append(Player(interaction.user))
        await new_game_view.update_lobby_embed()
        self.active_games.append(new_game_view)

class PlayTurnView(ui.View):
    '''
    A view showing a button to take the current player's turn and one to view rules.
    '''
    def __init__(self, game_view: TraditionalGameView):
        super().__init__(timeout=None)
        self.game_view = game_view
        self.play_turn_button = PlayTurnButton(game_view)
        self.view_rules_button = ViewRulesButton()
        self.add_item(self.play_turn_button)
        self.add_item(self.view_rules_button)
        self.current_player_id = self.game_view.players[self.game_view.current_player_index].user.id

class PlayTurnButton(ui.Button):
    '''
    A button that lets the current player start their turn and view their hand.
    '''
    def __init__(self, game_view: TraditionalGameView):
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

        title = f'Your Turn | Round {self.game_view.round}'
        description = f'**Your Hand:** {current_player.get_cards_string()}\n**Total:** {current_player.get_total()}'
        embed, file = await create_embed_with_cards(
            title=title,
            description=description,
            cards=current_player.cards,
            thumbnail_url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/Traditional.png'
        )

        turn_view = TurnView(self.game_view, current_player)
        if file:
            await interaction.followup.send(embed=embed, view=turn_view, file=file, ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, view=turn_view, ephemeral=True)

class TurnView(ui.View):
    '''
    A view with actions for the current player's turn: draw, replace, stand, call Alderaan, or junk.
    '''
    def __init__(self, game_view: TraditionalGameView, player: Player):
        super().__init__(timeout=None)
        self.game_view = game_view
        self.player = player

        self.draw_card_button = ui.Button(label='Draw Card', style=ButtonStyle.primary)
        self.draw_card_button.callback = self.draw_card_callback
        self.add_item(self.draw_card_button)

        self.replace_card_button = ui.Button(label='Replace Card', style=ButtonStyle.secondary)
        self.replace_card_button.callback = self.replace_card_callback
        self.add_item(self.replace_card_button)

        self.stand_button = ui.Button(label='Stand', style=ButtonStyle.success)
        self.stand_button.callback = self.stand_callback
        self.add_item(self.stand_button)

        self.junk_button = ui.Button(label='Junk', style=ButtonStyle.danger)
        self.junk_button.callback = self.junk_callback
        self.add_item(self.junk_button)

        self.call_alderaan_button = ui.Button(label='Call "Alderaan" to End the Game', style=ButtonStyle.danger)
        self.call_alderaan_button.callback = self.call_alderaan_callback
        self.add_item(self.call_alderaan_button)
        if self.game_view.alderaan_called:
            self.call_alderaan_button.disabled = True

    async def interaction_check(self, interaction: Interaction) -> bool:
        '''
        Ensure only the current player can use these options.
        '''
        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message('It\'s not your turn.', ephemeral=True)
            return False
        return True

    async def draw_card_callback(self, interaction: Interaction):
        '''
        Draw a card from the deck and end the current player's turn.
        '''
        await interaction.response.defer()
        try:
            self.player.draw_card(self.game_view.deck)
        except ValueError as e:
            await interaction.followup.send(str(e), ephemeral=True)
            return

        title = f'You Drew a Card | Round {self.game_view.round}'
        description = f'**Your Hand:** {self.player.get_cards_string()}\n**Total:** {self.player.get_total()}'
        embed, file = await create_embed_with_cards(
            title=title,
            description=description,
            cards=self.player.cards,
            thumbnail_url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/Traditional.png'
        )

        if file:
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None, attachments=[file])
        else:
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)

        self.stop()
        await self.game_view.proceed_to_next_player()

    async def replace_card_callback(self, interaction: Interaction):
        '''
        Replace one of the player's cards with a new draw.
        '''
        await interaction.response.defer()
        card_select_view = CardSelectView(self, 'replace')

        title = f'Replace a Card | Round {self.game_view.round}'
        description = (f'**Your Hand:** {self.player.get_cards_string()}\n'
                       f'**Total:** {self.player.get_total()}\n\n'
                       'Click the button corresponding to the card you want to replace.')
        embed, file = await create_embed_with_cards(
            title=title,
            description=description,
            cards=self.player.cards,
            thumbnail_url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/Traditional.png'
        )

        if file:
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=card_select_view, attachments=[file])
        else:
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=card_select_view)

    async def stand_callback(self, interaction: Interaction):
        '''
        Stand without taking additional actions.
        '''
        await interaction.response.defer()

        title = f'You Chose to Stand | Round {self.game_view.round}'
        description = f'**Your Hand:** {self.player.get_cards_string()}\n**Total:** {self.player.get_total()}'
        embed, file = await create_embed_with_cards(
            title=title,
            description=description,
            cards=self.player.cards,
            thumbnail_url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/Traditional.png'
        )

        if file:
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None, attachments=[file])
        else:
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)

        self.stop()
        await self.game_view.proceed_to_next_player()

    async def call_alderaan_callback(self, interaction: Interaction):
        '''
        Call Alderaan to trigger the final round. When called, all remaining players get a final turn.
        Once Alderaan is called, this option is disabled for subsequent turns.
        '''
        await interaction.response.defer()
        if not self.game_view.alderaan_called:
            self.game_view.alderaan_called = True
            self.game_view.alderaan_caller_index = self.game_view.current_player_index
            self.game_view.alderaan_caller_mention = self.player.user.mention

        title = f'You Called Alderaan | Round {self.game_view.round}'
        description = f'All remaining players will now have one final turn because {self.game_view.alderaan_caller_mention} called Alderaan.'
        embed = Embed(title=title, description=description, color=0xE8E8E8)
        embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/Traditional.png')
        
        await interaction.followup.send(embed=embed)
        self.stop()
        await self.game_view.proceed_to_next_player()

    async def junk_callback(self, interaction: Interaction):
        '''
        Junk your hand and leave the game.
        '''
        await interaction.response.defer()

        title = f'You Junked Your Hand | Round {self.game_view.round}'
        description = 'You have given up and are out of the game.'
        embed, file = await create_embed_with_cards(
            title=title,
            description=description,
            cards=self.player.cards,
            thumbnail_url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/Traditional.png'
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
    A view for selecting a specific card from the player's hand for replacement.
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
        Create a button for each card to select for replacement, plus a Go Back button.
        '''
        for idx, card in enumerate(self.player.cards):
            button_label = f"{'+' if card > 0 else ''}{card}"
            button = ui.Button(label=button_label, style=ButtonStyle.primary)
            button.callback = self.make_callback(idx)
            self.add_item(button)
            if len(self.children) >= 25:
                break
        self.add_item(GoBackButton(self))

    def make_callback(self, card_index: int):
        '''
        Return a callback for the chosen card to handle the replacement action.
        '''
        async def callback(interaction: Interaction) -> None:
            await interaction.response.defer()
            if self.action == 'replace':
                old_card = self.player.cards.pop(card_index)
                self.game_view.deck.insert(0, old_card)
                try:
                    self.player.draw_card(self.game_view.deck)
                except ValueError as e:
                    await interaction.followup.send(str(e), ephemeral=True)
                    self.player.cards.insert(card_index, old_card)
                    return
                new_card = self.player.cards[-1]
                title = f'You Replaced {old_card} with {new_card} | Round {self.game_view.round}'
                description = f'**Your Hand:** {self.player.get_cards_string()}\n**Total:** {self.player.get_total()}'
            else:
                embed = Embed(title='Unknown Action', description='An error occurred.', color=0xFF0000)
                embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/Traditional.png')
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
                return

            embed, file = await create_embed_with_cards(
                title=title,
                description=description,
                cards=self.player.cards,
                thumbnail_url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/Traditional.png'
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
    A button to return to the TurnView without performing replacement.
    '''
    def __init__(self, card_select_view: CardSelectView):
        super().__init__(label='Go Back', style=ButtonStyle.secondary)
        self.card_select_view = card_select_view

    async def callback(self, interaction: Interaction) -> None:
        '''
        Return to the TurnView without replacing a card.
        '''
        await interaction.response.defer()
        turn_view = self.card_select_view.turn_view

        title = f'Your Turn | Round {turn_view.game_view.round}'
        description = f'**Your Hand:** {turn_view.player.get_cards_string()}\n**Total:** {turn_view.player.get_total()}'
        embed, file = await create_embed_with_cards(
            title=title,
            description=description,
            cards=turn_view.player.cards,
            thumbnail_url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/Traditional.png'
        )

        if file:
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=turn_view, attachments=[file])
        else:
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=turn_view)

        self.card_select_view.stop()

class ViewRulesButton(ui.Button):
    '''
    A button that displays the Traditional Sabacc rules.
    '''
    def __init__(self):
        super().__init__(label='View Rules', style=ButtonStyle.secondary)

    async def callback(self, interaction: Interaction) -> None:
        '''
        Show the rules embed as an ephemeral message.
        '''
        rules_embed = get_traditional_rules_embed()
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)