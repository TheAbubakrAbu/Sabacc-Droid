import random
import logging
from urllib.parse import quote
import discord
from discord import Embed, ButtonStyle, ui, Interaction
import requests
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from rules import get_coruscant_shift_rules_embed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Card:
    '''
    Represents a Coruscant Shift Sabacc card.
    For non-zero cards, 'suit' is one of "Circles", "Triangles", or "Squares".
    Sylop (wild) cards have a value of 0 and suit "Sylop".
    '''
    def __init__(self, value: int, suit: str):
        self.value = value
        self.suit = suit

    def __str__(self):
        if self.suit == 'Sylop':
            return '0'
        sign = '+' if self.value > 0 else ''
        return f'{self.suit} {sign}{self.value}'

    def image_filename(self) -> str:
        '''
        Returns the filename for the card image.
        Format for non-sylop cards: "Suit_+Value.png" or "Suit_-Value.png"
        Sylop cards use "0.png".
        '''
        if self.suit == 'Sylop':
            return '0.png'
        sign = '+' if self.value > 0 else ''
        return f'{self.suit}_{sign}{self.value}.png'


def get_card_image_urls(cards: list[Card]) -> list[str]:
    '''
    Generate image URLs for the given Card objects.
    '''
    base_url = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/coruscant_shift/'
    return [f'{base_url}{quote(card.image_filename())}' for card in cards]


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
        futures = [(i, executor.submit(download_and_process_image, url, resize_width, resize_height))
                   for i, url in enumerate(card_image_urls)]
        results = []
        for idx, future in futures:
            img = future.result()
            results.append((idx, img))
    results.sort(key=lambda x: x[0])
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


