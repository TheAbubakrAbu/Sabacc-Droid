# rules.py

from discord import Embed

RULES_DESCRIPTION = (
    'Welcome to **Sabacc Droid**! You can play any of the following Sabacc variations:\n\n'
    '• [**Corellian Spike Sabacc**](https://starwars.fandom.com/wiki/Corellian_Spike) – A **three-round game** where players aim for **zero**, featuring **Sylop (0) cards**. Seen in *Solo: A Star Wars Story* and *Galaxy\'s Edge*.\n'
    '• [**Coruscant Shift Sabacc**](https://starwars.fandom.com/wiki/Coruscant_Shift) – A **two-round game** with a **random target sum** set by a gold die and a **tiebreaker suit** from a silver die. Played on the **Halcyon** at *Galactic Starcruiser*.\n'
    '• [**Kessel Sabacc**](https://starwars.fandom.com/wiki/Kessel_Sabacc) – A **three-round game** where players hold **exactly two cards**, featuring **Impostor (Ψ) and Sylop (Ø) cards**. Seen in *Star Wars Outlaws*.\n'
    '• [**Traditional Sabacc**](https://starwars.fandom.com/wiki/Sabacc) – A **high-stakes game** with **no set rounds**, where players aim for **+23 or -23** and can call **"Alderaan"** to end the game. Seen in *Star Wars: Rebels*.\n\n'

    '### **Game Rules & Variations**\n'
    'Each mode aims for a hand sum close to its target (0, a dice-determined value, or +23/-23), but they differ in decks and rules.\n'
    'For more details on Sabacc rules, card designs, and gameplay resources, visit **[Hyperspace Props](https://hyperspaceprops.com/sabacc-resources/)**.\n\n'

    '### **Additional Star Wars Apps**\n'
    'Want to translate **Aurebesh**? Check out:\n'
    '- **[Datapad | Aurebesh Translator](https://apps.apple.com/us/app/datapad-aurebesh-translator/id6450498054?platform=iphone)** – A feature-rich, immersive Aurebesh translator with a themed interface and keyboard.\n'
    '- **[Aurebesh Translator](https://apps.apple.com/us/app/aurebesh-translator/id6670201513?platform=iphone)** – A free, offline, ad-free translator for quick Aurebesh conversions.\n\n'

    '### **Credits & Disclaimers**\n'
    '• **Corellian Spike & Coruscant Shift Cards:** [Winz](https://cults3d.com/en/3d-model/game/sabacc-cards-and-spike-dice-printable)\n'
    '• **Kessel Sabacc Cards:** [u/Gold-Ad-4525](https://www.reddit.com/r/StarWarsSabacc/comments/1exatgi/kessel_sabaac_v3/)\n'
    '• **Traditional Sabacc Cards:** [Multiversal Exports Rick Scott](https://design.multiversalexports.com)\n'
    '• All other creative content is fan-made and not affiliated with or endorsed by Lucasfilm/Disney.\n\n'

    'Created by **[Abubakr Elmallah](https://abubakrelmallah.com/)**.\n\n'
    '[📂 GitHub Repository](https://github.com/TheAbubakrAbu/Sabacc-Droid)\n\n'

    'May the Force be with you—choose a game mode and have fun!'
)

sabacc_thumbnail = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/sabacc.png'
sabacc_footer = 'The Star Wars card game'

