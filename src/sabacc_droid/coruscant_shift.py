# coruscant_shift.py
#
# Coruscant Shift Sabacc, as played on the Halcyon at Galactic Starcruiser.
# A gold die sets the target number and a silver die sets the target suit;
# each round, every player chooses which cards to keep.

from __future__ import annotations

import asyncio
import random

import discord
from discord import ButtonStyle, Embed, Interaction

import cards
from corellian_spike import Card, spike_back, spike_deck, staves
from game import Deck, Game, Player, Settings, notice
from theme import button, icon, images, plural, signed

symbols = {'circle': '●', 'triangle': '▲', 'square': '■'}
gold_die = (-10, 10, -5, 5, 0, 0)


class CoruscantShift(Game):
    key = 'coruscant_shift'
    name = 'Coruscant Shift'
    icon = icon.coruscant_shift
    color = 0xAB9032
    thumbnail = images + 'coruscant_shift.png'
    footer = 'As seen on the Halcyon at Galactic Starcruiser'
    defaults = Settings(rounds=2, cards=5)
    limits = {'rounds': (1, 5), 'cards': (1, 10)}

    @classmethod
    def settings_lines(cls, settings: Settings) -> list[str]:
        return [plural(settings.rounds, 'round'), plural(settings.cards, 'starting card'),
                'Dice set the target number and suit']

    def deal(self) -> None:
        self.deck = Deck(spike_deck)
        self.target_number = random.choice(gold_die)
        self.target_suit = random.choice(staves)
        self.keep: list[bool] = []
        self.keep_turn = -1
        for player in self.players:
            player.hand = [self.deck.draw() for _ in range(self.settings.cards)]
            player.locked = 0  # how many cards at the front of the hand were kept in earlier rounds

    async def start_message(self) -> tuple[Embed, list[discord.File]]:
        embed = self.lobby_embed()
        embed.description += (f'\n\n{icon.dice} The gold die rolled **{signed(self.target_number)}** and the silver die rolled '
                              f'**{symbols[self.target_suit]}**: get as close to {signed(self.target_number)} as you can, '
                              f'and {symbols[self.target_suit]} cards break ties.')
        dice = await asyncio.to_thread(cards.render_dice, [('gold', self.target_number), ('silver', self.target_suit)])
        embed.set_image(url='attachment://dice.png')
        return embed, [cards.as_file(dice, 'dice.png')]

    def new_round(self) -> None:
        for player in self.players:
            player.locked = len(player.hand)
            while len(player.hand) < self.settings.cards:
                player.hand.append(self.deck.draw())

    def label(self, card: Card) -> str:
        return '0' if card.suit == 'sylop' else f'{symbols[card.suit]} {signed(card.value)}'

    def labels(self, player: Player) -> list[str]:
        return [self.label(card) for card in player.hand]

    def faces(self, player: Player) -> list[str]:
        return [card.face() for card in player.hand]

    def backs(self, player: Player) -> list[str]:
        return [spike_back] * len(player.hand)

    def target(self) -> str:
        return f'**{signed(self.target_number)}**, suit {symbols[self.target_suit]}'

    # Choosing cards ---------------------------------------------------------

    def choosing(self, player: Player) -> bool:
        return self.phase == 'playing' and self.keep_turn == self.turn and player is self.players[self.current]

    def kept(self, player: Player) -> list[Card]:
        if self.choosing(player):
            return [card for card, keep in zip(player.hand, self.keep) if keep]
        return player.hand

    def matches(self, hand: list[Card]) -> int:
        return sum(1 for card in hand if card.suit in (self.target_suit, 'sylop'))

    def total(self, player: Player) -> str:
        return signed(sum(card.value for card in self.kept(player)))

    def standing(self, player: Player) -> str:
        return f'**{self.rank(self.kept(player))[1]}**'

    def turn_buttons(self, player: Player) -> list[discord.ui.Button]:
        items = []
        for index, card in enumerate(player.hand):
            choice = self.id_for('toggle', str(index))
            if index < player.locked:
                items.append(discord.ui.Button(emoji='🔒', label=self.label(card), custom_id=choice, disabled=True))
            elif self.keep[index]:
                items.append(discord.ui.Button(emoji=icon.confirm, label=self.label(card), custom_id=choice, style=ButtonStyle.success))
            else:
                items.append(discord.ui.Button(emoji=icon.error, label=self.label(card), custom_id=choice, style=ButtonStyle.danger))
        items.append(button(icon.confirm, 'Confirm Cards', self.id_for('confirm'), ButtonStyle.primary))
        items.append(button(icon.junk, 'Junk', self.id_for('junk'), ButtonStyle.danger))
        return items

    async def show_turn(self, it: Interaction, player: Player, note: str = '', new: bool = False) -> None:
        if self.keep_turn != self.turn:
            self.keep, self.keep_turn = [True] * len(player.hand), self.turn
        faces = [card.face() if keep else spike_back for card, keep in zip(player.hand, self.keep)]
        note = note or ('Click a card to keep it ✅ or discard it ❌, then **Confirm Cards**.'
                        + (' Cards kept in earlier rounds are locked 🔒.' if player.locked else ''))
        await self.show_hand(it, player, 'Your Turn', note, self.turn_buttons(player), faces=faces, new=new)

    def keep_move(self, player: Player, keep: list[bool]) -> str:
        '''
        Keeps the chosen cards, discards the rest, and returns the game log line.
        '''

        dropped = [card for card, kept in zip(player.hand, keep) if not kept]
        player.hand = [card for card, kept in zip(player.hand, keep) if kept]
        for card in dropped:
            self.deck.discard(card)
        return f'{icon.confirm} {player.user.mention} keeps {plural(len(player.hand), "card")} and discards {len(dropped)}.'

    async def act(self, it: Interaction, player: Player, action: str, choice: str) -> None:
        if self.keep_turn != self.turn:
            return await notice(it, 'Click **Play Turn** to choose your cards.')

        if action == 'toggle':
            index = int(choice) if choice.isdigit() else -1
            if not player.locked <= index < len(player.hand):
                return await notice(it, "You can't discard cards you kept in an earlier round.")
            if self.keep[index] and sum(self.keep) == 1:
                return await notice(it, 'You must keep at least one card.')
            self.keep[index] = not self.keep[index]
            await self.show_turn(it, player)

        elif action == 'confirm':
            line = self.keep_move(player, self.keep)
            self.keep_turn = -1
            await self.show_hand(it, player, 'You Confirmed Your Cards', 'Your choices are locked in for this round.')
            await self.next_turn(line)

        else:
            await notice(it, "That action isn't available.")

    def auto_play(self, player: Player) -> str:
        self.keep_turn = -1
        return 'keeps every card'

    def ai_move(self, player: Player) -> str:
        '''
        Lando tries every set of cards he could keep and keeps the best hand.
        New cards can always be discarded later, so locking in the best hand
        now never costs him anything.
        '''

        free = len(player.hand) - player.locked
        best = None
        for mask in range(1 << free):
            keep = [True] * player.locked + [bool(mask >> index & 1) for index in range(free)]
            kept = [card for card, chosen in zip(player.hand, keep) if chosen]
            if kept and (best is None or self.rank(kept)[0] < best[0]):
                best = (self.rank(kept)[0], keep)
        return self.keep_move(player, best[1])

    # Scoring ----------------------------------------------------------------

    def rank(self, hand: list[Card]) -> tuple[tuple, str]:
        if len(hand) == 2 and all(card.suit == 'sylop' for card in hand):
            return (0,), 'Pure Sabacc'
        total = sum(card.value for card in hand)
        off = abs(total - self.target_number)
        matches = self.matches(hand)
        largest = max((card.value for card in hand if card.value > 0), default=0)
        distance = 'On target' if off == 0 else f'Off by {off}'
        return (1, off, -matches, -total, -largest), f'{distance}, {matches} suit match{"es" * (matches != 1)}'

    def score(self, player: Player) -> tuple[tuple, str]:
        return self.rank(player.hand)

    def headline(self, name: str) -> str:
        return f'wins with **{name}**!' if name == 'Pure Sabacc' else 'wins!'

    @classmethod
    def rules_embed(cls):
        return cls.styled('Coruscant Shift Rules', (
            '### Objective\n'
            'Finish with a hand whose total is as close as possible to the **target number** rolled on the gold die. '
            'Ties go to the player with the most cards in the **target suit** rolled on the silver die.\n\n'
            '### Deck\n'
            '- **62 cards:** +1 to +10 and -1 to -10 in each of **3 suits** (●, ▲, ■), plus **2 Sylops (0)**, which match any suit.\n\n'
            '### Dice\n'
            '- The **gold die** (faces: -10, +10, -5, +5, 0, 0) sets the target number.\n'
            '- The **silver die** (two faces each of ●, ▲, ■) sets the target suit.\n\n'
            '### Rounds\n'
            'The game lasts **2 rounds** by default, and each player starts with **5 cards**.\n'
            '- On your turn, choose which cards to keep. Cards you don\'t keep are discarded.\n'
            '- At the start of every later round, everyone draws back up to 5 cards. Cards kept in earlier rounds are **locked in**; only new cards can be discarded.\n'
            '- After the last round, every hand is revealed.\n\n'
            '### Actions\n'
            '- **Toggle a Card:** Keep it (✅) or discard it (❌). You must keep at least one card.\n'
            '- **Confirm Cards:** Lock in your choices and end your turn.\n'
            '- **Junk:** Give up and leave the game.\n\n'
            '### Winning and Tiebreakers\n'
            '1. **Pure Sabacc** (exactly two Sylops) beats every other hand.\n'
            '2. Closest to the target number.\n'
            '3. Most cards matching the target suit (Sylops count as a match).\n'
            '4. Highest total.\n'
            '5. Highest single positive card.\n'
            '6. If still tied, the game ends in a tie.\n\n'
            'Good luck, and may the Force be with you!'
        ))
