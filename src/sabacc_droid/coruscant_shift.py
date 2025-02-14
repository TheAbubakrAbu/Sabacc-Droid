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

SUITS = ['Circles', 'Triangles', 'Squares']

def roll_gold_die() -> int:
    '''
    Returns a random face from the gold die (-10, 10, -5, 5, 0, 0).
    '''
    return random.choice([-10, 10, -5, 5, 0, 0])

def roll_silver_die() -> str:
    '''
    Returns a random suit from the silver die (Circles, Triangles, Squares).
    '''
    return random.choice(['Circles', 'Circles', 'Triangles', 'Triangles', 'Squares', 'Squares'])

def get_card_image_urls(cards: list[int]) -> list[str]:
    '''
    Generates image URLs for each integer card value.
    Positive values are prefixed with '+', negative as-is, zero as '0'.
    '''
    base_url = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/corellian_spike/'
    return [f'{base_url}{quote(f"+{val}" if val > 0 else str(val))}.png' for val in cards]

def download_and_process_image(url: str, resize_width: int, resize_height: int) -> Image.Image:
    '''
    Downloads and resizes an image to RGBA. Returns None on failure.
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

def combine_card_images(
    card_image_urls: list[str],
    resize_width: int = 80,
    resize_height: int = 120,
    padding: int = 10
) -> BytesIO:
    '''
    Combines multiple card images horizontally into a single PNG. Returns BytesIO.
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

