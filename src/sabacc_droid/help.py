# help.py
#
# /help, the /sabacc variant menu, and the comparison of the four variants.

from discord import ButtonStyle, Embed

import theme
from game import turn_time, variants
from theme import Components, button, icon, link_button, titled

order = ('corellian_spike', 'coruscant_shift', 'kessel', 'traditional')

wiki = {
    'corellian_spike': 'https://starwars.fandom.com/wiki/Corellian_Spike',
    'coruscant_shift': 'https://starwars.fandom.com/wiki/Coruscant_Shift',
    'kessel': 'https://starwars.fandom.com/wiki/Kessel_Sabacc',
    'traditional': 'https://starwars.fandom.com/wiki/Sabacc',
}

blurbs = {
    'corellian_spike': "Aim for **0**, with Sylops and a long list of special hands. Seen in *Solo: A Star Wars Story* and *Galaxy's Edge*.",
    'coruscant_shift': 'A gold die sets the **target number** and a silver die sets the **target suit**. Played on the *Halcyon* at *Galactic Starcruiser*.',
    'kessel': 'Hold **exactly 2 cards**, one Sand and one Blood, with Impostors and Sylops. Seen in *Star Wars Outlaws*.',
    'traditional': 'Aim for **+23 or -23** with no round limit, until someone calls **Alderaan**. Seen in *Star Wars Rebels*.',
}


def chooser_message() -> tuple[Embed, Components]:
    embed = theme.embed(titled(icon.sabacc, 'Choose a Sabacc Variant'),
                        'Pick a variant to open a lobby in this channel, or let the dice decide.')
    for key in order:
        game = variants[key]
        defaults = ', '.join(game.settings_lines(game.defaults)).replace('Discarding is off', 'no discarding')
        embed.add_field(name=f'{game.icon} {game.name}', value=f'{blurbs[key]}\n*{defaults}*', inline=False)
    items = [button(variants[key].icon, variants[key].name, f'start:{key}', ButtonStyle.primary) for key in order]
    items += [button(icon.random, 'Play Random', 'start:random', ButtonStyle.success), button(icon.help, 'How to Play', 'help')]
    return embed, Components(*items)


def help_message() -> tuple[Embed, Components]:
    embed = theme.embed(titled(icon.help, 'Sabacc Droid'),
                        'Play **Sabacc**, the Star Wars card game, with up to 8 players in any channel. '
                        'Play alone and **Lando Calrissian AI** takes a seat and plays against you.')
    embed.add_field(name=f'{icon.sabacc} Start a Game', value=(
        '`/sabacc` opens a menu of the four variants.\n'
        '`/corellian_spike`, `/coruscant_shift`, `/kessel`, and `/traditional` start one with your own settings.\n'
        '`/random` starts a random variant.'), inline=False)
    for key in order:
        game = variants[key]
        embed.add_field(name=f'{game.icon} {game.name}', value=f'{blurbs[key]} [Wiki]({wiki[key]})', inline=False)
    embed.add_field(name=f'{icon.timeout} Taking Turns', value=(
        'Your hand is private: click **Play Turn** when the bot pings you, and **Ranks As** shows what your hand counts as right now. '
        f"You get a ping with a minute left, and if you don't act within {turn_time // 60} minutes, you stand automatically. "
        'A lobby closes if nobody starts it within an hour.'), inline=False)
    embed.add_field(name='📚 Learn More', value=(
        f'Card designs, rules, and more at **[Hyperspace Props]({theme.hyperspace_props_link})**.'), inline=False)

    # The same ending as Aurebesh Droid's /help (see theme.py).
    embed.add_field(name='🖼️ Card Art', value=(
        '[Winz](https://cults3d.com/en/3d-model/game/sabacc-cards-and-spike-dice-printable) (Corellian Spike and Coruscant Shift), '
        '[u/Gold-Ad-4525](https://www.reddit.com/r/StarWarsSabacc/comments/1exatgi/kessel_sabaac_v3/) (Kessel), and '
        '[Multiversal Exports](https://design.multiversalexports.com) (Traditional)'), inline=False)
    embed.add_field(name='🌌 More Star Wars', value=(
        f'- **[Aurebesh Droid]({theme.aurebesh_droid_link})**: Translate text into Aurebesh and 13 more Star Wars scripts.\n'
        + theme.star_wars_apps), inline=False)
    embed.add_field(name='🛠️ Made By', value=(
        f'Created by **{theme.creator}** with [discord.py](https://github.com/Rapptz/discord.py) and '
        '[Pillow](https://python-pillow.org).'), inline=False)
    embed.set_footer(text=theme.disclaimer)

    items = [button(variants[key].icon, f'{variants[key].name} Rules', f'rules:{key}') for key in order]
    items += [
        button(icon.compare, 'Compare Variants', 'rules:compare'),
        link_button(icon.join, 'Add Sabacc Droid', theme.add_bot_link),
        link_button(icon.app, 'Datapad App', theme.datapad_app),
        link_button(icon.github, 'GitHub', theme.github_link),
    ]
    return embed, Components(*items)


def comparison_embed() -> Embed:
    embed = theme.embed(titled(icon.compare, 'Compare the Variants'),
                        'Every variant aims for a hand total close to a target, has Sylops or similar special cards, '
                        'and rewards smart choices. Here is how they differ.')
    embed.add_field(name=f'{icon.corellian_spike} Corellian Spike', inline=False, value=(
        '- **Deck:** 62 cards, -10 to +10 in three staves, plus 2 Sylops (0).\n'
        '- **Target:** 0. **Rounds:** 3. **Hand:** no limit.\n'
        '- **Actions:** Draw, Replace, Discard (if on), Stand, or Junk.\n'
        '- **Special Hands:** Pure Sabacc, Fleet, Yee-Haa, and more.'))
    embed.add_field(name=f'{icon.coruscant_shift} Coruscant Shift', inline=False, value=(
        '- **Deck:** 62 cards, -10 to +10 in three suits (●, ▲, ■), plus 2 Sylops (0).\n'
        '- **Target:** set by the gold die (-10, +10, -5, +5, 0, 0); the silver die sets the suit that breaks ties.\n'
        '- **Rounds:** 2. **Hand:** 5 cards, refilled each round.\n'
        '- **Actions:** Choose which cards to keep, or Junk.'))
    embed.add_field(name=f'{icon.kessel} Kessel', inline=False, value=(
        '- **Deck:** Sand (positive) and Blood (negative), 22 cards each, with Impostors (Ψ) and Sylops (Ø).\n'
        '- **Target:** 0. **Rounds:** 3. **Hand:** exactly 2 cards, one of each.\n'
        '- **Actions:** Draw from either deck and keep one card, Stand, or Junk.\n'
        '- **Special Hands:** Pure Sabacc, Prime Sabacc, and more.'))
    embed.add_field(name=f'{icon.traditional} Traditional', inline=False, value=(
        '- **Deck:** 76 cards, four suits of +1 to +15, plus 16 special cards.\n'
        '- **Target:** +23 or -23. **Rounds:** until someone calls Alderaan. **Hand:** no limit.\n'
        '- **Actions:** Draw, Replace, Discard (if on), Stand, Junk, or Call Alderaan.\n'
        "- **Special Hands:** Idiot's Array, Natural Sabacc, and Fairy Empress."))
    return embed
