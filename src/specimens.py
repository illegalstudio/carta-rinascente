"""Reproducible English proof sheets rendered from the generated TTF files.

Copyright (c) 2026, Carta Rinascente contributors.
SPDX-License-Identifier: OFL-1.1
"""

from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

from .config import FAMILY, STYLES, VERSION, WHITESPACE, Style

PAPER = "#F7F2EA"
INK = "#332E2D"
ACCENT = "#762F3B"
MUTED = "#736669"
RULE = "#D8C9C4"


def font(directory: Path, style: Style, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(directory / f"{style.filename}.ttf"), size)


def label(size: int = 20) -> ImageFont.FreeTypeFont:
    return ImageFont.load_default(size=size)


def text(draw: ImageDraw.ImageDraw, directory: Path, style: Style, value: str,
         xy: tuple[int, int], size: int, width: int = 1400, fill: str = INK,
         *, fit: bool = True) -> None:
    """Fit a proof line by its real ink bounds, including italic overhangs."""
    x, y = xy
    face = font(directory, style, size)
    while True:
        left, top, right, bottom = draw.textbbox((0, 0), value, font=face)
        if right - left <= width:
            break
        if not fit:
            raise ValueError(f"Proof text exceeds its width at {size} px: {value!r}")
        size -= 1
        if size < 12:
            raise ValueError(f"Proof text cannot fit: {value!r}")
        face = font(directory, style, size)
    draw.text((x - left, y - top), value, font=face, fill=fill)


def family_sheet(directory: Path) -> Image.Image:
    image = Image.new("RGB", (1600, 1280), PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((100, 60), f"ILLEGAL STUDIO  /  FOUR ORIGINAL STYLES  /  {VERSION}", font=label(), fill=MUTED)
    text(draw, directory, STYLES[0], FAMILY, (100, 115), 120, fill=ACCENT)
    draw.line((100, 278, 1500, 278), fill=RULE, width=2)
    for index, style in enumerate(STYLES):
        y = 320 + index * 224
        draw.text((100, y), style.name.upper(), font=label(19), fill=MUTED)
        text(draw, directory, style, "A quiet page, an expressive voice.", (100, y + 44), 72)
        text(draw, directory, style, "Hamburgefontsiv  0123456789  à è é ì ò ù", (100, y + 143), 43, fill=ACCENT)
    return image


def style_sheet(directory: Path, style: Style) -> None:
    image = Image.new("RGB", (1600, 1540), PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((100, 65), f"CARTA RINASCENTE  /  {style.name.upper()}  /  {VERSION}", font=label(), fill=MUTED)
    text(draw, directory, style, "Letters with a little soul.", (100, 140), 112, fill=ACCENT)
    rows = (
        (330, "A quiet page, an expressive voice.", 72),
        (450, "The art of giving words a little character.", 64),
        (620, "A B C D E F G H I J K L M", 80),
        (740, "N O P Q R S T U V W X Y Z", 80),
        (860, "a b c d e f g h i j k l m", 76),
        (980, "n o p q r s t u v w x y z", 76),
        (1100, "0 1 2 3 4 5 6 7 8 9", 76),
        (1220, "À È É Ì Ò Ù  à è é ì ò ù  € & @", 68),
        (1340, "AVATAR WA VA To Ta Te Yo Wo fi fl ffi ffl", 55),
    )
    for y, value, size in rows:
        text(draw, directory, style, value, (100, y), size)
    draw.text((100, 1470), "Independent pen paths  /  TTF + WOFF2  /  SIL Open Font License 1.1",
              font=label(), fill=MUTED)
    image.save(directory / f"specimen-{style.slug}.png")


def character_sheet(directory: Path, style: Style) -> None:
    with TTFont(directory / f"{style.filename}.ttf") as face:
        codepoints = [cp for cp in face.getBestCmap() if cp not in WHITESPACE and cp != 0xAD]
    columns, cell = 12, 140
    rows = (len(codepoints) + columns - 1) // columns
    image = Image.new("RGB", (columns * cell + 80, rows * cell + 140), PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((40, 32), f"{FAMILY.upper()}  /  {style.name.upper()}  /  CHARACTER PROOF", font=label(23), fill=INK)
    for index, codepoint in enumerate(codepoints):
        x, y = 40 + (index % columns) * cell, 100 + (index // columns) * cell
        draw.rectangle((x, y, x + cell, y + cell), outline=RULE)
        face = font(directory, style, 76)
        value = chr(codepoint)
        bounds = draw.textbbox((0, 0), value, font=face)
        # Center the ink rather than the advance, which is zero for combining marks.
        draw.text((x + (cell - bounds[2] + bounds[0]) / 2 - bounds[0], y + 98),
                  value, font=face, fill=INK, anchor="ls")
        draw.text((x + 12, y + 118), f"U+{codepoint:04X}", font=label(13), fill=MUTED)
    name = "caratteri.png" if style.name == "Regular" else f"caratteri-{style.slug}.png"
    image.save(directory / name)


def reading_sheet(directory: Path) -> None:
    image = Image.new("RGB", (1000, 1720), "white")
    draw = ImageDraw.Draw(image)
    draw.text((60, 40), "CARTA RINASCENTE / ACTUAL PIXEL SIZES", font=label(24), fill=INK)
    draw.text((60, 78), "View at 100% zoom. Every row uses the exact size shown.", font=label(18), fill=MUTED)
    for index, style in enumerate(STYLES):
        top = 120 + index * 390
        draw.text((60, top), style.name, font=label(23), fill=ACCENT)
        for row, size in enumerate((18, 24, 36, 48)):
            y = top + 58 + row * 68
            draw.text((60, y), f"{size} px", font=label(16), fill=MUTED)
            text(draw, directory, style, "The art of a quiet page.",
                 (160, y), size, width=780, fit=False)
    image.save(directory / "prove-lettura.png")


def render_family(directory: Path, readme_output: Path | None = None) -> None:
    """Render every proof from the same installed family, with no borrowed outlines."""
    family = family_sheet(directory)
    family.save(directory / "anteprima.png")
    if readme_output is not None:
        readme_output.parent.mkdir(parents=True, exist_ok=True)
        family.save(readme_output)
    for style in STYLES:
        style_sheet(directory, style)
        character_sheet(directory, style)
    reading_sheet(directory)
