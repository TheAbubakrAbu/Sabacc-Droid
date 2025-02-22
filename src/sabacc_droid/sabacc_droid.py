# sabacc_droid.py

import os
import discord
from dotenv import load_dotenv
from discord import Intents, Interaction, Game, app_commands, ui
from discord.ext import commands

from corellian_spike import CorelliaGameView
from kessel import KesselGameView
from coruscant_shift import CoruscantGameView
from rules import (
    RULES_DESCRIPTION,
    get_corellian_spike_rules_embed,
    get_kessel_rules_embed,
    get_coruscant_shift_rules_embed,
    get_comparison_embed
)

# Load the bot token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN is None:
    raise ValueError('DISCORD_TOKEN environment variable not found in .env file.')

# Setup Bot
intents = Intents.default()
bot = commands.Bot(
    command_prefix='/',
    intents=intents,
    activity=Game(name='Sabacc')
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
    defer_first: bool = False,
    color: int = 0x764920
):
    '''
    Helper function to send a new game lobby embed + view, append to active_games,
    and handle any exceptions. If 'defer_first' is True, we assume the interaction
    was already deferred, so we use 'interaction.channel.send'; otherwise we use
    'interaction.response.send_message'.
    '''

    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    embed.set_thumbnail(url=thumbnail_url)

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

@bot.tree.command(name='sabacc', description='Select a Sabacc variant to play')
async def sabacc_command(interaction: Interaction):
    '''
    Presents a menu with buttons for the three Sabacc variants:
    - Corellian Spike (defaults: 3 rounds, 2 starting cards)
    - Coruscant Shift (defaults: 2 rounds, 5 starting cards)
    - Kessel (defaults: 3 rounds, 2 starting cards)
    Plus a View Rules button to show /help in fo.
    '''

    embed = discord.Embed(
        title='Choose Your Sabacc Variant',
        description=(
            'Select one of the three modes below to start a new game in this channel.\n\n'
            '**Corellian Spike** (3 rounds / 2 cards)\n'
            '**Coruscant Shift** (2 rounds / 5 cards)\n'
            '**Kessel** (3 rounds / 2 cards)\n\n'
            'Click a button to immediately start a lobby with default settings.\n\n'
            'Or click **View Rules** to see an overview of Sabacc.'
        ),
        color=0x764920
    )
    embed.set_thumbnail(
        url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/Corellian%20Spike.png'
    )

    view = SabaccChoiceView()
    await interaction.response.send_message(embed=embed, view=view)

