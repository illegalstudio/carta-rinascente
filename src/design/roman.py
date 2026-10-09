"""Original text roman with open proportions and bracketed serifs.

Copyright (c) 2026, Carta Rinascente contributors.
SPDX-License-Identifier: OFL-1.1
"""

from functools import partial

from shapely.affinity import scale, translate
from shapely.ops import unary_union

from ..geometry import FilledPath, GlyphBuilder, PenStroke, Shape, dot

SHOULDER_DEPTH = 19
BOWL_PRESSURE = ((0, 1), (0.48, 1), (0.72, 0.82), (1, 0.55))


def bracketed_serif(builder: GlyphBuilder, x: float, y: float = 0, *, top: bool = False) -> FilledPath:
    """Join a level serif to its stem with two concave shoulder curves."""
    weight = builder.style.pen_scale
    stem = 32 * weight
    spread = stem + 31 * weight ** 0.5
    lip = 11 * weight
    rise = 40 * weight ** 0.3
    direction = -1 if top else 1
    a, b, c = y + direction * lip, y + direction * rise * 0.35, y + direction * rise
    return FilledPath(
        f"M {x-spread} {y} L {x+spread} {y} L {x+spread} {a} "
        f"C {x+stem+8} {a} {x+stem} {b} {x+stem} {c} "
        f"L {x-stem} {c} C {x-stem} {b} {x-stem-8} {a} {x-spread} {a} Z"
    )


def head_serif(builder: GlyphBuilder, x: float, y: float) -> FilledPath:
    """A short, slightly rising left serif for lowercase stem entries."""
    stem = 32 * builder.style.pen_scale
    left = x - stem - 31
    return FilledPath(
        f"M {left} {y-6} L {x+stem} {y+13} L {x+stem} {y-48} "
        f"L {x-stem} {y-48} C {x-stem} {y-22} {left+17} {y-18} {left} {y-18} Z"
    )