async def create_embed_with_cards(title: str, description: str, cards: list[Card], thumbnail_url: str, color: int = 0x964B00) -> tuple[Embed, discord.File]:
    '''
    Create an embed showing card images for the given hand.
    Returns an Embed and a File if images are available.
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
        self.hand: list[Card] = []

    def draw_card(self, deck: list[Card]) -> None:
        if not deck:
            raise ValueError('The deck is empty. Cannot draw more cards.')
        card = deck.pop()
        self.hand.append(card)

    def get_hand_string(self) -> str:
        return ' | ' + ' | '.join(str(card) for card in self.hand) + ' |'

    def total_value(self) -> int:
        return sum(card.value for card in self.hand)


class CoruscantGameView(ui.View):
    '''
    Represents a Coruscant Shift Sabacc game instance.
    The game is played in two phases:
      1. Selection & Shift: Choose which cards to keep, discard the rest, and draw replacements.
      2. Final Selection & Reveal: Finalize your hand by repeating the selection process.
    The winner is determined by whose final hand total is closest to the target number (gold die roll).
    Ties are broken by the number of cards in the target suit (silver die roll, with Sylop cards counting as all suits).
    '''
    def __init__(self, rounds: int = 2, active_games=None, channel=None):
        super().__init__(timeout=None)
        self.players: list[Player] = []
        self.game_started = False
        self.phase = 1  # Phase 1: Selection & Shift; Phase 2: Final Selection & Reveal
        self.current_player_index = 0
        self.deck: list[Card] = []
        self.rounds_completed = 0  # Number of phases completed
        self.total_phases = 2
        self.active_games = active_games if active_games is not None else []
        self.channel = channel
        self.message = None
        self.add_item(ViewRulesButton())
        # Roll the dice to set target conditions.
        self.initialize_dice()

    def initialize_dice(self) -> None:
        gold_die_faces = [-10, 10, -5, 5, 0, 0]
        silver_die_faces = ['Circles', 'Circles', 'Triangles', 'Triangles', 'Squares', 'Squares']
        self.target_number = random.choice(gold_die_faces)
        self.target_suit = random.choice(silver_die_faces)
        logger.info(f'Dice rolled: Target Number = {self.target_number}, Target Suit = {self.target_suit}')

    async def update_lobby_embed(self, interaction=None) -> None:
        if len(self.players) == 0:
            if interaction:
                await self.reset_lobby(interaction)
            return

        description = f'**Players Joined ({len(self.players)}/8):**\n' + '\n'.join(player.user.mention for player in self.players) + '\n\n'
        if self.game_started:
            description += 'The game has started!'
        elif len(self.players) >= 8:
            description += 'The game lobby is full.'
        else:
            description += 'Click **Start Game** to begin!'
        description += (
            f'\n\n**Game Settings:**\nTarget Number: {self.target_number}\nTarget Suit: {self.target_suit}\n'
            '5 starting cards\n2 phases (Selection & Shift, then Final Selection)'
        )

        embed = Embed(
            title='Sabacc Game Lobby',
            description=description,
            color=0x964B00
        )
        embed.set_footer(text='Coruscant Shift Sabacc')
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')

        self.start_game_button.disabled = len(self.players) < 1 or self.game_started
        self.play_game_button.disabled = len(self.players) >= 8 or self.game_started

        if interaction:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await self.message.edit(embed=embed, view=self)

    async def reset_lobby(self, interaction: Interaction) -> None:
        self.game_started = False
        self.players.clear()
        self.current_player_index = 0
        self.deck.clear()
        self.phase = 1
        self.rounds_completed = 0
        self.initialize_dice()
        self.play_game_button.disabled = False
        self.leave_game_button.disabled = False
        self.start_game_button.disabled = True

        embed = Embed(
            title='Sabacc Game Lobby',
            description=('Click **Play Game** to join the game.\n\n'
                         f'**Game Settings:**\nTarget Number: {self.target_number}\nTarget Suit: {self.target_suit}\n'
                         '5 starting cards\n2 phases (Selection & Shift, then Final Selection)\n\n'
                         'Once someone has joined, the **Start Game** button will be enabled.'),
            color=0x964B00
        )
        embed.set_footer(text='Coruscant Shift Sabacc')
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label='Play Game', style=ButtonStyle.primary)
    async def play_game_button(self, interaction: Interaction, button: ui.Button) -> None:
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
        user = interaction.user
        if self.game_started:
            await interaction.response.send_message('You cannot leave the game after it has started.', ephemeral=True)
            return
        player = next((p for p in self.players if p.user.id == user.id), None)
        if player:
            self.players.remove(player)
            await self.update_lobby_embed(interaction)
        else:
            await interaction.response.send_message('You are not in the game.', ephemeral=True)

    @ui.button(label='Start Game', style=ButtonStyle.success, disabled=True)
    async def start_game_button(self, interaction: Interaction, button: ui.Button) -> None:
        if self.game_started:
            await interaction.response.send_message('The game has already started.', ephemeral=True)
            return
        if interaction.user.id not in [player.user.id for player in self.players]:
            await interaction.response.send_message('Only players in the game can start the game.', ephemeral=True)
            return
        if len(self.players) >= 1:
            self.game_started = True
            self.current_player_index = 0
            self.deck = self.generate_deck()
            random.shuffle(self.deck)
            # Deal 5 cards to each player
            for player in self.players:
                player.hand.clear()
                for _ in range(5):
                    player.draw_card(self.deck)
            await interaction.response.defer()
            await self.proceed_to_next_player()
        else:
            await interaction.response.send_message('Not enough players to start the game.', ephemeral=True)

    def generate_deck(self) -> list[Card]:
        deck = []
        suits = ['Circles', 'Triangles', 'Squares']
        # For each suit, add positive (+1 to +10) and negative (-1 to -10) cards (20 cards per suit)
        for suit in suits:
            for value in range(1, 11):
                deck.append(Card(value, suit))
                deck.append(Card(-value, suit))
        # Total from suits: 60 cards. Then add 2 Sylop cards (wild cards)
        deck.append(Card(0, 'Sylop'))
        deck.append(Card(0, 'Sylop'))
        random.shuffle(deck)
        return deck

    async def proceed_to_next_player(self) -> None:
        if not self.game_started:
            return

        if self.current_player_index >= len(self.players):
            # End of current phase
            self.rounds_completed += 1
            if self.phase == 1:
                # Move to Phase 2
                self.phase = 2
                self.current_player_index = 0
                await self.channel.send('Phase 1 complete. Proceeding to Final Selection & Reveal.')
            else:
                # Both phases complete; reveal final hands and determine the winner.
                await self.end_game()
                return

        current_player = self.players[self.current_player_index]
        await self.update_game_embed(current_player)

    async def update_game_embed(self, current_player: Player) -> None:
        description = f'**Players:**\n' + '\n'.join(player.user.mention for player in self.players) + '\n\n'
        description += f'**Phase {self.phase} of {self.total_phases}**\n'
        description += f'It is now {current_player.user.mention}’s turn to select cards.\n'
        description += 'Click **Select Cards** to proceed with your selection.'
        embed = Embed(
            title='Sabacc Game',
            description=description,
            color=0x964B00
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')
        select_view = SelectionPhaseView(self, current_player)
        await self.channel.send(content=f'{current_player.user.mention}', embed=embed, view=select_view)
        self.current_player_index += 1

    async def end_game(self) -> None:
        '''
        Reveal all players’ final hands and determine the winner.
        Winner is the player whose hand total is closest to the target number.
        Tie-breaker: highest count of cards matching the target suit (with Sylop counting as all suits).
        '''
        results = '**Final Hands:**\n'
        evaluations = []
        for player in self.players:
            total = player.total_value()
            diff = abs(total - self.target_number)
            count_target = sum(1 for card in player.hand if card.suit == self.target_suit or card.suit == 'Sylop')
            evaluations.append((diff, -count_target, player, total))
            results += f'{player.user.mention}: {player.get_hand_string()} (Total: {total})\n'
        evaluations.sort(key=lambda x: (x[0], x[1]))
        best = evaluations[0]
        winners = [ev for ev in evaluations if ev[0] == best[0] and ev[1] == best[1]]
        if len(winners) == 1:
            results += f'\n🎉 {winners[0][2].user.mention} wins!'
        else:
            results += '\nIt’s a tie between: ' + ', '.join(w[2].user.mention for w in winners)
        embed = Embed(
            title='Game Over',
            description=results,
            color=0x964B00
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')
        await self.channel.send(embed=embed)
        if self in self.active_games:
            self.active_games.remove(self)
        end_view = EndGameView(self.active_games, self.channel)
        await self.channel.send(view=end_view)


class SelectionPhaseView(ui.View):
    '''
    A view for a player's selection phase.
    The player can toggle which cards to keep.
    Unselected cards will be discarded and replaced from the deck.
    '''
    def __init__(self, game_view: CoruscantGameView, player: Player):
        super().__init__(timeout=None)
        self.game_view = game_view
        self.player = player
        self.selection_state = [True] * len(player.hand)  # Default: keep all cards
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        for idx, card in enumerate(self.player.hand):
            label = f"{str(card)} {'✅' if self.selection_state[idx] else '❌'}"
            button = ui.Button(label=label, style=ButtonStyle.primary)
            button.callback = self.make_toggle_callback(idx)
            self.add_item(button)
        confirm_button = ui.Button(label='Confirm Selection', style=ButtonStyle.success)
        confirm_button.callback = self.confirm_selection
        self.add_item(confirm_button)
        self.add_item(ViewRulesButton())

    def make_toggle_callback(self, index: int):
        async def callback(interaction: Interaction):
            if interaction.user.id != self.player.user.id:
                await interaction.response.send_message('This is not your selection.', ephemeral=True)
                return
            self.selection_state[index] = not self.selection_state[index]
            self.update_buttons()
            await interaction.response.edit_message(view=self)
        return callback

    async def confirm_selection(self, interaction: Interaction):
        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message('This is not your turn.', ephemeral=True)
            return
        new_hand = [card for selected, card in zip(self.selection_state, self.player.hand) if selected]
        self.player.hand = new_hand
        while len(self.player.hand) < 5 and self.game_view.deck:
            self.player.draw_card(self.game_view.deck)
        await interaction.response.send_message('Selection confirmed. Your hand has been updated.', ephemeral=True)
        self.stop()
        await self.game_view.proceed_to_next_player()


class EndGameView(ui.View):
    '''
    A view at the end of the game allowing players to start a new game.
    '''
    def __init__(self, active_games, channel):
        super().__init__(timeout=None)
        self.active_games = active_games
        self.channel = channel
        self.play_again_button = ui.Button(label='Play Again', style=ButtonStyle.success)
        self.play_again_button.callback = self.play_again_callback
        self.add_item(self.play_again_button)
        self.add_item(ViewRulesButton())

    async def play_again_callback(self, interaction: Interaction):
        self.play_again_button.disabled = True
        await interaction.response.edit_message(view=self)
        new_game_view = CoruscantGameView(active_games=self.active_games, channel=self.channel)
        new_game_view.message = await self.channel.send('New game lobby created!', view=new_game_view)
        new_game_view.players.append(Player(interaction.user))
        self.active_games.append(new_game_view)


class ViewRulesButton(ui.Button):
    '''
    A button to display the Coruscant Shift Sabacc rules.
    '''
    def __init__(self):
        super().__init__(label='View Rules', style=ButtonStyle.secondary)

    async def callback(self, interaction: Interaction):
        rules_embed = get_coruscant_shift_rules_embed()
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)