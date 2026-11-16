# sabacc_droid.py
#
# Starts the bot, registers the slash commands, and routes every button click
# to the game or menu it belongs to. `python sabacc_droid.py --self-test` runs
# the checks in self_test.py instead.

from __future__ import annotations

import asyncio
import dataclasses
import logging
import os
import random
import re
import signal
import sys
import time
from pathlib import Path

import discord
from discord import Interaction, app_commands

import corellian_spike  # noqa: F401  (each variant registers itself in game.variants)
import coruscant_shift  # noqa: F401
import game
import kessel  # noqa: F401
import traditional  # noqa: F401
from game import Game, Settings, games, goodbye_all, notice, variants, warning_time
from help import chooser_message, comparison_embed, help_message
from theme import icon

log = logging.getLogger('sabacc')

something_went_wrong = 'Something went wrong. Please try again.'
game_gone = 'This game has ended. Start a new one with `/sabacc`.'


def load_token() -> str | None:
    '''
    DISCORD_TOKEN from the environment, or from a .env file in the repository
    or next to this file.
    '''

    if os.getenv('DISCORD_TOKEN'):
        return os.environ['DISCORD_TOKEN']
    here = Path(__file__).resolve().parent
    for env in (here / '.env', here.parent.parent / '.env'):
        if env.is_file():
            for line in env.read_text().splitlines():
                name, _, value = line.partition('=')
                if name.strip() == 'DISCORD_TOKEN':
                    return value.strip().strip('\'"')
    return None


class SabaccDroid(discord.Client):
    farewell: asyncio.Task | None = None
    stopping: asyncio.Task | None = None

    async def setup_hook(self) -> None:
        await tree.sync()
        loop = asyncio.get_running_loop()
        self.sweeper = loop.create_task(sweep())
        # systemd stops the bot with SIGTERM on every deploy. Close cleanly
        # instead of dying, so close() can tell unfinished games first.
        loop.add_signal_handler(signal.SIGTERM, self.stop_soon)

    def stop_soon(self) -> None:
        # Only the first signal starts the shutdown. (discord.py clears
        # self.loop once it has closed, so later signals can't use it.)
        if self.stopping is None:
            self.stopping = asyncio.get_running_loop().create_task(self.close())

    async def close(self) -> None:
        # Every call waits on the same goodbyes, so a second SIGTERM (or
        # Ctrl+C) can't close the connection while they are still sending.
        if self.farewell is None and not self.is_closed():
            self.farewell = asyncio.create_task(goodbye_all())
        if self.farewell is not None:
            await self.farewell
        await super().close()


# Interactions arrive without any gateway intents, and nothing here reads the
# message or member caches, so subscribe to nothing and cache nothing.
client = SabaccDroid(
    intents=discord.Intents.none(),
    max_messages=None,
    member_cache_flags=discord.MemberCacheFlags.none(),
    chunk_guilds_at_startup=False,
    activity=discord.Game(f'{icon.sabacc} Sabacc'),  # "Playing 🃏 Sabacc", like Aurebesh Droid's "Playing 🔤 Aurebesh"
)
tree = app_commands.CommandTree(client)


async def sweep() -> None:
    '''
    Every few seconds, pings players with a minute left on their turn, and
    times out lobbies nobody started and turns nobody took.
    '''

    while True:
        await asyncio.sleep(15)
        await sweep_once()


async def sweep_once() -> None:
    soon = [current for current in games.values() if current.deadline - warning_time <= time.monotonic()]
    for current in soon:
        try:
            async with current.lock:
                # Look again now that the lock is held: while an earlier game
                # was being handled, a click may have restarted this one's timer.
                now = time.monotonic()
                if games.get(current.id) is not current:
                    continue
                if current.deadline <= now:
                    await current.expire()
                elif current.deadline - warning_time <= now and not current.warned and current.phase != 'lobby':
                    await current.warn()
        except Exception:
            log.exception('Timing out game %s failed', current.id)


async def open_lobby(it: Interaction, variant: type[Game], settings: Settings, first: object = None, content: str | None = None) -> bool:
    '''
    Opens a lobby as the reply to it. False if the bot is shutting down.
    '''

    if game.restarting:
        await notice(it, game.restarting_notice)
        return False
    await variant(variant.clamp(settings), it.channel).open_lobby(it, first, content)
    return True


# Slash commands -----------------------------------------------------------------

@tree.command(name='sabacc', description='Choose a Sabacc variant to play')
async def sabacc_command(it: Interaction) -> None:
    embed, view = chooser_message()
    await it.response.send_message(embed=embed, view=view)


@tree.command(name='random', description='Start a random Sabacc variant (use 0 for random rounds or cards)')
@app_commands.describe(rounds='Number of rounds (0 for random)', num_cards='Number of starting cards (0 for random)')
async def random_command(it: Interaction, rounds: app_commands.Range[int, 0, 10] = 0,
                         num_cards: app_commands.Range[int, 0, 10] = 0) -> None:
    variant = random.choice(list(variants.values()))
    await open_lobby(it, variant, variant.random_settings(rounds, num_cards))


@tree.command(name='corellian_spike', description='Start a Corellian Spike Sabacc game with optional custom settings')
@app_commands.describe(rounds='Number of rounds (default: 3, max: 10)', num_cards='Number of starting cards (default: 2, max: 5)',
                       discard='Allow discarding cards (default: off)')
