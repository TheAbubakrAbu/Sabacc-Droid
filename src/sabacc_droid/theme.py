# theme.py
#
# What every reply shares, so the bot looks the same everywhere: its colors,
# its images, and one icon per feature and action.
#
# Conventions for replies, the same in Sabacc Droid and Aurebesh Droid:
#   - Titles are "<icon> <Title Case>".
#   - Buttons have an icon and a Title Case label, except buttons that are
#     the choice itself (a card, a quiz answer), which show just that.
#   - Notices only the user sees are "❌ " and a full sentence.
#   - Text uses straight quotes and apostrophes.
#   - /help ends with the credits, More Star Wars, and Made By fields, link
#     buttons to add the bot, the Datapad app, and GitHub, and the disclaimer
#     below as its footer.
# And in Sabacc Droid:
#   - Cards are written as code chips, such as `+5` `-3`.
#   - Game log lines are "<icon> <player> <present tense>.", such as
#     "✋ @Han stands.", for people and Lando alike.
#   - Private replies to your own move are titled "You ...", such as
#     "You Drew a Card"; prompts are the action, such as "Replace a Card".

from discord import ButtonStyle, Embed, ui

color = 0x764920  # Sabacc Droid's brown
images = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/'
logo = images + 'sabacc.png'
footer = 'The Star Wars card game'

github_link = 'https://github.com/TheAbubakrAbu/Sabacc-Droid'
add_bot_link = 'https://discord.ly/sabaac-droid'
hyperspace_props_link = 'https://hyperspaceprops.com/sabacc-resources/'

# Shared word for word with Aurebesh Droid's /help.
creator = '[Abubakr Elmallah](https://abubakrelmallah.com)'
disclaimer = 'Fan-made and not affiliated with or endorsed by Lucasfilm or Disney. May the Force be with you!'
aurebesh_droid_link = 'https://discord.ly/aurebesh-droid'
datapad_app = 'https://apps.apple.com/us/app/datapad-aurebesh-translator/id6450498054?platform=iphone'
translator_app = 'https://apps.apple.com/us/app/aurebesh-translator/id6670201513?platform=iphone'
star_wars_apps = (
    f'- **[Datapad | Aurebesh Translator]({datapad_app})**: An immersive Aurebesh translator with a themed keyboard.\n'
    f'- **[Aurebesh Translator]({translator_app})**: A free, offline, ad-free translator.')


class icon:
    sabacc = '🃏'
    corellian_spike = '🔺'
    coruscant_shift = '🎲'
    kessel = '🌀'
    traditional = '🪐'
    random = '🔀'
    help = '📖'
    rules = '📜'
    compare = '⚖️'
    join = '➕'
    leave = '🚪'
    start = '▶️'
    play = '🎴'
    draw = '🃏'
    sand = '🟨'
    blood = '🟥'
    replace = '🔄'
    discard = '🗑️'
    stand = '✋'
    junk = '🏳️'
    alderaan = '💥'
    confirm = '✅'
    back = '↩️'
    again = '🔁'
    dice = '🎲'
    timeout = '⌛'
    update = '⚙️'
    winner = '🏆'
    error = '❌'
    link = '🔗'
    github = '📂'
    app = '📱'


def titled(emoji: str, text: str) -> str:
    '''
    "<icon> <text>", the form of every title.
    '''

    return f'{emoji} {text}'


def embed(title: str, description: str = '', *, color: int = color, thumbnail: str = logo, footer: str = footer) -> Embed:
    '''
    An embed in the house style: a colored bar, a thumbnail, and a footer.
    '''

    result = Embed(title=title, description=description or None, color=color)
    result.set_thumbnail(url=thumbnail)
    result.set_footer(text=footer)
    return result


def button(emoji: str, label: str, custom_id: str, style: ButtonStyle = ButtonStyle.secondary, *, disabled: bool = False, row: int | None = None) -> ui.Button:
    return ui.Button(emoji=emoji, label=label, custom_id=custom_id, style=style, disabled=disabled, row=row)


def link_button(emoji: str, label: str, url: str) -> ui.Button:
    return ui.Button(emoji=emoji, label=label, url=url)


class Components(ui.View):
    '''
    Buttons to attach to a message. Every click goes to the router in
    sabacc_droid.py by its custom id, so discord.py never has to remember
    these views (remembering them is how the old bot slowly filled its memory).
    '''

    def __init__(self, *items: ui.Item) -> None:
        super().__init__(timeout=None)
        for item in items:
            self.add_item(item)

    def is_finished(self) -> bool:
        return True


def plural(count: int, word: str) -> str:
    '''
    "1 round", "3 rounds".
    '''

    return f'{count} {word}' if count == 1 else f'{count} {word}s'


def signed(value: int) -> str:
    '''
    "+5", "-3", "0".
    '''

    return f'+{value}' if value > 0 else str(value)


def chips(labels) -> str:
    '''
    Cards as code chips: `+5` `-3`.
    '''

    return ' '.join(f'`{label}`' for label in labels) or '*No cards*'
