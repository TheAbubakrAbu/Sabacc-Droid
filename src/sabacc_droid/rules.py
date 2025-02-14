# rules.py

from discord import Embed

def get_corellian_spike_rules_embed() -> Embed:
    '''Create an embed containing the Corellian Spike Sabacc game rules.'''

    rules_embed = Embed(
        title='Corellian Spike Sabacc Game Rules',
        description='**Objective:**\n'
                    'Achieve a hand with a total sum as close to zero as possible.\n\n'
                    '**Deck Composition:**\n'
                    '- Single deck of **62 cards** ranging from **-10 to +10** (not including 0), plus 2 Sylops (0 cards).\n'
                    '- There are **three copies** (staves) of each card value, both positive and negative.\n\n'
                    '**Gameplay Mechanics:**\n'
                    '- Each player starts with **two cards**.\n'
                    '- **Hand Limit:** No specific limit; you can hold multiple cards.\n'
                    '- **Rounds:** The game is played over **3 rounds** by default.\n\n'
                    '**Available Actions:**\n'
                    '- **Draw Card:** Draw one card from the deck.\n'
                    '- **Discard Card:** Remove one card from your hand.\n'
                    '- **Replace Card:** Swap one card in your hand with a new one from the deck.\n'
                    '- **Stand:** Keep your current hand without changes.\n'
                    '- **Junk:** Give up and exit the game.\n\n'
                    '**Hand Value Calculation:**\n'
                    '- A player\'s hand value is the **sum** of all cards in their hand.\n'
                    '- Players aim for a total hand value of **zero**.\n\n'
                    '**Ranking Corellian Spike Hands (from best to worst):**\n\n'
                    '1. **Pure Sabacc:** Two sylops (0): 0, 0.\n\n'
                    '2. **Sarlacc Sabacc (Custom Hand that I made):** Sum zero, at least two sylops (0), any number of cards\n'
                    '   - Example: 0, 0, +3, -3\n\n'
                    '3. **Full Sabacc:** 0, +10, +10, -10, -10.\n\n'
                    '4. **Fleet:** Sum zero, one sylop (0), and four of a kind.\n'
                    '   - Tie-breaker: Lowest card value.\n'
                    '   - Example: 0, +5, +5, -5, -5\n\n'
                    '5. **Twin Sun (Custom Hand that I made):** Sum zero, one sylop (0), and at least two pairs.\n'
                    '   - Tie-breaker: Lowest pair value.\n'
                    '   - Example: 0, +5, -5, +3, -3\n\n'
                    '6. **Yee-Haa:** Sum zero, one sylop (0), exactly 3 cards, and one pair.\n'
                    '   - Tie-breaker: Lowest pair value.\n'
                    '   - Example: 0, +5, -5\n\n'
                    '7. **Kessel Run (Custom Hand that I made):** Sum zero, one sylop (0), and at least one pair (no card limit).\n'
                    '   - Tie-breaker: Lowest pair value.\n'
                    '   - Example: 0, +4, -4, +8\n\n'
                    '8. **Squadron:** Sum zero, four of a kind.\n'
                    '   - Tie-breaker: Lowest card value.\n'
                    '   - Example: +5, +5, -5, -5\n\n'
                    '9. **Bantha\'s Wild:** Sum zero, three of a kind.\n'
                    '   - Tie-breaker: Lowest card value.\n'
                    '   - Example: +4, +4, +4, -3, -9 or +5, -5, +5, -3, -2\n\n'
                    '10. **Rule of Two:** Sum zero, two pairs.\n'
                    '   - Tie-breaker: Lowest pair value.\n'
                    '   - Example: +3, +3, -5, +5, -6 or +9, -9, +4, -4\n\n'
                    '11. **Sabacc Pair:** Sum zero, one pair (cards with the same absolute value).\n'
                    '    - Pairs can be any sign: (+5, +5), (-5, -5), or (+5, -5).\n'
                    '    - Tie-breaker: Lowest pair value.\n'
                    '    - Example: +5, +5, -10 or +5, -5\n\n'
                    '12. **Sabacc:** Sum zero, no special hands.\n'
                    '    - Tie-breakers:\n'
                    '      1. Lowest absolute card value.\n'
                    '      2. Most cards in hand.\n'
                    '      3. Highest positive sum.\n'
                    '      4. Highest single positive card.\n'
                    '    - Example: +1, +2, -3\n\n'
                    '13. **Nulrhek:** Sum not zero.\n'
                    '    - Tie-breakers:\n'
                    '      1. Closest to zero (absolute value).\n'
                    '      2. Positive totals beat negative if same distance.\n'
                    '      3. Most cards in hand.\n'
                    '      4. Highest positive sum.\n'
                    '      5. Highest single positive card.\n'
                    '    - Example: Total of +1 beats total of -1\n\n'
                    'Good luck! May the Force be with you!',
        color=0x964B00
    )
    rules_embed.set_thumbnail(
        url='https://raw.githubusercontent.com/compycore/Sabacc/gh-pages/images/logo.png')
    return rules_embed

