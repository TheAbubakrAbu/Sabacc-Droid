# game.py
#
# What every Sabacc variant shares: the lobby, taking turns, the timer for
# players who walk away, Lando Calrissian AI, and the results. Each variant
# file adds its deck, its turn actions, how it scores a hand, and how Lando
# plays it.
#
# Every game button's custom id is "g:<game>:<turn>:<action>[:<choice>]".
# The turn number goes up the moment a turn ends, so a double click, an old
# message, or a stray click can never act twice or out of turn. A game is
# forgotten as soon as it ends; the Play Again and View Rules buttons carry
# everything they need in their ids, so they keep working after a restart.
#
# Every move, by a person or by Lando, becomes one line in the channel's game
# log, in the present tense: "🃏 @Han draws a card."

from __future__ import annotations

import asyncio
import logging
import random
import secrets
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Callable, ClassVar

import discord
from discord import ButtonStyle, Embed, Interaction

import cards
import theme
from theme import Components, button, chips, icon, plural, signed

log = logging.getLogger('sabacc')

games: dict[str, Game] = {}
variants: dict[str, type[Game]] = {}

max_players = 8
turn_time = 5 * 60  # seconds before a player who walked away stands automatically
warning_time = 60  # seconds left on that timer when the player is pinged
lobby_time = 60 * 60  # seconds before a lobby nobody started closes
medals = {1: '🥇', 2: '🥈', 3: '🥉'}


async def reply_safely(reply: Any) -> None:
    '''
    Sends a reply to a move that has already happened. If Discord drops the
    reply, the move still stands and the game goes on, so a lost message
    can never leave a turn half done.
    '''

    try:
        await reply
    except discord.HTTPException as error:
        log.warning('A reply was lost: %s', error)


background: set[asyncio.Task] = set()  # keeps tasks started by in_background alive until they finish


def in_background(work: Any) -> None:
    task = asyncio.get_running_loop().create_task(work)
    background.add(task)
    task.add_done_callback(background.discard)


async def delete_quietly(message: Any) -> None:
    try:
        await message.delete()
    except discord.HTTPException:
        pass


async def notice(it: Interaction, sentence: str) -> None:
    '''
    A private "❌ <sentence>" reply.
    '''

    text = f'{icon.error} {sentence}'
    if it.response.is_done():
        await it.followup.send(text, ephemeral=True)
    else:
        await it.response.send_message(text, ephemeral=True)


@dataclass
class Settings:
    rounds: int = 0  # 0 means no round limit
    cards: int = 0
    discard: bool = False

    def encode(self) -> str:
        return f'{self.rounds}.{self.cards}.{int(self.discard)}'

    @staticmethod
    def decode(text: str) -> Settings | None:
        parts = text.split('.')
        if len(parts) != 3 or not all(part.isdigit() and len(part) <= 2 for part in parts):
            return None
        return Settings(int(parts[0]), int(parts[1]), parts[2] == '1')


class Lando:
    '''
    Stands in for a Discord user when Lando takes a seat.
    '''

    id = 0
    mention = '**Lando Calrissian AI**'
    display_name = 'Lando Calrissian AI'


class Player:
    def __init__(self, user: Any) -> None:
        self.user = user
        self.hand: list = []

    @property
    def is_ai(self) -> bool:
        return self.user.id == Lando.id


class Deck:
    '''
    A shuffled deck with a discard pile. When the deck runs out, the discard
    pile is shuffled back in; if that is empty too, a fresh deck is opened.
    '''

    def __init__(self, make: Callable[[], list]) -> None:
        self.make = make
        self.cards = make()
        random.shuffle(self.cards)
        self.discards: list = []

    def draw(self) -> Any:
        if not self.cards:
            self.cards, self.discards = self.discards or self.make(), []
            random.shuffle(self.cards)
        return self.cards.pop()

    def discard(self, card: Any) -> None:
        self.discards.append(card)


