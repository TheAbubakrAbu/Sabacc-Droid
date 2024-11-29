# sabacc_droid.py

import os
import discord
from dotenv import load_dotenv
from discord import Intents, Interaction, Game, app_commands, ui
from discord.ext import commands
from corellian_spike import CorelliaGameView
from kessel import KesselGameView
from rules import get_corellian_spike_rules_embed, get_kessel_rules_embed, get_comparison_embed

# Load Token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if TOKEN is None:
    raise ValueError('DISCORD_TOKEN environment variable not found in .env file.')

# Setup Bot
intents = Intents.default()
intents.message_content = True
bot = commands.Bot(
    command_prefix='/',
    intents=intents,
    activity=Game(name='Sabacc')
)

active_games = []

@bot.tree.command(name='corellian_spike', description='Start a Corellian Spike Sabacc game with optional custom settings')
@app_commands.describe(
    rounds='Number of rounds (default: 3, max: 5)',
    num_cards='Number of initial cards (default: 2, max: 3)'
)
async def corellian_command(interaction: Interaction, rounds: int = 3, num_cards: int = 2) -> None:
    '''Initiate a new Corellian Spike Sabacc game with optional custom settings.'''

    rounds = max(1, min(rounds, 4))
    num_cards = max(1, min(num_cards, 3))

    view = CorelliaGameView(rounds=rounds, num_cards=num_cards, active_games=active_games)
    embed = discord.Embed(
        title='Corellian Spike Sabacc Game Lobby',
        description=f'Click **Play Game** to join the game.\n\n'
                    f'**Game Settings:**\n{rounds} rounds\n{num_cards} starting cards\n\n'
                    'Once at least two players have joined, the **Start Game** button will be enabled.',
        color=0x964B00
    )
    embed.set_footer(text='Corellian Spike Sabacc')
    embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')
    try:
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()
        active_games.append(view)
    except Exception as e:
        await interaction.response.send_message('An error occurred while starting the game.', ephemeral=True)
        print(f'Error in corellian_command: {e}')

@bot.tree.command(name='kessel', description='Start a Kessel Sabacc game')
async def kessel_command(interaction: Interaction) -> None:
    '''Initiate a new Kessel Sabacc game with optional custom settings.'''

    view = KesselGameView(rounds=3, active_games=active_games, channel=interaction.channel)
    embed = discord.Embed(
        title='Kessel Sabacc Game Lobby',
        description=f'Click **Play Game** to join the game.\n\n'
                    f'**Game Settings:**\n3 rounds\n\n'
                    'Once at least two players have joined, the **Start Game** button will be enabled.',
        color=0x964B00
    )
    embed.set_footer(text='Kessel Sabacc')
    embed.set_thumbnail(url='https://static.wikia.nocookie.net/starwars/images/9/90/Sylop.png/revision/latest?cb=20180530101050')
    try:
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()
        active_games.append(view)
    except Exception as e:
        await interaction.response.send_message('An error occurred while starting the game.', ephemeral=True)
        print(f'Error in kessel_command: {e}')

@bot.tree.command(name='help', description='Display the Sabacc game rules')
async def help_command(interaction: Interaction) -> None:
    '''Display the game rules publicly.'''

    embed = discord.Embed(
        title='Sabacc Droid',
        description=(
            'Welcome to Sabacc Droid! Play either **Corellian Spike Sabacc** (from *Solo* and Galaxy\'s Edge) '
            'or **Kessel Sabacc** (from *Star Wars: Outlaws*).\n\n'
            'Both games focus on achieving a hand sum of zero or as close as possible, however there are many '
            'differences between the two.\n\n'
            'Default game settings are 3 rounds and 2 starting cards for both games.\n\n'
            'Created by **Abubakr Elmallah**.\n\n'
            '[📂 GitHub Repository](https://github.com/TheAbubakrAbu/Sabacc-Droid)'
        ),
        color=0x964B00
    )
    embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')

    view = HelpView()
    await interaction.response.send_message(embed=embed, view=view)

class HelpView(ui.View):
    '''View containing buttons to display rules for different game modes.'''

    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label='View Corellian Spike Rules', style=discord.ButtonStyle.primary)
    async def corellian_spike_button(self, interaction: Interaction, button: ui.Button):
        rules_embed = get_corellian_spike_rules_embed()
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)

    @ui.button(label='View Kessel Rules', style=discord.ButtonStyle.primary)
    async def kessel_button(self, interaction: Interaction, button: ui.Button):
        rules_embed = get_kessel_rules_embed()
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)

    @ui.button(label='View Comparison', style=discord.ButtonStyle.secondary)
    async def comparison_button(self, interaction: Interaction, button: ui.Button):
        comparison_embed = get_comparison_embed()
        await interaction.response.send_message(embed=comparison_embed, ephemeral=True)

# Handle Startup
@bot.event
async def on_ready() -> None:
    '''Event handler for when the bot is ready.'''

    await bot.tree.sync()
    print(f'{bot.user} is now running!')

# Run Bot
def main() -> None:

    '''Run the Discord bot.'''
    bot.run(TOKEN)

if __name__ == '__main__':
    main()