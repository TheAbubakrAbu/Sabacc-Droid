# coruscant_shift.py

import random
import copy
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
    '●': 'circle',
    '▲': 'triangle',
    '■': 'square'
}

class Card:
    '''
    Coruscant Shift card with suit (●, ▲, ■, Sylop) and value (−10..−1, 0, +1..+10).
    locked_in indicates it cannot be unselected in future rounds.
    '''
    def __init__(self, value: int, suit: str, locked_in: bool = False):
        self.value = value
        self.suit = suit
        self.locked_in = locked_in

    def __str__(self):
        if self.suit == 'Sylop':
            return '0'
        sign = '+' if self.value > 0 else ''
        return f'{self.suit} {sign}{self.value}'

    def image_filename(self) -> str:
        if self.suit == 'Sylop':
            return '0.png'
        folder = SUIT_TO_FOLDER.get(self.suit, 'circles')
        return f'''{folder}/{f'+{self.value}' if self.value > 0 else self.value}.png'''

def get_card_image_url(card: Card) -> str:
    base_url = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/corellian_spike/'
    return base_url + quote(card.image_filename())

def download_and_process_image(url: str, width: int, height: int) -> Image.Image:
    try:
        resp = requests.get(url, stream=True, timeout=5)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert('RGBA')
        return img.resize((width, height), Image.LANCZOS)
    except Exception as e:
        logger.error(f'Error processing image from {url}: {e}')
        return None

def combine_card_images(urls: list[str], width: int = 80, height: int = 120, pad: int = 10) -> BytesIO:
    with ThreadPoolExecutor(max_workers=12) as exe:
        futures = [(i, exe.submit(download_and_process_image, u, width, height))
                   for i, u in enumerate(urls)]
        results = []
        for idx, fut in futures:
            results.append((idx, fut.result()))
    results.sort(key=lambda x: x[0])
    images = [img for _, img in results if img is not None]
    if not images:
        raise ValueError('No valid images to combine.')
    total_w = sum(im.width for im in images) + pad * (len(images) - 1)
    max_h = max(im.height for im in images)
    combined = Image.new('RGBA', (total_w, max_h), (255, 255, 255, 0))
    x_off = 0
    for im in images:
        combined.paste(im, (x_off, 0))
        x_off += im.width + pad
    buf = BytesIO()
    combined.save(buf, format='PNG')
    buf.seek(0)
    return buf

class Player:
    def __init__(self, user):
        self.user = user
        self.hand: list[Card] = []

    def draw_card(self, deck: list[Card]):
        if not deck:
            raise ValueError('Deck is empty; cannot draw.')
        self.hand.append(deck.pop())

    def get_hand_string(self) -> str:
        return ' | ' + ' | '.join(str(c) for c in self.hand) + ' |'

    def total_value(self) -> int:
        return sum(c.value for c in self.hand)