def get_comparison_embed() -> Embed:
    '''
    Create an embed comparing Corellian Spike, Coruscant Shift, Kessel, and Traditional Sabacc game modes.
    '''

    comparison_embed = Embed(
        title='Sabacc Game Modes Comparison',
        description=(
            '### **Similarities:**\n'
            '- All modes aim for a hand total as close as possible to a specific target (zero, dice-determined, or +23/-23).\n'
            '- Each includes Sylop (0) or equivalent special cards.\n'
            '- Strategic card selection is key to winning.\n\n'

            '### **Differences:**\n\n'
            
            '### **Corellian Spike Sabacc:**\n'
            '- **Deck Composition:** A 62-card deck ranging from -10 to -1 and +1 to +10, plus 2 Sylops (0 cards).\n'
            '- **Hand Limit:** No fixed limit; players can accumulate multiple cards.\n'
            '- **Rounds:** Typically **3 rounds**.\n'
            '- **Actions:** Draw, Replace, Discard (off by default; must be enabled in the game lobby), Stand, or Junk.\n'
            '- **Special Hands:** Complex ranking system (Pure Sabacc, Fleet, Yee-Haa, etc.).\n\n'

            '### **Coruscant Shift Sabacc:**\n'
            '- **Deck Composition:** Standard 62-card deck (+1 to +10 and -1 to -10 for suits ●, ▲, ■; plus 2 Sylops (0 cards)).\n'
            '- **Dice Mechanics:**\n'
            '  • **Gold Die:** Sets target number (-10, +10, -5, 5, 0, 0).\n'
            '  • **Silver Die:** Sets target suit (●, ▲, ■) for tie-breakers.\n'
            '- **Rounds:** Typically **2 rounds** of card selection.\n'
            '- **Tie-Breakers:** Closest to gold die target → most cards of silver die suit → highest positive sum → highest single positive card. If still tied, the game ends in a tie.\n\n'

            '### **Kessel Sabacc:**\n'
            '- **Deck Composition:** Two separate decks (Sand for positives, Blood for negatives), 22 cards each (44 total), plus Sylops (not exactly a 0 card).\n'
            '- **Hand Limit:** Exactly **2 cards** (1 positive, 1 negative).\n'
            '- **Rounds:** Typically **3 rounds**.\n'
            '- **Actions:** Draw, Replace, Discard (off by default; must be enabled in the game lobby), Stand, or Junk.\n'
            '- **Impostor Cards (Ψ):** Roll dice to assign or modify values.\n'
            '- **Sylop (Ø) Cards:** Mirror the value of the other card in hand.\n'
            '- **Special Hands:** Pure Sabacc, Prime Sabacc, etc., all aimed at total 0.\n\n'

            '### **Traditional Sabacc:**\n'
            '- **Deck Composition:** 76-card deck (4 suits of 15 cards, plus 16 special cards with unique values).\n'
            '- **Hand Limit:** No fixed limit; players can accumulate multiple cards.\n'
            '- **Rounds:** **No set number of rounds**; play continues until someone calls **"Alderaan"**.\n'
            '- **Actions:** Draw, Replace, Stand, Junk, or Call "Alderaan".\n'
            '- **Winning Target:** Closest to **+23 or -23**.\n'
            '- **Special Hands:**\n'
            '  • **Idiot’s Array (0, 2, 3)** beats all hands.\n'
            '  • **Natural Sabacc (+23/-23)** beats all except Idiot’s Array.\n'
            '  • **Fairy Empress (-2, -2, totaling -22)** beats a normal 22 but loses to Sabacc hands.\n\n'

            'Choose your preferred mode—may the Force be with you!'
        ),
        color=0x764920
    )
    comparison_embed.set_thumbnail(url=sabacc_thumbnail)
    comparison_embed.set_footer(text=sabacc_footer)

    return comparison_embed

corellian_thumbnail = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/corellian_spike.png'
corellian_footer = 'As seen in Solo: A Star Wars Story and Galaxy\'s Edge'

