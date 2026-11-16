# self_test.py
#
# `python sabacc_droid.py --self-test` checks everything that can be checked
# without Discord: every reply fits Discord's limits and follows the reply
# conventions in theme.py, every card image exists, every hand ranks the way
# the rules say, and hundreds of simulated games (with double clicks, old
# buttons, the wrong player clicking, junks, and timeouts) all finish and are
# forgotten. It prints one line per check and returns 0 if they all pass.

from __future__ import annotations

import asyncio
import dataclasses
import io
import itertools
import random
import re
import time
from pathlib import Path

import discord
from PIL import Image

import cards
import game
import theme
from corellian_spike import Card as SpikeCard, rank_spike_hand, spike_deck
from game import Player, Settings, games, variants
from help import chooser_message, comparison_embed, help_message
from kessel import Card as KesselCard, kessel_deck
from traditional import Card as TraditionalCard, traditional_deck

failures: list[str] = []
lando_turns: dict[str, int] = {}
icons = {value for name, value in vars(theme.icon).items() if not name.startswith('_')}
small_words = {'a', 'an', 'and', 'for', 'in', 'of', 'or', 'the', 'to'}


def check(ok: bool, what: str) -> None:
    if not ok:
        failures.append(what)


def report(name: str, before: int) -> None:
    new = failures[before:]
    print(('ok    ' if not new else 'FAIL  ') + name)
    for failure in new[:10]:
        print('        ' + failure)


# Checking replies -----------------------------------------------------------------

def check_embed(embed: discord.Embed, where: str) -> None:
    title = embed.title or ''
    check(any(title.startswith(mark + ' ') for mark in icons), f'{where}: title {title!r} does not start with an icon')
    check(len(title) <= 256, f'{where}: title too long')
    check(len(embed.description or '') <= 4096, f'{where}: description is {len(embed.description or "")} characters')
    check(len(embed.fields) <= 25, f'{where}: too many fields')
    for field in embed.fields:
        check(0 < len(field.name) <= 256 and 0 < len(field.value) <= 1024, f'{where}: field {field.name!r} is empty or too long')
    check(len(embed.footer.text or '') <= 2048, f'{where}: footer too long')
    check(len(embed) <= 6000, f'{where}: embed is {len(embed)} characters')
    text = (embed.description or '') + ''.join(field.value for field in embed.fields)
    check(not any(mark in text for mark in ('\u2014', '\u2019', '\u201c')), f'{where}: curly quotes or a long dash')


def is_card_button(label: str) -> bool:
    return not re.search('[A-Za-z]', label) or label.startswith('Keep ')


def check_view(view: discord.ui.View | None, where: str) -> None:
    if view is None or view is discord.utils.MISSING:
        return
    check(view.is_finished(), f'{where}: discord.py would keep this view in memory')
    items = view.children
    check(len(items) <= 25, f'{where}: {len(items)} components')
    ids = [item.custom_id for item in items if getattr(item, 'url', None) is None]
    check(len(ids) == len(set(ids)), f'{where}: repeated custom ids {ids}')
    for item in items:
        label = item.label or ''
        check(len(label) <= 80, f'{where}: label {label!r} too long')
        if item.url is None:
            check(item.custom_id is not None and len(item.custom_id) <= 100, f'{where}: custom id {item.custom_id!r}')
        if is_card_button(label):
            continue
        words = [word for word in re.findall(r"[A-Za-z][A-Za-z']*", label)]
        title_case = all(word[0].isupper() or (index and word in small_words) for index, word in enumerate(words))
        check(item.emoji is not None and title_case, f'{where}: button {label!r} needs an icon and a Title Case label')


def check_png(data: bytes, where: str, name: str = 'cards.png') -> None:
    try:
        with Image.open(io.BytesIO(data)) as image:
            check(image.format == 'PNG', f'{where}: {name} is not a PNG')
            check(image.height == cards.height if name == 'cards.png' else max(image.size) <= 4000, f'{where}: {name} is {image.size}')
            check(len(data) < 1_000_000, f'{where}: {name} is {len(data)} bytes')
    except Exception as error:
        check(False, f'{where}: unreadable image ({error})')


def check_message(payload: dict, where: str) -> None:
    content = payload.get('content')
    check(content is None or len(content) <= 2000, f'{where}: content too long')
    if payload.get('ephemeral') and content:
        check(content.startswith(theme.icon.error + ' ') and content.rstrip('*`').endswith(('.', '!')),
              f'{where}: notice {content!r} is not "❌ <sentence>"')
    embed = payload.get('embed')
    if embed is not None:
        check_embed(embed, where)
    check_view(payload.get('view'), where)
    file = payload.get('file')
    files = [file] if file is not None else [f for f in payload.get('attachments') or [] if isinstance(f, discord.File)]
    for attachment in files:
        attachment.fp.seek(0)
        check_png(attachment.fp.read(), where, attachment.filename)
        attachment.fp.seek(0)
        if embed is not None:
            check(embed.image.url == f'attachment://{attachment.filename}', f'{where}: image not shown in the embed')


# Fake Discord ---------------------------------------------------------------

message_ids = itertools.count(1)


class FakeUser:
    def __init__(self, user_id: int) -> None:
        self.id = user_id
        self.mention = f'<@{user_id}>'
        self.display_name = f'Player {user_id}'


