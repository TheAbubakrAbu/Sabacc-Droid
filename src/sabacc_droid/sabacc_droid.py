# sabacc_droid.py

import os
import discord
from dotenv import load_dotenv
from discord import Interaction, app_commands, ui, ButtonStyle
from discord.ext import commands

from corellian_spike import CorelliaGameView
from coruscant_shift import CoruscantGameView
from kessel import KesselGameView
from traditional import TraditionalGameView
from rules import *

# Load the bot token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN is None:
    raise ValueError('DISCORD_TOKEN was not found in the .env file.')

# Set up the bot
intents = discord.Intents.default()
bot = commands.Bot(
    command_prefix='/',
    intents=intents,
    activity=discord.Game(name='Sabacc')
)

active_games = []

async def _send_sabacc_lobby(
    interaction: Interaction,
    view: ui.View,
    active_games_list: list,
    *,
    title: str,
    description: str,
    thumbnail_url: str,
    footer_text: str,
    defer_first: bool = False,
    color: int = 0x764920
):
    '''
    Send a new game lobby embed and view, add the view to active_games, and report any errors.
    If defer_first is True, the interaction was already deferred, so the lobby is sent with
    interaction.channel.send; otherwise it is sent with interaction.response.send_message.
    '''

    embed = Embed(
        title=title,
        description=description,
        color=color
    )
    embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text=footer_text)

    try:
        if defer_first:
            lobby_msg = await interaction.channel.send(embed=embed, view=view)
        else:
            await interaction.response.send_message(embed=embed, view=view)
            lobby_msg = await interaction.original_response()

        view.message = lobby_msg
        active_games_list.append(view)

    except Exception as e:
        await interaction.response.send_message(
            f'An error occurred while starting the game: {e}',
            ephemeral=True
        )

@bot.tree.command(name='sabacc', description='Choose a Sabacc variant to play')
async def sabacc_command(interaction: Interaction):
    '''
    Show a menu with a button for each Sabacc variant:
    - Corellian Spike (defaults: 3 rounds, 2 starting cards)
    - Coruscant Shift (defaults: 2 rounds, 5 starting cards)
    - Kessel (defaults: 3 rounds, 2 starting cards)
    - Traditional (defaults: no set number of rounds, 2 starting cards)
    Also includes Play Random and View Rules buttons.
    '''

    embed = Embed(
        title='Choose Your Sabacc Variant',
        description=(
            'Choose one of the four variants below to start a new game in this channel.\n\n'
            '- **Corellian Spike:** 3 rounds, 2 starting cards\n'
            '- **Coruscant Shift:** 2 rounds, 5 starting cards\n'
            '- **Kessel:** 3 rounds, 2 starting cards\n'
            '- **Traditional:** No set number of rounds, 2 starting cards\n\n'
            'Click a variant to open a lobby with default settings, or click **Play Random** for a random variant with random settings.\n\n'
            'Click **View Rules** for an overview of Sabacc.'
        ),
        color=0x764920
    )
    embed.set_thumbnail(url=sabacc_thumbnail)
    embed.set_footer(text=sabacc_footer)

    view = SabaccChoiceView()
    await interaction.response.send_message(embed=embed, view=view)