def draw(builder: GlyphBuilder) -> None:
    add = builder.add
    serif = partial(bracketed_serif, builder)
    head = partial(head_serif, builder)

    # Stem endpoints sit inside the serif so the bold nib cannot protrude below it.
    add('a', 'M 85 397 C 84 527 354 529 354 352 L 354 81 C 354 19 385 14 409 49',
        'M 351 290 C 230 280 75 251 74 128 C 73 2 237 -35 352 132')
    add('b', 'M 112 684 L 112 30', head(112, 686),
        'M 112 384 C 237 574 458 507 458 257 C 458 42 277 -53 112 70')
    add('c', 'M 424 413 C 371 566 77 519 77 251 C 77 23 284 -65 425 112',
        ('M 424 413 L 398 382', 0.85))
    add('d', 'M 422 391 C 289 573 74 480 74 246 C 74 38 242 -40 422 145',
        'M 424 684 L 424 36', head(424, 686), serif(424))
    add('e', 'M 77 273 L 438 273 C 438 564 75 572 75 267 C 75 37 288 -62 437 116')
    add('f', 'M 135 36 L 135 529 C 135 719 269 747 323 647',
        ('M 59 480 L 294 480', 0.76), serif(135))
    add('g', 'M 237 490 C 18 490 21 186 233 186 C 444 186 458 490 237 490 Z',
        ('M 323 466 Q 394 495 449 473', 0.65),
        ('M 128 205 C 69 146 112 92 220 82 L 295 82', 0.8),
        'M 295 82 C 492 88 488 -179 248 -180 C 33 -181 35 -22 145 35')
    add('h', 'M 112 684 L 112 36', head(112, 686), serif(112),
        PenStroke('M 113 340 C 227 570 441 549 441 351 L 441 36', nib_depth=SHOULDER_DEPTH), serif(441))
    stem_i = ('M 112 482 L 112 36', head(112, 486), serif(112))
    add('i', *stem_i, dot(112, 621, 1.38), bearing=61)
    add('ı', *stem_i, bearing=61)
    stem_j = ('M 112 482 L 112 -47 C 112 -207 -36 -222 -54 -117', head(112, 486))
    add('j', *stem_j, dot(112, 621, 1.38))
    add('ȷ', *stem_j)
    add('k', 'M 112 684 L 112 36', head(112, 686), serif(112),
        ('M 440 482 L 115 220', 0.74),
        'M 285 323 L 463 36',
        serif(440, 497, top=True), serif(463))
    add('l', 'M 112 684 L 112 36', head(112, 686), serif(112), bearing=61)
    add('m', 'M 112 482 L 112 36', head(112, 486), serif(112),
        PenStroke('M 113 342 C 212 568 402 546 402 351 L 402 36', nib_depth=SHOULDER_DEPTH), serif(402),
        PenStroke('M 403 342 C 519 568 706 546 706 351 L 706 36', nib_depth=SHOULDER_DEPTH), serif(706))
    add('n', 'M 112 482 L 112 36', head(112, 486), serif(112),
        PenStroke('M 113 343 C 226 576 445 543 445 351 L 445 36', nib_depth=SHOULDER_DEPTH), serif(445))
    add('o', 'M 267 494 C 139 494 76 397 76 252 C 76 107 139 8 267 8 C 395 8 458 107 458 252 C 458 397 395 494 267 494 Z')
    add('p', 'M 112 482 L 112 -176', head(112, 486), serif(112, -212),
        'M 112 380 C 244 584 457 500 457 258 C 457 45 279 -28 112 122')
    add('q', 'M 421 391 C 285 575 76 484 76 249 C 76 27 251 -35 422 148',
        'M 425 482 L 425 -176', serif(425, -212))
    add('r', 'M 112 482 L 112 36', head(112, 486), serif(112),
        PenStroke('M 113 342 C 191 507 316 553 358 421', nib_depth=SHOULDER_DEPTH),
        ('M 358 421 L 340 404', 0.85))
    add('s', 'M 351 407 C 289 563 66 499 77 363 C 86 250 360 267 358 127 C 358 -28 118 -35 60 98',
        ('M 60 98 L 60 146', 0.78))
    add('t', 'M 145 616 L 145 123 C 145 23 207 -15 296 71', ('M 61 480 L 304 480', 0.76))
    add('u', PenStroke('M 112 482 L 112 158 C 112 -47 319 -29 438 184', pressure=BOWL_PRESSURE), head(112, 486),
        'M 440 482 L 440 36', head(440, 486), serif(440))
    add('v', 'M 76 478 L 251 26', ('M 251 26 L 427 478', 0.75),
        serif(76, 497, top=True), serif(427, 497, top=True))
    add('w', 'M 75 478 L 225 25', ('M 225 25 L 396 475', 0.74),
        'M 396 478 L 551 25', ('M 551 25 L 719 478', 0.74),
        serif(75, 497, top=True), serif(396, 497, top=True), serif(719, 497, top=True))
    add('x', 'M 77 478 L 429 36', ('M 421 478 L 74 24', 0.74),
        serif(77, 497, top=True), serif(421, 497, top=True), serif(74), serif(429))
    add('y', 'M 75 478 L 248 57',
        ('M 433 478 L 229 -33 C 150 -241 63 -243 29 -129', 0.85),
        serif(75, 497, top=True), serif(433, 497, top=True))
    add('z', ('M 79 415 L 91 480 L 414 480', 0.8),
        'M 414 480 L 79 24', ('M 79 24 L 414 24 L 428 94', 0.8))

    add('A', ('M 79 25 L 339 682', 0.75), 'M 339 682 L 590 36',
        ('M 165 252 L 504 252', 0.72), serif(79), serif(590))
    add('B', 'M 127 677 L 127 36', serif(127, 700, top=True), serif(127),
        'M 127 683 L 300 683 C 584 683 600 369 299 365 L 127 365',
        'M 127 365 L 303 365 C 628 365 629 19 303 19 L 127 19')
    add('C', 'M 613 578 C 531 766 88 784 88 355 C 88 -41 498 -33 614 145',
        ('M 613 578 L 613 510', 0.8))
    add('D', 'M 127 677 L 127 36', serif(127, 700, top=True), serif(127),
        'M 127 683 L 300 683 C 746 683 746 19 300 19 L 127 19')
    add('E', 'M 127 677 L 127 36',
        ('M 68 683 L 552 683 L 572 606', 0.8),
        ('M 127 357 L 453 357', 0.76), ('M 451 406 L 451 308', 0.66),
        ('M 68 19 L 567 19 L 596 110', 0.8))
    add('F', 'M 127 677 L 127 36', serif(127),
        ('M 68 683 L 555 683 L 576 606', 0.8),
        ('M 127 357 L 452 357', 0.76), ('M 451 406 L 451 308', 0.66))
    add('G', 'M 610 579 C 525 780 89 771 89 355 C 89 -54 500 -35 595 160 L 595 320',
        ('M 470 320 L 654 320', 0.76), ('M 610 579 L 610 516', 0.8))
    add('H', 'M 127 677 L 127 36', 'M 617 677 L 617 36',
        ('M 127 358 L 617 358', 0.76), serif(127), serif(617),
        serif(127, 700, top=True), serif(617, 700, top=True))
    add('I', 'M 127 677 L 127 36', serif(127), serif(127, 700, top=True), bearing=73)
    add('J', 'M 377 677 L 377 199 C 377 -57 84 -49 77 112', serif(377, 700, top=True))
    add('K', 'M 127 677 L 127 36', serif(127), serif(127, 700, top=True),
        ('M 606 677 L 130 311', 0.78),
        'M 344 434 L 620 36',
        serif(606, 700, top=True), serif(620))
    add('L', 'M 127 677 L 127 36', serif(127, 700, top=True),
        ('M 66 19 L 551 19 L 590 119', 0.8))
    add('M', ('M 128 36 L 128 677', 0.76), 'M 128 677 L 414 78',
        ('M 414 78 L 714 677', 0.76), 'M 714 677 L 714 36',
        serif(128), serif(714), serif(128, 700, top=True), serif(714, 700, top=True))
    add('N', ('M 124 36 L 124 677', 0.76), 'M 124 677 L 622 25',
        ('M 622 25 L 622 677', 0.76), serif(124), serif(622, 700, top=True))
    add('O', 'M 355 697 C 176 697 79 565 79 352 C 79 139 176 5 355 5 C 534 5 631 139 631 352 C 631 565 534 697 355 697 Z')
    add('P', 'M 127 677 L 127 36', serif(127), serif(127, 700, top=True),
        'M 127 683 L 304 683 C 620 683 620 352 304 352 L 127 352')
    add('Q', 'M 355 697 C 176 697 79 565 79 352 C 79 139 176 5 355 5 C 534 5 631 139 631 352 C 631 565 534 697 355 697 Z',
        ('M 339 145 Q 457 -25 619 -66', 0.83))
    add('R', 'M 127 677 L 127 36', serif(127), serif(127, 700, top=True),
        'M 127 683 L 304 683 C 620 683 620 352 304 352 L 127 352',
        'M 304 352 C 426 296 454 57 596 36', serif(596))
    add('S', 'M 543 576 C 462 769 110 741 110 540 C 110 360 546 370 546 181 C 546 -62 170 -32 77 126',
        ('M 543 576 L 543 518', 0.76), ('M 77 126 L 77 182', 0.76))
    add('T', ('M 52 601 L 70 683 L 649 683 L 667 601', 0.8),
        'M 359 677 L 359 36', serif(359))
    add('U', 'M 127 677 L 127 241 C 127 -66 600 -66 600 241 L 600 677',
        serif(127, 700, top=True), serif(600, 700, top=True))
    add('V', 'M 83 677 L 355 24', ('M 355 24 L 625 677', 0.76),
        serif(83, 700, top=True), serif(625, 700, top=True))
    add('W', 'M 84 677 L 300 25', ('M 300 25 L 509 675', 0.76),
        'M 506 677 L 720 25', ('M 720 25 L 930 677', 0.76),
        serif(84, 700, top=True), serif(506, 700, top=True), serif(930, 700, top=True))
    add('X', 'M 88 677 L 621 36', ('M 613 677 L 80 25', 0.76),
        serif(88, 700, top=True), serif(613, 700, top=True), serif(80), serif(621))
    add('Y', 'M 78 677 L 357 344', ('M 631 677 L 357 344', 0.76),
        'M 357 344 L 357 36', serif(78, 700, top=True), serif(631, 700, top=True), serif(357))
    add('Z', ('M 87 602 L 87 683 L 609 683', 0.76), 'M 609 683 L 87 25',
        ('M 87 19 L 609 19 L 609 105', 0.76))

    extra = 17 if builder.style.weight == 700 else 0
    builder.set_spacing('f', 0, 348 + extra)
    for char in ('j', 'ȷ'):
        builder.set_spacing(char, -126, 257 + extra)