def get_corellian_spike_rules_embed() -> Embed:
    '''
    Create an embed containing the Corellian Spike Sabacc game rules.
    '''

    rules_embed = Embed(
        title='Corellian Spike Sabacc Game Rules',
        description='''### **Objective:**\n'
Achieve a hand with a total sum as close to zero as possible.\n\n'
### **Deck Composition:**\n'
- Single deck of **62 cards** ranging from **-10 to -1** and **+1 to +10**, plus 2 Sylops (0 cards).\n'
- There are **three copies** (staves) of each card value, both positive and negative.\n\n'
### **Gameplay Mechanics:**\n'
- Each player starts with **two cards**.\n'
- **Hand Limit:** No specific limit; you can hold multiple cards.\n'
- **Rounds:** The game is played over **3 rounds** by default.\n\n'
### **Available Actions:**\n'
- **Draw Card:** Draw one card from the deck.\n'
- **Replace Card:** Swap one card in your hand with a new one from the deck.\n'
- **Discard Card:** Remove one card from your hand.\n'
- **Stand:** Keep your current hand without changes.\n'
- **Junk:** Give up and exit the game.\n\n'
### **Hand Value Calculation:**\n'
- A player's hand value is the **sum** of all cards in their hand.\n'
- Players aim for a total hand value of **zero**.\n\n'
### **Ranking Corellian Spike Sabacc Hands (from best to worst):**\n\n'
1. **Pure Sabacc:** Two sylops (0): 0, 0.\n\n'
2. **Sarlacc Sabacc (Custom Hand):** Sum zero, at least two sylops (0), any number of cards\n   - Example: 0, 0, +3, -3\n\n'
3. **Full Sabacc:** 0, +10, +10, -10, -10.\n\n'
4. **Fleet:** Sum zero, one sylop (0), and four of a kind.\n   - Tie-breaker: Lowest card value.\n   - Example: 0, +5, +5, -5, -5\n\n'
5. **Twin Sun (Custom Hand):** Sum zero, one sylop (0), and at least two pairs.\n   - Tie-breaker: Lowest pair value.\n   - Example: 0, +5, -5, +3, -3\n\n'
6. **Yee-Haa:** Sum zero, one sylop (0), exactly 3 cards, and one pair.\n   - Tie-breaker: Lowest pair value.\n   - Example: 0, +5, -5\n\n'
7. **Kessel Run (Custom Hand):** Sum zero, one sylop (0), and at least one pair (no card limit).\n   - Tie-breaker: Lowest pair value.\n   - Example: 0, +4, -4, +8\n\n'
8. **Squadron:** Sum zero, four of a kind.\n   - Tie-breaker: Lowest card value.\n   - Example: +5, +5, -5, -5\n\n'
9. **Bantha's Wild:** Sum zero, three of a kind.\n   - Tie-breaker: Lowest card value.\n   - Example: +4, +4, +4, -3, -9 or +5, -5, +5, -3, -2\n\n'
10. **Rule of Two:** Sum zero, two pairs.\n   - Tie-breaker: Lowest pair value.\n   - Example: +3, +3, -5, +5, -6 or +9, -9, +4, -4\n\n'
11. **Sabacc Pair:** Sum zero, one pair (cards with the same absolute value).\n    - Pairs can be any sign: (+5, +5), (-5, -5), or (+5, -5).\n    - **Tie-breaker:** Lowest pair value (e.g., pair of 2 beats pair of 5).\n    - Example: +5, +5, -10 or +5, -5\n\n'
12. **Sabacc:** Sum zero, no special hands.\n    - **Tiebreakers (in order):**\n      1. Most cards in hand (the hand with the highest number of cards wins)\n      2. Highest positive sum (add all positive numbers, highest sum wins)\n      3. Highest single positive card (the hand with the single highest positive card)\n    - Example: +1, +2, -3\n\n'
13. **Nulrhek:** Sum not zero.\n    - **Tiebreakers (in order):**\n      1. Closest to zero (absolute value)\n      2. Positive totals beat negative if same distance (e.g., +3 beats -3)\n      3. Most cards in hand\n      4. Highest positive sum\n      5. Highest single positive card\n    - Example: Total of +1 beats total of -1\n\n'
Good luck! May the Force be with you!''',
        color=0x764920
    )
    rules_embed.set_thumbnail(url=corellian_thumbnail)
    rules_embed.set_footer(text=corellian_footer)

    return rules_embed

coruscant_thumbnail = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/coruscant_shift.png'
coruscant_footer = 'As seen on the Halcyon at Galactic Starcruiser'

