# kessel.py
#
# Kessel Sabacc, as seen in Star Wars Outlaws. Every hand is exactly one Sand
# (positive) card and one Blood (negative) card, aiming for 0. Impostors get
# their value from two dice at the end; a Sylop copies the other card.

from __future__ import annotations

import asyncio
import itertools
import random
from dataclasses import dataclass
from functools import lru_cache

import discord
from discord import ButtonStyle, Interaction

import cards
import game
from game import Deck, Game, Player, Settings, notice, reply_safely
from theme import Components, button, icon, images, plural, signed

decks = {1: 'Sand', -1: 'Blood'}
deck_icons = {1: icon.sand, -1: icon.blood}


@dataclass(frozen=True, slots=True)
class Card:
    sign: int  # +1 for Sand, -1 for Blood
    value: int = 0  # 1 to 6 for number cards
    kind: str = 'number'  # 'number', 'impostor', or 'sylop'

    def mark(self) -> str:
        return '+' if self.sign > 0 else '-'

    def label(self, resolved: int | None = None) -> str:
        if self.kind == 'number':
            return signed(self.sign * self.value)
        symbol = self.mark() + ('Ψ' if self.kind == 'impostor' else 'Ø')
        return symbol if resolved is None else f'{symbol}/{signed(resolved)}'

    def face(self) -> str:
        return f'kessel/{self.mark()}{self.value if self.kind == "number" else self.kind}.png'


def kessel_deck(sign: int) -> list[Card]:
    '''
    22 cards: 1 to 6 three times each, three Impostors, and one Sylop.
    '''

    return [Card(sign, value) for value in range(1, 7) for _ in range(3)] + [Card(sign, kind='impostor')] * 3 + [Card(sign, kind='sylop')]


@lru_cache(maxsize=512)
def expected_miss(sand: Card, blood: Card) -> float:
    '''
    How far from 0 a hand ends up on average, for Lando: every Impostor
    takes the better of its two dice, and a Sylop always makes 0.
    '''

    if 'sylop' in (sand.kind, blood.kind):
        return 0.0

    def rolls(card: Card) -> list[list[int]]:
        if card.kind == 'number':
            return [[card.sign * card.value]]
        return [[card.sign * first, card.sign * second] for first in range(1, 7) for second in range(1, 7)]

    outcomes = [min(abs(s + b) for s in sand_choices for b in blood_choices)
                for sand_choices in rolls(sand) for blood_choices in rolls(blood)]
    return sum(outcomes) / len(outcomes)


legend = {
    'impostor': 'Ψ is an **Impostor**: its value comes from two dice at the end of the game.',
    'sylop': 'Ø is a **Sylop**: it copies the value of the other card.',
}


