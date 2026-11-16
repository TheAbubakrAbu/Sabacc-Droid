# traditional.py
#
# Traditional Sabacc, as seen in Star Wars Rebels. Aim for +23 or -23. There
# is no round limit: the game ends after someone calls Alderaan and everyone
# else takes one final turn.

from __future__ import annotations

from dataclasses import dataclass

import discord
from discord import ButtonStyle, Interaction

from game import DrawGame, Player, Settings, notice
from theme import button, icon, images, plural, signed

suits = ('flask', 'saber', 'staff', 'coin')

# Two copies of each of these join the 60 suited cards.
special_cards = {
    0: 'The Idiot',
    -2: 'The Queen of Air and Darkness',
    -8: 'Endurance',
    -11: 'Balance',
    -13: 'Demise',
    -14: 'Moderation',
    -15: 'The Evil One',
    -17: 'The Star',
}


@dataclass(frozen=True, slots=True)
class Card:
    value: int
    suit: str  # a suit, or 'special'

    def face(self) -> str:
        folder = 'unique' if self.suit == 'special' else self.suit
        return f'traditional/{folder}/{signed(self.value)}.png'


def traditional_deck() -> list[Card]:
    '''
    The 76 cards: four suits of +1 to +15, plus two of each special card.
    '''

    deck = [Card(value, suit) for suit in suits for value in range(1, 16)]
    return deck + [Card(value, 'special') for value in special_cards for _ in range(2)]


class Traditional(DrawGame):
    key = 'traditional'
    name = 'Traditional'
    icon = icon.traditional
    color = 0x7A9494
    thumbnail = images + 'traditional.png'
    footer = 'As seen in Star Wars Rebels'
    defaults = Settings(rounds=0, cards=2)
    limits = {'cards': (1, 5)}
    has_discard = True

    @classmethod
    def settings_lines(cls, settings: Settings) -> list[str]:
        return ['No round limit: call Alderaan to end the game', plural(settings.cards, 'starting card'),
                f'Discarding is {"on" if settings.discard else "off"}']

    def deal(self) -> None:
        super().deal()
        self.caller: Player | None = None

    def deck_cards(self) -> list[Card]:
        return traditional_deck()

    def miss(self, total: int) -> int:
        return min(abs(23 - total), abs(-23 - total))

    def faces(self, player: Player) -> list[str]:
        return [card.face() for card in player.hand]

    def backs(self, player: Player) -> list[str]:
        return ['traditional/card.png'] * len(player.hand)

    def target(self) -> str:
        return '**+23** or **-23**'

    def turn_note(self) -> str:
        if self.caller is None:
            return ''
        return f'\n\n{icon.alderaan} {self.caller.user.mention} called Alderaan. This is the **final turn**.'

    def turn_buttons(self, player: Player) -> list[discord.ui.Button]:
        return super().turn_buttons(player) + [
            button(icon.alderaan, 'Call Alderaan', self.id_for('alderaan'), ButtonStyle.danger, disabled=self.caller is not None),
        ]

    def call_move(self, player: Player) -> str:
        self.caller = player
        return f'{icon.alderaan} {player.user.mention} calls Alderaan! Everyone else gets one final turn.'

    async def act(self, it: Interaction, player: Player, action: str, choice: str) -> None:
        if action != 'alderaan':
            return await super().act(it, player, action, choice)
        if self.caller is not None:
            return await notice(it, 'Alderaan has already been called.')
        line = self.call_move(player)
        await self.show_hand(it, player, 'You Called Alderaan', 'Everyone else gets one final turn, then all hands are revealed.')
        await self.next_turn(line)

    def ai_move(self, player: Player) -> str:
        '''
        Lando calls Alderaan once he is within 2 of 23, or by round 5 so a
        game against him always ends.
        '''

        if self.caller is None and (self.miss(sum(card.value for card in player.hand)) <= 2 or self.round >= 5):
            return self.call_move(player)
        return super().ai_move(player)

    def standing(self, player: Player) -> str:
        name = self.score(player)[1]
        miss = self.miss(sum(card.value for card in player.hand))
        return f'**{name}**' + (f', {miss} away from 23' if name == 'Nulrhek' else '')

    def game_over(self) -> bool:
        return self.caller is not None and self.players[self.current] is self.caller

    def score(self, player: Player) -> tuple[tuple, str]:
        values = [card.value for card in player.hand]
        total = sum(values)
        largest = -max((abs(value) for value in values), default=0)
        if len(values) == 3 and set(values) == {0, 2, 3}:
            return (1,), "Idiot's Array"
        if abs(total) == 23:
            return (2, -len(values), largest), 'Natural Sabacc'
        if values == [-2, -2]:
            return (3,), 'Fairy Empress'
        distance = min(abs(23 - total), abs(-23 - total))
        return (4, distance, 0 if total < 0 else 1, -len(values), -abs(total), largest), 'Nulrhek'

    def result_note(self) -> str:
        names = sorted({card.value for player in self.players for card in player.hand if card.suit == 'special'}, reverse=True)
        if not names:
            return ''
        return 'Special cards: ' + ', '.join(f'`{signed(value)}` {special_cards[value]}' for value in names)

    @classmethod
    def rules_embed(cls):
        return cls.styled('Traditional Rules', (
            '### Objective\n'
            'Get a hand total as close to **+23 or -23** as possible.\n\n'
            '### Deck\n'
            '- **76 cards:** four suits (Flasks, Sabers, Staves, and Coins) of +1 to +15, plus two copies of 8 special cards:\n'
            '- The Idiot (0), The Queen of Air and Darkness (-2), Endurance (-8), Balance (-11), Demise (-13), Moderation (-14), The Evil One (-15), and The Star (-17).\n\n'
            '### Gameplay\n'
            '- Each player starts with **2 cards** by default, and there is no hand limit.\n'
            '- There is no round limit. Once a player calls **Alderaan**, everyone else takes one final turn, then all hands are revealed.\n\n'
            '### Actions\n'
            '- **Draw Card:** Draw one card from the deck.\n'
            '- **Replace Card:** Swap one card in your hand for a new one from the deck.\n'
            '- **Discard Card:** Discard one card from your hand (only when discarding is on in the lobby).\n'
            '- **Stand:** Keep your hand as it is.\n'
            '- **Junk:** Give up and leave the game.\n'
            '- **Call Alderaan:** Start the final turns.\n\n'
            '### Hand Rankings (Best to Worst)\n'
            "1. **Idiot's Array:** Exactly The Idiot, a +2, and a +3 (read as a literal 23). Beats everything. `0` `+2` `+3`\n"
            '2. **Natural Sabacc:** A total of exactly +23 or -23. Ties go to the most cards, then the single card farthest from 0. `+15` `+8`\n'
            '3. **Fairy Empress:** Exactly both Queens of Air and Darkness (read as -22). Beats every hand but the two above. `-2` `-2`\n'
            '4. **Nulrhek:** Any other hand. Closest to +23 or -23 wins, then negative beats positive (-22 beats +22), then most cards, then the total farthest from 0, then the single card farthest from 0.\n\n'
            'Good luck, and may the Force be with you!'
        ))
