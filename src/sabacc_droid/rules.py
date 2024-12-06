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
                    '2. **Full Sabacc:** 0, +10, +10, -10, -10.\n\n'
                    '3. **Fleet:** Sum zero, one sylop (0), and four of a kind.\n'
                    '   - Tie-breaker: Lowest card value.\n'
                    '   - Example: 0, +5, +5, -5, -5\n\n'
                    '4. **Yee-Haa:** Sum zero, one sylop (0), and at least one pair.\n'
                    '   - Tie-breaker: Lowest pair value.\n'
                    '   - Example: 0, +4, -4, +8\n\n'
                    '5. **Rhylet:** Sum zero, three of a kind, additional cards.\n'
                    '   - Tie-breaker: Lowest three of a kind value.\n'
                    '   - Example: +2, +2, +2, -6\n\n'
                    '6. **Squadron:** Sum zero, four of a kind.\n'
                    '   - Tie-breaker: Lowest card value.\n'
                    '   - Example: +5, +5, -5, -5\n\n'
                    '7. **Bantha\'s Wild:** Sum zero, three of a kind.\n'
                    '   - Tie-breaker: Lowest card value.\n'
                    '   - Example: +4, +4, +4, -12\n\n'
                    '8. **Rule of Two:** Sum zero, two pairs.\n'
                    '   - Tie-breaker: Lowest pair value.\n'
                    '   - Example: +3, +3, -7, -7 or +3, -3, +7, -7\n\n'
                    '9. **Sabacc Pair:** Sum zero, one pair (cards with the same absolute value).\n'
                    '   - Pairs can be any sign: (+5, +5), (-5, -5), or (+5, -5).\n'
                    '   - Tie-breaker: Lowest pair value.\n'
                    '   - Example: +5, +5, -10 or +5, -5\n\n'
                    '10. **Sabacc:** Sum zero, no special hands.\n'
                    '   - Tie-breakers:\n'
                    '     1. Lowest absolute card value.\n'
                    '     2. Most cards in hand.\n'
                    '     3. Highest positive sum.\n'
                    '     4. Highest single positive card.\n'
                    '   - Example: +1, +2, -3\n\n'
                    '11. **Nulrhek:** Sum not zero.\n'
                    '   - Tie-breakers:\n'
                    '     1. Closest to zero (absolute value).\n'
                    '     2. Positive totals beat negative if same distance.\n'
                    '     3. Most cards in hand.\n'
                    '     4. Highest positive sum.\n'
                    '     5. Highest single positive card.\n'
                    '   - Example: Total of +1 beats total of -1\n\n'
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

def combine_card_imagess(card_image_urls: list[str], resize_width: int = 80, resize_height: int = 120, padding: int = 10) -> str:
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
            print(f'Error processing image from {url}: {e}')
            continue

    if not card_images:
        raise ValueError('No valid images were provided to combine.')

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

import requests
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed

def download_and_process_image(url, resize_width, resize_height):
    '''Download an image and resize it.'''
    try:
        response = requests.get(url, stream=True, timeout=5)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content)).convert('RGBA')
        img = img.resize((resize_width, resize_height), Image.LANCZOS)
        return img
    except Exception as e:
        # Log and continue without adding the faulty image
        print(f'Error processing image from {url}: {e}')
        return None

def combine_card_images(card_image_urls: list[str], resize_width: int = 80, resize_height: int = 120, padding: int = 10) -> BytesIO:
    '''Combine multiple card images horizontally into a single image with optional resizing and padding.'''
    # Download and process images in parallel
    card_images = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(download_and_process_image, url, resize_width, resize_height): url for url in card_image_urls}
        for future in as_completed(futures):
            img = future.result()
            if img is not None:
                card_images.append(img)
    
    if not card_images:
        raise ValueError('No valid images were provided to combine.')
    
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
    
    # Save the combined image to a BytesIO object
    image_bytes = BytesIO()
    combined_image.save(image_bytes, format='PNG')
    image_bytes.seek(0)
    return image_bytes