def draw_extended(builder: GlyphBuilder) -> None:
    """Keep less frequent Latin letters consistent with the upright alphabet."""
    add = builder.add
    serif = partial(bracketed_serif, builder)
    head = partial(head_serif, builder)
    add('ß', 'M 112 36 L 112 508 C 112 757 414 742 390 554 C 375 452 302 404 247 373',
        'M 247 373 C 501 362 500 22 283 22 Q 223 22 190 66', serif(112))
    add('µ', 'M 112 482 L 112 -176', head(112, 486), serif(112, -212),
        PenStroke('M 112 281 L 112 158 C 112 -47 319 -29 438 184',
                  pressure=((0, 1), (0.3, 1), (0.65, 0.82), (1, 0.55))),
        'M 440 482 L 440 36', head(440, 486), serif(440))
    add('þ', 'M 112 684 L 112 -176', head(112, 686), serif(112, -212),
        'M 112 380 C 244 584 457 500 457 258 C 457 45 279 -28 112 122')
    add('Þ', 'M 127 677 L 127 36', serif(127, 700, top=True), serif(127),
        'M 127 527 L 286 527 C 612 527 612 193 286 193 L 127 193')
    add('ð', 'M 122 672 C 327 628 462 430 452 249 C 448 89 375 8 263 8 '
        'C 137 8 77 111 77 251 C 77 438 269 552 415 371',
        ('M 108 535 L 327 662', 0.64))
    for char, left in (('æ', 'a'), ('œ', 'o')):
        a, e = builder.glyphs[left], builder.glyphs['e']
        factor = 0.88
        offset = (a.geometry.bounds[2] - e.geometry.bounds[0]) * factor - 56
        geometry = unary_union([scale(a.geometry, xfact=factor, yfact=1, origin=(0, 0)),
                                translate(scale(e.geometry, xfact=factor, yfact=1, origin=(0, 0)), xoff=offset)])
        builder.glyphs[char] = Shape(geometry, round(offset + e.advance * factor), char)