async def create_embed_with_cards(
    title: str,
    description: str,
    cards: list[int],
    thumbnail_url: str,
    color: int = 0x964B00
) -> tuple[Embed, discord.File]:
    '''
    Creates an embed with images for the given card values.
    Returns (Embed, File) if images are combined successfully, else just (Embed, None).
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

class CoruscantPlayer:
    '''
    Represents a player, storing a Discord user and their hand of (value, suit) cards.
    '''

    def __init__(self, user):
        self.user = user
        self.cards: list[tuple[int, str]] = []

    def draw_card(self, deck: list[tuple[int, str]]) -> None:
        '''
        Draws one card from the deck and adds it to the player's hand.
        Raises ValueError if the deck is empty.
        '''
        if not deck:
            raise ValueError('The deck is empty. Cannot draw more cards.')
        self.cards.append(deck.pop())

    def get_cards_string(self) -> str:
        '''
        Returns a string of the player's cards, e.g. '| +5 (Triangles) | -2 (Squares) |'.
        '''
        out = []
        for val, suit in self.cards:
            sign_val = f'+{val}' if val > 0 else str(val)
            out.append(f'{sign_val} ({suit})')
        return ' | ' + ' | '.join(out) + ' |'

    def get_values_only(self) -> list[int]:
        '''
        Returns only the integer values of each card, for image display.
        '''
        return [val for val, _ in self.cards]

    def get_total(self) -> int:
        '''
        Returns the sum of the player's card values.
        '''
        return sum(val for val, _ in self.cards)

    def count_suit(self, suit: str) -> int:
        '''
        Returns how many cards match the given suit.
        '''
        return sum(1 for val, s in self.cards if s == suit)

class CoruscantGameView(ui.View):
    '''
    Manages a Coruscant Shift Sabacc game, including players, deck, rounds, dice, and game flow.
    '''

    def __init__(self, active_games=None, channel=None):
        super().__init__(timeout=None)
        self.players: list[CoruscantPlayer] = []
        self.game_started = False
        self.current_player_index = -1
        self.deck: list[tuple[int, str]] = []
        self.round = 1
        self.total_rounds = 2
        self.game_ended = False
        self.active_games = active_games if active_games else []
        self.channel = channel
        self.current_message = None
        self.message = None
        self.target_number = None
        self.target_suit = None

        self.view_rules_button = CoruscantViewRulesButton()
        self.play_game_button = ui.Button(label='Play Game', style=ButtonStyle.primary)
        self.leave_game_button = ui.Button(label='Leave Game', style=ButtonStyle.danger)
        self.start_game_button = ui.Button(label='Start Game', style=ButtonStyle.success, disabled=True)

        self.play_game_button.callback = self.play_game_callback
        self.leave_game_button.callback = self.leave_game_callback
        self.start_game_button.callback = self.start_game_callback

        self.add_item(self.play_game_button)
        self.add_item(self.leave_game_button)
        self.add_item(self.start_game_button)
        self.add_item(self.view_rules_button)

    async def play_game_callback(self, interaction: Interaction):
        user = interaction.user
        if self.game_started:
            await interaction.response.send_message('The game has already started.', ephemeral=True)
            return
        if any(p.user.id == user.id for p in self.players):
            await interaction.response.send_message('You are already in the game!', ephemeral=True)
            return
        if len(self.players) >= 8:
            await interaction.response.send_message('The maximum number of players (8) has been reached.', ephemeral=True)
            return
        self.players.append(CoruscantPlayer(user))
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
            await interaction.response.send_message('Only a player in the game can start it.', ephemeral=True)
            return
        if len(self.players) < 1:
            await interaction.response.send_message('Not enough players to start.', ephemeral=True)
            return

        self.game_started = True
        self.start_game_button.disabled = True
        self.play_game_button.disabled = True
        self.leave_game_button.disabled = True

        self.target_number = roll_gold_die()
        self.target_suit = roll_silver_die()

        self.deck = self.generate_deck()
        random.shuffle(self.players)
        random.shuffle(self.deck)

        for player in self.players:
            player.cards.clear()
            for _ in range(5):
                player.draw_card(self.deck)

        dice_msg = (
            f'**Gold Die (Target Number):** {self.target_number}\n'
            f'**Silver Die (Target Suit):** {self.target_suit}'
        )
        embed = Embed(
            title='Coruscant Shift Begins!',
            description=f'{dice_msg}\n\nRound 1: Each player will now select or discard cards, then draw replacements.\n',
            color=0x964B00
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/Sabacc/gh-pages/images/logo.png')
        await interaction.response.edit_message(embed=embed, view=None)
        await self.proceed_to_next_player()

    async def update_lobby_embed(self, interaction=None):
        if len(self.players) == 0:
            await self.reset_lobby(interaction)
            return
        desc = f'**Players Joined ({len(self.players)}/8):**\n'
        desc += '\n'.join(p.user.mention for p in self.players)
        desc += '\n\nClick **Start Game** to begin the Coruscant Shift!'

        embed = Embed(title='Coruscant Shift Game Lobby', description=desc, color=0x964B00)
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')
        self.start_game_button.disabled = (len(self.players) < 1 or self.game_started)
        self.play_game_button.disabled = (len(self.players) >= 8 or self.game_started)

        if interaction:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await self.message.edit(embed=embed, view=self)

    async def reset_lobby(self, interaction: Interaction):
        self.game_started = False
        self.players.clear()
        self.deck.clear()
        self.round = 1
        self.game_ended = False
        self.play_game_button.disabled = False
        self.leave_game_button.disabled = False
        self.start_game_button.disabled = True

        embed = Embed(
            title='Coruscant Shift Game Lobby',
            description='Click **Play Game** to join!\n\nWe will start once we have at least 1 player.',
            color=0x964B00
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')
        await interaction.response.edit_message(embed=embed, view=self)

    def generate_deck(self) -> list[tuple[int, str]]:
        '''
        Builds a 62-card deck: 3 suits * 20 cards each (+1..+10, -1..-10), plus 2 zero cards.
        '''
        deck = []
        for suit in SUITS:
            for val in range(1, 11):
                deck.append((val, suit))
            for val in range(-1, -11, -1):
                deck.append((val, suit))
        deck.append((0, 'Sylop'))
        deck.append((0, 'Sylop'))
        return deck

    async def proceed_to_next_player(self):
        if self.game_ended:
            return
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        if self.current_player_index == 0:
            self.round += 1
            if self.round > self.total_rounds:
                await self.end_game()
                return
            else:
                await self.channel.send(f'**Starting Round {self.round}** — Make your final selections!')

        current_player = self.players[self.current_player_index]
        card_count = len(current_player.cards)
        desc = (
            'Players in game:\n' +
            '\n'.join(p.user.mention for p in self.players) +
            f'\n\n**Round {self.round} of {self.total_rounds}**\n'
            f"It's {current_player.user.mention}'s turn! Click **Play Turn** to proceed."
        )

        card_back = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/corellian_spike/card.png'
        card_urls = [card_back] * card_count
        embed = Embed(title='Coruscant Shift', description=desc, color=0x964B00)
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')

        turn_view = CoruscantPlayTurnView(self)
        try:
            image_bytes = combine_card_images(card_urls)
            embed.set_image(url='attachment://combined_cards.png')
            file = discord.File(fp=image_bytes, filename='combined_cards.png')
            await self.channel.send(content=current_player.user.mention, embed=embed, file=file, view=turn_view)
        except Exception as e:
            logger.error(f'Failed to combine card images: {e}')
            await self.channel.send(content=current_player.user.mention, embed=embed, view=turn_view)

    async def end_game(self):
        if self.game_ended:
            return
        self.game_ended = True
        results = []
        for player in self.players:
            total = player.get_total()
            dist = abs(total - self.target_number)
            suit_count = player.count_suit(self.target_suit)
            results.append((dist, suit_count, player))
        results.sort(key=lambda x: (x[0], -x[1]))

        final_summary = '**Final Hands:**\n'
        for _, _, p in results:
            final_summary += f'{p.user.mention}: {p.get_cards_string()} (Total: {p.get_total()})\n'

        winner_dist, winner_suit_count, winner_player = results[0]
        winners = [r for r in results if r[0] == winner_dist and r[1] == winner_suit_count]

        if len(winners) == 1:
            final_summary += (
                f'\n**Winner:** {winner_player.user.mention}\n'
                f'Closest to {self.target_number}, with {winner_suit_count} card(s) in {self.target_suit}!\n'
            )
        else:
            tie_names = ', '.join(w[2].user.mention for w in winners)
            final_summary += f'\n**It\'s a tie** between {tie_names}!\n'

        embed = Embed(
            title='Game Over — Coruscant Shift',
            description=(
                f'**Target Number:** {self.target_number} | '
                f'**Target Suit:** {self.target_suit}\n\n{final_summary}'
            ),
            color=0x964B00
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')
        mentions = ' '.join(p.user.mention for p in self.players)
        view = CoruscantEndGameView(self.channel, self.active_games)
        await self.channel.send(content=mentions, embed=embed, view=view)

        if self in self.active_games:
            self.active_games.remove(self)

class CoruscantEndGameView(ui.View):
    '''
    Shown at the end of the game, allowing a new lobby or viewing rules.
    '''

    def __init__(self, channel, active_games):
        super().__init__(timeout=None)
        self.channel = channel
        self.active_games = active_games
        self.play_again_clicked = False

        self.play_again_button = ui.Button(label='Play Again', style=ButtonStyle.success)
        self.play_again_button.callback = self.play_again
        self.add_item(self.play_again_button)

        self.view_rules_button = CoruscantViewRulesButton()
        self.add_item(self.view_rules_button)

    async def play_again(self, interaction: Interaction):
        if self.play_again_clicked:
            await interaction.response.send_message('A new lobby is already being created!', ephemeral=True)
            return
        self.play_again_clicked = True
        self.play_again_button.disabled = True
        await interaction.response.edit_message(view=self)

        new_game_view = CoruscantGameView(active_games=self.active_games, channel=self.channel)
        new_game_view.message = await self.channel.send('New Coruscant Shift game lobby created!', view=new_game_view)
        self.active_games.append(new_game_view)

class CoruscantPlayTurnView(ui.View):
    '''
    Shows a button for the current player to view their hand and a button to view rules.
    '''

    def __init__(self, game_view: CoruscantGameView):
        super().__init__(timeout=None)
        self.game_view = game_view
        self.play_turn_button = CoruscantPlayTurnButton(game_view)
        self.view_rules_button = CoruscantViewRulesButton()
        self.add_item(self.play_turn_button)
        self.add_item(self.view_rules_button)

class CoruscantPlayTurnButton(ui.Button):
    '''
    Shows the current player's hand and possible actions (draw, discard, stand, junk).
    '''

    def __init__(self, game_view: CoruscantGameView):
        super().__init__(label='Play Turn', style=ButtonStyle.primary)
        self.game_view = game_view

    async def callback(self, interaction: Interaction):
        current_player = self.game_view.players[self.game_view.current_player_index]
        if interaction.user.id != current_player.user.id:
            await interaction.response.send_message('It\'s not your turn.', ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        title = f'Your Turn | Round {self.game_view.round} of {self.game_view.total_rounds}'
        desc = (
            f'**Your Hand:** {current_player.get_cards_string()}\n'
            f'**Total:** {current_player.get_total()}\n\n'
            'Perform an action below (Draw, Discard, etc.) or Stand when ready.'
        )
        embed, file = await create_embed_with_cards(
            title=title,
            description=desc,
            cards=current_player.get_values_only(),
            thumbnail_url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png'
        )
        view = CoruscantTurnView(self.game_view, current_player)
        if file:
            await interaction.followup.send(embed=embed, file=file, view=view, ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

class CoruscantTurnView(ui.View):
    '''
    Basic turn actions: Draw, Discard, Stand, Junk.
    '''

    def __init__(self, game_view: CoruscantGameView, player: CoruscantPlayer):
        super().__init__(timeout=None)
        self.game_view = game_view
        self.player = player

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message('It\'s not your turn.', ephemeral=True)
            return False
        return True

    @ui.button(label='Draw Card', style=ButtonStyle.primary)
    async def draw_button(self, interaction: Interaction, button: ui.Button):
        try:
            self.player.draw_card(self.game_view.deck)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return
        await self.finish_turn(interaction, 'Drew a Card')

    @ui.button(label='Discard Card', style=ButtonStyle.secondary)
    async def discard_button(self, interaction: Interaction, button: ui.Button):
        if len(self.player.cards) <= 1:
            await interaction.response.send_message('You cannot discard when you have only one card!', ephemeral=True)
            return
        await interaction.response.defer()
        select_view = CoruscantCardSelectView(self, 'discard')
        embed = Embed(
            title='Discard a Card',
            description=(
                f'**Your Hand:** {self.player.get_cards_string()}\n'
                'Select which card to discard.'
            ),
            color=0x964B00
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')
        await interaction.followup.send(embed=embed, view=select_view, ephemeral=True)

    @ui.button(label='Stand', style=ButtonStyle.success)
    async def stand_button(self, interaction: Interaction, button: ui.Button):
        await self.finish_turn(interaction, 'Stood Pat')

    @ui.button(label='Junk', style=ButtonStyle.danger)
    async def junk_button(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer()
        self.game_view.players.remove(self.player)
        if len(self.game_view.players) < 1:
            await self.game_view.end_game()
            return
        embed = Embed(
            title='You Junked Your Hand',
            description='You have left the game!',
            color=0x964B00
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')
        await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
        self.stop()
        await self.game_view.proceed_to_next_player()

    async def finish_turn(self, interaction: Interaction, action_taken: str):
        await interaction.response.defer()
        title = f'You {action_taken} | Round {self.game_view.round} of {self.game_view.total_rounds}'
        desc = (
            f'**Your Hand:** {self.player.get_cards_string()}\n'
            f'**Total:** {self.player.get_total()}'
        )
        embed, file = await create_embed_with_cards(
            title=title,
            description=desc,
            cards=self.player.get_values_only(),
            thumbnail_url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png'
        )
        if file:
            await interaction.followup.edit_message(interaction.message.id, embed=embed, attachments=[file], view=None)
        else:
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
        self.stop()
        await self.game_view.proceed_to_next_player()

class CoruscantCardSelectView(ui.View):
    '''
    Allows a player to choose which card to discard or replace.
    '''

    def __init__(self, turn_view: CoruscantTurnView, action: str):
        super().__init__(timeout=None)
        self.turn_view = turn_view
        self.game_view = turn_view.game_view
        self.player = turn_view.player
        self.action = action
        self.add_card_buttons()

    def add_card_buttons(self):
        for idx, (val, suit) in enumerate(self.player.cards):
            label = f'{("+" if val > 0 else "")}{val} ({suit})'
            btn = ui.Button(label=label, style=ButtonStyle.primary)
            btn.callback = self.make_callback(idx)
            self.add_item(btn)
            if len(self.children) >= 25:
                break
        go_back = ui.Button(label='Go Back', style=ButtonStyle.secondary)
        go_back.callback = self.go_back_callback
        self.add_item(go_back)

    def make_callback(self, idx: int):
        async def callback(interaction: Interaction):
            if self.action == 'discard':
                if len(self.player.cards) <= 1:
                    await interaction.response.send_message('Cannot discard the last card.', ephemeral=True)
                    return
                discarded = self.player.cards.pop(idx)
                title = f'You Discarded {discarded[0]} ({discarded[1]})'
                desc = (
                    f'**Your Hand:** {self.player.get_cards_string()}\n'
                    f'**Total:** {self.player.get_total()}'
                )
            else:
                title = 'Unknown action'
                desc = 'No valid action performed.'
            embed, file = await create_embed_with_cards(
                title=title,
                description=desc,
                cards=self.player.get_values_only(),
                thumbnail_url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png'
            )
            await interaction.response.edit_message(embed=embed, attachments=[file] if file else None, view=None)
            self.stop()
            self.turn_view.stop()
            await self.game_view.proceed_to_next_player()
        return callback

    async def go_back_callback(self, interaction: Interaction):
        await interaction.response.defer()
        await self.turn_view.finish_turn(interaction, "didn't discard (Go Back)")

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message('Not your selection to make!', ephemeral=True)
            return False
        return True

class CoruscantViewRulesButton(ui.Button):
    '''
    Shows the Coruscant Shift Sabacc rules as an ephemeral embed.
    '''

    def __init__(self):
        super().__init__(label='View Rules', style=ButtonStyle.secondary)

    async def callback(self, interaction: Interaction):
        rules_embed = get_coruscant_shift_rules_embed()
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)