def get_kessel_rules_embed() -> Embed:
    '''Create an embed containing the Kessel Sabacc game rules.'''

    rules_embed = Embed(
        title='Kessel Sabacc Game Rules',
        description='**Objective:**\n'
                    'Achieve a hand with a total sum as close to zero as possible.\n\n'
                    '**Deck Composition:**\n'
                    '- Two decks: Sand (positive cards) and Blood (negative cards), each comprising **22 cards** (44 total).\n'
                    '- Each deck contains:\n'
                    '   - Value cards from **-6 to +6** (not including 0), with **three copies** (staves) of each.\n'
                    '   - Three Impostor cards (marked with this symbol: Ψ).\n'
                    '   - One Sylop card (marked with this symbol: Ø).\n\n'
                    '**Gameplay Mechanics:**\n'
                    '- Each player starts with **two cards**: one from Sand (positive) and one from Blood (negative).\n'
                    '- **Hand Limit:** You can only have **2 cards** in your hand at any time, one positive and one negative.\n'
                    '- **Rounds:** The game is played over **3 rounds** by default.\n\n'
                    '**Available Actions:**\n'
                    '- **Draw Card:** Draw one card from either deck.\n'
                    '   - After drawing, you must discard one of your existing cards to maintain a hand of two cards.\n'
                    '- **Stand:** Keep your current hand without changes.\n'
                    '- **Junk:** Give up and exit the game.\n\n'
                    '**Hand Value Calculation:**\n'
                    '- A player\'s hand value is the **sum** of their two cards (positive plus negative).\n'
                    '- Players aim for a hand value of zero for a "Sabacc" hand.\n'
                    '- **Impostor (Ψ) Cards:**\n'
                    '   - At the end of each round, every player who has an Impostor card will roll two dice and choose one of the rolled values to assign to their Impostor card.\n'
                    '   - If a player has two Impostor cards (one positive and one negative), they will perform this action twice, rolling a total of four dice.\n'
                    '   - This mechanic introduces an element of luck, allowing players to potentially enhance or harm their hands.\n'
                    '- **Sylop (Ø) Cards:**\n'
                    '   - A Sylop card takes the value of the other card in your hand.\n'
                    '   - If you have two Sylops, they both count as zero (best hand in the game).\n\n'
                    '**Ranking Kessel Hands (from best to worst):**\n\n'
                    '1. **Pure Sabacc:** A pair of Sylops (both count as 0).\n'
                    '   - Example: 0, 0\n\n'
                    '2. **Prime Sabacc:** A pair of ones (+1 and -1).\n'
                    '   - Example: +1, -1\n\n'
                    '3. **Standard Sabacc:** Two cards where one positive and one negative card have the same absolute value.\n'
                    '   - Standard Sabacc hands are ranked by the absolute values of their cards; lower integers are better.\n'
                    '     - For example, a hand of +2 and -2 beats a hand of +3 and -3 because 2 is lower than 3.\n'
                    '     - The best Sabacc is **+1, -1**, and the worst is **+6, -6**.\n'
                    '   - Example: +5, -5\n\n'
                    '4. **Cheap Sabacc (worst Sabacc hand):** A pair of sixes.\n'
                    '   - This hand is the worst Sabacc hand, but is still better than Nulrhek Hands because the sum equals 0.\n'
                    '   - Example: +6, -6\n\n'
                    '5. **Nulrhek Hands (Sum does not equal 0):**\n'
                    '   - If no player has a Sabacc hand, Nulrhek hands are considered.\n'
                    '   - Tie-breakers:\n'
                    '     1. Closest to zero wins.\n'
                    '     2. Positive totals beat negative totals.\n'
                    '     3. Highest positive card wins.\n\n'
                    'Good luck! May the Force be with you!',
        color=0x964B00
    )
    rules_embed.set_thumbnail(
        url='https://raw.githubusercontent.com/compycore/Sabacc/gh-pages/images/logo.png')
    return rules_embed