class FakeMessage:
    def __init__(self, channel: FakeChannel, payload: dict) -> None:
        self.id = next(message_ids)
        self.channel = channel
        self.payload = payload
        self.deleted = False

    @property
    def content(self) -> str | None:
        return self.payload.get('content')

    async def edit(self, **payload) -> None:
        check(not self.deleted, 'edited a deleted message')
        check_message(payload, 'message edit')
        self.payload.update(payload)

    async def delete(self) -> None:
        check(not self.deleted, 'deleted a message twice')
        self.deleted = True

    def buttons(self) -> list[discord.ui.Button]:
        view = self.payload.get('view')
        if view is None or view is discord.utils.MISSING:
            return []
        return [item for item in view.children if item.url is None and not item.disabled]


class FakeChannel:
    def __init__(self, refuse: bool = False) -> None:
        self.messages: list[FakeMessage] = []
        self.refuse = refuse

    async def send(self, content=None, **payload) -> FakeMessage:
        if self.refuse:
            raise discord.Forbidden(type('Response', (), {'status': 403, 'reason': 'Forbidden'})(), 'Missing Access')
        payload['content'] = content
        check_message(payload, 'channel message')
        message = FakeMessage(self, payload)
        self.messages.append(message)
        return message

    def get_partial_message(self, message_id: int) -> FakeMessage:
        return next(message for message in self.messages if message.id == message_id)


class FakeResponse:
    def __init__(self, it: FakeInteraction) -> None:
        self.it = it
        self.done = False

    def is_done(self) -> bool:
        return self.done

    def respond(self) -> None:
        check(not self.done, f'{self.it.custom_id}: answered twice')
        self.done = True
        if self.it.lost:  # Discord dropped the reply (a network blip, or the 3 second window passed)
            raise discord.NotFound(type('Response', (), {'status': 404, 'reason': 'Not Found'})(), 'Unknown interaction')

    async def send_message(self, content=None, *, ephemeral=False, **payload) -> None:
        self.respond()
        payload.update(content=content, ephemeral=ephemeral)
        check_message(payload, f'reply to {self.it.custom_id or "a command"}')
        message = FakeMessage(self.it.channel, payload)
        if not ephemeral:
            self.it.channel.messages.append(message)
        self.it.original = message
        self.it.replies.append(payload)

    async def edit_message(self, **payload) -> None:
        self.respond()
        check_message(payload, f'edit by {self.it.custom_id}')
        self.it.message.payload.update(payload)
        self.it.replies.append(payload)


class FakeFollowup:
    def __init__(self, it: FakeInteraction) -> None:
        self.it = it

    async def send(self, content=None, *, ephemeral=False, **payload) -> None:
        payload.update(content=content, ephemeral=ephemeral)
        check_message(payload, f'follow-up to {self.it.custom_id}')
        self.it.replies.append(payload)


class FakeInteraction:
    type = discord.InteractionType.component

    def __init__(self, user: FakeUser, channel: FakeChannel, custom_id: str = '', message: FakeMessage | None = None,
                 lost: bool = False) -> None:
        self.lost = lost
        self.user = user
        self.channel = channel
        self.custom_id = custom_id
        self.data = {'custom_id': custom_id}
        self.message = message
        self.response = FakeResponse(self)
        self.followup = FakeFollowup(self)
        self.original: FakeMessage | None = None
        self.replies: list[dict] = []

    async def original_response(self) -> FakeMessage:
        return self.original

    def notices(self) -> list[str]:
        return [reply['content'] for reply in self.replies if reply.get('ephemeral') and reply.get('content')]


exercised: set[str] = set()


async def click(message: FakeMessage, custom_id: str, user: FakeUser, lost: bool = False) -> FakeInteraction:
    from sabacc_droid import route

    it = FakeInteraction(user, message.channel, custom_id, message, lost)
    await route(it, custom_id)
    check(it.response.is_done(), f'{custom_id}: never answered')
    if not it.notices():
        parts = custom_id.split(':')
        exercised.add(parts[3] if parts[0] == 'g' else parts[0])
    return it


def button_id(message: FakeMessage, action: str) -> str | None:
    for item in message.buttons():
        if item.custom_id.split(':')[3:4] == [action] or item.custom_id == action:
            return item.custom_id
    return None


async def expire(current: game.Game) -> None:
    current.deadline = 0
    async with current.lock:
        await current.expire()


# Simulated games --------------------------------------------------------------

