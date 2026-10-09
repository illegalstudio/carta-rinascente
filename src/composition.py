"""Unicode composition from independent glyphs and shared mark anchors.

Copyright (c) 2026, Carta Rinascente contributors.
SPDX-License-Identifier: OFL-1.1
"""

import unicodedata

from shapely.affinity import translate, scale
from shapely.geometry import Polygon, box
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from .anchors import mark_anchor
from .design.accents import ACCENTS
from .geometry import GlyphBuilder, Shape


def _extended_letters(builder: GlyphBuilder) -> None:
    """Draw additional Latin letters and their shared components."""
    add = builder.add
    ink = builder.ink
    shapes = builder.glyphs
    add('ß', 'M 37 0 L 67 486 C 84 753 317 728 276 529 Q 258 441 173 378 C 365 385 391 119 234 56 Q 166 26 122 72')
    add('æ', 'M 277 380 C 222 500 62 433 59 204 C 55 21 151 -35 274 171',
        'M 293 435 C 282 292 250 148 304 50 C 369 -48 493 27 544 104',
        'M 280 259 C 416 245 537 327 489 417 C 441 504 315 434 280 259')
    add('œ', 'M 209 457 C 71 475 18 262 65 107 C 122 -84 295 3 307 224 C 319 391 272 456 209 457 Z',
        'M 302 259 C 438 245 559 327 511 417 C 459 510 307 409 303 233 C 286 42 413 -48 557 104')
    for char, left, right in [('Æ', 'A', 'E'), ('Œ', 'O', 'E')]:
        a, b = shapes[left], shapes[right]
        offset = a.advance - 92
        shapes[char] = Shape(unary_union([a.geometry, translate(b.geometry, xoff=offset)]), offset + b.advance, char)
    for char, base in [('ø', 'o'), ('Ø', 'O'), ('ł', 'l'), ('Ł', 'L')]:
        original = shapes[base]
        x0, y0, x1, y1 = original.geometry.bounds
        slash = ink(f'M {x0 + 6} {y0 + 25} L {x1 - 5} {y1 - 25}', 0.64)
        shapes[char] = Shape(unary_union([original.geometry, slash]), original.advance, base)
    for char, base in [('đ', 'd'), ('Đ', 'D')]:
        original = shapes[base]
        y = 564 if char.islower() else 354
        bar = ink(f'M 15 {y} L {original.advance - 20} {y + 8}', 0.66)
        shapes[char] = Shape(unary_union([original.geometry, bar]), original.advance, base)
    shapes['Ð'] = shapes['Đ']
    add('ð', 'M 99 676 C 279 615 368 421 319 214 C 275 11 107 -60 65 125 C 29 291 133 470 255 431 Q 303 416 327 356',
        ('M 101 513 L 294 645', 0.65))
    add('µ', 'M 92 449 L 48 -197',
        'M 92 444 L 73 146 C 55 -19 187 -40 279 180',
        'M 294 455 L 269 109 Q 256 -13 340 67')
    add('þ', 'M 56 704 Q 119 749 107 650 L 58 -197',
        'M 97 316 C 215 530 353 462 324 244 C 300 67 203 -23 90 78')
    add('Þ', 'M 88 685 L 56 18', 'M 82 522 C 353 620 464 436 344 284 Q 235 162 68 211')


def _accented_letters(builder: GlyphBuilder) -> dict[str, BaseGeometry]:
    """Place combining marks and precomposed accents using shared anchors."""
    ink = builder.ink
    shapes = builder.glyphs
    accent_geometry = {}
    for char, paths in ACCENTS.items():
        accent_geometry[char] = unary_union([ink(*p) for p in paths])
        shapes[char] = Shape(accent_geometry[char], 0, char)
    for cp in range(0xC0, 0x180):
        char = chr(cp)
        decomposition = unicodedata.normalize('NFD', char)
        if char in shapes or len(decomposition) != 2:
            continue
        base, mark = decomposition
        if base not in shapes or mark not in accent_geometry:
            continue
        original = shapes['ı' if base == 'i' else ('ȷ' if base == 'j' else base)]
        x, y = mark_anchor(original, base, mark, builder.style)
        accent = translate(accent_geometry[mark], xoff=x, yoff=y)
        shapes[char] = Shape(unary_union([original.geometry, accent]), original.advance, base)
    return accent_geometry


