# corellian_spike.py
#
# Corellian Spike Sabacc, as seen in Solo: A Star Wars Story and Galaxy's Edge.
# Get as close to 0 as you can; a long list of special hands breaks ties.
# The deck here is also the Coruscant Shift deck.

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from game import DrawGame, Player, Settings
from theme import icon, images, plural, signed

# Each value comes in three staves (suits), drawn as circles, triangles, and
# squares; Coruscant Shift uses them as its three suits.
staves = ('circle', 'triangle', 'square')


@dataclass(frozen=True, slots=True)
class Card:
    value: int
    suit: str  # a stave, or 'sylop'

    def face(self) -> str:
        if self.suit == 'sylop':
            return 'corellian_spike/0.png'
        return f'corellian_spike/{self.suit}/{signed(self.value)}.png'


def spike_deck() -> list[Card]:
    '''
    The 62 cards: +1 to +10 and -1 to -10 in each stave, plus two Sylops (0).
    '''

    deck = [Card(sign * value, suit) for suit in staves for value in range(1, 11) for sign in (1, -1)]
    return deck + [Card(0, 'sylop'), Card(0, 'sylop')]


spike_back = 'corellian_spike/card.png'


def rank_spike_hand(values: list[int]) -> tuple[tuple, str]:
    '''
    (sort key, hand name) for a Corellian Spike hand. Lower keys win.
    '''

    total = sum(values)
    sylops = values.count(0)
    sizes = Counter(abs(value) for value in values if value != 0)
    pairs = sorted(value for value, count in sizes.items() if count >= 2)
    trips = sorted(value for value, count in sizes.items() if count >= 3)
    quads = sorted(value for value, count in sizes.items() if count >= 4)
    positives = [value for value in values if value > 0]

    if total == 0:
        if sylops == 2 and len(values) == 2:
            return (1,), 'Pure Sabacc'
        if sylops >= 2:
            return (2,), 'Sarlacc Sabacc'
        if sorted(values) == [-10, -10, 0, 10, 10]:
            return (3,), 'Full Sabacc'
        if sylops == 1 and quads:
            return (4, quads[0]), 'Fleet'
        if sylops == 1 and len(pairs) >= 2:
            return (5, pairs[0]), 'Twin Sun'
        if sylops == 1 and pairs and len(values) == 3:
            return (6, pairs[0]), 'Yee-Haa'
        if sylops == 1 and pairs:
            return (7, pairs[0]), 'Kessel Run'
        if quads:
            return (8, quads[0]), 'Squadron'
        if trips:
            return (9, trips[0]), "Bantha's Wild"
        if len(pairs) >= 2:
            return (10, pairs[0]), 'Rule of Two'
        if pairs:
            return (11, pairs[0]), 'Sabacc Pair'
        return (12, -len(values), -sum(positives), -max(positives, default=0)), 'Sabacc'
    return (13, abs(total), 0 if total > 0 else 1, -len(values), -sum(positives), -max(positives, default=0)), 'Nulrhek'


class CorellianSpike(DrawGame):
    key = 'corellian_spike'
    name = 'Corellian Spike'
    icon = icon.corellian_spike
    color = 0xCBB7A0
    thumbnail = images + 'corellian_spike.png'
    footer = "As seen in Solo: A Star Wars Story and Galaxy's Edge"
    defaults = Settings(rounds=3, cards=2)
    limits = {'rounds': (1, 10), 'cards': (1, 5)}
    has_discard = True

    @classmethod
    def settings_lines(cls, settings: Settings) -> list[str]:
        return [plural(settings.rounds, 'round'), plural(settings.cards, 'starting card'),
                f'Discarding is {"on" if settings.discard else "off"}']

    def deck_cards(self) -> list[Card]:
        return spike_deck()

    def miss(self, total: int) -> int:
        return abs(total)

    def faces(self, player: Player) -> list[str]:
        return [card.face() for card in player.hand]

    def backs(self, player: Player) -> list[str]:
        return [spike_back] * len(player.hand)

    def score(self, player: Player) -> tuple[tuple, str]:
        return rank_spike_hand([card.value for card in player.hand])

    def standing(self, player: Player) -> str:
        name = self.score(player)[1]
        total = sum(card.value for card in player.hand)
        return f'**{name}**' + (f', {abs(total)} away from 0' if name == 'Nulrhek' else '')

    @classmethod
    def rules_embed(cls):
        embed = cls.styled('Corellian Spike Rules', (
            '### Objective\n'
            'Get a hand total as close to **0** as possible.\n\n'
            '### Deck\n'
            '- **62 cards:** -10 to -1 and +1 to +10 in three staves (circle, triangle, and square), plus 2 Sylops (0).\n\n'
            '### Gameplay\n'
            '- Each player starts with **2 cards** by default, and there is no hand limit.\n'
            '- The game lasts **3 rounds** by default. Each round, every player takes one turn.\n\n'
            '### Actions\n'
            '- **Draw Card:** Draw one card from the deck.\n'
            '- **Replace Card:** Swap one card in your hand for a new one from the deck.\n'
            '- **Discard Card:** Discard one card from your hand (only when discarding is on in the lobby).\n'
            '- **Stand:** Keep your hand as it is.\n'
            '- **Junk:** Give up and leave the game.\n\n'
            '### Hand Rankings (Best to Worst)\n'
            '1. **Pure Sabacc:** Exactly two Sylops. `0` `0`\n'
            '2. **Sarlacc Sabacc** (custom): Total of 0 with both Sylops and more cards. `0` `0` `+3` `-3`\n'
            '3. **Full Sabacc:** A Sylop with +10, +10, -10, -10. `0` `+10` `+10` `-10` `-10`\n'
            '4. **Fleet:** Total of 0, one Sylop, and four of a kind. `0` `+5` `+5` `-5` `-5`\n'
            '5. **Twin Sun** (custom): Total of 0, one Sylop, and two pairs. `0` `+5` `-5` `+3` `-3`\n'
            '6. **Yee-Haa:** Total of 0, one Sylop, and one pair (3 cards). `0` `+5` `-5`\n'
            '7. **Kessel Run** (custom): Total of 0, one Sylop, and a pair. `0` `+4` `+4` `-8`\n'
            '8. **Squadron:** Total of 0 and four of a kind. `+5` `+5` `-5` `-5`\n'
            "9. **Bantha's Wild:** Total of 0 and three of a kind. `+4` `+4` `+4` `-3` `-9`\n"
            '10. **Rule of Two:** Total of 0 and two pairs. `+9` `-9` `+4` `-4`\n'
            '11. **Sabacc Pair:** Total of 0 and one pair. `+5` `-5`\n'
            '12. **Sabacc:** Total of 0 with no special hand. `+1` `+2` `-3`\n'
            '13. **Nulrhek:** Any total other than 0.\n\n'
            '### Tiebreakers\n'
            '- A pair is two cards with the same number, whatever their signs. Between hands of the same kind, the **lowest** pair or set wins (a pair of 2s beats a pair of 5s).\n'
            '- **Sabacc:** most cards, then the highest sum of positive cards, then the highest positive card.\n'
            '- **Nulrhek:** closest to 0, then positive beats negative (+3 beats -3), then most cards, then the highest sum of positive cards, then the highest positive card.\n\n'
            'Good luck, and may the Force be with you!'
        ))
        return embed