async def play(rng: random.Random, variant: type[game.Game], settings: Settings, players: int) -> None:
    from sabacc_droid import open_lobby

    channel = FakeChannel()
    users = [FakeUser(1000 + index) for index in range(players)]
    stranger = FakeUser(9999)

    it = FakeInteraction(users[0], channel)
    await open_lobby(it, variant, settings)
    lobby = it.original
    current = next(g for g in games.values() if g.lobby_message is lobby)

    for user in users:
        await click(lobby, button_id(lobby, 'join'), user)
    if rng.random() < 0.3:
        repeat = await click(lobby, f'g:{current.id}:0:join', users[0])
        check(repeat.notices() == [f"{theme.icon.error} You're already in this game."], 'joining twice was allowed')
    if variant.has_discard and rng.random() < 0.5:
        await click(lobby, button_id(lobby, 'discarding'), stranger)
    if rng.random() < 0.3:
        await click(lobby, button_id(lobby, 'leave'), users[0])
        gone = await click(lobby, f'g:{current.id}:0:leave', users[0])
        check(gone.notices() == [f"{theme.icon.error} You're not in this game."], 'left a game twice')
        await click(lobby, button_id(lobby, 'join'), users[0])
    refused = await click(lobby, button_id(lobby, 'start'), stranger)
    check(bool(refused.notices()), 'a stranger started the game')
    start = button_id(lobby, 'start')
    await click(lobby, start, users[-1])
    solo = len(current.players) == 2 and any(player.is_ai for player in current.players)
    lando_seated = solo
    check(current.phase != 'lobby', 'the game did not start')
    late = await click(lobby, start, users[0])
    check(bool(late.notices()) or current.phase == 'over', 'the game started twice')

    hands: list[FakeMessage] = []
    for _ in range(2000):
        if games.get(current.id) is not current:
            break
        if current.phase == 'ending':
            for message in list(channel.messages):
                for item in message.buttons():
                    if ':psi:' in item.custom_id:
                        owner = next(user for user in users if user.mention == message.payload.get('content'))
                        if rng.random() < 0.1:
                            await click(message, item.custom_id, stranger)
                        other = next((user for user in users if user is not owner), None)
                        if other is not None and rng.random() < 0.3:
                            before = dict(current.rolls.get(owner.id, {}))
                            taken = await click(message, item.custom_id, other)
                            check(taken.notices() == [f"{theme.icon.error} These aren't your Impostor dice."]
                                  and current.rolls.get(owner.id, {}) == before, "another player picked someone else's Impostor dice")
                        await click(message, item.custom_id, owner)
                        break
            if current.phase == 'ending' and rng.random() < 0.3:
                await expire(current)
            continue

        seat = current.players[current.current]
        roll = rng.random()
        if roll < 0.04:
            await expire(current)
            continue
        announcement = current.turn_message
        if roll < 0.08:
            wrong = await click(announcement, button_id(announcement, 'play'), stranger)
            check(wrong.notices() == [f"{theme.icon.error} It's not your turn."], 'a stranger played a turn')
        opened = await click(announcement, button_id(announcement, 'play'), seat.user)
        hands.append(opened.original)
        fields = [field.name for field in opened.original.payload['embed'].fields]
        check('Ranks As' in fields, f'{variant.name}: a hand without Ranks As')
        if rng.random() < 0.15 and len(hands) > 2:
            old = hands[-3]
            for item in old.buttons()[:1]:
                stale = await click(old, item.custom_id, seat.user)
                check(stale.notices() in ([f'{theme.icon.error} That turn is already over.'], [f'{theme.icon.error} This game has ended. Start a new one with `/sabacc`.']),
                      f'an old button did something: {stale.notices()}')

        turn = current.turn
        for _ in range(12):
            if current.turn != turn or games.get(current.id) is not current:
                break
            options = [item.custom_id for item in opened.original.buttons()]
            if not options:
                break
            if variant.key == 'coruscant_shift' and rng.random() < 0.4:
                options = [option for option in options if ':confirm' in option] or options
            if variant.key == 'traditional' and current.round > 6:
                options = [option for option in options if ':alderaan' in option] or options
            if rng.random() < 0.85:
                options = [option for option in options if ':junk' not in option] or options
            choice = rng.choice(options)
            if rng.random() < 0.1:
                double = await click(opened.original, choice, seat.user)
                check(double.response.is_done(), 'double click went unanswered')
            await click(opened.original, choice, seat.user)
        if current.turn == turn and games.get(current.id) is current:
            await expire(current)

    check(games.get(current.id) is not current, f'{variant.name} with {players} players never ended')
    results = [message for message in channel.messages if (message.payload.get('embed') and 'Game Over' in (message.payload['embed'].title or ''))]
    check(len(results) == 1, f'{variant.name}: {len(results)} results messages')
    if solo and lando_seated:
        moves = [message for message in channel.messages if game.Lando.mention in (message.payload['embed'].description or '')
                 and 'Game Over' not in (message.payload['embed'].title or '')]
        lando_turns[variant.key] = lando_turns.get(variant.key, 0) + len(moves)
    if results:
        description = results[0].payload['embed'].description
        check('🥇' in description and results[0].payload['embed'].image.url == 'attachment://table.png',
              f'{variant.name}: results without medals or the table picture')
        again = button_id(results[0], f'again:{variant.key}:{current.settings.encode()}')
        check(again is not None, 'results have no Play Again button')
        replay = await click(results[0], again, users[0])
        check(replay.original is not None, 'Play Again opened no lobby')
        new = next(g for g in games.values() if g.lobby_message is replay.original)
        check(len(new.players) == 1 and new.settings == current.settings, 'Play Again lost the players or settings')
        pinged = replay.original.payload.get('content') or ''
        others = [user for user in users[1:] if user.mention in (results[0].payload.get('content') or '')]
        check(all(user.mention in pinged for user in others) and users[0].mention not in pinged.split(':')[0],
              f'the rematch should ping the other players: {pinged!r}')
        await expire(new)


# Checks -----------------------------------------------------------------------

