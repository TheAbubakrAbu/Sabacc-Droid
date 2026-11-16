# cards.py
#
# Draws every picture the bot sends: a row of cards, the table of final hands,
# and dice. The card art ships in images/ at 240 pixels tall with at most 256
# colors, so a card is read straight from disk in about a millisecond; nothing
# is downloaded and nothing big stays in memory. Every picture is saved as a
# 256-color PNG, about a fifth of the size of a full-color one.

from functools import lru_cache
from io import BytesIO
from pathlib import Path

import discord
from PIL import Image, ImageDraw, ImageFont

folder = Path(__file__).parent / 'images'
height = 240  # pixels; twice the size the old bot drew, so cards stay sharp on phones
gap = 12

table_height = 160  # each row of the final table
places = {1: (226, 182, 64), 2: (190, 196, 206), 3: (201, 128, 70)}  # gold, silver, bronze
other_place = (96, 102, 112)

die_size = 150
dice_colors = {  # (body, marks)
    'gold': ((227, 181, 59), (58, 42, 5)),
    'silver': ((201, 206, 214), (43, 47, 54)),
    'sand': ((232, 176, 75), (59, 36, 10)),
    'blood': ((166, 58, 46), (250, 235, 225)),
}
pips = {
    1: [(0.5, 0.5)],
    2: [(0.27, 0.27), (0.73, 0.73)],
    3: [(0.27, 0.27), (0.5, 0.5), (0.73, 0.73)],
    4: [(0.27, 0.27), (0.73, 0.27), (0.27, 0.73), (0.73, 0.73)],
    5: [(0.27, 0.27), (0.73, 0.27), (0.5, 0.5), (0.27, 0.73), (0.73, 0.73)],
    6: [(0.27, 0.25), (0.73, 0.25), (0.27, 0.5), (0.73, 0.5), (0.27, 0.75), (0.73, 0.75)],
}


@lru_cache(maxsize=48)
def face(path: str, size: int = height) -> Image.Image:
    '''
    One card, as RGBA at the given height. The most used cards (backs,
    common values) stay cached; the cache holds about 5 MB at most.
    '''

    with Image.open(folder / path) as image:
        image = image.convert('RGBA')
    if image.height != size:
        image = image.resize((round(image.width * size / image.height), size), Image.LANCZOS)
    return image


@lru_cache(maxsize=4)
def font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.load_default(size=size)
    except (TypeError, OSError):  # Pillow without FreeType: a small bitmap font still works
        return ImageFont.load_default()


def png(canvas: Image.Image) -> bytes:
    out = BytesIO()
    canvas.quantize(256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE).save(out, 'PNG')
    return out.getvalue()


def paste_row(canvas: Image.Image, paths: list[str], x: int, y: int, size: int) -> None:
    for path in paths:
        card = face(path, size)
        canvas.alpha_composite(card, (x, y))
        x += card.width + gap


def row_width(paths: list[str], size: int) -> int:
    return sum(face(path, size).width for path in paths) + gap * max(len(paths) - 1, 0)


def render(paths: list[str]) -> bytes:
    '''
    Cards side by side on a transparent background.
    '''

    canvas = Image.new('RGBA', (max(row_width(paths, height), 1), height), (0, 0, 0, 0))
    paste_row(canvas, paths, 0, 0, height)
    return png(canvas)


def render_table(rows: list[tuple[int, list[str]]]) -> bytes:
    '''
    Every final hand in finishing order, each behind a numbered badge:
    gold, silver, and bronze for the top three places.
    '''

    badge = table_height * 6 // 10
    left = badge + 2 * gap
    width = left + max((row_width(paths, table_height) for _, paths in rows), default=1)
    canvas = Image.new('RGBA', (width, len(rows) * (table_height + 2 * gap) - 2 * gap), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    for index, (place, paths) in enumerate(rows):
        y = index * (table_height + 2 * gap)
        top = y + (table_height - badge) // 2
        draw.ellipse((gap, top, gap + badge, top + badge), fill=places.get(place, other_place), outline=(30, 31, 34), width=4)
        draw.text((gap + badge / 2, top + badge / 2), str(place), fill=(30, 31, 34), font=font(badge // 2), anchor='mm')
        paste_row(canvas, paths, left, y, table_height)
    return png(canvas)


def draw_die(draw: ImageDraw.ImageDraw, x: int, kind: str, value: object) -> None:
    body, mark = dice_colors[kind]
    size = die_size
    draw.rounded_rectangle((x, 0, x + size - 1, size - 1), radius=size // 5, fill=body, outline=mark, width=5)
    center = (x + size / 2, size / 2)
    if kind in ('sand', 'blood'):
        dot = size // 14
        for px, py in pips[int(value)]:
            cx, cy = x + px * size, py * size
            draw.ellipse((cx - dot, cy - dot, cx + dot, cy + dot), fill=mark)
    elif kind == 'gold':
        text = f'+{value}' if int(value) > 0 else str(value)
        draw.text(center, text, fill=mark, font=font(size * 2 // 5), anchor='mm')
    else:  # the silver die shows a suit
        half = size * 0.26
        cx, cy = center
        if value == 'circle':
            draw.ellipse((cx - half, cy - half, cx + half, cy + half), fill=mark)
        elif value == 'square':
            draw.rectangle((cx - half * 0.9, cy - half * 0.9, cx + half * 0.9, cy + half * 0.9), fill=mark)
        else:
            draw.polygon([(cx, cy - half), (cx + half * 1.1, cy + half * 0.8), (cx - half * 1.1, cy + half * 0.8)], fill=mark)


def render_dice(dice: list[tuple[str, object]]) -> bytes:
    '''
    Dice side by side: ('gold', -5) shows a number, ('silver', 'circle') a
    suit, and ('sand', 4) or ('blood', 2) pips.
    '''

    canvas = Image.new('RGBA', (len(dice) * (die_size + 2 * gap) - 2 * gap, die_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    for index, (kind, value) in enumerate(dice):
        draw_die(draw, index * (die_size + 2 * gap), kind, value)
    return png(canvas)


def as_file(data: bytes, name: str = 'cards.png') -> discord.File:
    return discord.File(BytesIO(data), filename=name)
