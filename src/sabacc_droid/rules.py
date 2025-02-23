# rules.py

from discord import Embed

RULES_DESCRIPTION = (
    'Welcome to **Sabacc Droid**! You can play any of the following Sabacc variations:\n\n'
    '• [**Corellian Spike**](https://starwars.fandom.com/wiki/Corellian_Spike) – Featured in *Solo: A Star Wars Story* and *Galaxy\'s Edge*.\n'
    '• [**Coruscant Shift**](https://starwars.fandom.com/wiki/Coruscant_Shift) – Played aboard the **Halcyon** at *Galactic Starcruiser*.\n'
    '• [**Kessel Sabacc**](https://starwars.fandom.com/wiki/Kessel_Sabacc) – Featured in *Star Wars: Outlaws*.\n'
    '• [**Traditional Sabacc**](https://starwars.fandom.com/wiki/Sabacc) – Featured in *Star Wars: Rebels*.\n\n'

    '### **Game Rules & Variations**\n'
    'Each mode aims for a hand sum close to its target (0, a dice-determined value, or +23/-23), but they differ in decks and rules:\n\n'

    '**Default Game Settings:**\n'
    '- **Corellian Spike, Kessel, and Traditional Sabacc** each have **3 rounds** and **2 starting cards**.\n'
    '- **Coruscant Shift** has **2 rounds** and **5 starting cards**.\n\n'

    '### **Credits & Disclaimers**\n'
    '• **Corellian Spike & Coruscant Shift Cards:** [Winz](https://cults3d.com/en/3d-model/game/sabacc-cards-and-spike-dice-printable)\n'
    '• **Kessel Sabacc Cards:** [u/Gold-Ad-4525](https://www.reddit.com/r/StarWarsSabacc/comments/1exatgi/kessel_sabaac_v3/)\n'
    '• All other creative content is fan-made and not affiliated with or endorsed by Lucasfilm/Disney.\n\n'

    'Created by **[Abubakr Elmallah](https://abubakrelmallah.com/)**.\n\n'
    '[📂 GitHub Repository](https://github.com/TheAbubakrAbu/Sabacc-Droid)\n\n'

    'May the Force be with you—choose a game mode and have fun!'
)

def get_corellian_spike_rules_embed() -> Embed:
    '''
    Create an embed containing the Corellian Spike Sabacc game rules.
    '''

    rules_embed = Embed(
        title='Corellian Spike Sabacc Game Rules',
        description='**Objective:**\n'
                    'Achieve a hand with a total sum as close to zero as possible.\n\n'
                    '**Deck Composition:**\n'
                    '- Single deck of **62 cards** ranging from **-10 to -1** and **+1 to +10**, plus 2 Sylops (0 cards).\n'
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
        color=0x764920
    )
    rules_embed.set_thumbnail(
        url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/Corellian%20Spike.png'
    )
    return rules_embed

def get_coruscant_shift_rules_embed() -> Embed:
    '''
    Create an embed containing the Coruscant Shift Sabacc game rules,
    formatted similarly to Corellian Spike and Kessel.
    '''

    rules_embed = Embed(
        title='Coruscant Shift Sabacc Game Rules',
        description='**Objective:**\n'
                    'Achieve a final hand (between **1 and 5 cards**) whose total is as close as possible to the target number determined by the gold die.'
                    'If there is a tie, the winner is determined by who has the most cards matching the target suit (from the silver die).'
                    'Further ties are decided by highest positive “added total,” then highest single positive card, and if still tied, sudden death draws.\n\n'

                    '**Deck Composition:**\n'
                    '- **62 cards** total.\n'
                    '- **3 suits** (●, ▲, ■), each containing **20 cards**: +1 to +10 and -1 to -10.\n'
                    '- **2 Sylop (0)** cards act as wild/wildcard suits.\n\n'

                    '**Gameplay Mechanics:**\n'
                    '- You start each round with **5 cards**.\n'
                    '- The **gold die** (faces: -10, 10, -5, 5, 0, 0) sets the target number.\n'
                    '- The **silver die** (faces: two each of ●, ▲, ■) sets the target suit.\n\n'

                    '**Rounds:**\n'
                    '- By default, Coruscant Shift is played over **2 rounds** of card selection.\n'
                    '- **Round 1 – Selection & Shift:**\n'
                    '  1. Each player is dealt 5 cards.\n'
                    '  2. In turn order, choose which cards you want to keep (face down). Any unkept cards are discarded.\n'
                    '- **Round 2 – Final Selection & Reveal:**\n'
                    '  1. Draw new cards equal to the number discarded, returning you to 5 cards.\n\n'
                    '  2. Each player again selects which cards to keep.\n'
                    '  3. You **cannot** discard any card you kept from Round 1. You may only discard newly drawn cards.\n'
                    '  4. Reveal all final hands.\n\n'

                    '**Hand Value Calculation:**\n'
                    '- Each card contributes its face value (+ or -). Sylops (0) can count as any suit.\n'
                    '- Your final total is simply the sum of all cards you kept.\n\n'

                    '**Tie-Breakers:**\n'
                    '1. Closest to the target number (absolute difference).\n'
                    '2. Most cards matching the target suit.\n'
                    '3. Highest total.\n'
                    '4. Highest single positive card.\n'
                    '5. Else it\'s a tie.\n\n'

                    'Good luck! May the Force be with you!',
        color=0x764920
    )
    rules_embed.set_thumbnail(
        url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/Coruscant%20Shift.png'
    )
    return rules_embed