def check_ranks() -> None:
    def spike(*values: int) -> str:
        return rank_spike_hand(list(values))[1]

    expected = {
        (0, 0): 'Pure Sabacc', (0, 0, 3, -3): 'Sarlacc Sabacc', (0, 10, 10, -10, -10): 'Full Sabacc',
        (0, 5, 5, -5, -5): 'Fleet', (0, 5, -5, 3, -3): 'Twin Sun', (0, 5, -5): 'Yee-Haa', (0, 4, 4, -8): 'Kessel Run',
        (5, 5, -5, -5): 'Squadron', (4, 4, 4, -3, -9): "Bantha's Wild", (9, -9, 4, -4): 'Rule of Two',
        (5, 5, -10): 'Sabacc Pair', (1, 2, -3): 'Sabacc', (1,): 'Nulrhek',
    }
    for hand, name in expected.items():
        check(spike(*hand) == name, f'Corellian Spike {hand} is {spike(*hand)}, not {name}')
    ranked = [rank_spike_hand(list(hand))[0] for hand in expected]
    check(ranked == sorted(ranked), 'Corellian Spike hands are not ranked in rules order')
    check(rank_spike_hand([1])[0] < rank_spike_hand([-1])[0], '+1 should beat -1')
    check(rank_spike_hand([2, -2])[0] < rank_spike_hand([5, -5])[0], 'a pair of 2s should beat a pair of 5s')
    check(rank_spike_hand([4, -6])[0] < rank_spike_hand([-3])[0], '-2 should beat -3')

    kessel = variants['kessel'](Settings(3, 2), None)
    games.pop(kessel.id)
    kessel.phase = 'over'

    def kessel_hand(sand: KesselCard, blood: KesselCard, chosen: dict | None = None) -> tuple:
        player = Player(FakeUser(1))
        player.hand, player.chosen = [sand, blood], chosen or {}
        return kessel.score(player)

    sylop, impostor = KesselCard(1, kind='sylop'), KesselCard(1, kind='impostor')
    blood_sylop, blood_impostor = KesselCard(-1, kind='sylop'), KesselCard(-1, kind='impostor')
    kessel_expected = [
        ((sylop, blood_sylop), 'Pure Sabacc'), ((KesselCard(1, 1), KesselCard(-1, 1)), 'Prime Sabacc'),
        ((KesselCard(1, 2), KesselCard(-1, 2)), 'Standard Sabacc'), ((KesselCard(1, 5), KesselCard(-1, 5)), 'Standard Sabacc'),
        ((KesselCard(1, 6), KesselCard(-1, 6)), 'Cheap Sabacc'), ((KesselCard(1, 3), KesselCard(-1, 2)), 'Nulrhek'),
        ((KesselCard(1, 1), KesselCard(-1, 3)), 'Nulrhek'),
    ]
    keys = []
    for (sand, blood), name in kessel_expected:
        key, got = kessel_hand(sand, blood)
        keys.append(key)
        check(got == name, f'Kessel {sand.label()} {blood.label()} is {got}, not {name}')
    check(keys == sorted(keys), 'Kessel hands are not ranked in rules order')
    check(kessel_hand(sylop, KesselCard(-1, 4))[1] == 'Standard Sabacc', 'a Sylop should copy the other card')
    check(kessel_hand(sylop, KesselCard(-1, 1))[1] == 'Prime Sabacc', 'a Sylop and -1 should be Prime Sabacc')
    check(kessel_hand(impostor, KesselCard(-1, 3), {1: 3})[1] == 'Standard Sabacc', 'an Impostor should use its chosen value')
    check(kessel_hand(sylop, blood_impostor, {-1: -2})[1] == 'Standard Sabacc', 'a Sylop should copy an Impostor')

    traditional = variants['traditional'](Settings(0, 2), None)
    games.pop(traditional.id)

    def traditional_hand(*values: int) -> str:
        player = Player(FakeUser(1))
        player.hand = [TraditionalCard(value, 'special' if value <= 0 else 'coin') for value in values]
        return traditional.score(player)

    for values, name in [((0, 2, 3), "Idiot's Array"), ((15, 8), 'Natural Sabacc'), ((-15, -8), 'Natural Sabacc'),
                         ((-2, -2), 'Fairy Empress'), ((15, 7), 'Nulrhek')]:
        check(traditional_hand(*values)[1] == name, f'Traditional {values} should be {name}')
    check(traditional_hand(0, 2, 3)[0] < traditional_hand(15, 8)[0] < traditional_hand(-2, -2)[0] < traditional_hand(15, 7)[0],
          "Traditional ranks should be Idiot's Array, Natural Sabacc, Fairy Empress, Nulrhek")
    check(traditional_hand(-15, -7)[0] < traditional_hand(15, 7)[0], '-22 should beat +22')

    coruscant = variants['coruscant_shift'](Settings(2, 5), None)
    games.pop(coruscant.id)
    coruscant.target_number, coruscant.target_suit, coruscant.phase = 5, 'circle', 'over'

    def coruscant_hand(*cards: SpikeCard) -> tuple:
        player = Player(FakeUser(1))
        player.hand = list(cards)
        return coruscant.score(player)

    pure = coruscant_hand(SpikeCard(0, 'sylop'), SpikeCard(0, 'sylop'))
    on_target = coruscant_hand(SpikeCard(5, 'square'))
    suited = coruscant_hand(SpikeCard(4, 'circle'), SpikeCard(1, 'circle'))
    check(pure[1] == 'Pure Sabacc' and pure[0] < suited[0] < on_target[0], 'Coruscant Shift should rank Pure Sabacc, then suit matches on target')
    check(coruscant_hand(SpikeCard(6, 'square'))[0] < coruscant_hand(SpikeCard(4, 'square'))[0], 'at the same distance, the higher total should win')


