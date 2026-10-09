"""Expressive italic alternates with controlled exit strokes and descenders.

Copyright (c) 2026, Carta Rinascente contributors.
SPDX-License-Identifier: OFL-1.1
"""

from ..geometry import GlyphBuilder


def draw(builder: GlyphBuilder) -> None:
    add = builder.add
    add('f', 'M -21 -169 C 98 -215 83 20 106 257 L 142 595 C 158 778 318 761 294 639',
        ('M 17 414 C 116 440 227 417 306 450', 0.74))
    add('g', 'M 279 377 C 220 515 73 449 61 250 C 50 83 143 17 260 153',
        'M 299 458 C 273 314 279 119 253 -51 C 212 -286 -29 -229 28 -93')
    add('k', 'M 54 704 Q 126 758 109 638 L 82 17',
        ('M 115 210 C 209 270 298 392 301 466', 0.74),
        'M 173 276 C 272 281 204 46 294 27 Q 331 18 369 80')
    add('l', 'M 44 696 C 201 832 188 567 98 410 C 78 276 69 102 94 39 Q 114 7 180 75')
    add('y', 'M 41 431 Q 107 498 98 382 L 79 173 C 58 -6 190 -24 277 164',
        'M 298 455 C 274 187 278 -111 113 -208 Q 22 -259 -3 -149')
    add('z', 'M 46 385 Q 104 470 161 438 L 298 422 C 225 301 109 141 53 36 Q 174 4 302 72',
        ('M 105 227 Q 207 252 278 244', 0.58))
    add('Q', 'M 299 704 C 125 716 31 437 79 206 C 132 -103 425 -20 476 283 C 524 536 451 704 299 704 Z',
        'M 242 151 C 295 -34 434 -165 605 -60')
    add('ı', 'M 57 435 Q 119 480 111 398 L 83 109 C 70 -13 119 15 161 74')
    add('ȷ', 'M 92 434 Q 151 477 146 396 L 103 -43 C 81 -241 -32 -251 -42 -126')
    extra = 14 if builder.style.weight == 700 else 0
    builder.set_spacing('f', -66, 319 + extra)
    for char in ('j', 'ȷ'):
        builder.set_spacing(char, -145, 243 + extra)
