# rules.py

from discord import Embed

def plural(count: int, word: str) -> str:
    '''
    Return the count with the word, adding an s unless the count is 1 (for example, 1 round or 3 rounds).
    '''

    return f'{count} {word}' if count == 1 else f'{count} {word}s'

RULES_DESCRIPTION = (
    'Welcome to **Sabacc Droid**! You can play any of these four Sabacc variants:\n\n'
    '- [**Corellian Spike Sabacc**](https://starwars.fandom.com/wiki/Corellian_Spike): A **3-round** game where players aim for **0**, featuring **Sylop (0)** cards. Seen in *Solo: A Star Wars Story* and *Galaxy\'s Edge*.\n'
    '- [**Coruscant Shift Sabacc**](https://starwars.fandom.com/wiki/Coruscant_Shift): A **2-round** game with a **random target number** set by a gold die and a **target suit** for tiebreakers set by a silver die. Played on the *Halcyon* at *Galactic Starcruiser*.\n'
    '- [**Kessel Sabacc**](https://starwars.fandom.com/wiki/Kessel_Sabacc): A **3-round** game where each player holds **exactly 2 cards**, featuring **Impostor (Ψ)** and **Sylop (Ø)** cards. Seen in *Star Wars Outlaws*.\n'
    '- [**Traditional Sabacc**](https://starwars.fandom.com/wiki/Sabacc): A game with **no set number of rounds** where players aim for **+23 or -23** and anyone can **call Alderaan** to end the game. Seen in *Star Wars Rebels*.\n\n'

    '### Game Rules\n'
    'Every variant aims for a hand total close to its target (0, a dice-determined number, or +23/-23), but each has its own deck and rules. Use the buttons below to read the full rules for each variant.\n'
    'For more on Sabacc rules, card designs, and gameplay resources, visit **[Hyperspace Props](https://hyperspaceprops.com/sabacc-resources/)**.\n\n'

    '### More Star Wars Apps\n'
    'Want to translate **Aurebesh**? Check out:\n'
    '- **[Datapad | Aurebesh Translator](https://apps.apple.com/us/app/datapad-aurebesh-translator/id6450498054?platform=iphone)**: A feature-rich, immersive Aurebesh translator with a themed interface and keyboard.\n'
    '- **[Aurebesh Translator](https://apps.apple.com/us/app/aurebesh-translator/id6670201513?platform=iphone)**: A free, offline, ad-free translator for quick Aurebesh conversions.\n\n'

    '### Credits & Disclaimers\n'
    '- **Corellian Spike & Coruscant Shift Cards:** [Winz](https://cults3d.com/en/3d-model/game/sabacc-cards-and-spike-dice-printable)\n'
    '- **Kessel Sabacc Cards:** [u/Gold-Ad-4525](https://www.reddit.com/r/StarWarsSabacc/comments/1exatgi/kessel_sabaac_v3/)\n'
    '- **Traditional Sabacc Cards:** [Multiversal Exports Rick Scott](https://design.multiversalexports.com)\n'
    '- All other creative content is fan-made and not affiliated with or endorsed by Lucasfilm or Disney.\n\n'

    'Created by **[Abubakr Elmallah](https://abubakrelmallah.com/)**.\n\n'
    '[📂 GitHub Repository](https://github.com/TheAbubakrAbu/Sabacc-Droid)\n\n'

    'Choose a variant and have fun. May the Force be with you!'
)

sabacc_thumbnail = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/sabacc.png'
sabacc_footer = 'The Star Wars card game'