def check_lando() -> None:
    lando = Player(game.Lando())

    corellian = variants['corellian_spike'](Settings(3, 2, True), None)
    games.pop(corellian.id)
    corellian.deck = game.Deck(spike_deck)
    lando.hand = [SpikeCard(5, 'circle'), SpikeCard(-5, 'square')]
    check('stands' in corellian.ai_move(lando), 'Lando should stand on 0 in Corellian Spike')
    lando.hand = [SpikeCard(10, 'circle'), SpikeCard(9, 'square')]
    check('stands' not in corellian.ai_move(lando), 'Lando should not stand on +19')
    lando.hand = [SpikeCard(4, 'circle'), SpikeCard(-1, 'square'), SpikeCard(-3, 'triangle'), SpikeCard(7, 'circle')]
    check('discards `+7`' in corellian.ai_move(lando), 'Lando should discard the +7 that keeps him off 0')

    traditional = variants['traditional'](Settings(0, 2), None)
    games.pop(traditional.id)
    traditional.deck, traditional.caller = game.Deck(traditional_deck), None
    lando.hand = [TraditionalCard(15, 'coin'), TraditionalCard(8, 'flask')]
    check('calls Alderaan' in traditional.ai_move(lando), 'Lando should call Alderaan on 23')
    traditional.caller, traditional.round = None, 1
    lando.hand = [TraditionalCard(3, 'coin'), TraditionalCard(2, 'staff')]
    line = traditional.ai_move(lando)
    check('calls' not in line and 'stands' not in line, f'Lando should play on with 5 in round 1, not {line!r}')
    traditional.caller, traditional.round = None, 5
    check('calls Alderaan' in traditional.ai_move(lando), 'Lando should call Alderaan by round 5')

    kessel = variants['kessel'](Settings(3, 2), None)
    games.pop(kessel.id)
    kessel.decks = {1: game.Deck(lambda: kessel_deck(1)), -1: game.Deck(lambda: kessel_deck(-1))}
    lando.hand, lando.chosen = [KesselCard(1, 3), KesselCard(-1, 3)], {}
    check('stands' in kessel.ai_move(lando), 'Lando should stand on +3 -3 in Kessel')
    lando.hand = [KesselCard(1, 6), KesselCard(-1, 1)]
    check('draws from the' in kessel.ai_move(lando), 'Lando should draw on +6 -1 in Kessel')

    coruscant = variants['coruscant_shift'](Settings(2, 5), None)
    games.pop(coruscant.id)
    coruscant.deck, coruscant.target_number, coruscant.target_suit = game.Deck(spike_deck), 5, 'circle'
    lando.hand, lando.locked = [SpikeCard(5, 'circle'), SpikeCard(10, 'square'), SpikeCard(-7, 'triangle')], 0
    coruscant.ai_move(lando)
    check(lando.hand == [SpikeCard(5, 'circle')], f'Lando should keep only the +5 on a +5 target, not {lando.hand}')


async def check_solo_games_end() -> None:
    '''
    A player who only ever stands still sees every game end, because
    Lando keeps playing (in Traditional, he calls Alderaan).
    '''

    from sabacc_droid import open_lobby

    for variant in variants.values():
        channel = FakeChannel()
        user = FakeUser(1)
        it = FakeInteraction(user, channel)
        await open_lobby(it, variant, dataclasses.replace(variant.defaults))
        lobby = it.original
        current = next(g for g in games.values() if g.lobby_message is lobby)
        await click(lobby, button_id(lobby, 'join'), user)
        await click(lobby, button_id(lobby, 'start'), user)
        for _ in range(40):
            if games.get(current.id) is not current:
                break
            if current.phase == 'ending':
                await expire(current)
                continue
            announcement = current.turn_message
            opened = await click(announcement, button_id(announcement, 'play'), user)
            await click(opened.original, button_id(opened.original, 'stand') or button_id(opened.original, 'confirm'), user)
        check(current.id not in games, f'a solo {variant.name} game where the player always stands never ended')


async def start_game(variant: type[game.Game], settings: Settings, users: list[FakeUser]) -> tuple[game.Game, FakeChannel]:
    from sabacc_droid import open_lobby

    channel = FakeChannel()
    it = FakeInteraction(users[0], channel)
    await open_lobby(it, variant, settings)
    lobby = it.original
    current = next(g for g in games.values() if g.lobby_message is lobby)
    for user in users:
        await click(lobby, button_id(lobby, 'join'), user)
    await click(lobby, button_id(lobby, 'start'), users[0])
    return current, channel


async def check_lost_replies() -> None:
    '''
    If Discord drops the reply to a move, the move still counts once and
    the game moves on.
    '''

    users = [FakeUser(1), FakeUser(2)]
    current, channel = await start_game(variants['corellian_spike'], Settings(3, 2), users)
    seat = current.players[current.current]
    opened = await click(current.turn_message, button_id(current.turn_message, 'play'), seat.user)
    turn, cards_before = current.turn, len(seat.hand)
    await click(opened.original, button_id(opened.original, 'draw'), seat.user, lost=True)
    check(current.turn == turn + 1 and len(seat.hand) == cards_before + 1, 'a lost reply left the turn open')
    again = await click(opened.original, button_id(opened.original, 'draw'), seat.user)
    check(again.notices() == [f'{theme.icon.error} That turn is already over.'] and len(seat.hand) == cards_before + 1,
          'a second click after a lost reply drew again')
    await expire(current)
    await expire(current)