def get_coruscant_shift_rules_embed() -> Embed:
    '''Create an embed containing the Coruscant Shift Sabacc game rules.'''
    
    rules_embed = Embed(
        title='Coruscant Shift Sabacc Game Rules',
        description=(
            "**Objective:**\n"
            "Achieve a final 5‑card hand whose total is as close as possible to the target number rolled on the gold die.\n"
            "If there’s a tie, the hand with the most cards matching the target suit (from the silver die) wins.\n\n"
            "**Deck Composition:**\n"
            "- **Total Cards:** 62 cards\n"
            "- **Suits:** 3 suits – **Circles**, **Triangles**, and **Squares**\n"
            "  - Each suit contains **20 cards**: half with positive values (+1 to +10) and half with negative values (-1 to -10).\n"
            "- **Sylop Cards:** 2 zero cards (0) that act as wildcards (count as any suit).\n\n"
            "**Dice:**\n"
            "- **Gold Die (Numbered):** Faces: -10, 10, -5, 5, 0, 0 (sets the target number)\n"
            "- **Silver Die (Suit):** 6 faces with 2 of each suit (Circles, Triangles, Squares) (sets the target suit for tie-breakers)\n\n"
            "**Gameplay Overview:**\n"
            "The game is played over **2 rounds** using a full hand of 5 cards.\n\n"
            "**Round 1 – Selection & Shift:**\n"
            "1. **Initial Deal:** Each player is dealt 5 cards.\n"
            "2. **Select:** Choose any number of cards from your hand that best work toward achieving a total near the target number.\n"
            "3. **Shift:** Discard the cards you did not select, then draw new cards from the draw pile equal to the number discarded. \n"
            "   (This refreshes your hand back to 5 cards.)\n\n"
            "**Round 2 – Final Selection & Reveal:**\n"
            "1. **Final Select:** Look at your current 5‑card hand (post-shift) and choose again which cards to keep.\n"
            "2. **Discard & Draw:** For every card you discard, draw a replacement so that you end with a complete 5‑card hand.\n"
            "3. **Reveal:** All players reveal their final hands.\n\n"
            "**Winning:**\n"
            "- The player whose hand total is closest to the target number (gold die) wins.\n"
            "- In the event of a tie, the winner is determined by who has the most cards in the target suit (silver die).\n\n"
            "**No Gambling:**\n"
            "This version of Coruscant Shift Sabacc is played without betting, focusing entirely on strategic card selection."
        ),
        color=0x964B00
    )
    rules_embed.set_thumbnail(
        url='https://raw.githubusercontent.com/compycore/Sabacc/gh-pages/images/logo.png'
    )
    return rules_embed

def get_comparison_embed() -> Embed:
    '''Create an embed comparing Corellian Spike, Kessel, and Coruscant Shift Sabacc game modes.'''

    comparison_embed = Embed(
        title='Sabacc Game Modes Comparison',
        description=(
            "**Similarities:**\n"
            "- All modes aim for a hand total as close as possible to a target (zero or a dice-determined number).\n"
            "- Each game uses unique decks that include wild Sylop (0) cards.\n"
            "- Strategic card selection is at the heart of gameplay.\n\n"
            "**Differences:**\n\n"
            "**Corellian Spike Sabacc:**\n"
            "- **Deck Composition:** A single deck of 62 cards ranging from -10 to +10 (excluding 0), plus 2 Sylops (0).\n"
            "- **Hand Limit:** No fixed hand size; players can accumulate multiple cards.\n"
            "- **Actions:** Options include drawing, discarding, replacing, standing, and junking.\n"
            "- **Special Hands:** Includes unique combinations like Pure Sabacc, Full Sabacc, Yee-Haa, etc.\n\n"
            "**Kessel Sabacc:**\n"
            "- **Deck Composition:** Two separate decks (Sand for positives and Blood for negatives) with 22 cards each (44 total), plus Sylops.\n"
            "- **Hand Limit:** Exactly 2 cards (one positive and one negative).\n"
            "- **Actions:** Limited to drawing, standing, and junking, with special mechanics for Impostor cards.\n"
            "- **Special Hands:** Ranked by the absolute values of paired cards (e.g., Pure Sabacc, Prime Sabacc).\n\n"
            "**Coruscant Shift Sabacc:**\n"
            "- **Deck Composition:** Standard 62‑card deck with 3 suits (Circles, Triangles, Squares), each suit having 20 cards (+1 to +10 and -1 to -10), plus 2 Sylop (0) cards.\n"
            "- **Dice Mechanics:**\n"
            "   - **Gold Die:** Determines the target number (-10, 10, -5, 5, 0, 0).\n"
            "   - **Silver Die:** Determines the target suit (2 of each suit) for tie-breakers.\n"
            "- **Gameplay:** Played in 2 rounds:\n"
            "   1. **Round 1 – Selection & Shift:** Choose cards to keep, discard the rest, and draw replacements to refill your 5‑card hand.\n"
            "   2. **Round 2 – Final Selection:** Discard unwanted cards and draw to finish with a final 5‑card hand before revealing.\n"
            "- **Winning:** The hand closest to the gold die’s target number wins; ties are broken by the count of cards in the silver die’s target suit.\n"
            "- **No Gambling:** This mode is purely strategic with no betting involved.\n\n"
            "Choose your preferred game mode and may the Force be with you!"
        ),
        color=0x964B00
    )
    comparison_embed.set_thumbnail(
        url='https://raw.githubusercontent.com/compycore/Sabacc/gh-pages/images/logo.png'
    )
    return comparison_embed