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
                    '- Players aim for a total hand value of zero.\n\n'
                    '**Ranking Corellian Spike Hands (from best to worst):**\n\n'
                    '**Special Hands:**\n'
                    '- **Pure Sabacc:** Two Sylops (0).\n'
                    '   - 0, 0\n'
                    '- **Full Sabacc:** 2 +10s, 2 -10s, and a Sylop (0)\n'
                    '   - +10, +10, -10, -10, 0\n'
                    '- **Yee-Haa:** One Sabacc Pair and a Sylop (0).\n'
                    '   - Follows the same rules as Sabacc Pairs (view below); lower integer wins.\n'
                    '   - *Example:* +5, -5, 0 beats +8, -8, 0 \n'
                    '- **Rule of Two:** Two Sabacc Pairs.\n'
                    '   - Follows the same rules as Sabacc Pairs (view below); lower integer wins.\n'
                    '   - *Example:* +3, -3, +7, -7 beats +4, -4, +5, -5\n'
                    '- **Sabacc Pair:** Two cards where one positive and one negative card have the same absolute value.\n'
                    '   - *Example:* +5, -5\n'
                    '   - Sabacc Pair hands are ranked by the absolute values of their cards; lower integers are better.\n'
                    '      - For example, a hand of +2 and -2 beats a hand of +3 and -3 because 2 is lower than 3.\n'
                    '      - The best Sabacc Pair is **+1, -1**, and the worst is **+10, -10**.\n\n'
                    '**Sabacc Hands (Sum equals 0):**\n'
                    '- If no player has a Special hand, players with a Sabacc (sum of zero) are ranked next.\n'
                    '- Tie-breakers (in order):\n'
                    '   - Most cards win.\n'
                    '   - Highest positive sum wins.\n'
                    '   - Highest single positive card wins.\n\n'
                    '**Nulrhek Hands (Sum does not equal 0):**\n'
                    '- If no player has a total sum of 0, Nulrhek hands are considered.\n'
                    '- Tie-breakers (in order):\n'
                    '   - Closest to zero wins.\n'
                    '   - Positive totals beat negative totals.\n'
                    '   - Most cards win.\n'
                    '   - Highest positive sum wins.\n'
                    '   - Highest single positive card wins.\n\n'
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
                    '**Sabacc Hands (Sum equals 0):**\n'
                    '- **Pure Sabacc:** A pair of Sylops (both count as 0).\n'
                    '   - 0, 0\n'
                    '- **Prime Sabacc:** A pair of ones (+1 and -1).\n'
                    '   - +1, -1\n'
                    '- **Standard Sabacc:** Two cards where one positive and one negative card have the same absolute value.\n'
                    '   - *Example:* +5, -5\n'
                    '   - Standard Sabacc hands are ranked by the absolute values of their cards; lower integers are better.\n'
                    '      - For example, a hand of +2 and -2 beats a hand of +3 and -3 because 2 is lower than 3.\n'
                    '      - The best Sabacc is **+1, -1**, and the worst is **+6, -6**.\n'
                    '- **Cheap Sabacc (worst Sabacc hand):** A pair of sixes.\n'
                    '   - +6, -6\n'
                    '   - This hand is the worst Sabacc hand, but is still better than Nulrhek Hands because the sum equals 0.\n\n'
                    '**Nulrhek Hands (Sum does not equal 0):**\n'
                    '- If no player has a Sabacc hand, Nulrhek hands are considered.\n'
                    '- Tie-breakers (in order):\n'
                    '   - Closest to zero wins.\n'
                    '   - Positive totals beat negative totals.\n'
                    '   - Highest positive card wins.\n\n'
                    'Good luck! May the Force be with you!',
        color=0x964B00
    )
    rules_embed.set_thumbnail(
        url='https://raw.githubusercontent.com/compycore/Sabacc/gh-pages/images/logo.png')
    return rules_embed

def get_comparison_embed() -> Embed:
    '''Create an embed comparing Corellian Spike and Kessel Sabacc.'''

    comparison_embed = Embed(
        title='Sabacc Game Modes Comparison',
        description='**Similarities:**\n'
                    '- Both games aim to have a hand total as close to zero as possible.\n'
                    '- Players can achieve special hands called "Sabacc" when their hand totals zero.\n'
                    '- Both use Sylop cards as wildcards.\n'
                    '- Both games are played over **3 rounds** by default.\n'
                    '- Nulrhek hands are hands that do not total zero; in both games, the hand closest to zero wins among Nulrhek hands.\n'
                    '- **Hand Value Calculation:** Sum of all cards in hand.\n\n'
                    '**Differences:**\n\n'
                    '**Corellian Spike Sabacc:**\n'
                    '- **Deck Composition:** Single deck of **62 cards** ranging from **-10 to +10** (not including 0), plus 2 Sylops (0). There are **three copies** of each card value.\n'
                    '- **Hand Limit:** No specific limit; you can hold multiple cards.\n'
                    '- **Available Actions:** Draw, Discard, Replace, Stand, Junk.\n'
                    '- **Special Hands:** Includes combinations like Pure Sabacc, Full Sabacc, Yee-Haa, etc.\n\n'
                    '**Kessel Sabacc:**\n'
                    '- **Deck Composition:** Two decks: Sand (positive) and Blood (negative), each with **22 cards** (44 total) ranging from **-6 to +6** (not including 0), including Sylops. There are **three copies** of each card value.\n'
                    '- **Hand Limit:** Exactly 2 cards; one positive and one negative.\n'
                    '- **Available Actions:** Draw, Stand, Junk.\n'
                    '- **Special Hands:** Ranked by lower absolute card values; includes Prime Sabacc, Pure Sabacc, Cheap Sabacc.\n\n'
                    'Choose your preferred game mode and may the Force be with you!',
        color=0x964B00
    )
    comparison_embed.set_thumbnail(
        url='https://raw.githubusercontent.com/compycore/Sabacc/gh-pages/images/logo.png')
    return comparison_embed

import requests
from PIL import Image
from io import BytesIO
import tempfile

def combine_card_images(card_image_urls: list[str], resize_width: int = 80, resize_height: int = 120, padding: int = 10) -> str:
    '''Combine multiple card images horizontally into a single image with optional resizing and padding.'''
    # Streamlining image loading and resizing
    card_images = []
    for url in card_image_urls:
        try:
            # Fetch and load the image in one step
            response = requests.get(url, stream=True, timeout=5)  # Timeout to prevent hanging
            response.raise_for_status()  # Raise an exception for HTTP errors
            img = Image.open(BytesIO(response.content)).convert('RGBA')  # Ensure consistent mode
            img = img.resize((resize_width, resize_height), Image.LANCZOS)
            card_images.append(img)
        except Exception as e:
            # Log and continue without adding the faulty image
            print(f"Error processing image from {url}: {e}")
            continue

    if not card_images:
        raise ValueError("No valid images were provided to combine.")

    # Pre-calculate dimensions for the combined image
    total_width = sum(img.width for img in card_images) + padding * (len(card_images) - 1)
    max_height = max(img.height for img in card_images)

    # Create a blank canvas with the calculated dimensions
    combined_image = Image.new('RGBA', (total_width, max_height), (255, 255, 255, 0))

    # Paste images onto the canvas with padding
    x_offset = 0
    for img in card_images:
        combined_image.paste(img, (x_offset, 0))
        x_offset += img.width + padding

    # Save the combined image to a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    combined_image.save(temp_file.name, format='PNG')
    return temp_file.name