async def check_round_count() -> None:
    '''
    When the first seat calls Alderaan, the final turns don't count as a new round.
    '''

    users = [FakeUser(1), FakeUser(2)]
    current, channel = await start_game(variants['traditional'], Settings(0, 2), users)
    for action in ('alderaan', 'stand'):
        seat = current.players[current.current]
        opened = await click(current.turn_message, button_id(current.turn_message, 'play'), seat.user)
        await click(opened.original, button_id(opened.original, action), seat.user)
    results = channel.messages[-1].payload['embed']
    played = next((field.value for field in results.fields if field.name == 'Rounds Played'), None)
    check(current.id not in games and played == '1', f'Rounds Played should be 1, not {played}')


async def check_dice_owners() -> None:
    '''
    Only the owner of Impostor dice can pick from them.
    '''

    from kessel import Card

    users = [FakeUser(1), FakeUser(2)]
    current, channel = await start_game(variants['kessel'], Settings(1, 2), users)
    for player in current.players:
        player.hand = [Card(1, kind='impostor'), Card(-1, 3)]
    current.turn += 1
    await current.finish()
    first, second = (next(m for m in channel.messages if m.payload.get('content') == user.mention
                          and any(':psi:' in item.custom_id for item in m.buttons())) for user in users)
    taken = await click(first, first.buttons()[0].custom_id, users[1])
    check(taken.notices() == [f"{theme.icon.error} These aren't your Impostor dice."] and 1 in current.rolls.get(1, {}),
          "another player picked someone else's Impostor dice")
    await click(first, first.buttons()[0].custom_id, users[0])
    await click(second, second.buttons()[1].custom_id, users[1])
    check(current.id not in games and 'Game Over' in channel.messages[-1].payload['embed'].title, 'the game should end once both picked')


async def check_warnings() -> None:
    '''
    A minute before time runs out, the player is pinged once, and the ping
    is deleted when the turn ends.
    '''

    from kessel import Card

    users = [FakeUser(1), FakeUser(2)]
    current, channel = await start_game(variants['corellian_spike'], Settings(3, 2), users)
    seat = current.players[current.current]
    async with current.lock:
        await current.warn()
    ping = channel.messages[-1]
    check(ping.content == f'{theme.icon.timeout} {seat.user.mention}, you have 1 minute left to play your turn.',
          f'the warning reads {ping.content!r}')
    check(current.warned and current.warning is ping, 'the game should remember it warned')
    async with current.lock:
        await current.warn()
    check(ping.deleted and current.warning is channel.messages[-1], 'a second warning should replace the first')
    ping = channel.messages[-1]
    opened = await click(current.turn_message, button_id(current.turn_message, 'play'), seat.user)
    await asyncio.sleep(0)
    check(not current.warned and ping.deleted and current.warning is None,
          'a click should restart the timer and delete the ping, which is out of date')
    async with current.lock:
        await current.warn()
    ping = channel.messages[-1]
    await click(opened.original, button_id(opened.original, 'stand'), seat.user)
    check(ping.deleted and current.warning is None, 'the warning should be deleted once the turn ends')

    # The sweep looks again once it holds a game's lock, because a click may
    # have restarted the timer while it waited.
    from sabacc_droid import sweep_once

    posted = len(channel.messages)
    current.deadline = time.monotonic() + 30
    await current.lock.acquire()
    sweeping = asyncio.ensure_future(sweep_once())
    await asyncio.sleep(0)
    current.start_timer(game.turn_time)
    current.lock.release()
    await sweeping
    check(len(channel.messages) == posted and not current.warned, 'the sweep warned a player whose timer had just restarted')
    current.deadline = time.monotonic() + 30
    await sweep_once()
    await sweep_once()
    check(len(channel.messages) == posted + 1 and current.warned, 'the sweep should warn once with a minute left')
    await expire(current)
    await expire(current)

    current, channel = await start_game(variants['kessel'], Settings(1, 2), users)
    for player in current.players:
        player.hand = [Card(1, kind='impostor'), Card(-1, 3)]
    current.turn += 1
    await current.finish()
    async with current.lock:
        await current.warn()
    ping = channel.messages[-1]
    seats = ' '.join(player.user.mention for player in current.players)  # seats are shuffled at the start
    check(ping.content == f'{theme.icon.timeout} {seats}, you have 1 minute left to choose your Impostor values.',
          f'the Impostor warning reads {ping.content!r}')
    await expire(current)
    check(ping.deleted and current.id not in games, 'the Impostor warning should be deleted at the reveal')


