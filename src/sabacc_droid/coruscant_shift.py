# coruscant_shift.py

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

SUIT_TO_FOLDER = {
    '●': 'circles',
    '▲': 'triangles',
    '■': 'squares'
}

class Card:
    '''
    Represent a Coruscant Shift card with a certain suit (●, ▲, ■, or Sylop)
    and a numeric value (including 0 for Sylop).
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
        Returns subfolder-based filenames like:
          circles/+3.png
          triangles/-7.png
          squares/-10.png
        If suit == 'Sylop', return '0.png' at the top level.
        '''
        if self.suit == 'Sylop':
            return '0.png'

        folder = SUIT_TO_FOLDER.get(self.suit, 'circles')
        if self.value > 0:
            return f'{folder}/+{self.value}.png'
        else:
            return f'{folder}/{self.value}.png'

def get_card_image_urls(cards: list[Card]) -> list[str]:
    '''
    Generate image URLs for the given Card objects,
    pointing to subfolders under coruscant_shift.
    '''
    base_url = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/coruscant_shift/'
    return [f'{base_url}{quote(card.image_filename())}' for card in cards]

def download_and_process_image(url: str, resize_width: int, resize_height: int) -> Image.Image:
    '''
    Download and resize an image (RGBA). Returns Image or None on failure.
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
    Combine multiple card images horizontally into a single PNG. Returns a BytesIO.
    '''
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [
            (i, executor.submit(download_and_process_image, url, resize_width, resize_height))
            for i, url in enumerate(card_image_urls)
        ]
        results = []
        for idx, future in futures:
            img = future.result()
            results.append((idx, img))
    results.sort(key=lambda x: x[0])
    card_images = [img for _, img in results if img is not None]
    if not card_images:
        raise ValueError('No valid images to combine.')

    total_width = sum(img.width for img in card_images) + padding * (len(card_images) - 1)
    max_height = max(img.height for img in card_images)
    combined = Image.new('RGBA', (total_width, max_height), (255, 255, 255, 0))

    x_offset = 0
    for img in card_images:
        combined.paste(img, (x_offset, 0))
        x_offset += img.width + padding

    image_bytes = BytesIO()
    combined.save(image_bytes, format='PNG')
    image_bytes.seek(0)
    return image_bytes

async def create_embed_with_cards(
    title: str,
    description: str,
    cards: list[Card],
    thumbnail_url: str,
    color: int = 0x964B00
) -> tuple[Embed, discord.File]:
    '''
    Create an embed and possibly a File if images can be combined.
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
    Represents a player with a Discord user and a hand of Card objects.
    '''
    def __init__(self, user):
        self.user = user
        self.hand: list[Card] = []

    def draw_card(self, deck: list[Card]) -> None:
        if not deck:
            raise ValueError('Deck is empty. Cannot draw.')
        self.hand.append(deck.pop())

    def get_hand_string(self) -> str:
        return ' | ' + ' | '.join(str(c) for c in self.hand) + ' |'

    def total_value(self) -> int:
        return sum(c.value for c in self.hand)