class CoruscantGameView(ui.View):
    '''
    A Coruscant Shift multi-round game:
      - Topping up to 5 cards after each round (except after the final round ends).
      - If solo_game=True and there's only one real player, we add Lando Calrissian AI at game end.
      - No extra public embed messages unless it's turn mention or final results mention.
    '''
    def __init__(
        self,
        rounds: int = 2,
        num_cards: int = 5,
        active_games=None,
        channel=None,
        solo_game: bool = False
    ):
        super().__init__(timeout=None)
        self.players: list[Player] = []
        self.rounds = rounds
        self.num_cards = num_cards
        self.current_round = 1
        self.current_player_index = 0
        self.deck: list[Card] = []
        self.game_started = False
        self.game_ended = False

        self.active_games = active_games if active_games else []
        self.channel = channel
        self.message = None

        self.solo_game = solo_game

        self.play_button = ui.Button(label='Play Game', style=ButtonStyle.primary)
        self.leave_button = ui.Button(label='Leave Game', style=ButtonStyle.danger)
        self.start_button = ui.Button(label='Start Game', style=ButtonStyle.success, disabled=True)
        self.rules_button = CoruscantShiftViewRulesButton()

        self.play_button.callback = self.play_callback
        self.leave_button.callback = self.leave_callback
        self.start_button.callback = self.start_callback

        self.add_item(self.play_button)
        self.add_item(self.leave_button)
        self.add_item(self.start_button)
        self.add_item(self.rules_button)

        self.target_number = None
        self.target_suit = None
        self.roll_dice()

    def roll_dice(self):
        gold_faces = [-10, 10, -5, 5, 0, 0]
        silver_faces = ['●', '●', '▲', '▲', '■', '■']
        self.target_number = random.choice(gold_faces)
        self.target_suit = random.choice(silver_faces)

    async def update_lobby(self, interaction: Interaction = None):
        '''
        Updates the lobby embed with current players. 
        (Allowed to send embed here, since it's the game-lobby pre-start.)
        '''
        if not self.players:
            if interaction:
                await self.reset_lobby(interaction)
            return

        desc = f'**Players Joined ({len(self.players)}/8):**\n'
        desc += '\n'.join(p.user.mention for p in self.players)
        desc += '\n'
        if len(self.players) >= 8:
            desc += 'The game lobby is full.'

        desc += (
            f'\n**Game Settings:**\n'
            f'• {self.rounds} rounds\n'
            f'• {self.num_cards} starting cards\n\n'
        )

        if len(self.players) < 2:
            desc += 'Waiting for more players to join...\n'
            desc += 'Click **Start Game** if you want to play with an AI.\n'
        else:
            desc += 'Click **Start Game** to begin!\n'

        embed = Embed(
            title='Coruscant Shift Sabacc Lobby',
            description=desc,
            color=0xAB9032
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/coruscant_shift.png')

        self.start_button.disabled = (len(self.players) < 1 or self.game_started)
        self.play_button.disabled = (len(self.players) >= 8 or self.game_started)

        if interaction:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await self.message.edit(embed=embed, view=self)

    async def reset_lobby(self, interaction: Interaction):
        '''
        Resets the lobby if no players remain, or forcibly.
        '''
        self.players.clear()
        self.deck.clear()
        self.current_round = 1
        self.current_player_index = 0
        self.game_started = False
        self.game_ended = False

        self.play_button.disabled = False
        self.leave_button.disabled = False
        self.start_button.disabled = True
        self.roll_dice()

        desc = (
            'Click **Play Game** to join the game!\n\n'
            f'**Game Settings:**\n'
            f'• {self.rounds} rounds\n'
            f'• {self.num_cards} starting cards\n\n'
            'Once someone has joined, **Start Game** will be enabled.'
        )
        embed = Embed(title='Coruscant Shift Sabacc Lobby', description=desc, color=0xAB9032)
        embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/coruscant_shift.png')
        await interaction.response.edit_message(embed=embed, view=self)

    async def play_callback(self, interaction: Interaction):
        if self.game_started:
            await interaction.response.send_message(
                'The game has already started.', ephemeral=True
            )
            return
        user = interaction.user
        if any(p.user.id == user.id for p in self.players):
            await interaction.response.send_message(
                'You are already in the game.', ephemeral=True
            )
            return
        if len(self.players) >= 8:
            await interaction.response.send_message(
                'Game is full (8 max).', ephemeral=True
            )
            return

        self.players.append(Player(user))
        await self.update_lobby(interaction)

    async def leave_callback(self, interaction: Interaction):
        if self.game_started:
            await interaction.response.send_message(
                'You cannot leave after the game has started.', ephemeral=True
            )
            return
        user = interaction.user
        pl = next((p for p in self.players if p.user.id == user.id), None)
        if pl:
            self.players.remove(pl)
            await self.update_lobby(interaction)
        else:
            await interaction.response.send_message('You are not in the game.', ephemeral=True)

    async def start_callback(self, interaction: Interaction):
        if self.game_started:
            await interaction.response.send_message('The game has already started.', ephemeral=True)
            return
        if interaction.user.id not in [p.user.id for p in self.players]:
            await interaction.response.send_message('Only a player in the lobby can start.', ephemeral=True)
            return
        if not self.players:
            await interaction.response.send_message('No players to start!', ephemeral=True)
            return

        self.game_started = True

        if len(self.players) == 1:
            self.solo_game = True

        self.deck = self.generate_deck()
        for p in self.players:
            p.hand.clear()
            for _ in range(self.num_cards):
                p.draw_card(self.deck)

        self.play_button.disabled = True
        self.leave_button.disabled = True
        self.start_button.disabled = True

        if self.message:
            await self.message.edit(view=self)

        await interaction.response.defer()
        await self.next_turn()

    def generate_deck(self) -> list[Card]:
        suits = ['●', '▲', '■']
        deck = []

        base_deck = []
        for s in suits:
            for val in range(1, 11):
                base_deck.append(Card(val, s))
                base_deck.append(Card(-val, s))
        base_deck.append(Card(0, 'Sylop'))
        base_deck.append(Card(0, 'Sylop'))

        for _ in range(7):
            new_deck = copy.deepcopy(base_deck)
            random.shuffle(new_deck)
            deck.extend(new_deck)

        return deck

    async def next_turn(self):
        '''
        Move to next player's turn, or next round, or end game.
        '''
        if not self.game_started or self.game_ended:
            return

        if self.current_player_index >= len(self.players):
            self.current_round += 1

            if self.current_round > self.rounds:
                await self.end_game()
                return

            for p in self.players:
                for c in p.hand:
                    c.locked_in = True
                while len(p.hand) < self.num_cards and self.deck:
                    p.draw_card(self.deck)

            self.current_player_index = 0

        if self.current_player_index < len(self.players):
            pl = self.players[self.current_player_index]
            await self.announce_turn(pl)

    async def announce_turn(self, player: Player):
        '''
        Announces whose turn it is (mention + embed).
        '''
        desc = f'**Players:**\n'
        desc += '\n'.join(p.user.mention for p in self.players)
        desc += f'\n\n**Round {self.current_round}/{self.rounds}**\n'
        desc += f'It\'s now {player.user.mention}\'s turn.\n'
        desc += 'Click **Play Turn** to proceed.\n\n'
        desc += f'**Target Number:** {self.target_number} | **Target Suit:** {self.target_suit}'

        card_back = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/corellian_spike/card.png'
        card_count = len(player.hand)
        try:
            back_buf = combine_card_images([card_back] * card_count)
        except:
            back_buf = None

        embed = Embed(
            title='Coruscant Shift Sabacc',
            description=desc,
            color=0xAB9032
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/coruscant_shift.png')
        view = TurnView(self)

        if back_buf:
            embed.set_image(url='attachment://combined_cards.png')
            f = discord.File(fp=back_buf, filename='combined_cards.png')
            await self.channel.send(
                content=player.user.mention,
                embed=embed,
                file=f,
                view=view
            )
        else:
            await self.channel.send(
                content=player.user.mention,
                embed=embed,
                view=view
            )

    async def end_game(self):
        '''
        End the game, evaluate final results, mention all non-AI players.
        If solo_game = True and there's only 1 real player, add Lando if not present.

        Pure Sabacc:
        - Exactly 2 cards, both Sylops => auto-win over non-Pure-Sabacc.
        Tie-breakers (if no Pure Sabacc):
        1) closest to target_number (lowest abs diff)
        2) most suit matches
        3) highest total
        4) highest single positive card
        5) otherwise tie
        '''
        if self.game_ended:
            return
        self.game_ended = True

        if self.solo_game:
            if not any(pl.user.name == 'Lando Calrissian AI' for pl in self.players):
                lando_user = type('AIUser', (object,), {
                    'mention': 'Lando Calrissian AI',
                    'name': 'Lando Calrissian AI',
                    'id': -1
                })()
                lando = Player(user=lando_user)
                while len(lando.hand) < self.num_cards and self.deck:
                    lando.draw_card(self.deck)
                self.players.append(lando)

        if not self.players:
            emb = Embed(
                title='Game Over',
                description='Nobody won because everyone junked!',
                color=0xAB9032
            )
            emb.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/coruscant_shift.png')
            emb.set_footer(text='Coruscant Shift Sabacc')
            await self.channel.send(embed=emb, view=EndGameView(self.active_games, self.channel))
            if self in self.active_games:
                self.active_games.remove(self)
            return

        result_text = f'**Target Number:** {self.target_number} | **Target Suit:** {self.target_suit}\n\n'
        result_text += '**Final Hands:**'

        pure_sabacc_players = []
        suit_counts = {}

        for pl in self.players:
            suit_count = sum(1 for c in pl.hand if c.suit == self.target_suit or c.suit == 'Sylop')
            suit_counts[pl] = suit_count

            if len(pl.hand) == 2 and all(c.suit == 'Sylop' for c in pl.hand):
                pure_sabacc_players.append(pl)
                line1 = f'\n- {pl.user.mention}: {pl.get_hand_string()}'
                line2 = f'   - Total: Pure Sabacc (2 Sylops)'
                result_text += f'{line1}\n{line2}\n'
            else:
                total = pl.total_value()
                line1 = f'\n- {pl.user.mention}: {pl.get_hand_string()}'
                line2 = f'   - Total: {total}'
                line3 = f'   - Suit Matches: {suit_count}'
                result_text += f'{line1}\n{line2}\n{line3}'

        if pure_sabacc_players:
            if len(pure_sabacc_players) == 1:
                winner = pure_sabacc_players[0]
                result_text += f'\n\n🎉 {winner.user.mention} wins with a **Pure Sabacc**!'
            else:
                tie_names = ', '.join(pl.user.mention for pl in pure_sabacc_players)
                result_text += f'\n\nIt\'s a tie between: {tie_names} (all **Pure Sabacc**)'
        else:
            evals = []
            for pl in self.players:
                total = pl.total_value()
                diff = abs(total - self.target_number)
                sc = suit_counts[pl]

                largest_pos_card = max([0] + [c.value for c in pl.hand if c.value > 0])

                evals.append((diff, -sc, -total, -largest_pos_card, pl))

            evals.sort(key=lambda x: (x[0], x[1], x[2], x[3]))
            
            best_key = evals[0][:4]
            winners = [e for e in evals if e[:4] == best_key]

            if len(winners) == 1:
                wpl = winners[0][4]
                result_text += f'\n\n🎉 {wpl.user.mention} wins!'
            else:
                tie_names = ', '.join(e[4].user.mention for e in winners)
                result_text += f'\n\nIt\'s a tie between: {tie_names}'

        emb = Embed(title='Game Over', description=result_text, color=0xAB9032)
        emb.set_thumbnail(
            url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/coruscant_shift.png'
        )
        emb.set_footer(text='Coruscant Shift Sabacc')

        mention_line = ' '.join(
            pl.user.mention for pl in self.players if 'AIUser' not in type(pl.user).__name__
        )
        await self.channel.send(content=mention_line, embed=emb, view=EndGameView(self.active_games, self.channel))

        if self in self.active_games:
            self.active_games.remove(self)

class TurnView(ui.View):
    '''
    Public ephemeral-later view with Play Turn + View Rules only
    '''
    def __init__(self, game_view: CoruscantGameView):
        super().__init__(timeout=None)
        self.game_view = game_view
        self.add_item(TurnButton(game_view))
        self.add_item(CoruscantShiftViewRulesButton())

class TurnButton(ui.Button):
    '''
    Play Turn ephemeral: shows your hand, toggles, confirm, junk, etc.
    '''
    def __init__(self, game_view: CoruscantGameView):
        super().__init__(label='Play Turn', style=ButtonStyle.primary)
        self.game_view = game_view

    async def callback(self, interaction: Interaction):
        if not self.game_view.game_started or self.game_view.game_ended:
            await interaction.response.send_message('Game not active or invalid turn.', ephemeral=True)
            return
        idx = self.game_view.current_player_index
        if idx < 0 or idx >= len(self.game_view.players):
            await interaction.response.send_message('No current player to act.', ephemeral=True)
            return
        player = self.game_view.players[idx]
        if player.user.id != interaction.user.id:
            await interaction.response.send_message('It is not your turn.', ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        embed, file = await ephemeral_hand_embed(player, self.game_view, None)
        view = EphemeralSelectView(self.game_view, player)
        if file:
            await interaction.followup.send(embed=embed, file=file, view=view, ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

async def ephemeral_hand_embed(player: Player, game_view: CoruscantGameView, toggles: list[bool] = None):
    '''
    Build ephemeral embed for the player's toggles, showing partial or full card images.
    If a card is locked_in, we do not show a checkmark and do not allow unselecting.
    Also forbid the final scenario of 0 cards.
    '''
    if toggles is None:
        toggles = [True for _ in player.hand]

    image_urls = []
    kept_cards = []
    for flag, c in zip(toggles, player.hand):
        if flag:
            image_urls.append(get_card_image_url(c))
            kept_cards.append(c)
        else:
            image_urls.append('https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/corellian_spike/card.png')

    total = sum(c.value for c in kept_cards)
    suit_matches = sum(1 for c in kept_cards if c.suit == game_view.target_suit or c.suit == 'Sylop')

    desc = (
        f'**Target Number:** {game_view.target_number} | **Target Suit:** {game_view.target_suit}\n\n'
        f'**Your Cards:** {player.get_hand_string()}\n'
        f'**Total:** {total} | **Suit Matches:** {suit_matches}\n\n'
        'Toggle any card to remove or bring it back. Any card you select cannot be unselected in future rounds.'
    )

    try:
        buf = combine_card_images(image_urls)
        emb = Embed(
            title=f'Your Turn | Round {game_view.current_round}/{game_view.rounds}',
            description=desc,
            color=0xAB9032
        )
        emb.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/coruscant_shift.png')
        emb.set_image(url='attachment://combined_cards.png')
        file = discord.File(fp=buf, filename='combined_cards.png')
        return emb, file
    except Exception as e:
        logger.error(f'ephemeral_hand_embed: {e}')
        emb = Embed(
            title='Your Turn',
            description=desc,
            color=0xAB9032
        )
        emb.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/coruscant_shift.png')
        return emb, None

class EphemeralSelectView(ui.View):
    '''
    The ephemeral view letting a user toggle each card or junk, confirm, etc.
    We keep a local toggles array that we re-render each time.
    If a card is locked_in, we do not let you unselect it.
    Also cannot reduce total selected to 0.
    '''
    def __init__(self, game_view: CoruscantGameView, player: Player):
        super().__init__(timeout=None)
        self.game_view = game_view
        self.player = player
        self.toggles = [True] * len(player.hand)
        self.build_buttons()

    def build_buttons(self):
        self.clear_items()

        for idx, c in enumerate(self.player.hand):
            if c.locked_in:
                label = f'{str(c)}'
                btn = ui.Button(label=label, style=ButtonStyle.secondary)
                btn.disabled = False
                btn.callback = self.make_locked_callback()
            else:
                if self.toggles[idx]:
                    label = f'{str(c)} ✅'
                else:
                    label = f'{str(c)} ❌'
                btn = ui.Button(label=label, style=ButtonStyle.primary)
                btn.callback = self.make_toggle_callback(idx)

            self.add_item(btn)

        confirm = ui.Button(label='Confirm Selection', style=ButtonStyle.success)
        confirm.callback = self.confirm_callback
        self.add_item(confirm)

        junk = ui.Button(label='Junk', style=ButtonStyle.danger)
        junk.callback = self.junk_callback
        self.add_item(junk)

    def make_locked_callback(self):
        async def callback(interaction: Interaction):
            if interaction.user.id != self.player.user.id:
                await interaction.response.send_message('Not your selection to make!', ephemeral=True)
                return
            await interaction.response.send_message(
                'You cannot unselect cards locked in from previous rounds.', ephemeral=True
            )
        return callback

    def make_toggle_callback(self, i: int):
        async def callback(interaction: Interaction):
            if interaction.user.id != self.player.user.id:
                await interaction.response.send_message('Not your selection to make!', ephemeral=True)
                return

            selected_count = sum(1 for x in self.toggles if x)
            if self.toggles[i]:
                if selected_count == 1:
                    await interaction.response.send_message('You cannot have 0 cards.', ephemeral=True)
                    return

            self.toggles[i] = not self.toggles[i]

            emb, file = await ephemeral_hand_embed(self.player, self.game_view, self.toggles)
            self.build_buttons()
            if file:
                await interaction.response.edit_message(embed=emb, attachments=[file], view=self)
            else:
                await interaction.response.edit_message(embed=emb, attachments=[], view=self)

        return callback

    async def confirm_callback(self, interaction: Interaction):
        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message('Not your turn to confirm!', ephemeral=True)
            return

        final_cards = []
        for keep, c in zip(self.toggles, self.player.hand):
            if keep:
                final_cards.append(c)
        self.player.hand = final_cards

        total = sum(c.value for c in self.player.hand)
        embed = Embed(
            title=f'Selection Confirmed | Round {self.game_view.current_round}/{self.game_view.rounds}',
            description=(
                f'**You chose:** {self.player.get_hand_string()}\n'
                f'**Total:** {total}\n\n'
                'Selection locked in for this round.'
            ),
            color=0xAB9032
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/coruscant_shift.png')

        efile = None
        if self.player.hand:
            try:
                fbuf = combine_card_images([get_card_image_url(c) for c in self.player.hand])
                embed.set_image(url='attachment://chosen.png')
                efile = discord.File(fp=fbuf, filename='chosen.png')
            except Exception as e:
                logger.error(f'confirm_callback image error: {e}')

        for ch in self.children:
            ch.disabled = True

        await interaction.response.edit_message(embed=embed, view=None, attachments=[efile] if efile else [])

        self.game_view.current_player_index += 1
        self.stop()
        await self.game_view.next_turn()

    async def junk_callback(self, interaction: Interaction):
        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message('Not your turn to junk!', ephemeral=True)
            return

        self.game_view.players.remove(self.player)

        total = sum(c.value for c in self.player.hand)
        desc = (
            'You have given up and are out of the game.'
        )
        embed = Embed(
            title=f'You Chose to Junk | Round {self.game_view.current_round}/{self.game_view.rounds}',
            description=desc,
            color=0xAB9032
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/coruscant_shift.png')

        efile = None
        if self.player.hand:
            try:
                fbuf = combine_card_images([get_card_image_url(c) for c in self.player.hand])
                embed.set_image(url='attachment://junked.png')
                efile = discord.File(fp=fbuf, filename='junked.png')
            except Exception as e:
                logger.error(f'junk_callback image error: {e}')

        for ch in self.children:
            ch.disabled = True
        await interaction.response.edit_message(embed=embed, view=None, attachments=[efile] if efile else [])

        if len(self.game_view.players) < 2:
            await self.game_view.end_game()
        else:
            self.stop()
            await self.game_view.next_turn()

    async def interaction_check(self, interaction: Interaction) -> bool:
        return (interaction.user.id == self.player.user.id)

class EndGameView(ui.View):
    '''
    End-of-game with Play Again + View Rules.
    No extra mention is done here (the mention was in end_game).
    '''
    def __init__(self, active_games, channel):
        super().__init__(timeout=None)
        self.active_games = active_games
        self.channel = channel
        self.clicked = False

        again = ui.Button(label='Play Again', style=ButtonStyle.success)
        again.callback = self.play_again
        self.add_item(again)

        self.add_item(CoruscantShiftViewRulesButton())

    async def play_again(self, interaction: Interaction):
        if self.clicked:
            await interaction.response.send_message('Play Again is already in progress.', ephemeral=True)
            return
        self.clicked = True
        for ch in self.children:
            if isinstance(ch, ui.Button) and ch.label == 'Play Again':
                ch.disabled = True

        await interaction.response.edit_message(view=self)

        new_g = CoruscantGameView(
            rounds=2,
            num_cards=5,
            active_games=self.active_games,
            channel=self.channel
        )
        new_g.message = await self.channel.send('New game lobby created!', view=new_g)
        new_g.players.append(Player(interaction.user))
        await new_g.update_lobby()
        self.active_games.append(new_g)

class CoruscantShiftViewRulesButton(ui.Button):
    '''
    Button to show rules ephemeral
    '''
    def __init__(self):
        super().__init__(label='View Rules', style=ButtonStyle.secondary)

    async def callback(self, interaction: Interaction):
        embed = get_coruscant_shift_rules_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)