async def check_restart_goodbye() -> None:
    '''
    When the bot shuts down, every lobby and game says why it ended and
    offers Play Again with the same settings.
    '''

    from sabacc_droid import open_lobby

    users = [FakeUser(1), FakeUser(2)]
    current, channel = await start_game(variants['traditional'], Settings(0, 3, True), users)
    seats = ' '.join(player.user.mention for player in current.players)  # seats are shuffled at the start
    turn = current.turn_message
    async with current.lock:
        await current.warn()
    ping = channel.messages[-1]
    it = FakeInteraction(users[0], FakeChannel())
    await open_lobby(it, variants['kessel'], Settings(5, 2))
    lobby = it.original

    await game.goodbye_all()
    check(not games, 'every game should be forgotten at shutdown')
    ended = channel.messages[-1]
    check(ended.content == seats and 'Game Ended' in ended.payload['embed'].title
          and 'restarting' in ended.payload['embed'].description, 'the table should hear the game ended for a restart')
    check(button_id(ended, 'again:traditional:0.3.1') == 'again:traditional:0.3.1', 'Play Again should keep the settings')
    check(not turn.buttons() and theme.icon.update in turn.payload['embed'].description, 'the last turn should become a log line')
    check(ping.deleted, 'a pending warning should be deleted at shutdown')
    check('restarting' in lobby.payload['embed'].description and button_id(lobby, 'again:kessel:5.2.0') is not None,
          'a lobby should close for the restart with Play Again')
    refused = await click(ended, 'again:traditional:0.3.1', users[1])
    check(refused.notices() == [f'{theme.icon.error} {game.restarting_notice}'] and not games
          and button_id(ended, 'again:traditional:0.3.1') is not None,
          'Play Again during a restart should say so, open nothing, and stay clickable')

    game.restarting = False  # the bot came back up
    rematch = await click(ended, 'again:traditional:0.3.1', users[1])
    check(rematch.original is not None and rematch.original.content and '<@1>' in rematch.original.content,
          'Play Again after a restart should ping the other players')
    for leftover in list(games.values()):
        await expire(leftover)


def check_decks() -> None:
    spike = spike_deck()
    check(len(spike) == 62 and sum(card.value == 0 for card in spike) == 2, 'the spike deck should have 62 cards and 2 Sylops')
    sand = kessel_deck(1)
    check(len(sand) == 22 and sum(card.kind == 'sylop' for card in sand) == 1 and sum(card.kind == 'impostor' for card in sand) == 3,
          'each Kessel deck should have 22 cards, 3 Impostors, and 1 Sylop')
    deck = traditional_deck()
    check(len(deck) == 76, 'the Traditional deck should have 76 cards')
    paths = {card.face() for card in spike + sand + kessel_deck(-1) + deck}
    paths |= {'corellian_spike/card.png', 'kessel/+card.png', 'kessel/-card.png', 'traditional/card.png'}
    for path in sorted(paths):
        check((cards.folder / path).is_file(), f'missing card image {path}')
    for variant in variants.values():
        check((cards.folder / variant.thumbnail.removeprefix(theme.images)).is_file(), f'missing thumbnail for {variant.name}')
    check((cards.folder / theme.logo.removeprefix(theme.images)).is_file(), 'missing logo')

    pile = game.Deck(lambda: [1, 2, 3])
    drawn = [pile.draw() for _ in range(3)]
    for card in drawn:
        pile.discard(card)
    check(sorted(pile.draw() for _ in range(3)) == [1, 2, 3], 'the discard pile should be reshuffled into an empty deck')
    check(pile.draw() in (1, 2, 3), 'an empty deck and discard pile should open a fresh deck')


def check_images() -> None:
    for path in sorted(cards.folder.rglob('*.png')):
        with Image.open(path) as image:
            check(image.height <= cards.height, f'{path.relative_to(cards.folder)} is {image.height} pixels tall')
    start = time.perf_counter()
    png = cards.render([card.face() for card in traditional_deck()[:10]])
    elapsed = time.perf_counter() - start
    check(elapsed < 1, f'drawing 10 cards took {elapsed:.2f} s')
    check(len(png) < 400_000, f'10 cards came out at {len(png)} bytes')
    check_png(png, '10 cards')

    dice = cards.render_dice([('gold', value) for value in (-10, 10, -5, 5, 0)] + [('silver', suit) for suit in ('circle', 'triangle', 'square')]
                             + [('sand', pips) for pips in range(1, 7)] + [('blood', pips) for pips in range(1, 7)])
    check_png(dice, 'every die face', 'dice.png')
    start = time.perf_counter()
    table = cards.render_table([(place, [card.face() for card in traditional_deck()[place:place + 10]]) for place in range(1, 10)])
    elapsed = time.perf_counter() - start
    check(elapsed < 2, f'a full table of 9 hands took {elapsed:.2f} s')
    check_png(table, 'a full table of 9 hands', 'table.png')


async def check_menus() -> None:
    for name, (embed, view) in {'/sabacc': chooser_message(), '/help': help_message()}.items():
        check_embed(embed, name)
        check_view(view, name)

    # /help ends the same way as Aurebesh Droid's (see theme.py).
    embed, view = help_message()
    ending = [field.name for field in embed.fields][-3:]
    check(ending == ['🖼️ Card Art', '🌌 More Star Wars', '🛠️ Made By'], f'/help ends with {ending}')
    check(embed.footer.text == theme.disclaimer, '/help should end with the shared disclaimer')
    check(theme.star_wars_apps in embed.fields[-2].value and theme.creator in embed.fields[-1].value, '/help should share the apps and credit')
    links = [item.label for item in view.children if item.url]
    check(links == ['Add Sabacc Droid', 'Datapad App', 'GitHub'], f'/help links are {links}')
    check_embed(comparison_embed(), 'comparison')
    for variant in variants.values():
        check_embed(variant.rules_embed(), f'{variant.name} rules')
        check_view(variant.results_view(variant.defaults), f'{variant.name} results')