def get_coruscant_shift_rules_embed() -> Embed:
    '''
    Create an embed containing the Coruscant Shift Sabacc game rules.
    '''

    rules_embed = Embed(
        title='Coruscant Shift Sabacc Game Rules',
        description='### **Objective:**\n'
                    'Achieve a final hand (between **1 and 5 cards**) whose total is as close as possible to the target number determined by the gold die.'
                    'If there is a tie, the winner is determined by who has the most cards matching the target suit (from the silver die).'
                    'Further ties are decided by highest positive “added total” (the sum of all cards in your hand), then highest single positive card (the largest positive-value card in your hand). If still tied, the game ends in a tie.\n\n'

                    '### **Deck Composition:**\n'
                    '- **62 cards** total.\n'
                    '- **3 suits** (●, ▲, ■), each containing **20 cards**: +1 to +10 and -1 to -10.\n'
                    '- **2 Sylop (0)** cards act as wild/wildcard suits.\n\n'

                    '### **Gameplay Mechanics:**\n'
                    '- You start each round with **5 cards**.\n'
                    '- The **gold die** (faces: -10, 10, -5, 5, 0, 0) sets the target number.\n'
                    '- The **silver die** (faces: two each of ●, ▲, ■) sets the target suit.\n\n'

                    '### **Rounds:**\n'
                    '- By default, Coruscant Shift is played over **2 rounds** of card selection.\n'
                    '- **Round 1 – Selection & Shift:**\n'
                    '  1. Each player is dealt 5 cards.\n'
                    '  2. In turn order, choose which cards you want to keep (face down). Any unkept cards are discarded.\n'
                    '- **Round 2 – Final Selection & Reveal:**\n'
                    '  1. Draw new cards equal to the number discarded, returning you to 5 cards.\n\n'
                    '  2. Each player again selects which cards to keep.\n'
                    '  3. You **cannot** discard any card you kept from Round 1. You may only discard newly drawn cards.\n'
                    '  4. Reveal all final hands.\n\n'

                    '### **Hand Value Calculation:**\n'
                    '- Each card contributes its face value (+ or -). Sylops (0) can count as any suit.\n'
                    '- Your final total is simply the sum of all cards you kept.\n\n'

                    '### **Tie-Breakers:**\n'
                    '1. Closest to the target number (absolute difference).\n'
                    '2. Most cards matching the target suit (Sylop counts as a match).\n'
                    '3. Highest total (if two players are equally close to the target, the higher total wins—so positive totals beat negative totals).\n'
                    '4. Highest single positive card (largest positive-value card in hand).\n'
                    '5. If still tied, the game ends in a tie.\n\n'

                    'Good luck! May the Force be with you!',
        color=0x764920
    )
    rules_embed.set_thumbnail(url=coruscant_thumbnail)
    rules_embed.set_footer(text=coruscant_footer)

    return rules_embed

kessel_thumbnail = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/kessel.png'
kessel_footer = 'As seen in Star Wars Outlaws'

def get_kessel_rules_embed() -> Embed:
    '''
    Create an embed containing the Kessel Sabacc game rules.
    '''

    rules_embed = Embed(
        title='Kessel Sabacc Game Rules',
        description='### **Objective:**\n'
                    'Achieve a hand with a total sum as close to zero as possible.\n\n'
                    '### **Deck Composition:**\n'
                    '- Two decks: Sand (positive cards) and Blood (negative cards), each comprising **22 cards** (44 total).\n'
                    '- Each deck contains:\n'
                    '   - Value cards from **-6 to -1** and **+1 to +6**, with **three copies** (staves) of each.\n'
                    '   - Three Impostor cards (marked with this symbol: Ψ).\n'
                    '   - One Sylop card (marked with this symbol: Ø).\n\n'
                    '### **Gameplay Mechanics:**\n'
                    '- Each player starts with **two cards**: one from Sand (positive) and one from Blood (negative).\n'
                    '- **Hand Limit:** You can only have **2 cards** in your hand at any time, one positive and one negative.\n'
                    '- **Rounds:** The game is played over **3 rounds** by default.\n\n'
                    '### **Available Actions:**\n'
                    '- **Draw Card:** Draw one card from either deck.\n'
                    '   - After drawing, you must discard one of your existing cards to maintain a hand of two cards.\n'
                    '- **Stand:** Keep your current hand without changes.\n'
                    '- **Junk:** Give up and exit the game.\n\n'
                    '### **Hand Value Calculation:**\n'
                    '- A player\'s hand value is the **sum** of their two cards (positive plus negative).\n'
                    '- Players aim for a hand value of zero for a Sabacc hand.\n'
                    '- **Impostor (Ψ) Cards:**\n'
                    '   - At the end of each round, every player who has an Impostor card will roll two dice and choose one of the rolled values to assign to their Impostor card.\n'
                    '   - If a player has two Impostor cards (one positive and one negative), they will perform this action twice, rolling a total of four dice.\n'
                    '   - This mechanic introduces an element of luck, allowing players to potentially enhance or harm their hands.\n'
                    '- **Sylop (Ø) Cards:**\n'
                    '   - A Sylop card takes the value of the other card in your hand.\n'
                    '   - If you have two Sylops, they both count as zero (best hand in the game).\n\n'
                    '### **Ranking Kessel Sabacc Hands (from best to worst):**\n\n'
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
                    '   - Tie-breakers:\n'
                    '     1. Closest to zero wins.\n'
                    '     2. Positive totals beat negative totals.\n'
                    '     3. Highest positive card wins.\n\n'
                    'Good luck! May the Force be with you!',
        color=0x764920
    )
    rules_embed.set_thumbnail(url=kessel_thumbnail)
    rules_embed.set_footer(text=kessel_footer)

    return rules_embed

