# sabacc_droid.py

import os
import discord
from dotenv import load_dotenv
from discord import Intents, Interaction, Game, app_commands, ui
from discord.ext import commands
from corellian_spike import CorelliaGameView
from kessel import KesselGameView
from coruscant_shift import CoruscantGameView
from rules import get_corellian_spike_rules_embed, get_kessel_rules_embed, get_coruscant_shift_rules_embed, get_comparison_embed

# Load Token
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

@bot.tree.command(name='corellian_spike', description='Start a Corellian Spike Sabacc game with optional custom settings')
@app_commands.describe(
    rounds='Number of rounds (default: 3, max: 10)',
    num_cards='Number of initial cards (default: 2, max: 5)'
)
async def corellian_command(interaction: Interaction, rounds: int = 3, num_cards: int = 2) -> None:
    '''Initiate a new Corellian Spike Sabacc game with optional custom settings.'''

    rounds = max(1, min(rounds, 10))
    num_cards = max(1, min(num_cards, 5))

    view = CorelliaGameView(rounds=rounds, num_cards=num_cards, active_games=active_games, channel=interaction.channel)
    embed = discord.Embed(
        title='Sabacc Game Lobby',
        description='Click **Play Game** to join the game.\n\n'
                    f'**Game Settings:**\n{rounds} rounds\n{num_cards} starting cards\n\n'
                    'Once someone has joined, the **Start Game** button will be enabled.',
        color=0x964B00
    )
    embed.set_footer(text='Corellian Spike Sabacc')
    embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/Corellian%20Spike.png')
    try:
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()
        active_games.append(view)
    except Exception as e:
        await interaction.response.send_message('An error occurred while starting the game.', ephemeral=True)
        print(f'Error in corellian_command: {e}')


@bot.tree.command(name='kessel', description='Start a Kessel Sabacc game')
@app_commands.describe(
    rounds='Number of rounds (default: 3, max: 10)'
)
async def kessel_command(interaction: Interaction, rounds: int = 3) -> None:
    '''Initiate a new Kessel Sabacc game with optional custom settings.'''

    rounds = max(1, min(rounds, 10))

    view = KesselGameView(rounds=rounds, active_games=active_games, channel=interaction.channel)
    embed = discord.Embed(
        title='Sabacc Game Lobby',
        description='Click **Play Game** to join the game.\n\n'
                    f'**Game Settings:**\n{rounds} rounds\n2 starting cards\n\n'
                    'Once someone has joined, the **Start Game** button will be enabled.',
        color=0x964B00
    )
    embed.set_footer(text='Kessel Sabacc')
    embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/kessel/logo.png')
    try:
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()
        active_games.append(view)
    except Exception as e:
        await interaction.response.send_message('An error occurred while starting the game.', ephemeral=True)
        print(f'Error in kessel_command: {e}')


@bot.tree.command(name='coruscant_shift', description='Start a Coruscant Shift Sabacc game')
async def coruscant_shift_command(interaction: Interaction) -> None:
    '''
    Initiate a new Coruscant Shift Sabacc game.
    This version is fixed to 2 rounds by default.
    '''
    view = CoruscantGameView(
        active_games=active_games,
        channel=interaction.channel
    )

    embed = discord.Embed(
        title='Sabacc Game Lobby',
        description=(
            'Click **Play Game** to join the Coruscant Shift Sabacc game.\n\n'
            '**Game Settings:**\n'
            '• 2 Rounds (fixed)\n'
            '• 5 starting cards\n\n'
            'Once someone has joined, the **Start Game** button will be enabled.'
        ),
        color=0x964B00
    )
    embed.set_footer(text='Coruscant Shift Sabacc')
    embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/Coruscant%20Shift.png')

    try:
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()
        active_games.append(view)
    except Exception as e:
        await interaction.response.send_message(
            'An error occurred while starting the Coruscant Shift game.',
            ephemeral=True
        )
        print(f'Error in coruscant_shift_command: {e}')


@bot.tree.command(name='help', description='Display the Sabacc game rules')
async def help_command(interaction: Interaction) -> None:
    '''
    Display a public message summarizing the available Sabacc game modes
    (Corellian Spike, Kessel Sabacc, and Coruscant Shift),
    along with credits and repository links.
    '''

    embed = discord.Embed(
        title='Sabacc Droid',
        description=(
            'Welcome to **Sabacc Droid**! You can play any of the following Sabacc variations:\n\n'
            '• **Corellian Spike** (famously seen in *Solo* and at Galaxy\'s Edge)\n'
            '• **Kessel Sabacc** (inspired by *Star Wars: Outlaws*)\n'
            '• **Coruscant Shift** (a dice‑based mode featuring target numbers and suits)\n\n'

            'All modes aim for a hand sum near their target (zero or a dice‑determined value), but each uses unique decks and rules:\n'
            '- **Corellian Spike**: 62 cards, can hold multiple cards, 3 rounds, specialized hands.\n'
            '- **Kessel**: Two separate decks (positive & negative), strictly 2 cards, Impostor & Sylop mechanics.\n'
            '- **Coruscant Shift**: 62 cards, 2 rounds with 5 initial cards, gold/silver dice set a target number & suit. '
            'Final hand can be 1–5 cards.\n\n'

            'By default, Corellian Spike and Kessel each have 3 rounds (2 starting cards), while Coruscant Shift has 2 rounds (5 starting cards).\n\n'

            '**Credits & Disclaimers:**\n'
            '• **Corellian Spike Cards:** [Winz](https://cults3d.com/en/3d-model/game/sabacc-cards-and-spike-dice-printable)\n'
            '• **Kessel Sabacc Cards:** [u/Gold-Ad-4525](https://www.reddit.com/r/StarWarsSabacc/comments/1exatgi/kessel_sabaac_v3/)\n'
            '• All other creative content is fan-made, not affiliated with or endorsed by Lucasfilm/Disney.\n\n'
            'Created by **[Abubakr Elmallah](https://abubakrelmallah.com/)**.\n\n'
            '[📂 GitHub Repository](https://github.com/TheAbubakrAbu/Sabacc-Droid)\n\n'
            'May the Force be with you—choose a game mode and have fun!'
        ),
        color=0x964B00
    )
    embed.set_thumbnail(
        url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/refs/heads/main/src/sabacc_droid/images/Corellian%20Spike.png'
    )

    view = HelpView()  # Your existing view that offers buttons to see each ruleset, etc.
    await interaction.response.send_message(embed=embed, view=view)

class HelpView(ui.View):
    '''View containing buttons to display rules for different game modes.'''

    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label='Corellian Rules', style=discord.ButtonStyle.primary)
    async def corellian_spike_button(self, interaction: Interaction, button: ui.Button):
        rules_embed = get_corellian_spike_rules_embed()
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)

    @ui.button(label='Kessel Rules', style=discord.ButtonStyle.primary)
    async def kessel_button(self, interaction: Interaction, button: ui.Button):
        rules_embed = get_kessel_rules_embed()
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)

    @ui.button(label='Coruscant Rules', style=discord.ButtonStyle.primary)
    async def coruscant_button(self, interaction: Interaction, button: ui.Button):
        rules_embed = get_coruscant_shift_rules_embed()
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)

    @ui.button(label='Comparison', style=discord.ButtonStyle.secondary)
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