async def corellian_spike_command(it: Interaction, rounds: app_commands.Range[int, 1, 10] = 3,
                                  num_cards: app_commands.Range[int, 1, 5] = 2, discard: bool = False) -> None:
    await open_lobby(it, variants['corellian_spike'], Settings(rounds, num_cards, discard))


@tree.command(name='coruscant_shift', description='Start a Coruscant Shift Sabacc game with optional custom settings')
@app_commands.describe(rounds='Number of rounds (default: 2, max: 5)', num_cards='Number of starting cards (default: 5, max: 10)')
async def coruscant_shift_command(it: Interaction, rounds: app_commands.Range[int, 1, 5] = 2,
                                  num_cards: app_commands.Range[int, 1, 10] = 5) -> None:
    await open_lobby(it, variants['coruscant_shift'], Settings(rounds, num_cards))


@tree.command(name='kessel', description='Start a Kessel Sabacc game with optional custom settings')
@app_commands.describe(rounds='Number of rounds (default: 3, max: 10)')
async def kessel_command(it: Interaction, rounds: app_commands.Range[int, 1, 10] = 3) -> None:
    await open_lobby(it, variants['kessel'], Settings(rounds, 2))


@tree.command(name='traditional', description='Start a Traditional Sabacc game with optional custom settings')
@app_commands.describe(num_cards='Number of starting cards (default: 2, max: 5)', discard='Allow discarding cards (default: off)')
async def traditional_command(it: Interaction, num_cards: app_commands.Range[int, 1, 5] = 2, discard: bool = False) -> None:
    await open_lobby(it, variants['traditional'], Settings(0, num_cards, discard))


@tree.command(name='help', description='Show how to use Sabacc Droid')
async def help_command(it: Interaction) -> None:
    embed, view = help_message()
    await it.response.send_message(embed=embed, view=view)


@tree.error
async def on_command_error(it: Interaction, error: app_commands.AppCommandError) -> None:
    log.error('/%s failed', it.command.name if it.command else '?', exc_info=error)
    try:
        await notice(it, something_went_wrong)
    except discord.HTTPException:
        pass


# Buttons ------------------------------------------------------------------------

async def route(it: Interaction, custom_id: str) -> None:
    '''
    "g:..." buttons belong to a game in progress; the rest work on their own:
    "start:<variant>", "again:<variant>:<settings>", "rules:<variant>", and "help".
    '''

    kind, _, rest = custom_id.partition(':')

    if kind == 'g':
        parts = rest.split(':', 3)
        current = games.get(parts[0])
        if current is None or len(parts) < 3:
            return await notice(it, game_gone)
        async with current.lock:
            if games.get(current.id) is not current:
                return await notice(it, game_gone)
            await current.handle(it, parts[1], parts[2], parts[3] if len(parts) > 3 else '')

    elif kind == 'start':
        if rest == 'random':
            variant = random.choice(list(variants.values()))
            await open_lobby(it, variant, variant.random_settings())
        elif rest in variants:
            await open_lobby(it, variants[rest], dataclasses.replace(variants[rest].defaults))
        else:
            await notice(it, game_gone)

    elif kind == 'again':
        key, _, encoded = rest.partition(':')
        settings = Settings.decode(encoded)
        if key not in variants or settings is None:
            return await notice(it, game_gone)
        # A rematch pings everyone the results message pinged, apart from whoever clicked.
        pinged = dict.fromkeys(re.findall(r'<@!?(\d+)>', getattr(it.message, 'content', None) or ''))
        others = [f'<@{user_id}>' for user_id in pinged if int(user_id) != it.user.id]
        content = (f'{icon.again} {" ".join(others)}: {it.user.mention} started a rematch. Click **Join Game** to play again.'
                   if others else None)
        if not await open_lobby(it, variants[key], settings, first=it.user, content=content):
            return  # the bot is restarting, so Play Again stays clickable
        try:
            await it.message.edit(view=variants[key].results_view(settings, again=False))
        except (discord.HTTPException, AttributeError):
            pass

    elif kind == 'rules':
        embed = comparison_embed() if rest == 'compare' else variants[rest].rules_embed() if rest in variants else None
        if embed is None:
            return await notice(it, game_gone)
        await it.response.send_message(embed=embed, ephemeral=True)

    elif custom_id == 'help':
        embed, view = help_message()
        await it.response.send_message(embed=embed, view=view, ephemeral=True)

    else:
        await notice(it, 'This button is from an older version of Sabacc Droid. Start a new game with `/sabacc`.')


@client.event
async def on_interaction(it: Interaction) -> None:
    if it.type is not discord.InteractionType.component:
        return
    custom_id = str((it.data or {}).get('custom_id', ''))
    try:
        await route(it, custom_id)
    except Exception:
        log.exception('Button %s failed', custom_id)
        try:
            await notice(it, something_went_wrong)
        except discord.HTTPException:
            pass


@client.event
async def on_ready() -> None:
    log.info('Sabacc Droid is online as %s', client.user)


def main() -> None:
    if '--self-test' in sys.argv:
        from self_test import self_test
        sys.exit(asyncio.run(self_test()))

    token = load_token()
    if not token:
        sys.exit('DISCORD_TOKEN is not set. Put it in the environment or in a .env file.')
    client.run(token, root_logger=True)  # so the bot's own log lines show up, not just discord.py's


if __name__ == '__main__':
    main()