def get_comparison_embed() -> Embed:
    '''
    Create an embed comparing the Corellian Spike, Coruscant Shift, Kessel, and Traditional Sabacc variants.
    '''

    comparison_embed = Embed(
        title='Sabacc Variant Comparison',
        description=(
            '### Similarities\n'
            '- Every variant aims for a hand total as close as possible to a target (0, a dice-determined number, or +23/-23).\n'
            '- Every variant has Sylops or similar special cards.\n'
            '- Smart card choices are the key to winning.\n\n'

            '### Corellian Spike Sabacc\n'
            '- **Deck:** 62 cards: -10 to -1 and +1 to +10 (three of each), plus 2 Sylops (0).\n'
            '- **Hand Limit:** None; players can hold any number of cards.\n'
            '- **Rounds:** 3 by default.\n'
            '- **Actions:** Draw, Replace, Discard (off by default; turn it on in the lobby), Stand, or Junk.\n'
            '- **Special Hands:** A detailed ranking (Pure Sabacc, Fleet, Yee-Haa, and more).\n\n'

            '### Coruscant Shift Sabacc\n'
            '- **Deck:** 62 cards: +1 to +10 and -1 to -10 in each of three suits (●, ▲, ■), plus 2 Sylops (0).\n'
            '- **Dice:**\n'
            '   - **Gold Die:** Sets the target number (-10, +10, -5, +5, 0, 0).\n'
            '   - **Silver Die:** Sets the target suit (●, ▲, ■) for tiebreakers.\n'
            '- **Rounds:** 2 by default.\n'
            '- **Actions:** Choose which cards to keep, or Junk.\n'
            '- **Tiebreakers:** Closest to the target number, then most cards in the target suit, then highest total, then highest single positive card. If still tied, the game ends in a tie.\n\n'

            '### Kessel Sabacc\n'
            '- **Deck:** Two decks, Sand (positive) and Blood (negative), with 22 cards each (44 total), including Impostors and Sylops.\n'
            '- **Hand Limit:** Exactly **2 cards** (1 positive, 1 negative).\n'
            '- **Rounds:** 3 by default.\n'
            '- **Actions:** Draw (then keep either the drawn card or your existing one), Stand, or Junk.\n'
            '- **Impostor (Ψ) Cards:** Roll two dice at the end of the game and pick one value.\n'
            '- **Sylop (Ø) Cards:** Take the value of the other card in your hand.\n'
            '- **Special Hands:** Pure Sabacc, Prime Sabacc, and more, all with a total of 0.\n\n'

            '### Traditional Sabacc\n'
            '- **Deck:** 76 cards: 4 suits of 15 cards, plus 16 special cards with unique values.\n'
            '- **Hand Limit:** None; players can hold any number of cards.\n'
            '- **Rounds:** No set number; play continues until someone calls **Alderaan**.\n'
            '- **Actions:** Draw, Replace, Discard (off by default; turn it on in the lobby), Stand, Junk, or Call Alderaan.\n'
            '- **Target:** Closest to **+23 or -23**.\n'
            '- **Special Hands:**\n'
            '   - **Idiot\'s Array (0, +2, +3):** Beats every other hand.\n'
            '   - **Natural Sabacc (+23 or -23):** Beats every hand except Idiot\'s Array.\n'
            '   - **Fairy Empress (-2, -2, read as -22):** Beats a normal 22 but loses to a Natural Sabacc.\n\n'

            'Good luck, and may the Force be with you!'
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
    Create an embed containing the Corellian Spike Sabacc rules.
    '''

    rules_embed = Embed(
        title='Corellian Spike Sabacc Rules',
        description='### Objective\n'
                    'Get a hand total as close to **0** as possible.\n\n'

                    '### Deck\n'
                    '- **62 cards:** -10 to -1 and +1 to +10, plus 2 Sylops (0).\n'
                    '- There are **three copies** (staves) of each value, positive and negative.\n\n'

                    '### Gameplay\n'
                    '- Each player starts with **2 cards** by default.\n'
                    '- **Hand Limit:** None; you can hold any number of cards.\n'
                    '- **Rounds:** 3 by default.\n\n'

                    '### Actions\n'
                    '- **Draw Card:** Draw one card from the deck.\n'
                    '- **Replace Card:** Swap one card in your hand for a new card from the deck.\n'
                    '- **Discard Card:** Remove one card from your hand (only when discarding is turned on in the lobby).\n'
                    '- **Stand:** Keep your hand as it is.\n'
                    '- **Junk:** Give up and leave the game.\n\n'

                    '### Hand Value\n'
                    '- Your hand value is the **sum** of all your cards.\n'
                    '- The goal is a total of **0**.\n\n'

                    '### Hand Rankings (Best to Worst)\n'
                    '1. **Pure Sabacc:** Exactly two Sylops.\n'
                    '   - Example: 0, 0\n\n'
                    '2. **Sarlacc Sabacc (Custom Hand):** Total of 0 with at least two Sylops and any number of cards.\n'
                    '   - Example: 0, 0, +3, -3\n\n'
                    '3. **Full Sabacc:** A Sylop with +10, +10, -10, -10.\n'
                    '   - Example: 0, +10, +10, -10, -10\n\n'
                    '4. **Fleet:** Total of 0, one Sylop, and four of a kind.\n'
                    '   - Tiebreaker: Lowest card value.\n'
                    '   - Example: 0, +5, +5, -5, -5\n\n'
                    '5. **Twin Sun (Custom Hand):** Total of 0, one Sylop, and at least two pairs.\n'
                    '   - Tiebreaker: Lowest pair value.\n'
                    '   - Example: 0, +5, -5, +3, -3\n\n'
                    '6. **Yee-Haa:** Total of 0, one Sylop, and one pair (exactly 3 cards).\n'
                    '   - Tiebreaker: Lowest pair value.\n'
                    '   - Example: 0, +5, -5\n\n'
                    '7. **Kessel Run (Custom Hand):** Total of 0, one Sylop, and at least one pair (any number of cards).\n'
                    '   - Tiebreaker: Lowest pair value.\n'
                    '   - Example: 0, +4, +4, -8\n\n'
                    '8. **Squadron:** Total of 0 and four of a kind.\n'
                    '   - Tiebreaker: Lowest card value.\n'
                    '   - Example: +5, +5, -5, -5\n\n'
                    '9. **Bantha\'s Wild:** Total of 0 and three of a kind.\n'
                    '   - Tiebreaker: Lowest card value.\n'
                    '   - Example: +4, +4, +4, -3, -9 or +5, -5, +5, -3, -2\n\n'
                    '10. **Rule of Two:** Total of 0 and two pairs.\n'
                    '   - Tiebreaker: Lowest pair value.\n'
                    '   - Example: +3, +3, -5, +5, -6 or +9, -9, +4, -4\n\n'
                    '11. **Sabacc Pair:** Total of 0 and one pair (two cards with the same absolute value).\n'
                    '   - A pair can have any signs: (+5, +5), (-5, -5), or (+5, -5).\n'
                    '   - Tiebreaker: Lowest pair value (a pair of 2s beats a pair of 5s).\n'
                    '   - Example: +5, +5, -10 or +5, -5\n\n'
                    '12. **Sabacc:** Total of 0 with no special hand.\n'
                    '   - Tiebreakers (in order):\n'
                    '      1. Most cards in hand\n'
                    '      2. Highest sum of positive cards\n'
                    '      3. Highest single positive card\n'
                    '   - Example: +1, +2, -3\n\n'
                    '13. **Nulrhek:** Any total other than 0.\n'
                    '   - Tiebreakers (in order):\n'
                    '      1. Closest to 0\n'
                    '      2. Positive beats negative at the same distance (+3 beats -3)\n'
                    '      3. Most cards in hand\n'
                    '      4. Highest sum of positive cards\n'
                    '      5. Highest single positive card\n'
                    '   - Example: A total of +1 beats a total of -1\n\n'

                    'Good luck, and may the Force be with you!',
        color=0x764920
    )
    rules_embed.set_thumbnail(url=corellian_thumbnail)
    rules_embed.set_footer(text=corellian_footer)

    return rules_embed

coruscant_thumbnail = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/coruscant_shift.png'
coruscant_footer = 'As seen on the Halcyon at Galactic Starcruiser'

def get_coruscant_shift_rules_embed() -> Embed:
    '''
    Create an embed containing the Coruscant Shift Sabacc rules.
    '''

    rules_embed = Embed(
        title='Coruscant Shift Sabacc Rules',
        description='### Objective\n'
                    'Finish with a hand (1 to 5 cards by default) whose total is as close as possible to the **target number** rolled on the gold die. '
                    'Ties go to the player with the most cards in the **target suit** rolled on the silver die.\n\n'

                    '### Deck\n'
                    '- **62 cards** total.\n'
                    '- **3 suits** (●, ▲, ■), each with **20 cards**: +1 to +10 and -1 to -10.\n'
                    '- **2 Sylops (0)**, which count as a match for any suit.\n\n'

                    '### Dice\n'
                    '- The **gold die** (faces: -10, +10, -5, +5, 0, 0) sets the target number.\n'
                    '- The **silver die** (faces: two each of ●, ▲, ■) sets the target suit.\n\n'

                    '### Rounds\n'
                    'Coruscant Shift is played over **2 rounds** by default.\n'
                    '- **Round 1: Selection and Shift**\n'
                    '   1. Each player is dealt 5 cards.\n'
                    '   2. On your turn, choose which cards to keep. Any cards you don\'t keep are discarded.\n'
                    '- **Round 2: Final Selection and Reveal**\n'
                    '   1. Draw back up to 5 cards.\n'
                    '   2. Choose which cards to keep again.\n'
                    '   3. Cards you kept in Round 1 are locked in; you can only discard newly drawn cards.\n'
                    '   4. All final hands are revealed.\n\n'

                    '### Actions\n'
                    '- **Toggle a Card:** Choose whether to keep (✅) or discard (❌) each card.\n'
                    '- **Confirm Selection:** Lock in your choices and end your turn.\n'
                    '- **Junk:** Give up and leave the game.\n\n'

                    '### Hand Value\n'
                    '- Each card counts for its face value (+ or -). Sylops count as 0.\n'
                    '- Your final total is the sum of the cards you kept.\n\n'

                    '### Winning and Tiebreakers\n'
                    '1. **Pure Sabacc** (exactly two Sylops) beats every other hand.\n'
                    '2. Closest to the target number.\n'
                    '3. Most cards matching the target suit (Sylops count as a match).\n'
                    '4. Highest total (at the same distance, a positive total beats a negative one).\n'
                    '5. Highest single positive card.\n'
                    '6. If still tied, the game ends in a tie.\n\n'

                    'Good luck, and may the Force be with you!',
        color=0x764920
    )
    rules_embed.set_thumbnail(url=coruscant_thumbnail)
    rules_embed.set_footer(text=coruscant_footer)

    return rules_embed

kessel_thumbnail = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/kessel.png'
kessel_footer = 'As seen in Star Wars Outlaws'

def get_kessel_rules_embed() -> Embed:
    '''
    Create an embed containing the Kessel Sabacc rules.
    '''

    rules_embed = Embed(
        title='Kessel Sabacc Rules',
        description='### Objective\n'
                    'Get a hand total as close to **0** as possible.\n\n'

                    '### Deck\n'
                    '- Two decks: **Sand** (positive) and **Blood** (negative), with **22 cards** each (44 total).\n'
                    '- Each deck has:\n'
                    '   - Value cards from **1 to 6** (+1 to +6 in Sand, -1 to -6 in Blood), with **three copies** (staves) of each.\n'
                    '   - Three **Impostor** cards (Ψ).\n'
                    '   - One **Sylop** card (Ø).\n\n'

                    '### Gameplay\n'
                    '- Each player starts with **2 cards**: one from Sand (positive) and one from Blood (negative).\n'
                    '- **Hand Limit:** Always exactly **2 cards**, one positive and one negative.\n'
                    '- **Rounds:** 3 by default.\n\n'

                    '### Actions\n'
                    '- **Draw Positive / Draw Negative:** Draw one card from that deck, then keep either the drawn card or your existing card of that sign.\n'
                    '- **Stand:** Keep your hand as it is.\n'
                    '- **Junk:** Give up and leave the game.\n\n'

                    '### Hand Value\n'
                    '- Your hand value is the **sum** of your two cards (positive plus negative).\n'
                    '- A total of **0** is a Sabacc hand.\n'
                    '- **Impostor (Ψ) Cards:**\n'
                    '   - At the end of the game, every player holding an Impostor rolls two dice and picks one of the rolled values for that card.\n'
                    '   - A player with two Impostors (one positive, one negative) does this twice, rolling four dice in total.\n'
                    '   - This adds an element of luck that can help or hurt your hand.\n'
                    '- **Sylop (Ø) Cards:**\n'
                    '   - A Sylop takes the value of the other card in your hand.\n'
                    '   - Two Sylops both count as 0 (the best hand in the game).\n\n'

                    '### Hand Rankings (Best to Worst)\n'
                    '1. **Pure Sabacc:** A pair of Sylops (both count as 0).\n'
                    '   - Example: 0, 0\n\n'
                    '2. **Prime Sabacc:** A pair of 1s.\n'
                    '   - Example: +1, -1\n\n'
                    '3. **Standard Sabacc:** A positive and a negative card with the same absolute value.\n'
                    '   - Lower values rank higher: +2, -2 beats +3, -3.\n'
                    '   - The best is **+1, -1** and the worst is **+6, -6**.\n'
                    '   - Example: +5, -5\n\n'
                    '4. **Cheap Sabacc (Worst Sabacc Hand):** A pair of 6s.\n'
                    '   - Still beats every Nulrhek hand because the total is 0.\n'
                    '   - Example: +6, -6\n\n'
                    '5. **Nulrhek:** Any total other than 0.\n'
                    '   - Tiebreakers (in order):\n'
                    '      1. Closest to 0\n'
                    '      2. Positive beats negative at the same distance\n'
                    '      3. Highest positive card\n\n'

                    'Good luck, and may the Force be with you!',
        color=0x764920
    )
    rules_embed.set_thumbnail(url=kessel_thumbnail)
    rules_embed.set_footer(text=kessel_footer)

    return rules_embed

traditional_thumbnail = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/traditional.png'
traditional_footer = 'As seen in Star Wars Rebels'

def get_traditional_rules_embed() -> Embed:
    '''
    Create an embed containing the Traditional Sabacc rules.
    '''

    rules_embed = Embed(
        title='Traditional Sabacc Rules',
        description='### Objective\n'
                    'Get a hand total as close to **+23 or -23** as possible.\n\n'

                    '### Deck\n'
                    '- **76 cards** total.\n'
                    '- **4 suits** (Flasks, Sabers, Staves, and Coins) with **15 cards** each (60 total).\n'
                    '- **16 special cards**: **2 copies** each of these 8 cards:\n'
                    '   - The Idiot (0), Balance (-11), Endurance (-8), Moderation (-14), The Evil One (-15), The Queen of Air and Darkness (-2), Demise (-13), and The Star (-17).\n\n'

                    '### Gameplay\n'
                    '- Each player starts with **2 cards** by default.\n'
                    '- **Hand Limit:** None; you can hold any number of cards.\n'
                    '- **Rounds:** No set number; play continues until a player calls **Alderaan**.\n\n'

                    '### Actions\n'
                    '- **Draw Card:** Draw one card from the deck.\n'
                    '- **Replace Card:** Swap one card in your hand for a new card from the deck.\n'
                    '- **Discard Card:** Remove one card from your hand (only when discarding is turned on in the lobby).\n'
                    '- **Stand:** Keep your hand as it is.\n'
                    '- **Junk:** Give up and leave the game.\n'
                    '- **Call Alderaan:** Every other player gets one final turn, then all hands are revealed.\n\n'

                    '### Hand Value\n'
                    '- Your hand value is the **sum** of all your cards.\n'
                    '- The goal is a total of **+23 or -23**.\n\n'

                    '### Hand Rankings (Best to Worst)\n'
                    '1. **Idiot\'s Array:** Exactly **0, +2, +3** (read as a literal 23).\n'
                    '   - Beats every other hand, including a Natural Sabacc.\n'
                    '   - Example: 0 (The Idiot), +2, +3\n\n'
                    '2. **Natural Sabacc:** A total of exactly **+23 or -23**.\n'
                    '   - Beats every hand except Idiot\'s Array.\n'
                    '   - Tiebreakers (in order):\n'
                    '      1. Most cards in hand\n'
                    '      2. Highest absolute total\n'
                    '      3. Highest single absolute card value\n'
                    '   - Example: +15, +8 or -15, -8\n\n'
                    '3. **Fairy Empress:** Exactly **-2, -2** (read as a literal -22).\n'
                    '   - Beats a 22 or -22 but loses to a Natural Sabacc.\n'
                    '   - Example: -2 (The Queen of Air and Darkness), -2\n\n'
                    '4. **Nulrhek:** Any other hand.\n'
                    '   - Tiebreakers (in order):\n'
                    '      1. Closest to +23 or -23\n'
                    '      2. Negative beats positive at the same distance\n'
                    '      3. Most cards in hand\n'
                    '      4. Highest absolute total\n'
                    '      5. Highest single absolute card value\n'
                    '   - If still tied, the game ends in a tie.\n'
                    '   - Example: A total of -22 beats a total of +22\n\n'

                    'Good luck, and may the Force be with you!',
        color=0x7A9494
    )
    rules_embed.set_thumbnail(url=traditional_thumbnail)
    rules_embed.set_footer(text=traditional_footer)

    return rules_embed