def _punctuation(builder: GlyphBuilder) -> None:
    """Derive quotation marks, dashes and related punctuation."""
    add = builder.add
    shapes = builder.glyphs
    add('ſ', 'M 18 -178 C 79 -156 78 21 102 255 L 137 592 C 152 757 283 755 293 639')
    shapes['ſ'] = Shape(translate(shapes['ſ'].geometry, xoff=-60), 302, 'ſ')
    # Reusable punctuation is transformed from our own paths.
    for char, xflip, yflip, offset in [('‘', -1, -1, 650), ('’', 1, 1, 590), ('‚', 1, 1, 0)]:
        g = shapes[',']
        geo = scale(g.geometry, xfact=xflip, yfact=yflip, origin=(g.advance/2, 30))
        shapes[char] = Shape(translate(geo, yoff=offset), g.advance, char)
    for char, base in [('“', '‘'), ('”', '’'), ('„', '‚')]:
        g = shapes[base]
        shapes[char] = Shape(unary_union([g.geometry, translate(g.geometry, xoff=g.advance-30)]), g.advance*2-30, char)
    for char, base in [('«', '<'), ('»', '>'), ('‹', '<'), ('›', '>')]:
        g = shapes[base]
        geo = scale(g.geometry, xfact=0.54, yfact=0.7, origin=(0, 310))
        adv = round(g.advance * 0.54)
        if char in '«»':
            geo = unary_union([geo, translate(geo, xoff=adv-10)])
            adv = adv*2-10
        shapes[char] = Shape(geo, adv, char)
    for cp, length in [(0x2013, 460), (0x2014, 800), (0x2212, 410)]:
        add(chr(cp), (f'M 35 280 L {length-35} 285', 0.76), bearing=35)
    g = shapes['.']
    shapes['…'] = Shape(unary_union([translate(g.geometry, xoff=i*g.advance) for i in range(3)]), 3*g.advance, '.')
    shapes['\u00ad'] = shapes['-']


def _small_forms(builder: GlyphBuilder) -> None:
    """Construct superscripts, fractions and enclosed symbols."""
    ink = builder.ink
    shapes = builder.glyphs
    for char, base in [('¹', '1'), ('²', '2'), ('³', '3'), ('ª', 'a'), ('º', 'o')]:
        g = shapes[base]
        shapes[char] = Shape(translate(scale(g.geometry, xfact=0.58, yfact=0.58, origin=(0, 0)), yoff=340), round(g.advance*0.58), char)
    for char, numerator, denominator in [('¼', '1', '4'), ('½', '1', '2'), ('¾', '3', '4')]:
        a, b = shapes[numerator], shapes[denominator]
        geo_a = translate(scale(a.geometry, xfact=0.52, yfact=0.52, origin=(0, 0)), yoff=340)
        geo_b = translate(scale(b.geometry, xfact=0.52, yfact=0.52, origin=(0, 0)), xoff=295)
        diagonal = ink('M 145 30 L 407 651', 0.58)
        shapes[char] = Shape(unary_union([geo_a, diagonal, geo_b]), 295 + round(b.advance*0.52), char)
    for char, base in [('©', 'C'), ('®', 'R')]:
        g = shapes[base]
        center = translate(scale(g.geometry, xfact=0.51, yfact=0.51, origin=(0, 0)), xoff=123, yoff=180)
        ring = ink('M 281 709 C -16 700 -8 12 279 10 C 565 10 578 711 281 709 Z', 0.48)
        shapes[char] = Shape(unary_union([center, ring]), 585, char)
    g_t, g_m = shapes['T'], shapes['M']
    tm = unary_union([scale(g_t.geometry, xfact=0.48, yfact=0.48, origin=(0, 0)),
                      translate(scale(g_m.geometry, xfact=0.48, yfact=0.48, origin=(0, 0)), xoff=g_t.advance*0.48)])
    shapes['™'] = Shape(translate(tm, yoff=350), round((g_t.advance+g_m.advance)*0.48), '™')


def _additional_symbols(builder: GlyphBuilder) -> None:
    """Draw paragraph, section and currency signs."""
    add = builder.add
    add('§', 'M 302 630 C 210 766 55 615 137 508 L 289 291 C 395 137 139 116 93 272 C 48 427 287 471 329 338',
        'M 106 492 C -14 382 138 225 244 148 C 347 66 221 -48 116 28')
    add('¶', 'M 260 672 C 22 759 12 363 251 398', 'M 271 675 L 235 -76', 'M 378 676 L 342 -76')
    add('¤', ('M 205 488 C 23 484 24 164 202 166 C 382 168 391 490 205 488 Z', 0.7),
        ('M 61 512 L 354 139', 0.56), ('M 360 517 L 52 135', 0.56))


def _spacing_and_diacritics(builder: GlyphBuilder, accent_geometry: dict[str, BaseGeometry]) -> None:
    """Complete Latin-1 spacing accents and Unicode whitespace."""
    shapes = builder.glyphs
    # Standalone diacritics, required for complete Latin-1 coverage.
    for char, combining in [('¨', '\u0308'), ('¯', '\u0304'), ('´', '\u0301'), ('¸', '\u0327')]:
        y = 530 if char != '¸' else -5
        shapes[char] = Shape(translate(accent_geometry[combining], xoff=145, yoff=y), 290, char)
    g = shapes['|']
    shapes['¦'] = Shape(g.geometry.difference(box(-100, 275, 400, 370)), g.advance, '¦')
    for char, width in [(' ', 248), ('\u00a0', 248), ('\u2009', 145), ('\u202f', 145), ('\u2002', 500), ('\u2003', 1000)]:
        shapes[char] = Shape(Polygon(), width, char)
    shapes['\u200b'] = Shape(Polygon(), 0, '\u200b')


def extend_alphabet(builder: GlyphBuilder) -> None:
    """Complete one style in dependency order, without any input font."""
    _extended_letters(builder)
    accents = _accented_letters(builder)
    _punctuation(builder)
    _small_forms(builder)
    _additional_symbols(builder)
    _spacing_and_diacritics(builder, accents)