async def check_router() -> None:
    from sabacc_droid import route

    channel = FakeChannel()
    user = FakeUser(1)
    replies = {}
    for custom_id in ['', 'g:', 'g:nope:1:play', 'g:nope', 'again:kessel:99.99.1', 'again:nope:1.1.1', 'again:kessel:x',
                      'rules:nope', 'start:nope', 'x' * 100, '0123456789abcdef0123456789abcdef', 'help', 'rules:compare',
                      'start:kessel', 'start:random', 'again:corellian_spike:3.2.1']:
        it = FakeInteraction(user, channel, custom_id, FakeMessage(channel, {}))
        await route(it, custom_id)
        check(it.response.is_done(), f'{custom_id!r} went unanswered')
        replies[custom_id] = it
    clamped = next((g for g in games.values() if g.lobby_message is replies['again:kessel:99.99.1'].original), None)
    check(clamped is not None and clamped.settings.rounds == 10 and len(clamped.players) == 1,
          'Play Again with 99 rounds should open a 10-round lobby with the clicker in it')
    for leftover in list(games.values()):
        await expire(leftover)


async def check_refused_channel() -> None:
    from sabacc_droid import open_lobby

    channel = FakeChannel()
    user = FakeUser(1)
    it = FakeInteraction(user, channel)
    await open_lobby(it, variants['corellian_spike'], Settings(3, 2))
    lobby = it.original
    current = next(g for g in games.values() if g.lobby_message is lobby)
    await click(lobby, button_id(lobby, 'join'), user)
    channel.refuse = True
    started = await click(lobby, button_id(lobby, 'start'), user)
    check(current.id not in games, 'a game in a channel the bot cannot post in should close')
    check(any("can't post" in text for text in started.notices()), 'the player should hear why the game closed')


async def check_lobby_timeout() -> None:
    from sabacc_droid import open_lobby

    channel = FakeChannel()
    it = FakeInteraction(FakeUser(1), channel)
    await open_lobby(it, variants['kessel'], Settings(3, 2))
    current = next(g for g in games.values() if g.lobby_message is it.original)
    await expire(current)
    check(current.id not in games and theme.icon.timeout in it.original.payload['embed'].description, 'an old lobby should close')


async def run_games() -> int:
    rng = random.Random(23)
    played = 0
    real_render = cards.render
    for index in range(60):
        for variant in variants.values():
            if index >= 6:
                cards.render = fake_render  # the first rounds draw real images; the rest only check the paths
            settings = variant.random_settings()
            await play(rng, variant, settings, rng.choice([1, 1, 2, 2, 3, 4, 8]))
            played += 1
    cards.render = real_render
    return played


blank = io.BytesIO()
Image.new('RGBA', (1, cards.height)).save(blank, 'PNG')


def fake_render(paths: list[str]) -> bytes:
    for path in paths:
        check((cards.folder / path).is_file(), f'missing card image {path}')
    return blank.getvalue()


async def self_test() -> int:
    tests = [
        ('Every hand ranks the way the rules say', check_ranks),
        ('Every deck is complete and every card image exists', check_decks),
        ('Lando makes sensible moves in every variant', check_lando),
        ('Solo games end even if the player only ever stands', check_solo_games_end),
        ('A move whose reply Discord drops still counts once', check_lost_replies),
        ('Calling Alderaan from the first seat counts rounds correctly', check_round_count),
        ('Only the owner of Impostor dice can pick from them', check_dice_owners),
        ('Players get one ping with a minute left, deleted when the turn ends', check_warnings),
        ('A restart ends every game politely, with Play Again', check_restart_goodbye),
        ('Card images are small and draw quickly', check_images),
        ('Menus, rules, and help fit Discord and follow the conventions', check_menus),
        ('Broken, old, and stateless buttons are all answered', check_router),
        ('A channel the bot cannot post in closes the game politely', check_refused_channel),
        ('A lobby nobody starts closes after an hour', check_lobby_timeout),
    ]
    for name, test in tests:
        before = len(failures)
        result = test()
        if asyncio.iscoroutine(result):
            await result
        report(name, before)

    before = len(failures)
    played = await run_games()
    report(f'{played} simulated games finish, follow the rules of Discord, and are forgotten', before)

    before = len(failures)
    every_action = {'join', 'leave', 'discarding', 'start', 'play', 'draw', 'replace', 'swap', 'discard', 'drop', 'back',
                    'stand', 'junk', 'alderaan', 'toggle', 'confirm', 'keep', 'psi', 'again'}
    check(every_action <= exercised, f'never worked: {sorted(every_action - exercised)}')
    report('Every button worked at least once in the simulated games', before)

    before = len(failures)
    for variant in variants.values():
        check(lando_turns.get(variant.key, 0) > 0, f'Lando never took a turn in solo {variant.name} games')
    report('Lando takes real turns in every variant', before)
    before = len(failures)
    check(not games, f'{len(games)} games were never forgotten')
    report('No game is left in memory', before)

    print('\n' + ('All checks passed' if not failures else theme.plural(len(failures), 'problem')))  # the same as Aurebesh Droid's
    return 1 if failures else 0