class CoruscantGameView(ui.View):
    '''
    Coruscant Shift Sabacc:
    - 2 phases total
    - Final hand can be 1 to 5 cards
    - Ties break by # in target suit, then advanced tie-breakers
    '''
    def __init__(self, rounds: int = 2, active_games=None, channel=None):
        super().__init__(timeout=None)
        self.players: list[Player] = []
        self.game_started = False
        self.phase = 1
        self.current_player_index = 0
        self.deck: list[Card] = []
        self.rounds_completed = 0
        self.total_phases = 2
        self.active_games = active_games if active_games else []
        self.channel = channel
        self.message = None

        self.play_game_button = ui.Button(label='Play Game', style=discord.ButtonStyle.primary)
        self.leave_game_button = ui.Button(label='Leave Game', style=discord.ButtonStyle.danger)
        self.start_game_button = ui.Button(label='Start Game', style=discord.ButtonStyle.success, disabled=True)
        self.view_rules_button = CoruscantShiftViewRulesButton()

        self.play_game_button.callback = self.play_game_callback
        self.leave_game_button.callback = self.leave_game_callback
        self.start_game_button.callback = self.start_game_callback

        self.add_item(self.play_game_button)
        self.add_item(self.leave_game_button)
        self.add_item(self.start_game_button)
        self.add_item(self.view_rules_button)

        self.initialize_dice()

    def initialize_dice(self) -> None:
        gold_faces = [-10, 10, -5, 5, 0, 0]
        silver_faces = ['●', '●', '▲', '▲', '■', '■']
        self.target_number = random.choice(gold_faces)
        self.target_suit = random.choice(silver_faces)
        logger.info(f'Rolled dice: target_number={self.target_number}, target_suit={self.target_suit}')

    async def update_lobby_embed(self, interaction=None) -> None:
        if not self.players:
            if interaction:
                await self.reset_lobby(interaction)
            return

        desc = f'**Players Joined ({len(self.players)}/8):**\n'
        desc += '\n'.join(p.user.mention for p in self.players)
        desc += '\n\n'
        if self.game_started:
            desc += 'The game has started!'
        elif len(self.players) >= 8:
            desc += 'The game lobby is full.'
        else:
            desc += 'Click **Start Game** to begin!\n'
        desc += (
            f'\n**Game Settings:**\n'
            f'Target Number: {self.target_number}\n'
            f'Target Suit: {self.target_suit}\n'
            '5 starting cards\n2 phases total'
        )

        embed = Embed(title='Sabacc Game Lobby', description=desc, color=0x964B00)
        embed.set_footer(text='Coruscant Shift Sabacc')
        embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/Coruscant%20Shift.png')

        self.start_game_button.disabled = (len(self.players) < 1 or self.game_started)
        self.play_game_button.disabled = (len(self.players) >= 8 or self.game_started)

        if interaction:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await self.message.edit(embed=embed, view=self)

    async def reset_lobby(self, interaction: Interaction) -> None:
        self.game_started = False
        self.players.clear()
        self.deck.clear()
        self.phase = 1
        self.rounds_completed = 0
        self.current_player_index = 0
        self.initialize_dice()

        self.play_game_button.disabled = False
        self.leave_game_button.disabled = False
        self.start_game_button.disabled = True

        embed = Embed(
            title='Sabacc Game Lobby',
            description=(
                'Click **Play Game** to join!\n\n'
                f'**Game Settings:**\n'
                f'Target Number: {self.target_number}\n'
                f'Target Suit: {self.target_suit}\n'
                '5 starting cards\n2 phases total\n\n'
                'Once someone has joined, **Start Game** will be enabled.'
            ),
            color=0x964B00
        )
        embed.set_footer(text='Coruscant Shift Sabacc')
        embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/Coruscant%20Shift.png')

        await interaction.response.edit_message(embed=embed, view=self)

    async def play_game_callback(self, interaction: Interaction):
        user = interaction.user
        if self.game_started:
            await interaction.response.send_message('The game has already started.', ephemeral=True)
            return
        if any(p.user.id == user.id for p in self.players):
            await interaction.response.send_message('You are already in the game!', ephemeral=True)
            return
        if len(self.players) >= 8:
            await interaction.response.send_message('Game is full.', ephemeral=True)
            return

        self.players.append(Player(user))
        await self.update_lobby_embed(interaction)

    async def leave_game_callback(self, interaction: Interaction):
        if self.game_started:
            await interaction.response.send_message('You cannot leave after the game has started.', ephemeral=True)
            return
        player = next((p for p in self.players if p.user.id == interaction.user.id), None)
        if player:
            self.players.remove(player)
            await self.update_lobby_embed(interaction)
        else:
            await interaction.response.send_message('You are not in the game.', ephemeral=True)

    async def start_game_callback(self, interaction: Interaction):
        if self.game_started:
            await interaction.response.send_message('The game has already started.', ephemeral=True)
            return
        if interaction.user.id not in [p.user.id for p in self.players]:
            await interaction.response.send_message('Only players in the game can start it.', ephemeral=True)
            return
        if len(self.players) < 1:
            await interaction.response.send_message('Need at least 1 player to start.', ephemeral=True)
            return

        self.game_started = True
        self.deck = self.generate_deck()
        random.shuffle(self.deck)

        for player in self.players:
            player.hand.clear()
            for _ in range(5):
                player.draw_card(self.deck)

        self.play_game_button.disabled = True
        self.leave_game_button.disabled = True
        self.start_game_button.disabled = True

        if self.message:
            await self.message.edit(view=self)

        await interaction.response.defer()
        await self.proceed_to_next_player()

    def generate_deck(self) -> list[Card]:
        '''
        Build the 62-card deck using ●, ▲, ■ suits, plus 2 Sylop (0).
        '''
        suits = ['●', '▲', '■']
        deck = []
        for s in suits:
            for val in range(1, 11):
                deck.append(Card(val, s))
                deck.append(Card(-val, s))
        deck.append(Card(0, 'Sylop'))
        deck.append(Card(0, 'Sylop'))
        return deck

    async def proceed_to_next_player(self) -> None:
        if not self.game_started:
            return

        if self.current_player_index >= len(self.players):
            self.rounds_completed += 1
            if self.phase == 1:
                self.phase = 2
                self.current_player_index = 0
                await self.channel.send('Phase 1 complete. Proceeding to Final Selection & Reveal.')
                if self.players:
                    await self.show_player_turn_view(self.players[self.current_player_index])
            else:
                await self.end_game()
            return

        current_player = self.players[self.current_player_index]
        await self.show_player_turn_view(current_player)

    async def show_player_turn_view(self, player: Player) -> None:
        desc = (
            f'**Players:**\n'
            + '\n'.join(p.user.mention for p in self.players)
            + '\n\n'
            f'**Phase {self.phase} of {self.total_phases}**\n'
            f'It\'s now {player.user.mention}\'s turn.\n'
            'Click **Play Turn** to proceed.\n\n'
        )

        # Use a generic 'card.png' from your coruscant_shift folder:
        card_back_url = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/coruscant_shift/card.png'
        card_count = len(player.hand)
        card_image_urls = [card_back_url] * card_count

        image_bytes = None
        try:
            image_bytes = combine_card_images(card_image_urls)
        except Exception as e:
            logger.error(f'Failed to combine card images: {e}')

        embed = Embed(title='Sabacc Game', description=desc, color=0x964B00)
        embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/Coruscant%20Shift.png')

        turn_view = PlayTurnView(self)
        if image_bytes:
            embed.set_image(url='attachment://combined_cards.png')
            file = discord.File(fp=image_bytes, filename='combined_cards.png')
            await self.channel.send(content=player.user.mention, embed=embed, file=file, view=turn_view)
        else:
            await self.channel.send(content=player.user.mention, embed=embed, view=turn_view)

    async def end_game(self) -> None:
        '''
        Evaluate all final hands, applying tie-breakers in the order:
        1) Closest to target_number
        2) Most matching target_suit
        3) Then advanced tie-breakers (in code, we only do 2: "lowest diff" & "−suit_count" for sorting).
        '''
        if len(self.players) == 1:
            lando_exists = any(pl.user.name == 'Lando Calrissian AI' for pl in self.players)
            if not lando_exists:
                lando_user = type('AIUser', (object,), {
                    'mention': 'Lando Calrissian AI',
                    'name': 'Lando Calrissian AI',
                    'id': -1
                })()
                lando = Player(lando_user)
                for _ in range(5):
                    lando.draw_card(self.deck)
                self.players.append(lando)

        if not self.players:
            embed = Embed(title='Game Over', description='Nobody won because everyone junked!', color=0x964B00)
            embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/Coruscant%20Shift.png')
            await self.channel.send(embed=embed, view=EndGameView(self.active_games, self.channel))
            if self in self.active_games:
                self.active_games.remove(self)
            return

        results = '**Final Hands:**\n'
        evaluations = []
        for pl in self.players:
            total = pl.total_value()
            diff = abs(total - self.target_number)
            # number of cards matching silver die suit
            suit_count = sum(1 for c in pl.hand if c.suit == self.target_suit or c.suit == 'Sylop')
            evaluations.append((diff, -suit_count, pl, total))
            results += f'{pl.user.mention}: {pl.get_hand_string()} (Total: {total})\n'

        # Sort by (lowest diff), then (highest suit_count => negative for sorting)
        evaluations.sort(key=lambda x: (x[0], x[1]))
        best = evaluations[0]
        winners = [ev for ev in evaluations if ev[0] == best[0] and ev[1] == best[1]]

        if len(winners) == 1:
            results += f'\n🎉 {winners[0][2].user.mention} wins!'
        else:
            results += '\nIt’s a tie between: ' + ', '.join(w[2].user.mention for w in winners)

        embed = Embed(title='Game Over', description=results, color=0x964B00)
        embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/Coruscant%20Shift.png')
        mentions = ' '.join(pl.user.mention for pl in self.players if 'AIUser' not in type(pl.user).__name__)
        await self.channel.send(content=mentions, embed=embed, view=EndGameView(self.active_games, self.channel))

        if self in self.active_games:
            self.active_games.remove(self)

