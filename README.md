# Sabacc Droid - Discord Bot

*Supports Corellian Spike, Coruscant Shift, Kessel, and Traditional Sabacc*

Welcome to the **Sabacc Droid**! This project brings the classic Star Wars card game Sabacc to life with multiple exciting versions:

1. **Console Version (`sabacc_console.py`)**: Play the Corellian Spike variant (prototype of Sabacc Droid) in your terminal or IDE.
2. **Discord Bot Version (`sabacc_droid.py`)**: Play Corellian Spike, Coruscant Shift, Kessel, and Traditional Sabacc by creating your own Discord bot. Or simply invite the bot to your server here: [**Invite Link**](https://discord.ly/sabaac-droid)

Experience the thrill of Sabacc as seen in _Galaxy's Edge_, _Solo: A Star Wars Story_, _Star Wars Outlaws_, and _Star Wars: Rebels_.

Created by **Abubakr Elmallah** on **November 14, 2024**.

[**Add Sabacc Droid to Your Server**](https://discord.ly/sabacc-droid)

<a href="https://discord.ly/sabacc-droid">
  <img src="logo.png" alt="Logo" width="120" style="border-radius:10px;"/>
</a>

## Features

### Console Version (Corellian Spike Sabacc)

- **Prototype of Sabacc Droid**: View the original prototype before Sabacc Droid existed.
- **Classic Gameplay**: Play the Corellian Spike variant against a computer opponent.
- **Simple Interface**: Enjoy a text-based interface that's easy to navigate.

### Discord Bot Version (All Four Variants)

- **Multiplayer Support**: Play with up to 8 players on a Discord server.
- **Interactive Gameplay**: Use buttons and embeds for seamless interaction.
- **Automated Game Management**: The bot handles turn order, card dealing, and scoring.
- **Game Variants**:  
  - **[Corellian Spike Sabacc](https://starwars.fandom.com/wiki/Corellian_Spike)** – Featured in *Solo: A Star Wars Story* and *Galaxy’s Edge*, this is a fast-paced version of Sabacc with three rounds and a target hand sum of **zero**.
  - **[Coruscant Shift Sabacc](https://starwars.fandom.com/wiki/Coruscant_Shift)** – Played on the **Halcyon** at *Galactic Starcruiser*, this variant uses dice mechanics to set the winning hand target.
  - **[Kessel Sabacc](https://starwars.fandom.com/wiki/Kessel_Sabacc)** – Featured in *Star Wars Outlaws*, this mode includes unique **Impostor** and **Sylop** cards with special mechanics.
  - **[Traditional Sabacc](https://starwars.fandom.com/wiki/Sabacc)** – Featured in *Star Wars: Rebels*, including a high-stakes game aiming for a total of **+23 or -23**.
- **Rulebook Access**: View game rules directly in Discord for all variants.

## Getting Started

### Console Version

1. **Install Python 3.12 or Higher**: Ensure you have Python 3.12+ installed on your system (earlier versions may work but are not tested).

2. **Run the Game**:
    ```bash
    python sabacc_console.py
    ```

### Discord Bot Version

- **Add the Bot to Your Server**: [Invite Link](https://discord.ly/sabaac-droid)
- If you want to make your own Discord Sabacc bot, watch this video: https://www.youtube.com/watch?v=UYJDKSah-Ww&t=330s, then replace the `.py` files you created with the modules in `src`.

## Game Rules & Variations

Each mode aims for a hand sum close to its target (0, a dice-determined value, or +23/-23), but they differ in decks and rules.
For more details on Sabacc rules, card designs, and gameplay resources, visit **[Hyperspace Props](https://hyperspaceprops.com/sabacc-resources/)**.

### **Default Game Settings:**
- **Corellian Spike and Kessel Sabacc** each have **3 rounds** and **2 starting cards**.
- **Coruscant Shift Sabacc** has **2 rounds** and **5 starting cards**.
- **Traditional Sabacc** has **2 starting cards** and an **unlimited amount** of rounds until someone calls "Alderaan" to end the game.

### **Game Variations**

#### **Corellian Spike Sabacc**
- **Deck:** 62-card deck (-10 to -1 and +1 to +10, plus 2 Sylops (0 cards)).
- **Rounds:** 3 rounds.
- **Actions:** Draw, Discard, Replace, Stand, or Junk.
- **Winning Target:** Closest to 0.
- **Special Hands:** Pure Sabacc, Fleet, Yee-Haa, etc.

#### **Coruscant Shift Sabacc**
- **Deck:** Standard 62-card deck (+1 to +10 and -1 to -10 for suits ●, ▲, ■; plus 2 Sylops (0 cards)).
- **Dice Mechanics:**
  - **Gold Die:** Sets target number (-10, +10, -5, 5, 0, 0).
  - **Silver Die:** Sets target suit (●, ▲, ■) for tie-breakers.
- **Rounds:** 2 rounds.
- **Winning Target:** Closest to gold die target.
- **Tie-Breakers:** Closest to gold die target → most cards of silver die suit → highest positive sum → highest single positive card → sudden death.

#### **Kessel Sabacc**
- **Deck:** Two separate decks (Sand for positives, Blood for negatives), 22 cards each (44 total), plus Sylops.
- **Hand Limit:** Exactly **2 cards** (1 positive, 1 negative).
- **Rounds:** 3 rounds.
- **Actions:** Draw (then discard to maintain 2 cards), Stand, or Junk.
- **Winning Target:** Closest to 0.
- **Special Mechanics:**
  - **Impostor Cards (Ψ):** Roll dice to assign or modify values.
  - **Sylop (Ø) Cards:** Mirror the value of the other card in hand.
  - **Special Hands:** Pure Sabacc, Prime Sabacc, etc.

#### **Traditional Sabacc**
- **Deck:** 76-card deck (4 suits of 15 cards, plus 16 special cards with unique values).
- **Hand Limit:** No fixed limit; players can accumulate multiple cards.
- **Rounds:** No set number of rounds; play continues until someone calls **"Alderaan"**.
- **Actions:** Draw, Replace, Stand, Junk, or Call "Alderaan".
- **Winning Target:** Closest to **+23 or -23**.
- **Special Hands:**
  - **Idiot’s Array (0, 2, 3)** beats all hands.
  - **Natural Sabacc (+23/-23)** beats all except Idiot’s Array.
  - **Fairy Empress (-2, -2, totaling -22)** beats a normal 22 but loses to Sabacc hands.

## Privacy & Data

**Sabacc Droid** respects your privacy:
- **No Personal Data Collected** – Only temporary game data is stored.
- **Secure & Compliant** – Fully adheres to Discord’s Terms of Service and Privacy Policy.

## License

This project is licensed under the [MIT License](LICENSE). Feel free to use, modify, and distribute the code, but please provide attribution.

## Feedback

I would love to hear your thoughts and suggestions! Feel free to open an issue or contact me.

## Contact

For feedback, feature requests, or questions, feel free to reach out:
- **Email**: ammelmallah@icloud.com
- **Website**: [abubakrelmallah.com](https://abubakrelmallah.com/)
- **LinkedIn**: [linkedin.com/abubakr](https://www.linkedin.com/in/abubakr-elmallah-416a0b273/)

Created by **Abubakr Elmallah**