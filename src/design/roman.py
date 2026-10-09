"""Upright, restrained letterforms with a double-storey a and g.

These paths are drawn for the roman, not obtained by unslanting the italic.
Copyright (c) 2026, Carta Rinascente contributors.
SPDX-License-Identifier: OFL-1.1
"""

from ..geometry import GlyphBuilder, Stroke, dot


def serif(x: int, y: int = 18) -> Stroke:
    return (f"M {x - 34} {y} Q {x} {y + 9} {x + 34} {y}", 0.52)


def draw(builder: GlyphBuilder) -> None:
    add = builder.add
    add('a', 'M 66 392 C 95 497 297 493 298 355 L 298 65 Q 298 13 341 32',
        'M 295 272 C 205 268 63 235 62 111 C 59 -5 211 -19 297 108')
    add('b', 'M 58 700 L 99 714 L 99 28',
        'M 101 350 C 211 518 334 468 333 243 C 333 49 223 -37 100 42')
    add('c', 'M 309 393 C 279 510 76 476 65 244 C 54 28 196 -45 314 93',
        ('M 309 393 L 286 369', 0.65))
    add('d', 'M 294 378 C 185 523 57 445 58 219 C 59 34 180 -36 294 127',
        'M 255 701 L 298 714 L 298 31', serif(304))
    add('e', 'M 62 264 L 305 271 C 303 527 73 511 61 272 C 48 49 189 -46 317 94')
    add('f', 'M 107 20 L 107 559 C 107 735 206 763 257 661',
        ('M 35 438 L 231 438', 0.65), serif(107))
    add('g', 'M 190 460 C 36 460 23 167 183 164 C 333 161 340 459 190 460 Z',
        ('M 251 437 Q 291 461 340 449', 0.65),
        ('M 112 179 C 30 107 91 47 193 41', 0.68),
        'M 192 41 C 376 52 367 -192 184 -194 C 21 -196 17 -46 97 8')
    add('h', 'M 53 700 L 97 714 L 97 20',
        'M 99 319 C 179 494 303 481 303 336 L 303 20', serif(97), serif(303))
    stem_i = ('M 57 439 L 98 453 L 98 20', serif(98))
    add('i', *stem_i, dot(98, 591, 0.82))
    add('ı', *stem_i)
    stem_j = ('M 53 439 L 98 453 L 98 -58 C 98 -206 -13 -239 -48 -135',)
    add('j', *stem_j, dot(98, 591, 0.82))
    add('ȷ', *stem_j)
    add('k', 'M 54 700 L 98 714 L 98 20',
        ('M 305 450 L 102 221', 0.68), 'M 179 306 L 324 27',
        serif(98), serif(320), serif(301, 442))
    add('l', 'M 56 700 L 98 714 L 98 20', serif(98))
    add('m', 'M 51 438 L 95 453 L 95 20',
        'M 97 319 C 165 493 284 478 284 327 L 284 20',
        'M 286 319 C 363 493 480 478 480 327 L 480 20',
        serif(95), serif(284), serif(480))
    add('n', 'M 51 438 L 95 453 L 95 20',
        'M 97 320 C 183 499 308 477 308 329 L 308 20', serif(95), serif(308))
    add('o', 'M 200 462 C 23 462 21 8 200 8 C 379 8 377 462 200 462 Z')
    add('p', 'M 53 438 L 98 453 L 98 -198',
        'M 99 337 C 211 528 339 453 336 235 C 333 47 209 -33 100 92', serif(98, -200))
    add('q', 'M 299 375 C 190 522 58 445 60 220 C 61 32 183 -35 300 129',
        'M 301 451 L 301 -198', serif(301, -200))
    add('r', 'M 53 438 L 97 453 L 97 20',
        'M 99 317 C 157 468 242 492 275 402', serif(97))
    add('s', 'M 278 389 C 237 503 73 467 79 347 C 84 255 268 252 270 129 C 272 -16 99 -24 54 78',
        ('M 54 78 L 52 122', 0.62))
    add('t', 'M 129 578 L 129 118 C 129 18 176 -12 261 62', ('M 39 438 L 264 438', 0.66))
    add('u', 'M 56 443 L 94 452 L 94 143 C 94 -23 218 -15 306 158',
        'M 307 450 L 307 30', serif(310))
    add('v', 'M 56 443 L 190 22', ('M 190 22 L 330 443', 0.66), serif(58, 443), serif(331, 443))
    add('w', 'M 54 443 L 171 24', ('M 171 24 L 304 419', 0.65),
        'M 292 443 L 411 24', ('M 411 24 L 548 443', 0.65), serif(54, 443), serif(548, 443))
    add('x', 'M 53 443 L 326 22', ('M 324 443 L 54 22', 0.66),
        serif(53, 443), serif(324, 443), serif(54), serif(326))
    add('y', 'M 54 443 L 193 60',
        ('M 332 443 L 178 -29 C 128 -184 64 -246 20 -147', 0.77),
        serif(54, 443), serif(332, 443))
    add('z', ('M 54 382 L 66 443 L 303 443', 0.76),
        'M 303 443 L 53 24', ('M 53 24 L 302 24 L 316 91', 0.76))

    # Upright capitals retain the inscriptional bowls of the original design.
    add('H', 'M 99 681 L 99 23', 'M 422 681 L 422 23',
        ('M 99 352 L 422 352', 0.76), serif(99), serif(422), serif(99, 681), serif(422, 681))
    add('I', 'M 114 681 L 114 23', serif(114), serif(114, 681))
    add('L', 'M 98 681 L 98 29', ('M 98 29 L 419 29 L 449 116', 0.74), serif(98, 681))
    add('T', ('M 51 607 L 69 682 L 491 682 L 507 607', 0.75),
        'M 279 679 L 279 23', serif(279))
    add('E', 'M 105 681 L 105 29', ('M 69 681 L 414 681 L 432 610', 0.73),
        ('M 106 357 L 342 357', 0.72), ('M 337 402 L 337 310', 0.55),
        ('M 73 29 L 424 29 L 449 106', 0.74))
    add('F', 'M 105 681 L 105 23', ('M 69 681 L 414 681 L 432 610', 0.73),
        ('M 106 357 L 342 357', 0.72), ('M 337 402 L 337 310', 0.55), serif(105))
    add('Q', 'M 281 699 C 31 699 23 8 281 8 C 539 8 531 699 281 699 Z',
        ('M 265 136 Q 361 -37 493 -76', 0.8))
    # Keep descender overhangs out of the advance, so words remain evenly spaced.
    extra = 12 if builder.style.weight == 700 else 0
    builder.set_spacing('f', 0, 254 + extra)
    for char in ('j', 'ȷ'):
        builder.set_spacing(char, -92, 162 + extra)