def draw_numerals(builder: GlyphBuilder) -> None:
    """Level lining figures for the roman, without calligraphic entry strokes."""
    add = builder.add
    serif = partial(bracketed_serif, builder)
    add('0', 'M 224 674 C 7 674 7 14 224 14 C 441 14 441 674 224 674 Z')
    add('1', ('M 93 547 L 214 671', 0.65), 'M 214 671 L 214 36', serif(214))
    add('2', 'M 64 518 C 66 732 390 728 385 515 C 381 330 185 237 63 26',
        ('M 63 26 L 394 26 L 394 109', 0.65))
    add('3', 'M 75 563 C 162 744 394 691 365 518 C 349 420 263 366 190 356',
        'M 190 356 C 425 405 447 54 237 18 C 150 0 83 38 58 100')
    add('4', ('M 309 674 L 48 239 L 423 239', 0.67), 'M 309 674 L 309 36', serif(309))
    add('5', ('M 381 662 L 116 662 L 94 377', 0.8),
        'M 94 377 C 312 486 452 308 357 121 C 294 -11 139 -24 65 98')
    add('6', 'M 364 604 C 254 783 41 617 65 265 C 87 -80 411 -48 403 223 C 399 408 210 438 76 289')
    add('7', ('M 61 585 L 61 662 L 412 662', 0.65), 'M 412 662 C 258 430 190 233 164 24')
    add('8', 'M 228 676 C 57 676 16 464 170 368 C 350 256 433 217 380 100 C 318 -48 100 -12 65 122 C 23 276 253 346 354 472 C 443 593 346 676 228 676 Z')
    add('9', 'M 74 89 C 192 -67 409 100 385 440 C 361 789 36 739 46 478 C 54 286 249 261 374 412')