def get_kessel_rules_embed() -> Embed:
    '''
    Create an embed containing the Kessel Sabacc game rules.
    '''

    rules_embed = Embed(
        title='Kessel Sabacc Game Rules',
        description='**Objective:**\n'
                    'Achieve a hand with a total sum as close to zero as possible.\n\n'
                    '**Deck Composition:**\n'
                    '- Two decks: Sand (positive cards) and Blood (negative cards), each comprising **22 cards** (44 total).\n'
                    '- Each deck contains:\n'
                    '   - Value cards from **-6 to -1** and **+1 to +6**, with **three copies** (staves) of each.\n'
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
                    '- Players aim for a hand value of zero for a Sabacc hand.\n'
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
        color=0x764920
    )
    rules_embed.set_thumbnail(
        url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/kessel/logo.png'
    )
    return rules_embed

def get_comparison_embed() -> Embed:
    '''
    Create an embed comparing Corellian Spike, Kessel, and Coruscant Shift Sabacc game modes,
    reflecting the latest Coruscant Shift rules changes.
    '''

    comparison_embed = Embed(
        title='Sabacc Game Modes Comparison',
        description=(
            '**Similarities:**\n'
            '- All modes aim for a hand total as close as possible to a specific target (zero or dice‑determined).\n'
            '- Each includes Sylop (0) cards with special properties.\n'
            '- Strategic card selection is key to winning.\n\n'

            '**Differences:**\n\n'
            '**Corellian Spike Sabacc:**\n'
            '- **Deck Composition:** A single 62‑card deck ranging from −10 to +10 (no zero), plus 2 Sylops (0).\n'
            '- **Hand Limit:** No fixed limit; players can accumulate multiple cards.\n'
            '- **Rounds:** Typically 3 rounds.\n'
            '- **Actions:** Draw, Discard, Replace, Stand, or Junk.\n'
            '- **Special Hands:** Complex ranking system (Pure Sabacc, Fleet, Yee‑Haa, etc.).\n\n'

            '**Coruscant Shift Sabacc:**\n'
            '- **Deck Composition:** Standard 62‑card deck (+1..+10, −1..−10 for suits ●, ▲, ■; plus 2 Sylops).\n'
            '- **Dice Mechanics:**\n'
            '  • **Gold Die:** Sets target number (−10, +10, −5, +5, 0, 0).\n'
            '  • **Silver Die:** Sets target suit (●, ▲, ■) for tie‑breakers.\n'
            '- **Rounds:** Played in 2 “phases” of card selection.\n'
            '  1. **Round 1 – Selection & Shift:** Each player discards unwanted cards from their initial 5, draws replacements back to 5.\n'
            '  2. **Round 2 – Final Selection & Reveal:** Players choose again, but cannot discard any cards they kept from Round 1. '
            'They may discard newly drawn cards, aiming for **1–5 total** in their final hand.\n'
            '- **Tie-Breakers:** Closest to the gold die target → most cards of silver die suit → highest positive “added total” → highest single positive card → sudden death.\n\n'

            '**Kessel Sabacc:**\n'
            '- **Deck Composition:** Two separate decks (Sand for positives, Blood for negatives), 22 cards each (44 total), plus Sylops.\n'
            '- **Hand Limit:** Exactly 2 cards (1 positive, 1 negative).\n'
            '- **Rounds:** Typically 3 rounds.\n'
            '- **Actions:** Draw (then discard to maintain 2 cards), Stand, or Junk.\n'
            '- **Impostor Cards (Ψ):** Roll dice to assign or modify values.\n'
            '- **Sylop (Ø) Cards:** Mirror the value of the other card in hand.\n'
            '- **Special Hands:** Includes Pure Sabacc, Prime Sabacc, etc., all aimed at total 0.\n\n'

            'Choose your preferred mode—may the Force be with you!'
        ),
        color=0x764920
    )
    comparison_embed.set_thumbnail(
        url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/Corellian%20Spike.png'
    )
    return comparison_embed