traditional_thumbnail = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/traditional.png'
traditional_footer = 'As seen in Star Wars: Rebels'

def get_traditional_rules_embed() -> Embed:
    '''
    Create an embed containing the Traditional Sabacc game rules.
    '''

    rules_embed = Embed(
        title='Traditional Sabacc Game Rules',
        description='### **Objective:**\n'
                    'Achieve a hand with a total sum as close to **+23 or -23** as possible.\n\n'
                    '### **Deck Composition:**\n'
                    '- **76 cards** total.\n'
                    '- **4 suits** (Flasks, Sabers, Staves, and Coins), each containing **15 cards** (60 total).\n'
                    '- **16 special (neutral/negative) cards** consisting of **2 copies each** of the following 8 unique cards:\n'
                    '  - The Idiot (0), Balance (-11), Endurance (-8), Moderation (-14), The Evil One (-15), The Queen of Air and Darkness (-2), Demise (-13), The Star (-17).\n\n'
                    '### **Gameplay Mechanics:**\n'
                    '- Each player starts with **two cards**.\n'
                    '- **Hand Limit:** No specific limit; players can accumulate multiple cards.\n'
                    '### **Rounds:** There is **no set number of rounds**; play continues until a player calls **"Alderaan"** to end the game.\n\n'
                    '### **Available Actions:**\n'
                    '- **Draw Card:** Draw one card from the deck.\n'
                    '- **Replace Card:** Draw a new card and discard one from your hand.\n'
                    '- **Discard Card:** Remove one card from your hand (only after Replace Card, not at the end of your turn).\n'
                    '- **Call "Alderaan":** End the round and reveal hands.\n'
                    '- **Stand:** Keep your current hand without changes.\n'
                    '- **Junk:** Give up and exit the game.\n\n'
                    '### **Hand Value Calculation:**\n'
                    '- A player\'s hand value is the **sum** of all cards in their hand.\n'
                    '- Players aim for a total hand value of **+23 or -23**.\n\n'
                    '### **Ranking Traditional Sabacc Hands (from best to worst):**\n\n'
                    '1. **Idiot’s Array:** A hand of **0, 2, and 3** (literal 23).\n'
                    '   - **Beats a 23 or -23** and **wins the Sabacc pot**.\n'
                    '   - Example: 0 (The Idiot), 2, 3.\n\n'
                    '2. **Natural Sabacc:** A hand that totals exactly **+23 or -23**.\n'
                    '   - **Beats all hands except Idiot’s Array**.\n'
                    '   - If multiple players have Natural Sabacc, tiebreakers are:\n'
                    '      1. Most cards in hand.\n'
                    '      2. Highest absolute value sum.\n'
                    '      3. Highest single absolute value card.\n'
                    '   - Example: +15, +8 or -15, -8.\n\n'
                    '3. **Fairy Empress:** A hand of **-2 and -2** (literal -22).\n'
                    '   - **Beats a 22 or -22** but **loses to a Natural Sabacc hand (+23/-23)**.\n'
                    '   - Example: -2 (The Queen of Air and Darkness), -2.\n\n'
                    '4. **Nulrhek:** Sum not zero.\n'
                    '    - Tie-breakers:\n'
                    '      1. Closest to 23 or -23 (absolute value).\n'
                    '      2. Negative totals beat positive totals if same distance.\n'
                    '      3. Most cards in hand.\n'
                    '      4. Highest absolute value sum.\n'
                    '      5. Highest single absolute value card.\n'
                    '    - If still tied, the game ends in a tie.\n'
                    '    - Example: Total of -22 beats total of +22\n\n'
                    'Good luck! May the Force be with you!',
        color=0x7A9494
    )
    rules_embed.set_thumbnail(url=traditional_thumbnail)
    rules_embed.set_footer(text=traditional_footer)

    return rules_embed