class SabaccChoiceView(ui.View):
    '''
    View with four buttons:
    - Corellian Spike (3 rounds, 2 cards)
    - Kessel (3 rounds, 2 cards)
    - Coruscant Shift (2 rounds, 5 cards)
    - View Rules (ephemeral help info)
    '''

    @ui.button(label='Start Corellian', style=discord.ButtonStyle.primary)
    async def start_corellian_spike(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer()
        corellian_view = CorelliaGameView(
            rounds=3,
            num_cards=2,
            active_games=active_games,
            channel=interaction.channel
        )
        desc = (
            'Click **Play Game** to join.\n\n'
            '**Game Settings:**\n3 rounds\n2 starting cards\n\n'
            'Once someone has joined, **Start Game** will be enabled.'
        )
        await _send_sabacc_lobby(
            interaction,
            corellian_view,
            active_games,
            title='Corellian Spike Sabacc Lobby',
            description=desc,
            thumbnail_url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/Corellian%20Spike.png',
            defer_first=True,
            color=0xCBB7A0
        )

    @ui.button(label='Start Coruscant', style=discord.ButtonStyle.primary)
    async def start_coruscant_shift(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer()
        coruscant_view = CoruscantGameView(
            rounds=2,
            num_cards=5,
            active_games=active_games,
            channel=interaction.channel
        )
        desc = (
            'Click **Play Game** to join.\n\n'
            '**Game Settings:**\n2 rounds\n5 starting cards\n\n'
            'Once someone has joined, **Start Game** will be enabled.'
        )
        await _send_sabacc_lobby(
            interaction,
            coruscant_view,
            active_games,
            title='Coruscant Shift Sabacc Lobby',
            description=desc,
            thumbnail_url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/Coruscant%20Shift.png',
            defer_first=True,
            color=0xAB9032
        )

    @ui.button(label='Start Kessel', style=discord.ButtonStyle.primary)
    async def start_kessel(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer()
        kessel_view = KesselGameView(rounds=3, active_games=active_games, channel=interaction.channel)
        desc = (
            'Click **Play Game** to join.\n\n'
            '**Game Settings:**\n3 rounds\n2 starting cards\n\n'
            'Once someone has joined, **Start Game** will be enabled.'
        )
        await _send_sabacc_lobby(
            interaction,
            kessel_view,
            active_games,
            title='Kessel Sabacc Lobby',
            description=desc,
            thumbnail_url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/kessel/logo.png',
            defer_first=True,
            color=0x7F3335
        )

    @ui.button(label='View Rules', style=discord.ButtonStyle.secondary)
    async def view_rules(self, interaction: Interaction, button: ui.Button):
        '''Shows the same info as the /help command.'''
        embed = discord.Embed(
            title='Sabacc Droid Help',
            description=RULES_DESCRIPTION,
            color=0x764920
        )
        embed.set_thumbnail(
            url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/Corellian%20Spike.png'
        )
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name='corellian_spike', description='Start a Corellian Spike Sabacc game with optional custom settings')
@app_commands.describe(
    rounds='Number of rounds (default: 3, max: 10)',
    num_cards='Number of initial cards (default: 2, max: 5)'
)
async def corellian_command(interaction: Interaction, rounds: int = 3, num_cards: int = 2) -> None:
    '''Initiate a new Corellian Spike Sabacc game with optional custom settings.'''
    rounds = max(1, min(rounds, 10))
    num_cards = max(1, min(num_cards, 5))

    view = CorelliaGameView(
        rounds=rounds,
        num_cards=num_cards,
        active_games=active_games,
        channel=interaction.channel
    )
    desc = (
        'Click **Play Game** to join the game.\n\n'
        f'**Game Settings:**\n{rounds} rounds\n{num_cards} starting cards\n\n'
        'Once someone has joined, the **Start Game** button will be enabled.'
    )
    await _send_sabacc_lobby(
        interaction,
        view,
        active_games,
        title='Corellian Spike Sabacc Lobby',
        description=desc,
        thumbnail_url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/Corellian%20Spike.png',
        defer_first=False,
        color=0xCBB7A0
    )

@bot.tree.command(name='coruscant_shift', description='Start a Coruscant Shift Sabacc game with optional custom settings')
@app_commands.describe(
    rounds='Number of rounds (default: 2, max: 5)',
    num_cards='Number of starting cards (default: 5, max: 10)'
)
async def coruscant_shift_command(interaction: Interaction, rounds: int = 2, num_cards: int = 5) -> None:
    '''Initiate a new Coruscant Shift Sabacc game with optional custom settings.'''
    rounds = max(1, min(rounds, 5))
    num_cards = max(1, min(num_cards, 10))

    view = CoruscantGameView(
        rounds=rounds,
        num_cards=num_cards,
        active_games=active_games,
        channel=interaction.channel
    )
    desc = (
        'Click **Play Game** to join.\n\n'
        f'**Game Settings:**\n{rounds} rounds\n{num_cards} starting cards\n\n'
        'Once someone has joined, the **Start Game** button will be enabled.'
    )
    await _send_sabacc_lobby(
        interaction,
        view,
        active_games,
        title='Coruscant Shift Sabacc Lobby',
        description=desc,
        thumbnail_url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/Coruscant%20Shift.png',
        defer_first=False,
        color=0xAB9032
    )

@bot.tree.command(name='kessel', description='Start a Kessel Sabacc game with optional custom settings')
@app_commands.describe(
    rounds='Number of rounds (default: 3, max: 10)'
)
async def kessel_command(interaction: Interaction, rounds: int = 3) -> None:
    '''Initiate a new Kessel Sabacc game with optional custom settings.'''
    rounds = max(1, min(rounds, 10))
    view = KesselGameView(rounds=rounds, active_games=active_games, channel=interaction.channel)

    desc = (
        'Click **Play Game** to join the game.\n\n'
        f'**Game Settings:**\n{rounds} rounds\n2 starting cards\n\n'
        'Once someone has joined, the **Start Game** button will be enabled.'
    )
    await _send_sabacc_lobby(
        interaction,
        view,
        active_games,
        title='Kessel Sabacc Lobby',
        description=desc,
        thumbnail_url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/kessel/logo.png',
        defer_first=False,
        color=0x7F3335
    )

@bot.tree.command(name='help', description='Display Sabacc rules')
async def help_command(interaction: Interaction) -> None:
    '''
    Display a public message summarizing the available Sabacc game modes
    (Corellian Spike, Kessel Sabacc, and Coruscant Shift),
    along with credits and repository links.
    '''
    embed = discord.Embed(
        title='Sabacc Droid Help',
        description=RULES_DESCRIPTION,
        color=0x764920
    )
    embed.set_thumbnail(
        url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/Corellian%20Spike.png'
    )

    view = HelpView()
    await interaction.response.send_message(embed=embed, view=view)


class HelpView(ui.View):
    '''View containing buttons to display rules for different game modes.'''

    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label='Corellian Rules', style=discord.ButtonStyle.primary)
    async def corellian_spike_button(self, interaction: Interaction, button: ui.Button):
        rules_embed = get_corellian_spike_rules_embed()
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)

    @ui.button(label='Coruscant Rules', style=discord.ButtonStyle.primary)
    async def coruscant_button(self, interaction: Interaction, button: ui.Button):
        rules_embed = get_coruscant_shift_rules_embed()
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)

    @ui.button(label='Kessel Rules', style=discord.ButtonStyle.primary)
    async def kessel_button(self, interaction: Interaction, button: ui.Button):
        rules_embed = get_kessel_rules_embed()
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)

    @ui.button(label='Comparison', style=discord.ButtonStyle.secondary)
    async def comparison_button(self, interaction: Interaction, button: ui.Button):
        comparison_embed = get_comparison_embed()
        await interaction.response.send_message(embed=comparison_embed, ephemeral=True)


@bot.event
async def on_ready() -> None:
    '''Event handler for when the bot is ready.'''
    await bot.tree.sync()
    print(f'{bot.user} is now running!')

def main() -> None:
    '''Run the Discord bot.'''
    bot.run(TOKEN)

if __name__ == '__main__':
    main()