@lru_cache(maxsize=16)
def backs_png(paths: tuple[str, ...]) -> bytes:
    return cards.render(list(paths))


class Game:
    # Set by each variant.
    key: ClassVar[str]
    name: ClassVar[str]
    icon: ClassVar[str]
    color: ClassVar[int]
    thumbnail: ClassVar[str]
    footer: ClassVar[str]
    defaults: ClassVar[Settings]
    limits: ClassVar[dict[str, tuple[int, int]]] = {}  # 'rounds' and 'cards' when they can be changed
    has_discard: ClassVar[bool] = False

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if 'key' in cls.__dict__:
            variants[cls.key] = cls

    def __init__(self, settings: Settings, channel: Any) -> None:
        self.id = secrets.token_hex(4)
        self.settings = settings
        self.channel = channel
        self.players: list[Player] = []
        self.phase = 'lobby'  # then 'playing', 'ending' (Kessel's Impostor dice), and 'over'
        self.turn = 0
        self.current = 0
        self.round = 1
        self.solo = False
        self.idle_turns = 0
        self.lobby_message: Any = None
        self.turn_message: Any = None
        self.last_interaction: Interaction | None = None
        self.warning: Any = None  # the "1 minute left" ping, deleted when the turn ends
        self.start_timer(lobby_time)
        self.lock = asyncio.Lock()
        games[self.id] = self

    # Settings ---------------------------------------------------------------

    @classmethod
    def clamp(cls, settings: Settings) -> Settings:
        def fit(name: str, value: int) -> int:
            if name not in cls.limits:
                return getattr(cls.defaults, name)
            low, high = cls.limits[name]
            return max(low, min(value, high))

        return Settings(fit('rounds', settings.rounds), fit('cards', settings.cards),
                        settings.discard and cls.has_discard)

    @classmethod
    def random_settings(cls, rounds: int = 0, cards: int = 0) -> Settings:
        def pick(name: str, wanted: int) -> int:
            if name not in cls.limits:
                return getattr(cls.defaults, name)
            return wanted or random.randint(*cls.limits[name])

        return cls.clamp(Settings(pick('rounds', rounds), pick('cards', cards), random.choice([True, False])))

    @classmethod
    def settings_lines(cls, settings: Settings) -> list[str]:
        raise NotImplementedError

    @classmethod
    def rules_embed(cls) -> Embed:
        raise NotImplementedError

    @classmethod
    def styled(cls, title: str, description: str = '') -> Embed:
        return theme.embed(theme.titled(cls.icon, title), description, color=cls.color,
                           thumbnail=cls.thumbnail, footer=cls.footer)

    @classmethod
    def rules_button(cls) -> discord.ui.Button:
        return button(icon.rules, 'View Rules', f'rules:{cls.key}')

    # What each variant fills in -----------------------------------------------

    def deal(self) -> None:
        raise NotImplementedError

    def labels(self, player: Player) -> list[str]:
        raise NotImplementedError

    def faces(self, player: Player) -> list[str]:
        raise NotImplementedError

    def backs(self, player: Player) -> list[str]:
        raise NotImplementedError

    def total(self, player: Player) -> str:
        return signed(sum(card.value for card in player.hand))

    def target(self) -> str:
        return '0'

    def score(self, player: Player) -> tuple[tuple, str]:
        '''
        (sort key, hand name). The lowest key wins; equal keys tie.
        '''

        raise NotImplementedError

    def standing(self, player: Player) -> str:
        '''
        What the hand counts as right now, for the "Ranks As" field.
        '''

        return f'**{self.score(player)[1]}**'

    def turn_buttons(self, player: Player) -> list[discord.ui.Button]:
        raise NotImplementedError

    async def act(self, it: Interaction, player: Player, action: str, choice: str) -> None:
        raise NotImplementedError

    def ai_move(self, player: Player) -> str:
        '''
        Plays Lando's turn and returns its game log line.
        '''

        raise NotImplementedError

    def settle(self, player: Player) -> None:
        '''
        Finishes anything the player left half done (Kessel's drawn card)
        before they stand, junk, or run out of time.
        '''

    def auto_play(self, player: Player) -> str:
        '''
        What a player who ran out of time does, as the end of a sentence.
        '''

        self.settle(player)
        return 'stands'

    def headline(self, name: str) -> str:
        return f'wins with **{name}**!'

    def hand_fields(self, player: Player) -> list[tuple]:
        '''
        Extra (name, value) or (name, value, inline) fields under a hand.
        '''

        return []

    def result_note(self) -> str:
        return ''

    async def start_message(self) -> tuple[Embed, list[discord.File]]:
        '''
        What the lobby turns into when the game starts.
        '''

        return self.lobby_embed(), []

    # Small helpers ------------------------------------------------------------

    def id_for(self, action: str, choice: str = '') -> str:
        return f'g:{self.id}:{self.turn}:{action}' + (f':{choice}' if choice else '')

    def round_text(self) -> str:
        if self.settings.rounds:
            return f'Round {self.round} of {self.settings.rounds}'
        return f'Round {self.round}'

    def humans(self) -> list[Player]:
        return [player for player in self.players if not player.is_ai]

    def start_timer(self, seconds: float) -> None:
        '''
        Restarts the clock that sweep() in sabacc_droid.py watches.
        '''

        self.deadline = time.monotonic() + seconds
        self.warned = False

    async def post(self, **message: Any) -> Any:
        '''
        Sends a message to the game's channel. If the bot can't post there,
        the game closes and the last player to click is told why.
        '''

        try:
            return await self.channel.send(**message)
        except (discord.Forbidden, discord.NotFound):
            await self.close("I can't post in this channel. Ask a server admin to let me send messages and attach files here.")
            return None

    async def close(self, reason: str) -> None:
        self.phase = 'over'
        games.pop(self.id, None)
        if self.last_interaction is not None:
            try:
                await notice(self.last_interaction, reason)
            except discord.HTTPException:
                pass

    async def hand_reply(self, player: Player, title: str, note: str = '',
                         faces: list[str] | None = None) -> tuple[Embed, discord.File]:
        '''
        The private message that shows a player their hand.
        '''

        embed = self.styled(f'{title}: {self.round_text()}', note)
        embed.add_field(name='Your Hand', value=chips(self.labels(player)), inline=False)
        embed.add_field(name='Total', value=self.total(player), inline=True)
        embed.add_field(name='Target', value=self.target(), inline=True)
        embed.add_field(name='Ranks As', value=self.standing(player), inline=True)
        for name, value, *inline in self.hand_fields(player):
            embed.add_field(name=name, value=value, inline=inline[0] if inline else True)
        png = await asyncio.to_thread(cards.render, faces or self.faces(player))
        embed.set_image(url='attachment://cards.png')
        return embed, cards.as_file(png)

    async def show_hand(self, it: Interaction, player: Player, title: str, note: str = '',
                        buttons: list[discord.ui.Button] | None = None, faces: list[str] | None = None,
                        new: bool = False) -> None:
        embed, file = await self.hand_reply(player, title, note, faces)
        view = Components(*buttons) if buttons else None
        if new:
            await reply_safely(it.response.send_message(embed=embed, file=file, view=view or discord.utils.MISSING, ephemeral=True))
        else:
            await reply_safely(it.response.edit_message(embed=embed, attachments=[file], view=view))

    async def show_turn(self, it: Interaction, player: Player, note: str = '', new: bool = False) -> None:
        await self.show_hand(it, player, 'Your Turn', note, self.turn_buttons(player), new=new)

    # The lobby --------------------------------------------------------------

    def lobby_embed(self) -> Embed:
        if self.phase != 'lobby':
            names = ', '.join(player.user.mention for player in self.players)
            description = f'{icon.start} The game has started with {names}.'
        elif self.players:
            joined = '\n'.join(player.user.mention for player in self.players)
            description = f'**Players ({len(self.players)}/{max_players})**\n{joined}\n\n'
            description += ('Click **Start Game** when everyone is in.' if len(self.players) > 1 else
                            'Waiting for more players. Start now to play against Lando Calrissian AI.')
        else:
            description = 'Click **Join Game** to take a seat. Up to 8 players can join.'
        embed = self.styled(f'{self.name} Lobby', description)
        embed.add_field(name='Settings', value='\n'.join(f'- {line}' for line in self.settings_lines(self.settings)), inline=False)
        return embed

    def lobby_view(self) -> Components:
        if self.phase != 'lobby':
            return Components(self.rules_button())
        items = [
            button(icon.join, 'Join Game', self.id_for('join'), ButtonStyle.primary, disabled=len(self.players) >= max_players),
            button(icon.leave, 'Leave Game', self.id_for('leave'), ButtonStyle.danger, disabled=not self.players),
            button(icon.start, 'Start Game', self.id_for('start'), ButtonStyle.success, disabled=not self.players),
        ]
        if self.has_discard:
            state = 'On' if self.settings.discard else 'Off'
            items.append(button(icon.discard, f'Discarding: {state}', self.id_for('discarding')))
        items.append(self.rules_button())
        return Components(*items)

    async def open_lobby(self, it: Interaction, first: Any = None, content: str | None = None) -> None:
        '''
        Posts the lobby as the reply to it. first, if given, has already
        joined; content pings players for a rematch.
        '''

        if first is not None:
            self.players.append(Player(first))
        self.last_interaction = it
        await it.response.send_message(content=content, embed=self.lobby_embed(), view=self.lobby_view())
        message = await it.original_response()
        self.lobby_message = self.channel.get_partial_message(message.id)

    async def lobby_join(self, it: Interaction) -> None:
        if any(player.user.id == it.user.id for player in self.players):
            return await notice(it, "You're already in this game.")
        if len(self.players) >= max_players:
            return await notice(it, 'This game is full.')
        self.players.append(Player(it.user))
        self.start_timer(lobby_time)
        await it.response.edit_message(embed=self.lobby_embed(), view=self.lobby_view())

    async def lobby_leave(self, it: Interaction) -> None:
        player = next((player for player in self.players if player.user.id == it.user.id), None)
        if player is None:
            return await notice(it, "You're not in this game.")
        self.players.remove(player)
        await it.response.edit_message(embed=self.lobby_embed(), view=self.lobby_view())

    async def lobby_discarding(self, it: Interaction) -> None:
        self.settings.discard = not self.settings.discard
        await it.response.edit_message(embed=self.lobby_embed(), view=self.lobby_view())

    async def lobby_start(self, it: Interaction) -> None:
        if not any(player.user.id == it.user.id for player in self.players):
            return await notice(it, 'Only players in this game can start it.')
        self.phase = 'playing'
        self.solo = len(self.players) == 1
        if self.solo:
            self.players.append(Player(Lando()))
        random.shuffle(self.players)
        self.deal()
        self.turn = 1
        embed, files = await self.start_message()
        await it.response.edit_message(embed=embed, attachments=files, view=self.lobby_view())
        await self.announce()

    # Turns ------------------------------------------------------------------

    async def handle(self, it: Interaction, turn: str, action: str, choice: str) -> None:
        '''
        Every click on one of this game's buttons, already holding self.lock.
        '''

        self.last_interaction = it
        if action in ('join', 'leave', 'start', 'discarding'):
            if self.phase != 'lobby':
                return await notice(it, 'This game has already started.')
            if action == 'discarding' and not self.has_discard:
                return await notice(it, "This variant doesn't use discarding.")
            return await getattr(self, f'lobby_{action}')(it)

        if turn != str(self.turn):
            return await notice(it, 'That turn is already over.')
        if self.phase == 'ending':
            return await self.act_after(it, action, choice)
        if self.phase != 'playing':
            return await notice(it, 'This game is over.')

        player = self.players[self.current]
        if it.user.id != player.user.id:
            return await notice(it, "It's not your turn.")
        self.idle_turns = 0
        self.start_timer(turn_time)  # someone still deciding is never cut off
        self.drop_warning()
        if action == 'play':
            return await self.show_turn(it, player, new=True)
        if action == 'back':
            return await self.show_turn(it, player)
        if action == 'stand':
            self.settle(player)
            await self.show_hand(it, player, 'You Stand')
            return await self.next_turn(f'{icon.stand} {player.user.mention} stands.')
        if action == 'junk':
            self.settle(player)
            await self.show_hand(it, player, 'You Junked Your Hand', 'You are out of this game.')
            return await self.junk(player, f'{icon.junk} {player.user.mention} junks their hand and leaves the game.')
        await self.act(it, player, action, choice)

    async def act_after(self, it: Interaction, action: str, choice: str) -> None:
        await notice(it, 'This game is over.')

    async def announce(self) -> None:
        '''
        Tells the channel whose turn it is, or plays Lando's turn.
        '''

        player = self.players[self.current]
        if player.is_ai:
            line = self.ai_move(player)
            await self.post(embed=self.styled(f'{self.name}: {self.round_text()}', line))
            if self.phase == 'playing':
                await self.next_turn(line)
            return

        self.start_timer(turn_time)
        seats = []
        for index, seat in enumerate(self.players):
            mark = icon.confirm if index < self.current else icon.start if index == self.current else '⏳'
            seats.append(f'{mark} {seat.user.mention}: {plural(len(seat.hand), "card")}')

        embed = self.styled(f'{self.name}: {self.round_text()}',
                            f"It's {player.user.mention}'s turn. Click **Play Turn** to see your hand." + self.turn_note())
        embed.add_field(name='Players', value='\n'.join(seats), inline=False)
        embed.add_field(name='Target', value=self.target(), inline=True)
        png = await asyncio.to_thread(backs_png, tuple(self.backs(player)))
        embed.set_image(url='attachment://cards.png')
        view = Components(button(icon.play, 'Play Turn', self.id_for('play'), ButtonStyle.primary), self.rules_button())
        self.turn_message = await self.post(content=player.user.mention, embed=embed, file=cards.as_file(png), view=view)

    def turn_note(self) -> str:
        return ''

    async def log_turn(self, line: str) -> None:
        '''
        Turns the last "it's your turn" message into its line of the game log.
        '''

        await self.clear_warning()
        message, self.turn_message = self.turn_message, None
        if message is None:
            return
        try:
            await message.edit(content=None, embed=self.styled(f'{self.name}: {self.round_text()}', line),
                               attachments=[], view=None)
        except discord.HTTPException:
            pass

    async def next_turn(self, line: str, removed: bool = False) -> None:
        '''
        Ends the current turn and starts the next one, or ends the game.
        removed means the current player just left, so the next player is
        already in their seat.
        '''

        await self.log_turn(line)
        self.turn += 1
        if not removed:
            self.current += 1
        wrapped = self.current >= len(self.players)
        if wrapped:
            self.current = 0
        if self.game_over() or (wrapped and self.settings.rounds and self.round >= self.settings.rounds):
            return await self.finish()
        if wrapped:
            self.round += 1
            self.new_round()
        await self.announce()

    def new_round(self) -> None:
        pass

    def game_over(self) -> bool:
        return False

    async def junk(self, player: Player, line: str) -> None:
        self.players.remove(player)
        if len(self.players) < 2:
            await self.log_turn(line)
            self.turn += 1
            return await self.finish()
        await self.next_turn(line, removed=True)

    async def expire(self) -> None:
        '''
        Called when self.deadline passes, holding self.lock.
        '''

        if self.phase == 'lobby':
            self.phase = 'over'
            games.pop(self.id, None)
            embed = self.styled(f'{self.name} Lobby', f'{icon.timeout} This lobby closed after an hour without starting. Start a new game with `/sabacc`.')
            if self.lobby_message is not None:
                try:
                    await self.lobby_message.edit(embed=embed, view=Components(self.rules_button()))
                except discord.HTTPException:
                    pass
        elif self.phase == 'playing':
            player = self.players[self.current]
            line = f'{icon.timeout} {player.user.mention} runs out of time and {self.auto_play(player)}.'
            self.idle_turns += 1
            if self.idle_turns >= len(self.humans()):
                await self.log_turn(line)
                self.turn += 1
                return await self.finish(f'{icon.timeout} Everyone stepped away, so the game ended early.')
            await self.next_turn(line)
        else:
            await self.expire_after()

    async def expire_after(self) -> None:
        pass

    def waiting_on(self) -> tuple[list[Player], str]:
        '''
        Who the game is waiting on, and for what, for the "1 minute left" ping.
        '''

        if self.phase == 'playing' and not self.players[self.current].is_ai:
            return [self.players[self.current]], 'play your turn'
        return [], ''

    async def warn(self) -> None:
        '''
        Called a minute before self.deadline, holding self.lock.
        '''

        self.warned = True
        await self.clear_warning()  # never leave an older ping behind
        players, task = self.waiting_on()
        if players:
            names = ' '.join(player.user.mention for player in players)
            self.warning = await self.post(content=f'{icon.timeout} {names}, you have 1 minute left to {task}.')

    async def clear_warning(self) -> None:
        message, self.warning = self.warning, None
        if message is not None:
            await delete_quietly(message)

    def drop_warning(self) -> None:
        '''
        Deletes the ping in the background once a click restarts the timer, so
        it never sits there out of date and the click's reply isn't delayed.
        '''

        message, self.warning = self.warning, None
        if message is not None:
            in_background(delete_quietly(message))

    async def goodbye(self) -> None:
        '''
        Ends the game because the bot is restarting, so nobody waits on a game
        that is about to be forgotten. Play Again starts it over.
        '''

        phase, self.phase = self.phase, 'over'
        games.pop(self.id, None)
        await self.clear_warning()
        what = 'lobby closed' if phase == 'lobby' else 'game ended'
        text = (f'{icon.update} Sabacc Droid is restarting for an update, so this {what}. '
                'Click **Play Again** to start over with the same settings.')
        if phase == 'lobby':
            if self.lobby_message is not None:
                try:
                    await self.lobby_message.edit(embed=self.styled(f'{self.name} Lobby', text), view=self.results_view(self.settings))
                except discord.HTTPException:
                    pass
            return
        await self.log_turn(f'{icon.update} The game stops here because Sabacc Droid is restarting.')
        content = ' '.join(player.user.mention for player in self.humans()) or None
        await self.post(content=content, embed=self.styled(f'{self.name}: Game Ended', text), view=self.results_view(self.settings))

    # The end ----------------------------------------------------------------

    async def finish(self, note: str = '') -> None:
        self.phase = 'ending'
        self.deadline = float('inf')
        await self.reveal(note)

    async def reveal(self, note: str = '') -> None:
        '''
        Shows everyone's hands and the winner, then forgets the game.
        '''

        self.phase = 'over'
        games.pop(self.id, None)
        await self.clear_warning()

        if not self.players:
            embed = self.styled(f'{self.name}: Game Over', 'Nobody won because everyone junked their hands.')
            return await self.post(embed=embed, view=self.results_view(self.settings))

        scored = sorted(((self.score(player), player) for player in self.players), key=lambda entry: entry[0][0])
        places = []  # tied hands share a place
        for index, ((key, _), _player) in enumerate(scored):
            places.append(places[-1] if index and key == scored[index - 1][0][0] else index + 1)
        winners = [player for place, (_, player) in zip(places, scored) if place == 1]
        if len(winners) == 1:
            headline = f'{icon.winner} {winners[0].user.mention} {self.headline(scored[0][0][1])}'
        else:
            headline = f'🤝 It\'s a tie between {" and ".join(player.user.mention for player in winners)}!'

        lines = []
        for place, ((_, hand_name), player) in zip(places, scored):
            lines.append(f'{medals.get(place, f"**{place}.**")} {player.user.mention}: {chips(self.labels(player))}'
                         f' · **{self.total(player)}** · {hand_name}')
        description = (note + '\n\n' if note else '') + headline + '\n\n**Final Hands**\n' + '\n'.join(lines)
        extra = self.result_note()
        if extra:
            description += '\n\n' + extra

        embed = self.styled(f'{self.name}: Game Over', description)
        embed.add_field(name='Target', value=self.target(), inline=True)
        embed.add_field(name='Rounds Played', value=str(self.round), inline=True)
        table = await asyncio.to_thread(cards.render_table, [(place, self.faces(player)) for place, (_, player) in zip(places, scored)])
        embed.set_image(url='attachment://table.png')
        content = ' '.join(player.user.mention for player in self.humans()) or None
        await self.post(content=content, embed=embed, file=cards.as_file(table, 'table.png'), view=self.results_view(self.settings))

    @classmethod
    def results_view(cls, settings: Settings, again: bool = True) -> Components:
        '''
        Play Again carries the settings in its id, so it works long after
        the game itself is forgotten.
        '''

        return Components(
            button(icon.again, 'Play Again', f'again:{cls.key}:{settings.encode()}', ButtonStyle.success, disabled=not again),
            cls.rules_button(),
        )


