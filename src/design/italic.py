"""Expressive italic alternates with controlled exit strokes and descenders.

Copyright (c) 2026, Carta Rinascente contributors.
SPDX-License-Identifier: OFL-1.1
"""

from ..geometry import GlyphBuilder, PenStroke, dot

SHOULDER_DEPTH = 14
# Keep the expressive crown full while easing into stems at both bowl joins.
SHOULDER_PRESSURE = ((0, 0.35), (0.15, 0.65), (0.3, 1), (1, 1))
ARM_PRESSURE = ((0, 0.35), (0.23, 0.65), (0.46, 1), (1, 1))
BOWL_JOINS = ((0, 0.5), (0.16, 1), (0.68, 1), (0.9, 0.45), (1, 0.25))
LEFT_BOWL_JOINS = ((0, 0.5), (0.16, 1), (0.76, 1), (1, 0.55))
BOWL_PRESSURE = ((0, 1), (0.56, 1), (0.74, 0.65), (0.9, 0.36), (1, 0.25))


def draw(builder: GlyphBuilder) -> None:
    add = builder.add
    add('a', PenStroke('M 285 385 C 241 516 75 457 55 235 C 36 28 139 -28 259 168', pressure=BOWL_JOINS),
        'M 300 460 L 267 93 Q 246 -39 359 73')
    add('b', 'M 211 683 C 193 746 123 737 112 620 L 62 36',
        PenStroke('M 80 314 C 196 548 356 480 321 254 C 288 43 170 -23 63 37', pressure=LEFT_BOWL_JOINS))
    add('d', PenStroke('M 284 389 C 220 516 64 444 54 212 C 46 26 153 -34 263 155', pressure=BOWL_JOINS),
        'M 286 686 Q 348 734 344 649 L 281 94 Q 259 -30 369 80')
    add('e', 'M 62 240 C 167 252 335 358 261 433 C 184 519 77 391 61 252 C 40 54 159 -33 323 119')
    add('f', 'M 26 -167 C 75 -208 110 -116 122 41 L 161 548 C 174 711 265 757 306 672',
        ('M 50 430 C 128 445 224 435 296 451', 0.64))
    add('g', PenStroke('M 279 377 C 217 525 53 433 54 246 C 48 69 158 30 269 183', pressure=BOWL_JOINS),
        'M 299 458 C 275 324 278 119 241 -56 C 192 -300 -86 -242 -17 -123 Q 17 -61 131 -73')
    add('h', 'M 216 683 C 196 746 123 739 114 622 L 73 19',
        PenStroke('M 91 289 C 182 523 315 482 293 324 L 265 104 Q 241 -33 358 84', nib_depth=SHOULDER_DEPTH, pressure=SHOULDER_PRESSURE))
    stem_i = ('M 43 397 Q 118 514 105 380 L 74 105 Q 55 -25 172 92',)
    add('i', *stem_i, dot(110, 587, 1.3))
    add('ı', *stem_i)
    stem_j = ('M 79 398 Q 160 513 142 374 L 95 -53 C 69 -274 -74 -242 -60 -117',)
    add('j', *stem_j, dot(149, 587, 1.3))
    add('ȷ', *stem_j)
    add('k', 'M 218 686 C 191 745 129 736 118 621 L 82 17',
        ('M 115 210 C 209 270 298 392 301 466', 0.74),
        ('M 173 276 C 272 281 204 46 294 27 Q 331 18 369 80', 1.0, (0.35, 0.6)))
    add('l', 'M 214 683 C 195 746 130 742 119 621 L 76 126 C 61 13 109 13 194 88')
    add('m', 'M 32 397 Q 108 511 91 378 L 69 20',
        PenStroke('M 86 294 C 166 518 284 484 263 327 L 229 21', nib_depth=SHOULDER_DEPTH, pressure=SHOULDER_PRESSURE),
        PenStroke('M 249 294 C 336 516 456 480 432 326 L 402 102 Q 381 -32 501 86', nib_depth=SHOULDER_DEPTH, pressure=SHOULDER_PRESSURE))
    add('n', 'M 34 397 Q 108 511 91 378 L 69 20',
        PenStroke('M 86 294 C 172 530 320 480 294 321 L 265 103 Q 241 -32 364 86', nib_depth=SHOULDER_DEPTH, pressure=SHOULDER_PRESSURE))
    add('p', 'M 30 396 Q 113 516 97 371 L 41 -211',
        PenStroke('M 89 309 C 210 551 367 466 325 242 C 293 74 190 7 74 90', pressure=LEFT_BOWL_JOINS))
    add('q', PenStroke('M 278 388 C 215 515 65 440 50 235 C 32 35 149 -31 264 156', pressure=BOWL_JOINS),
        'M 298 457 L 242 -132 Q 222 -278 340 -176')
    add('r', 'M 34 396 Q 109 512 91 376 L 70 20',
        PenStroke('M 87 287 C 156 468 242 521 276 405 Q 271 361 237 385', nib_depth=SHOULDER_DEPTH, pressure=ARM_PRESSURE))
    add('t', 'M 165 613 C 137 444 89 203 98 94 C 108 -29 209 15 287 119',
        ('M 34 410 Q 161 439 283 452', 0.62))
    add('u', PenStroke('M 35 397 Q 110 509 96 375 L 70 143 C 45 -38 194 -25 280 188',
                       nib_depth=SHOULDER_DEPTH, pressure=BOWL_PRESSURE),
        'M 296 456 L 265 104 Q 242 -30 365 86')
    add('v', 'M 38 400 Q 108 500 115 365 L 160 39',
        ('M 160 39 C 239 146 325 332 318 430 Q 315 465 282 448', 0.82))
    add('w', 'M 40 400 Q 109 497 114 364 L 146 36',
        ('M 146 36 C 202 140 252 273 278 436', 0.82),
        'M 278 436 L 329 37',
        ('M 329 37 C 412 163 478 344 450 443 Q 440 467 417 445', 0.82))
    add('y', PenStroke('M 41 431 Q 107 498 98 382 L 79 173 C 58 -6 190 -24 277 164',
                       nib_depth=SHOULDER_DEPTH, pressure=BOWL_PRESSURE),
        'M 298 455 C 274 187 278 -133 89 -226 C 1 -263 -74 -175 -4 -117')
    add('z', 'M 46 385 Q 104 470 161 438 L 298 422 C 225 301 109 141 53 36 Q 174 4 302 72',
        ('M 105 227 Q 207 252 278 244', 0.58))
    add('Q', 'M 299 704 C 125 716 31 437 79 206 C 132 -103 425 -20 476 283 C 524 536 451 704 299 704 Z',
        'M 242 151 C 295 -34 434 -165 605 -60')
    # Let loops and sweeping descenders overhang their advances. Whole-outline
    # bounds otherwise insert visible gaps inside words such as page and yellow.
    for char, shift, reduction in (('d', 0, 80), ('g', -140, 140),
                                   ('l', 0, 100), ('p', -75, 75), ('y', -145, 145)):
        advance = round(builder.glyphs[char].advance / builder.style.spacing_scale) - reduction
        builder.set_spacing(char, shift, advance)
    extra = 14 if builder.style.weight == 700 else 0
    builder.set_spacing('f', -66, 319 + extra)
    for char in ('j', 'ȷ'):
        builder.set_spacing(char, -145, 243 + extra)


def draw_extended(builder: GlyphBuilder) -> None:
    """Keep bowl joins consistent in ligatures, thorn and the micro sign."""
    builder.add('æ', PenStroke('M 277 380 C 222 500 62 433 59 204 C 55 21 151 -35 274 171',
                              pressure=BOWL_JOINS),
                'M 293 435 C 282 292 250 148 304 50 C 369 -48 493 27 544 104',
                'M 280 259 C 416 245 537 327 489 417 C 441 504 315 434 280 259')
    builder.add('þ', 'M 56 704 Q 119 749 107 650 L 58 -197',
                PenStroke('M 97 316 C 215 530 353 462 324 244 C 300 67 203 -23 90 78',
                          pressure=LEFT_BOWL_JOINS))
    builder.add('µ', 'M 92 449 L 48 -197',
                PenStroke('M 92 444 L 73 146 C 55 -19 187 -40 279 180',
                          nib_depth=SHOULDER_DEPTH, pressure=BOWL_PRESSURE),
                'M 294 455 L 269 109 Q 256 -13 340 67')