class Kessel(Game):
    key = 'kessel'
    name = 'Kessel'
    icon = icon.kessel
    color = 0x7F3335
    thumbnail = images + 'kessel.png'
    footer = 'As seen in Star Wars Outlaws'
    defaults = Settings(rounds=3, cards=2)
    limits = {'rounds': (1, 10)}

    @classmethod
    def settings_lines(cls, settings: Settings) -> list[str]:
        return [plural(settings.rounds, 'round'), 'Every hand is one Sand card and one Blood card']

    def deal(self) -> None:
        self.decks = {1: Deck(lambda: kessel_deck(1)), -1: Deck(lambda: kessel_deck(-1))}
        self.pending: Card | None = None  # a card drawn this turn, before the player picks one to keep
        self.rolls: dict[int, dict[int, tuple[int, int]]] = {}
        self.dice_messages: dict[int, object] = {}
        self.note = ''
        for player in self.players:
            player.hand = [self.decks[1].draw(), self.decks[-1].draw()]
            player.chosen = {}

    # Values -----------------------------------------------------------------

    def values(self, player: Player) -> list[int | None]:
        '''
        The Sand and Blood values, with Impostors as chosen (None until then)
        and Sylops copying the other card.
        '''

        values = [card.sign * card.value if card.kind == 'number' else player.chosen.get(card.sign) if card.kind == 'impostor' else None
                  for card in player.hand]
        sylops = [index for index, card in enumerate(player.hand) if card.kind == 'sylop']
        if len(sylops) == 2:
            return [0, 0]
        if sylops and values[1 - sylops[0]] is not None:
            values[sylops[0]] = -values[1 - sylops[0]]
        return values

    def revealed(self) -> bool:
        return self.phase in ('ending', 'over')

    def labels(self, player: Player) -> list[str]:
        values = self.values(player) if self.revealed() else [None, None]
        return [card.label(value if card.kind != 'number' else None) for card, value in zip(player.hand, values)]

    def faces(self, player: Player) -> list[str]:
        return [card.face() for card in player.hand]

    def backs(self, player: Player) -> list[str]:
        return ['kessel/+card.png', 'kessel/-card.png']

    def total(self, player: Player) -> str:
        if any(card.kind == 'sylop' for card in player.hand):
            return '0'  # a Sylop always cancels the other card
        values = self.values(player)
        return '?' if None in values else signed(sum(values))

    def standing(self, player: Player) -> str:
        if not self.revealed() and any(card.kind == 'impostor' for card in player.hand):
            return '**Depends on the Impostor dice**'
        name = self.score(player)[1]
        return f'**{name}**' + (f', {abs(sum(self.values(player)))} away from 0' if name == 'Nulrhek' else '')

    def hand_fields(self, player: Player) -> list[tuple]:
        kinds = {card.kind for card in player.hand + ([self.pending] if self.pending else [])}
        lines = [text for kind, text in legend.items() if kind in kinds]
        return [('Legend', '\n'.join(lines), False)] if lines else []

    def result_note(self) -> str:
        kinds = {card.kind for player in self.players for card in player.hand}
        return '\n'.join(text for kind, text in legend.items() if kind in kinds)

    # Turns ------------------------------------------------------------------

    def turn_buttons(self, player: Player) -> list[discord.ui.Button]:
        if self.pending is not None:
            return self.keep_buttons(player)
        return [
            button(icon.sand, 'Draw Sand', self.id_for('draw', 'sand'), ButtonStyle.primary),
            button(icon.blood, 'Draw Blood', self.id_for('draw', 'blood'), ButtonStyle.danger),
            button(icon.stand, 'Stand', self.id_for('stand'), ButtonStyle.success),
            button(icon.junk, 'Junk', self.id_for('junk'), ButtonStyle.danger),
        ]

    def keep_buttons(self, player: Player) -> list[discord.ui.Button]:
        sign = self.pending.sign
        old = player.hand[0 if sign > 0 else 1]
        style = ButtonStyle.primary if sign > 0 else ButtonStyle.danger
        return [
            discord.ui.Button(emoji=deck_icons[sign], label=f'Keep {old.label()}', custom_id=self.id_for('keep', 'old'), style=style),
            discord.ui.Button(emoji=deck_icons[sign], label=f'Keep {self.pending.label()}', custom_id=self.id_for('keep', 'new'), style=style),
        ]

    def keep_move(self, player: Player, card: Card, keep_new: bool) -> str:
        '''
        Keeps either the drawn card or the old one, discards the other, and
        returns the game log line.
        '''

        index = 0 if card.sign > 0 else 1
        old = player.hand[index]
        if keep_new:
            player.hand[index] = card
        dropped = old if keep_new else card
        self.decks[card.sign].discard(dropped)
        return f'{deck_icons[card.sign]} {player.user.mention} draws from the {decks[card.sign]} deck and discards `{dropped.label()}`.'

    async def act(self, it: Interaction, player: Player, action: str, choice: str) -> None:
        if action == 'draw' and choice in ('sand', 'blood'):
            if self.pending is None:
                self.pending = self.decks[1 if choice == 'sand' else -1].draw()
            card = self.pending
            special = {'impostor': ' You will roll for its value at the end of the game.',
                       'sylop': ' It copies the value of your other card.'}.get(card.kind, '')
            old = player.hand[0 if card.sign > 0 else 1]
            await self.show_hand(it, player, 'Keep a Card',
                                 f'You drew `{card.label()}` from the {decks[card.sign]} deck.{special} Keep it, or keep `{old.label()}`?',
                                 self.keep_buttons(player), faces=self.faces(player) + [card.face()])

        elif action == 'keep' and choice in ('old', 'new'):
            if self.pending is None:
                return await notice(it, 'Draw a card first.')
            card, self.pending = self.pending, None
            old = player.hand[0 if card.sign > 0 else 1]
            line = self.keep_move(player, card, choice == 'new')
            kept, dropped = (card, old) if choice == 'new' else (old, card)
            await self.show_hand(it, player, 'You Kept a Card', f'You kept `{kept.label()}` and discarded `{dropped.label()}`.')
            await self.next_turn(line)

        else:
            await notice(it, "That action isn't available.")

    def settle(self, player: Player) -> None:
        if self.pending is not None:
            self.decks[self.pending.sign].discard(self.pending)
            self.pending = None

    def ai_move(self, player: Player) -> str:
        '''
        Lando draws from whichever deck helps him most on average (reckoning
        with full decks, so he never peeks), then keeps the better card.
        '''

        def swapped(card: Card) -> list[Card]:
            hand = list(player.hand)
            hand[0 if card.sign > 0 else 1] = card
            return hand

        now = expected_miss(*player.hand)
        best_gain, best_sign = 0.01, None
        for sign in (1, -1):
            pool = kessel_deck(sign)
            after = sum(min(now, expected_miss(*swapped(card))) for card in pool) / len(pool)
            if now - after > best_gain:
                best_gain, best_sign = now - after, sign
        if best_sign is None:
            return f'{icon.stand} {player.user.mention} stands.'
        card = self.decks[best_sign].draw()
        return self.keep_move(player, card, expected_miss(*swapped(card)) < now)

    # Impostor dice, then the results -------------------------------------------

    async def finish(self, note: str = '') -> None:
        self.phase = 'ending'
        self.deadline = float('inf')
        self.note = note
        for player in self.players:
            dice = {card.sign: (random.randint(1, 6), random.randint(1, 6)) for card in player.hand if card.kind == 'impostor'}
            if dice and player.is_ai:
                self.choose_best(player, dice)  # Lando picks at once
            elif dice:
                self.rolls[player.user.id] = dice
        if not self.rolls:
            return await self.reveal(note)

        self.start_timer(game.turn_time)
        for player in self.humans():
            if player.user.id in self.rolls:
                dice = [('sand' if sign > 0 else 'blood', die) for sign, pair in sorted(self.rolls[player.user.id].items(), reverse=True) for die in pair]
                png = await asyncio.to_thread(cards.render_dice, dice)
                message = await self.post(content=player.user.mention, embed=self.dice_embed(player), view=self.dice_view(player),
                                          file=cards.as_file(png, 'dice.png'))
                if self.phase != 'ending':
                    return  # the channel refused the message and the game closed
                self.dice_messages[player.user.id] = message

    def dice_embed(self, player: Player, note: str = '') -> discord.Embed:
        lines = []
        for card in player.hand:
            if card.kind != 'impostor':
                continue
            name = f'{decks[card.sign]} Impostor `{card.label()}`'
            if card.sign in player.chosen:
                lines.append(f'- {name}: **{signed(player.chosen[card.sign])}**')
            else:
                low, high = self.rolls[player.user.id][card.sign]
                lines.append(f'- {name}: rolled **{low}** and **{high}**')
        waiting = player.user.id in self.rolls
        intro = (f'{player.user.mention}, choose a value for each Impostor.' if waiting else
                 f'{player.user.mention} chose their Impostor values.')
        embed = self.styled('Impostor Dice', '\n\n'.join(part for part in (note, intro, '\n'.join(lines)) if part))
        embed.set_image(url='attachment://dice.png')
        return embed

    def dice_view(self, player: Player) -> Components | None:
        items = []
        for sign, dice in self.rolls.get(player.user.id, {}).items():
            for index, die in enumerate(dice):
                items.append(discord.ui.Button(emoji=deck_icons[sign], label=signed(sign * die),
                                               custom_id=self.id_for('psi', f'{player.user.id}{"+" if sign > 0 else "-"}{index}'),
                                               style=ButtonStyle.primary if sign > 0 else ButtonStyle.danger,
                                               row=0 if sign > 0 else 1))
        return Components(*items) if items else None

    async def act_after(self, it: Interaction, action: str, choice: str) -> None:
        # The choice is "<owner's user id><+ or -><die 0 or 1>", so only the owner can pick.
        if action != 'psi' or len(choice) < 3 or choice[:-2] != str(it.user.id):
            return await notice(it, "These aren't your Impostor dice.")
        rolls = self.rolls.get(it.user.id)
        sign = 1 if choice[-2] == '+' else -1
        if rolls is None or sign not in rolls or choice[-1] not in ('0', '1'):
            return await notice(it, 'You already chose that value.')
        player = next(player for player in self.players if player.user.id == it.user.id)
        player.chosen[sign] = sign * rolls.pop(sign)[int(choice[-1])]
        if not rolls:
            del self.rolls[it.user.id]
        await reply_safely(it.response.edit_message(embed=self.dice_embed(player), view=self.dice_view(player)))
        if not self.rolls:
            await self.reveal(self.note)

    def choose_best(self, player: Player, rolls: dict[int, tuple[int, int]]) -> None:
        '''
        Tries every combination of the rolled dice and keeps the best hand.
        '''

        best = None
        for picks in itertools.product(*rolls.values()):
            for sign, die in zip(rolls, picks):
                player.chosen[sign] = sign * die
            key = self.score(player)[0]
            if best is None or key < best[0]:
                best = (key, dict(player.chosen))
        player.chosen = best[1]

    def waiting_on(self) -> tuple[list[Player], str]:
        if self.phase == 'ending':
            return [player for player in self.players if player.user.id in self.rolls], 'choose your Impostor values'
        return super().waiting_on()

    async def expire_after(self) -> None:
        '''
        Picks the better value for anyone who didn't choose in time.
        '''

        for user_id, rolls in list(self.rolls.items()):
            player = next(player for player in self.players if player.user.id == user_id)
            self.choose_best(player, rolls)
            del self.rolls[user_id]
            message = self.dice_messages.get(user_id)
            if message is not None:
                try:
                    await message.edit(embed=self.dice_embed(player, f'{icon.timeout} Time ran out, so the better value was picked.'), view=None)
                except discord.HTTPException:
                    pass
        await self.reveal(self.note)

    # Scoring ----------------------------------------------------------------

    def score(self, player: Player) -> tuple[tuple, str]:
        if all(card.kind == 'sylop' for card in player.hand):
            return (1,), 'Pure Sabacc'
        sand, blood = (value or 0 for value in self.values(player))
        total = sand + blood
        sizes = sorted((abs(sand), abs(blood)))
        if total == 0 and sizes == [1, 1]:
            return (2,), 'Prime Sabacc'
        if total == 0 and sizes == [6, 6]:
            return (4,), 'Cheap Sabacc'
        if total == 0:
            return (3, sizes[0]), 'Standard Sabacc'
        return (10, abs(total), 0 if total > 0 else 1, -max(sand, 0), -max(sand, blood)), 'Nulrhek'

    @classmethod
    def rules_embed(cls):
        return cls.styled('Kessel Rules', (
            '### Objective\n'
            'Get a hand total as close to **0** as possible.\n\n'
            '### Deck\n'
            '- Two decks: **Sand** (positive) and **Blood** (negative), with **22 cards** each.\n'
            '- Each deck has the values **1 to 6** three times each, three **Impostors** (Ψ), and one **Sylop** (Ø).\n\n'
            '### Gameplay\n'
            '- Your hand is always exactly **2 cards**: one Sand and one Blood.\n'
            '- The game lasts **3 rounds** by default. Each round, every player takes one turn.\n\n'
            '### Actions\n'
            '- **Draw Sand / Draw Blood:** Draw from that deck, then keep either the new card or the one you had.\n'
            '- **Stand:** Keep your hand as it is.\n'
            '- **Junk:** Give up and leave the game.\n\n'
            '### Special Cards\n'
            '- **Impostor (Ψ):** At the end of the game, roll two dice and choose one of them as its value. With two Impostors, you roll for each.\n'
            '- **Sylop (Ø):** Copies the value of your other card, so the total is always 0. Two Sylops are both 0.\n\n'
            '### Hand Rankings (Best to Worst)\n'
            '1. **Pure Sabacc:** Two Sylops. `+Ø` `-Ø`\n'
            '2. **Prime Sabacc:** A pair of 1s. `+1` `-1`\n'
            '3. **Standard Sabacc:** A pair of any other value; lower pairs win (+2 -2 beats +3 -3). `+5` `-5`\n'
            '4. **Cheap Sabacc:** A pair of 6s, the worst Sabacc, though it still beats every Nulrhek. `+6` `-6`\n'
            '5. **Nulrhek:** Any total other than 0. Closest to 0 wins, then positive beats negative, then the highest Sand card.\n\n'
            'Good luck, and may the Force be with you!'
        ))