restarting = False  # set for good once the bot starts shutting down, so no new lobby opens
restarting_notice = 'Sabacc Droid is restarting for an update. Try again in a minute.'


async def goodbye_all(wait: float = 10) -> None:
    '''
    Ends every game in progress when the bot shuts down (a deploy restarts it),
    telling each table why.
    '''

    global restarting
    restarting = True
    if games:
        log.info('Ending %s before shutting down', plural(len(games), 'unfinished game'))

    async def one(current: Game) -> None:
        try:
            async with asyncio.timeout(wait):
                async with current.lock:
                    if games.get(current.id) is current:
                        await current.goodbye()
        except Exception:
            log.exception('Ending game %s for the restart failed', current.id)

    await asyncio.gather(*(one(current) for current in list(games.values())))


# Turn actions shared by Corellian Spike and Traditional Sabacc ------------------

class DrawGame(Game):
    '''
    Draw, replace, discard (when the lobby turns it on), stand, or junk.
    '''

    def deck_cards(self) -> list:
        raise NotImplementedError

    def miss(self, total: int) -> int:
        '''
        How far a total is from the target, for Lando.
        '''

        raise NotImplementedError

    def deal(self) -> None:
        self.deck = Deck(self.deck_cards)
        for player in self.players:
            player.hand = [self.deck.draw() for _ in range(self.settings.cards)]

    def label(self, card: Any) -> str:
        return signed(card.value)

    def labels(self, player: Player) -> list[str]:
        return [self.label(card) for card in player.hand]

    def turn_buttons(self, player: Player) -> list[discord.ui.Button]:
        items = [
            button(icon.draw, 'Draw Card', self.id_for('draw'), ButtonStyle.primary),
            button(icon.replace, 'Replace Card', self.id_for('replace')),
        ]
        if self.settings.discard:
            items.append(button(icon.discard, 'Discard Card', self.id_for('discard'), disabled=len(player.hand) < 2))
        items += [
            button(icon.stand, 'Stand', self.id_for('stand'), ButtonStyle.success),
            button(icon.junk, 'Junk', self.id_for('junk'), ButtonStyle.danger),
        ]
        return items

    def pick_buttons(self, player: Player, action: str) -> list[discord.ui.Button]:
        '''
        One button per card (Discord allows 24 next to Go Back).
        '''

        items = [discord.ui.Button(label=self.label(card), custom_id=self.id_for(action, str(index)), style=ButtonStyle.primary)
                 for index, card in enumerate(player.hand[:24])]
        items.append(button(icon.back, 'Go Back', self.id_for('back')))
        return items

    def picked(self, player: Player, choice: str) -> int | None:
        if choice.isdigit() and int(choice) < min(len(player.hand), 24):
            return int(choice)
        return None

    # Each move changes the hand and returns its game log line, for people and Lando alike.

    def draw_move(self, player: Player) -> str:
        player.hand.append(self.deck.draw())
        return f'{icon.draw} {player.user.mention} draws a card.'

    def swap_move(self, player: Player, index: int) -> str:
        old = player.hand[index]
        player.hand[index] = self.deck.draw()
        self.deck.discard(old)
        return f'{icon.replace} {player.user.mention} swaps out `{self.label(old)}` for a new card.'

    def drop_move(self, player: Player, index: int) -> str:
        old = player.hand.pop(index)
        self.deck.discard(old)
        return f'{icon.discard} {player.user.mention} discards `{self.label(old)}`.'

    async def act(self, it: Interaction, player: Player, action: str, choice: str) -> None:
        if action == 'draw':
            line = self.draw_move(player)
            await self.show_hand(it, player, 'You Drew a Card', f'You drew `{self.label(player.hand[-1])}`.')
            await self.next_turn(line)

        elif action == 'replace':
            await self.show_hand(it, player, 'Replace a Card', 'Choose the card to swap for a new one.', self.pick_buttons(player, 'swap'))

        elif action == 'swap':
            index = self.picked(player, choice)
            if index is None:
                return await notice(it, "That card isn't in your hand anymore.")
            old = player.hand[index]
            line = self.swap_move(player, index)
            await self.show_hand(it, player, 'You Replaced a Card', f'You swapped `{self.label(old)}` for `{self.label(player.hand[index])}`.')
            await self.next_turn(line)

        elif action == 'discard' and self.settings.discard:
            if len(player.hand) < 2:
                return await notice(it, "You can't discard your last card.")
            await self.show_hand(it, player, 'Discard a Card', 'Choose the card to discard.', self.pick_buttons(player, 'drop'))

        elif action == 'drop' and self.settings.discard:
            index = self.picked(player, choice)
            if index is None or len(player.hand) < 2:
                return await notice(it, "You can't discard that card.")
            old = player.hand[index]
            line = self.drop_move(player, index)
            await self.show_hand(it, player, 'You Discarded a Card', f'You discarded `{self.label(old)}`.')
            await self.next_turn(line)

        else:
            await notice(it, "That action isn't available.")

    def ai_move(self, player: Player) -> str:
        '''
        Lando picks the move that leaves him closest to the target on
        average. He reckons with a full deck, so he never peeks at the cards.
        '''

        values = [card.value for card in self.deck_cards()]
        total = sum(card.value for card in player.hand)

        def after_draw(base: int) -> float:
            return sum(self.miss(base + value) for value in values) / len(values)

        moves = [(self.miss(total), 'stand', 0), (after_draw(total), 'draw', 0)]
        for index, card in enumerate(player.hand[:24]):
            moves.append((after_draw(total - card.value), 'swap', index))
            if self.settings.discard and len(player.hand) > 1:
                moves.append((self.miss(total - card.value), 'drop', index))
        _, move, index = min(moves, key=lambda option: option[0])  # ties go to the earliest, so Lando prefers to stand
        if move == 'draw':
            return self.draw_move(player)
        if move == 'swap':
            return self.swap_move(player, index)
        if move == 'drop':
            return self.drop_move(player, index)
        return f'{icon.stand} {player.user.mention} stands.'