class SabaccChoiceView(ui.View):
    '''
    View with a button for each variant, plus Play Random and View Rules:
    - Start Corellian (3 rounds, 2 starting cards)
    - Start Coruscant (2 rounds, 5 starting cards)
    - Start Kessel (3 rounds, 2 starting cards)
    - Start Traditional (2 starting cards)
    - Play Random (random variant and settings)
    - View Rules (Sabacc overview)
    '''

    @ui.button(label='Start Corellian', style=ButtonStyle.primary)
    async def start_corellian_spike(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer()
        corellian_view = CorelliaGameView(
            rounds=3,
            num_cards=2,
            active_games=active_games,
            channel=interaction.channel
        )
        desc = (
            'Click **Join Game** to join the game.\n\n'
            '**Game Settings:**\n'
            '- 3 rounds\n'
            '- 2 starting cards\n'
            f'- Discarding cards is {"enabled" if corellian_view.allow_discard else "disabled"}\n\n'
            'Once someone has joined, **Start Game** will be enabled.'
        )
        await _send_sabacc_lobby(
            interaction,
            corellian_view,
            active_games,
            title='Corellian Spike Sabacc Lobby',
            description=desc,
            thumbnail_url=corellian_thumbnail,
            footer_text=corellian_footer,
            defer_first=True,
            color=0xCBB7A0
        )

    @ui.button(label='Start Coruscant', style=ButtonStyle.primary)
    async def start_coruscant_shift(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer()
        coruscant_view = CoruscantGameView(
            rounds=2,
            num_cards=5,
            active_games=active_games,
            channel=interaction.channel
        )
        desc = (
            'Click **Join Game** to join the game.\n\n'
            '**Game Settings:**\n'
            '- 2 rounds\n'
            '- 5 starting cards\n\n'
            'Once someone has joined, **Start Game** will be enabled.'
        )
        await _send_sabacc_lobby(
            interaction,
            coruscant_view,
            active_games,
            title='Coruscant Shift Sabacc Lobby',
            description=desc,
            thumbnail_url=coruscant_thumbnail,
            footer_text=coruscant_footer,
            defer_first=True,
            color=0xAB9032
        )

    @ui.button(label='Start Kessel', style=ButtonStyle.primary)
    async def start_kessel(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer()
        kessel_view = KesselGameView(rounds=3, active_games=active_games, channel=interaction.channel)
        desc = (
            'Click **Join Game** to join the game.\n\n'
            '**Game Settings:**\n'
            '- 3 rounds\n'
            '- 2 starting cards\n\n'
            'Once someone has joined, **Start Game** will be enabled.'
        )
        await _send_sabacc_lobby(
            interaction,
            kessel_view,
            active_games,
            title='Kessel Sabacc Lobby',
            description=desc,
            thumbnail_url=kessel_thumbnail,
            footer_text=kessel_footer,
            defer_first=True,
            color=0x7F3335
        )

    @ui.button(label='Start Traditional', style=ButtonStyle.primary)
    async def start_traditional(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer()
        traditional_view = TraditionalGameView(
            active_games=active_games,
            channel=interaction.channel
        )
        desc = (
            'Click **Join Game** to join the game.\n\n'
            '**Game Settings:**\n'
            '- No set number of rounds\n'
            '- Call Alderaan to end the game\n'
            '- 2 starting cards\n'
            f'- Discarding cards is {"enabled" if traditional_view.allow_discard else "disabled"}\n\n'
            'Once someone has joined, **Start Game** will be enabled.'
        )
        await _send_sabacc_lobby(
            interaction,
            traditional_view,
            active_games,
            title='Traditional Sabacc Lobby',
            description=desc,
            thumbnail_url=traditional_thumbnail,
            footer_text=traditional_footer,
            defer_first=True,
            color=0x7A9494
        )

    @ui.button(label='Play Random', style=ButtonStyle.success)
    async def play_random_button(self, interaction: Interaction, button: ui.Button):
        import random
        # Define the game configs
        game_types = [
            {
                'name': 'Corellian Spike',
                'view': CorelliaGameView,
                'rounds_range': (1, 10),
                'num_cards_range': (1, 5),
                'desc': lambda rounds, num_cards, allow_discard: (
                    f'Click **Join Game** to join the game.\n\n'
                    f'**Game Settings:**\n'
                    f'- {plural(rounds, "round")}\n'
                    f'- {plural(num_cards, "starting card")}\n'
                    f'- Discarding cards is {"enabled" if allow_discard else "disabled"}\n\n'
                    'Once someone has joined, **Start Game** will be enabled.'
                ),
                'thumbnail': corellian_thumbnail,
                'footer': corellian_footer,
                'color': 0xCBB7A0
            },
            {
                'name': 'Coruscant Shift',
                'view': CoruscantGameView,
                'rounds_range': (1, 5),
                'num_cards_range': (1, 10),
                'desc': lambda rounds, num_cards, allow_discard: (
                    f'Click **Join Game** to join the game.\n\n'
                    f'**Game Settings:**\n'
                    f'- {plural(rounds, "round")}\n'
                    f'- {plural(num_cards, "starting card")}\n\n'
                    'Once someone has joined, **Start Game** will be enabled.'
                ),
                'thumbnail': coruscant_thumbnail,
                'footer': coruscant_footer,
                'color': 0xAB9032
            },
            {
                'name': 'Kessel',
                'view': KesselGameView,
                'rounds_range': (1, 10),
                'num_cards_range': None,
                'desc': lambda rounds, num_cards, allow_discard: (
                    f'Click **Join Game** to join the game.\n\n'
                    f'**Game Settings:**\n'
                    f'- {plural(rounds, "round")}\n'
                    f'- 2 starting cards\n\n'
                    'Once someone has joined, **Start Game** will be enabled.'
                ),
                'thumbnail': kessel_thumbnail,
                'footer': kessel_footer,
                'color': 0x7F3335
            },
            {
                'name': 'Traditional',
                'view': TraditionalGameView,
                'rounds_range': None,
                'num_cards_range': (1, 5),
                'desc': lambda rounds, num_cards, allow_discard: (
                    f'Click **Join Game** to join the game.\n\n'
                    f'**Game Settings:**\n'
                    f'- No set number of rounds\n'
                    f'- Call Alderaan to end the game\n'
                    f'- {plural(num_cards, "starting card")}\n'
                    f'- Discarding cards is {"enabled" if allow_discard else "disabled"}\n\n'
                    'Once someone has joined, **Start Game** will be enabled.'
                ),
                'thumbnail': traditional_thumbnail,
                'footer': traditional_footer,
                'color': 0x7A9494
            }
        ]
        game = random.choice(game_types)
        # Randomize the settings
        rounds = None
        num_cards = None
        allow_discard = False
        if game['rounds_range']:
            rounds = random.randint(*game['rounds_range'])
        if game['num_cards_range']:
            num_cards = random.randint(*game['num_cards_range'])
        # For variants with a discard toggle, randomly turn it on
        if game['name'] in ['Corellian Spike', 'Traditional']:
            allow_discard = random.choice([True, False])
        # Create the view
        if game['name'] == 'Corellian Spike':
            view = game['view'](rounds=rounds, num_cards=num_cards, active_games=active_games, channel=interaction.channel)
            view.allow_discard = allow_discard
        elif game['name'] == 'Coruscant Shift':
            view = game['view'](rounds=rounds, num_cards=num_cards, active_games=active_games, channel=interaction.channel)
        elif game['name'] == 'Kessel':
            view = game['view'](rounds=rounds, active_games=active_games, channel=interaction.channel)
        elif game['name'] == 'Traditional':
            view = game['view'](num_cards=num_cards, active_games=active_games, channel=interaction.channel)
            view.allow_discard = allow_discard
        desc = game['desc'](rounds, num_cards, allow_discard)
        await _send_sabacc_lobby(
            interaction,
            view,
            active_games,
            title=f'{game["name"]} Sabacc Lobby',
            description=desc,
            thumbnail_url=game['thumbnail'],
            footer_text=game['footer'],
            defer_first=True,
            color=game['color']
        )

    @ui.button(label='View Rules', style=ButtonStyle.secondary)
    async def view_rules(self, interaction: Interaction, button: ui.Button):
        embed = Embed(
            title='Sabacc Droid Help',
            description=RULES_DESCRIPTION,
            color=0x764920
        )
        embed.set_thumbnail(url=sabacc_thumbnail)
        embed.set_footer(text=sabacc_footer)

        view = HelpView()
        await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name='random', description='Start a random Sabacc variant (use 0 for random rounds or cards)')
@app_commands.describe(
    rounds='Number of rounds (0 for random)',
    num_cards='Number of starting cards (0 for random)'
)
async def random_command(interaction: Interaction, rounds: int = 0, num_cards: int = 0):
    '''
    Start a lobby for a random Sabacc variant. Settings left at 0 are randomized.
    '''

    import random
    game_types = [
        {
            'name': 'Corellian Spike',
            'view': CorelliaGameView,
            'rounds_range': (1, 10),
            'num_cards_range': (1, 5),
            'desc': lambda rounds, num_cards, allow_discard: (
                f'Click **Join Game** to join the game.\n\n'
                f'**Game Settings:**\n'
                f'- {plural(rounds, "round")}\n'
                f'- {plural(num_cards, "starting card")}\n'
                f'- Discarding cards is {"enabled" if allow_discard else "disabled"}\n\n'
                'Once someone has joined, **Start Game** will be enabled.'
            ),
            'thumbnail': corellian_thumbnail,
            'footer': corellian_footer,
            'color': 0xCBB7A0
        },
        {
            'name': 'Coruscant Shift',
            'view': CoruscantGameView,
            'rounds_range': (1, 5),
            'num_cards_range': (1, 10),
            'desc': lambda rounds, num_cards, allow_discard: (
                f'Click **Join Game** to join the game.\n\n'
                f'**Game Settings:**\n'
                f'- {plural(rounds, "round")}\n'
                f'- {plural(num_cards, "starting card")}\n\n'
                'Once someone has joined, **Start Game** will be enabled.'
            ),
            'thumbnail': coruscant_thumbnail,
            'footer': coruscant_footer,
            'color': 0xAB9032
        },
        {
            'name': 'Kessel',
            'view': KesselGameView,
            'rounds_range': (1, 10),
            'num_cards_range': None,
            'desc': lambda rounds, num_cards, allow_discard: (
                f'Click **Join Game** to join the game.\n\n'
                f'**Game Settings:**\n'
                f'- {plural(rounds, "round")}\n'
                f'- 2 starting cards\n\n'
                'Once someone has joined, **Start Game** will be enabled.'
            ),
            'thumbnail': kessel_thumbnail,
            'footer': kessel_footer,
            'color': 0x7F3335
        },
        {
            'name': 'Traditional',
            'view': TraditionalGameView,
            'rounds_range': None,
            'num_cards_range': (1, 5),
            'desc': lambda rounds, num_cards, allow_discard: (
                f'Click **Join Game** to join the game.\n\n'
                f'**Game Settings:**\n'
                f'- No set number of rounds\n'
                f'- Call Alderaan to end the game\n'
                f'- {plural(num_cards, "starting card")}\n'
                f'- Discarding cards is {"enabled" if allow_discard else "disabled"}\n\n'
                'Once someone has joined, **Start Game** will be enabled.'
            ),
            'thumbnail': traditional_thumbnail,
            'footer': traditional_footer,
            'color': 0x7A9494
        }
    ]
    game = random.choice(game_types)
    allow_discard = False
    # Randomize rounds and num_cards, or clamp them to the variant's range
    if game['rounds_range']:
        if rounds == 0:
            rounds = random.randint(*game['rounds_range'])
        else:
            rounds = max(game['rounds_range'][0], min(rounds, game['rounds_range'][1]))
    if game['num_cards_range']:
        if num_cards == 0:
            num_cards = random.randint(*game['num_cards_range'])
        else:
            num_cards = max(game['num_cards_range'][0], min(num_cards, game['num_cards_range'][1]))
    # For variants with a discard toggle, randomly turn it on
    if game['name'] in ['Corellian Spike', 'Traditional']:
        allow_discard = random.choice([True, False])
    # Create the view
    if game['name'] == 'Corellian Spike':
        view = game['view'](rounds=rounds, num_cards=num_cards, active_games=active_games, channel=interaction.channel)
        view.allow_discard = allow_discard
    elif game['name'] == 'Coruscant Shift':
        view = game['view'](rounds=rounds, num_cards=num_cards, active_games=active_games, channel=interaction.channel)
    elif game['name'] == 'Kessel':
        view = game['view'](rounds=rounds, active_games=active_games, channel=interaction.channel)
    elif game['name'] == 'Traditional':
        view = game['view'](num_cards=num_cards, active_games=active_games, channel=interaction.channel)
        view.allow_discard = allow_discard
    desc = game['desc'](rounds, num_cards, allow_discard)
    await _send_sabacc_lobby(
        interaction,
        view,
        active_games,
        title=f'{game["name"]} Sabacc Lobby',
        description=desc,
        thumbnail_url=game['thumbnail'],
        footer_text=game['footer'],
        defer_first=False,
        color=game['color']
    )

@bot.tree.command(name='corellian_spike', description='Start a Corellian Spike Sabacc game with optional custom settings')
@app_commands.describe(
    rounds='Number of rounds (default: 3, max: 10)',
    num_cards='Number of starting cards (default: 2, max: 5)'
)
async def corellian_command(interaction: Interaction, rounds: int = 3, num_cards: int = 2) -> None:
    '''
    Start a new Corellian Spike Sabacc game with optional custom settings.
    '''

    rounds = max(1, min(rounds, 10))
    num_cards = max(1, min(num_cards, 5))

    view = CorelliaGameView(
        rounds=rounds,
        num_cards=num_cards,
        active_games=active_games,
        channel=interaction.channel
    )
    desc = (
        'Click **Join Game** to join the game.\n\n'
        f'**Game Settings:**\n'
        f'- {plural(rounds, "round")}\n'
        f'- {plural(num_cards, "starting card")}\n'
        f'- Discarding cards is {"enabled" if view.allow_discard else "disabled"}\n\n'
        'Once someone has joined, **Start Game** will be enabled.'
    )
    await _send_sabacc_lobby(
        interaction,
        view,
        active_games,
        title='Corellian Spike Sabacc Lobby',
        description=desc,
        thumbnail_url=corellian_thumbnail,
        footer_text=corellian_footer,
        defer_first=False,
        color=0xCBB7A0
    )

@bot.tree.command(name='coruscant_shift', description='Start a Coruscant Shift Sabacc game with optional custom settings')
@app_commands.describe(
    rounds='Number of rounds (default: 2, max: 5)',
    num_cards='Number of starting cards (default: 5, max: 10)'
)
async def coruscant_shift_command(interaction: Interaction, rounds: int = 2, num_cards: int = 5) -> None:
    '''
    Start a new Coruscant Shift Sabacc game with optional custom settings.
    '''

    rounds = max(1, min(rounds, 5))
    num_cards = max(1, min(num_cards, 10))

    view = CoruscantGameView(
        rounds=rounds,
        num_cards=num_cards,
        active_games=active_games,
        channel=interaction.channel
    )
    desc = (
        'Click **Join Game** to join the game.\n\n'
        f'**Game Settings:**\n'
        f'- {plural(rounds, "round")}\n'
        f'- {plural(num_cards, "starting card")}\n\n'
        'Once someone has joined, **Start Game** will be enabled.'
    )
    await _send_sabacc_lobby(
        interaction,
        view,
        active_games,
        title='Coruscant Shift Sabacc Lobby',
        description=desc,
        thumbnail_url=coruscant_thumbnail,
        footer_text=coruscant_footer,
        defer_first=False,
        color=0xAB9032
    )

@bot.tree.command(name='kessel', description='Start a Kessel Sabacc game with optional custom settings')
@app_commands.describe(
    rounds='Number of rounds (default: 3, max: 10)'
)
async def kessel_command(interaction: Interaction, rounds: int = 3) -> None:
    '''
    Start a new Kessel Sabacc game with optional custom settings.
    '''

    rounds = max(1, min(rounds, 10))
    view = KesselGameView(rounds=rounds, active_games=active_games, channel=interaction.channel)

    desc = (
        'Click **Join Game** to join the game.\n\n'
        f'**Game Settings:**\n'
        f'- {plural(rounds, "round")}\n'
        f'- 2 starting cards\n\n'
        'Once someone has joined, **Start Game** will be enabled.'
    )
    await _send_sabacc_lobby(
        interaction,
        view,
        active_games,
        title='Kessel Sabacc Lobby',
        description=desc,
        thumbnail_url=kessel_thumbnail,
        footer_text=kessel_footer,
        defer_first=False,
        color=0x7F3335
    )

@bot.tree.command(name='traditional', description='Start a Traditional Sabacc game with optional custom settings')
@app_commands.describe(
    num_cards='Number of starting cards (default: 2, max: 5)'
)
async def traditional_command(interaction: Interaction, num_cards: int = 2) -> None:
    '''
    Start a new Traditional Sabacc game with optional custom settings.
    '''

    num_cards = max(1, min(num_cards, 5))

    view = TraditionalGameView(
        num_cards=num_cards,
        active_games=active_games,
        channel=interaction.channel
    )
    desc = (
        'Click **Join Game** to join the game.\n\n'
        '**Game Settings:**\n'
        f'- No set number of rounds\n'
        f'- Call Alderaan to end the game\n'
        f'- {plural(num_cards, "starting card")}\n'
        f'- Discarding cards is {"enabled" if view.allow_discard else "disabled"}\n\n'
        'Once someone has joined, **Start Game** will be enabled.'
    )
    await _send_sabacc_lobby(
        interaction,
        view,
        active_games,
        title='Traditional Sabacc Lobby',
        description=desc,
        thumbnail_url=traditional_thumbnail,
        footer_text=traditional_footer,
        defer_first=False,
        color=0x7A9494
    )

@bot.tree.command(name='help', description='Show the Sabacc rules and variants')
async def help_command(interaction: Interaction) -> None:
    '''
    Show a public message summarizing the four Sabacc variants
    (Corellian Spike, Coruscant Shift, Kessel, and Traditional),
    along with credits and repository links.
    '''

    embed = Embed(
        title='Sabacc Droid Help',
        description=RULES_DESCRIPTION,
        color=0x764920
    )
    embed.set_thumbnail(url=sabacc_thumbnail)
    embed.set_footer(text=sabacc_footer)

    view = HelpView()
    await interaction.response.send_message(embed=embed, view=view)


class HelpView(ui.View):
    '''
    View with buttons that show the rules for each variant and a comparison.
    '''

    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label='Corellian Rules', style=ButtonStyle.primary)
    async def corellian_spike_button(self, interaction: Interaction, button: ui.Button):
        rules_embed = get_corellian_spike_rules_embed()
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)

    @ui.button(label='Coruscant Rules', style=ButtonStyle.primary)
    async def coruscant_button(self, interaction: Interaction, button: ui.Button):
        rules_embed = get_coruscant_shift_rules_embed()
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)

    @ui.button(label='Kessel Rules', style=ButtonStyle.primary)
    async def kessel_button(self, interaction: Interaction, button: ui.Button):
        rules_embed = get_kessel_rules_embed()
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)

    @ui.button(label='Traditional Rules', style=ButtonStyle.primary)
    async def traditional_button(self, interaction: Interaction, button: ui.Button):
        rules_embed = get_traditional_rules_embed()
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)

    @ui.button(label='Comparison', style=ButtonStyle.secondary)
    async def comparison_button(self, interaction: Interaction, button: ui.Button):
        comparison_embed = get_comparison_embed()
        await interaction.response.send_message(embed=comparison_embed, ephemeral=True)

@bot.event
async def on_ready() -> None:
    '''
    Sync the slash commands when the bot is ready.
    '''

    await bot.tree.sync()
    print(f'{bot.user} is now running!')

def main() -> None:
    '''
    Run the Discord bot.
    '''

    bot.run(TOKEN)

if __name__ == '__main__':
    main()