class PlayTurnView(ui.View):
    '''
    A view with "Play Turn" + "View Rules" buttons.
    '''
    def __init__(self, game_view: CoruscantGameView):
        super().__init__(timeout=None)
        self.game_view = game_view
        self.play_turn_button = PlayTurnButton(game_view)
        self.view_rules_button = CoruscantShiftViewRulesButton()
        self.add_item(self.play_turn_button)
        self.add_item(self.view_rules_button)

class PlayTurnButton(ui.Button):
    '''
    Show the current player's hand ephemeral, letting them confirm or junk.
    '''
    def __init__(self, game_view: CoruscantGameView):
        super().__init__(label='Play Turn', style=ButtonStyle.primary)
        self.game_view = game_view

    async def callback(self, interaction: Interaction) -> None:
        idx = self.game_view.current_player_index
        if 0 <= idx < len(self.game_view.players):
            current_player = self.game_view.players[idx]
        else:
            await interaction.response.send_message('No current player found.', ephemeral=True)
            return

        if interaction.user.id != current_player.user.id:
            await interaction.response.send_message('It\'s not your turn.', ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        title = f'Your Turn | Phase {self.game_view.phase} of {self.game_view.total_phases}'
        desc = f'**Your Hand:** {current_player.get_hand_string()}\n**Total:** {current_player.total_value()}'

        embed, file = await create_embed_with_cards(
            title=title,
            description=desc,
            cards=current_player.hand,
            thumbnail_url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/Coruscant%20Shift.png'
        )

        selection_view = SelectionPhaseView(self.game_view, current_player)
        if file:
            await interaction.followup.send(embed=embed, file=file, view=selection_view, ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, view=selection_view, ephemeral=True)

class SelectionPhaseView(ui.View):
    '''
    Ephemeral view for toggling which cards to keep or junk the entire hand.
    '''
    def __init__(self, game_view: CoruscantGameView, player: Player):
        super().__init__(timeout=None)
        self.game_view = game_view
        self.player = player
        self.selection_state = [True] * len(player.hand)
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        for idx, card in enumerate(self.player.hand):
            label = f'{card} {"✅" if self.selection_state[idx] else "❌"}'
            btn = ui.Button(label=label, style=ButtonStyle.primary)
            btn.callback = self.make_toggle_callback(idx)
            self.add_item(btn)

        confirm_btn = ui.Button(label='Confirm Selection', style=ButtonStyle.success)
        confirm_btn.callback = self.confirm_selection
        self.add_item(confirm_btn)

        junk_btn = ui.Button(label='Junk', style=ButtonStyle.danger)
        junk_btn.callback = self.junk_callback
        self.add_item(junk_btn)

        self.add_item(CoruscantShiftViewRulesButton())

    def make_toggle_callback(self, index: int):
        async def callback(interaction: Interaction):
            if interaction.user.id != self.player.user.id:
                await interaction.response.send_message('Not your selection to make!', ephemeral=True)
                return
            self.selection_state[index] = not self.selection_state[index]
            self.update_buttons()
            await interaction.response.edit_message(view=self)
        return callback

    async def confirm_selection(self, interaction: Interaction):
        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message('Not your turn.', ephemeral=True)
            return

        new_hand = [c for selected, c in zip(self.selection_state, self.player.hand) if selected]
        self.player.hand = new_hand
        while len(self.player.hand) < 5 and self.game_view.deck:
            self.player.draw_card(self.game_view.deck)

        await interaction.response.send_message('Selection confirmed. Your hand is updated.', ephemeral=True)

        self.game_view.current_player_index += 1
        self.stop()
        await self.game_view.proceed_to_next_player()

    async def junk_callback(self, interaction: Interaction):
        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message('Not your turn.', ephemeral=True)
            return

        self.game_view.players.remove(self.player)
        await interaction.response.send_message('You junked your hand.', ephemeral=True)

        if len(self.game_view.players) < 2:
            await self.game_view.end_game()
        else:
            self.stop()
            await self.game_view.proceed_to_next_player()

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message('This is not your selection to make!', ephemeral=True)
            return False
        return True

class EndGameView(ui.View):
    '''
    End-of-game view with 'Play Again' and 'View Rules'.
    '''
    def __init__(self, active_games, channel):
        super().__init__(timeout=None)
        self.active_games = active_games
        self.channel = channel
        self.play_again_clicked = False

        play_again_btn = ui.Button(label='Play Again', style=discord.ButtonStyle.success)
        play_again_btn.callback = self.play_again_callback
        self.add_item(play_again_btn)

        self.add_item(CoruscantShiftViewRulesButton())

    async def play_again_callback(self, interaction: Interaction):
        if self.play_again_clicked:
            await interaction.response.send_message('Play Again is already in progress.', ephemeral=True)
            return
        self.play_again_clicked = True
        for child in self.children:
            if isinstance(child, ui.Button) and child.label == 'Play Again':
                child.disabled = True
        await interaction.response.edit_message(view=self)

        new_game_view = CoruscantGameView(active_games=self.active_games, channel=self.channel)
        new_game_view.message = await self.channel.send('New game lobby created!', view=new_game_view)
        new_game_view.players.append(Player(interaction.user))
        self.active_games.append(new_game_view)

class CoruscantShiftViewRulesButton(ui.Button):
    '''
    Button to display the Coruscant Shift Sabacc rules.
    '''
    def __init__(self):
        super().__init__(label='View Rules', style=ButtonStyle.secondary)

    async def callback(self, interaction: Interaction):
        rules_embed = get_coruscant_shift_rules_embed()
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)