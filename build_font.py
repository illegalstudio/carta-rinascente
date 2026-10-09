"""Build Carta Rinascente from independently authored pen paths.

The design has no input font, traced alphabet, or third-party outline data.
Font Software, including this source: SIL Open Font License 1.1, see OFL.txt.
"""

from pathlib import Path
from dataclasses import dataclass
import json
import math
import re
import unicodedata

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib import TTFont, newTable
from fontTools.agl import UV2AGL
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
from shapely.affinity import affine_transform, translate, scale
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'dist'
UPM = 1000
SLANT = 0.105
FAMILY = 'Carta Rinascente'
VERSION = '0.100'
COPYRIGHT = 'Copyright (c) 2026, Carta Rinascente contributors.'


def points(path):
    """Sample our absolute M/L/C/Q pen paths to sub-unit accuracy."""
    tokens = re.findall(r'[MLCQZ]|-?\d+(?:\.\d+)?', path)
    result = []
    i = 0
    while i < len(tokens):
        cmd = tokens[i]
        i += 1
        count = {'M': 2, 'L': 2, 'Q': 4, 'C': 6, 'Z': 0}[cmd]
        values = list(map(float, tokens[i:i + count]))
        i += count
        if cmd == 'M':
            result.append(tuple(values))
            start = tuple(values)
            continue
        p0 = result[-1]
        if cmd == 'Z':
            values = list(start)
            cmd = 'L'
        controls = [p0] + list(zip(values[::2], values[1::2]))
        length = sum(math.dist(a, b) for a, b in zip(controls, controls[1:]))
        steps = max(3, math.ceil(length / 7))
        for step in range(1, steps + 1):
            t = step / steps
            p = controls
            while len(p) > 1:
                p = [(a[0] * (1-t) + b[0] * t, a[1] * (1-t) + b[1] * t)
                     for a, b in zip(p, p[1:])]
            result.append(p[0])
    return result


def ink(path, weight=1.0, tips=(0.75, 0.6)):
    """Sweep a slightly rounded broad nib over a path, with tapered terminals."""
    pts = points(path)
    closed = math.dist(pts[0], pts[-1]) < 1
    angle = math.radians(23)
    ca, sa = math.cos(angle), math.sin(angle)
    stamps = []
    for index, (x, y) in enumerate(pts):
        t = index / max(1, len(pts) - 1)
        pressure = 1.0 if closed else min(1, tips[0] + t * 5, tips[1] + (1-t) * 5)
        # A superellipse gives the pen a flatter edge than a circular brush.
        contour = []
        for j in range(16):
            a = j * math.tau / 16
            u, v = math.cos(a), math.sin(a)
            u = math.copysign(abs(u) ** 0.72, u) * 32 * weight * pressure
            v = math.copysign(abs(v) ** 0.72, v) * 8.5 * weight * pressure
            contour.append((x + ca*u - sa*v, y + sa*u + ca*v))
        stamps.append(Polygon(contour))
    return unary_union([a.union(b).convex_hull for a, b in zip(stamps, stamps[1:])])


@dataclass
class Shape:
    geometry: object
    advance: int
    base: str = ''


shapes = {}


def add(char, *paths, bearing=29, advance=None):
    pieces = []
    for path in paths:
        if isinstance(path, tuple):
            pieces.append(ink(*path))
        else:
            pieces.append(ink(path))
    geometry = unary_union(pieces).simplify(0.42, preserve_topology=True)
    geometry = affine_transform(geometry, [1, SLANT, 0, 1, 0, 0])
    geometry = translate(geometry, xoff=bearing - geometry.bounds[0])
    shapes[char] = Shape(geometry, advance or round(geometry.bounds[2] + bearing), char)


def dot(x, y, weight=1):
    return (f'M {x-3} {y-5} L {x+3} {y+5}', weight, (1, 1))


def alphabet():
    # Lowercase: open humanist forms, a single-storey a and descending g.
    add('a', 'M 288 391 C 231 510 85 460 60 239 C 34 44 104 -24 207 75 C 248 116 270 233 286 377',
        'M 295 465 C 279 321 266 164 286 45 C 294 1 326 24 353 64')
    add('b', 'M 55 710 Q 122 747 108 650 L 86 51',
        'M 102 351 C 209 532 334 484 330 287 C 328 82 226 -37 89 38')
    add('c', 'M 304 392 C 277 491 127 476 80 327 C 5 110 115 -65 306 93',
        'M 304 392 Q 283 359 257 366')
    add('d', 'M 289 389 C 226 517 69 436 58 209 C 49 28 156 -36 272 140',
        'M 316 716 Q 344 750 335 647 C 309 409 268 154 293 47 Q 305 4 350 55')
    add('e', 'M 73 258 C 201 252 308 316 276 415 C 242 513 106 445 72 295 C 14 72 130 -52 310 102')
    add('f', 'M 18 -178 C 79 -156 78 21 102 255 L 137 592 C 152 757 283 755 293 639',
        ('M 28 415 C 115 429 213 425 290 443', 0.8))
    add('g', 'M 277 377 C 226 507 82 452 67 254 C 54 94 137 17 256 151',
        'M 297 457 C 269 318 276 120 252 -43 C 214 -276 12 -244 39 -99')
    add('h', 'M 56 704 Q 119 749 107 650 L 82 20',
        'M 101 299 C 177 502 302 493 291 349 L 272 108 C 258 -14 302 15 343 70')
    add('i', 'M 57 435 Q 119 480 111 398 L 83 109 C 70 -13 119 15 161 74', dot(113, 590, 0.85))
    add('j', 'M 92 434 Q 151 477 146 396 L 103 -43 C 81 -241 -32 -251 -42 -126', dot(151, 591, 0.85))
    add('k', 'M 59 705 Q 126 748 109 638 L 82 17',
        ('M 115 210 C 205 277 273 374 294 461', 0.8),
        'M 168 275 C 252 276 208 72 286 27 Q 314 18 340 60')
    add('l', 'M 57 700 C 184 791 169 577 99 421 C 81 285 69 108 91 39 Q 110 6 158 63')
    add('m', 'M 46 429 Q 100 488 98 386 L 78 21',
        'M 94 292 C 163 492 274 478 260 334 L 239 22',
        'M 255 289 C 326 492 441 473 425 331 L 405 96 Q 392 -16 475 68')
    add('n', 'M 44 429 Q 104 490 98 381 L 78 20',
        'M 96 292 C 175 506 306 477 288 327 L 271 100 Q 258 -18 340 69')
    add('o', 'M 211 457 C 71 475 18 262 65 107 C 122 -84 298 4 311 224 C 322 391 274 456 211 457 Z')
    add('p', 'M 50 430 Q 106 478 99 388 L 56 -205',
        'M 99 319 C 218 532 353 462 324 244 C 300 67 203 -23 94 78')
    add('q', 'M 278 389 C 221 513 76 446 59 240 C 39 48 137 -35 266 137',
        'M 297 454 L 239 -142 Q 233 -217 301 -183')
    add('r', 'M 48 430 Q 104 488 98 386 L 76 20',
        'M 97 282 C 156 443 227 515 277 392',
        ('M 277 392 Q 260 353 239 367', 0.7))
    add('s', 'M 279 391 C 250 510 90 463 92 342 C 91 256 260 239 263 129 C 266 -17 96 -28 54 75',
        ('M 54 75 Q 45 103 61 132', 0.8))
    add('t', 'M 153 607 C 129 457 98 258 106 102 C 111 -5 183 -18 266 90',
        ('M 35 414 C 118 431 224 422 275 444', 0.8))
    add('u', 'M 48 429 Q 106 485 98 387 L 76 151 C 58 -19 189 -38 280 179',
        'M 294 455 L 269 109 Q 256 -13 340 67')
    add('v', 'M 44 434 Q 104 478 109 376 L 123 89 C 125 -66 282 65 312 338 Q 320 424 285 454')
    add('w', 'M 45 433 Q 99 479 104 375 L 115 119 C 120 -47 239 39 273 218',
        'M 262 429 L 269 117 C 275 -47 410 41 452 308 Q 473 411 433 456')
    add('x', 'M 38 403 Q 75 495 119 411 L 249 86 Q 282 7 334 57',
        ('M 305 451 C 270 314 169 151 67 33', 0.8))
    add('y', 'M 43 431 Q 105 488 97 384 L 78 174 C 59 -8 189 -20 276 162',
        'M 295 452 C 270 192 274 -105 120 -201 Q 45 -250 13 -161')
    add('z', 'M 51 386 Q 99 459 152 437 L 284 421 C 213 297 104 153 58 41 Q 150 15 270 45',
        ('M 96 229 Q 194 246 262 241', 0.62))
    # Descenders and ascender hooks may overhang the advance width.
    # Counting their full outline width would create gaps inside ordinary words.
    for char, shift, advance in [('f', -60, 302), ('j', -135, 243)]:
        g = shapes[char]
        shapes[char] = Shape(translate(g.geometry, xoff=shift), advance, char)

    # Capitals keep inscriptional structure with restrained pen flourishes.
    add('A', ('M 30 27 C 142 248 271 537 352 711', 0.8),
        'M 350 691 C 358 448 411 192 464 29',
        ('M 115 249 C 230 267 353 264 423 279', 0.74),
        ('M 21 24 Q 80 42 129 35', 0.65), ('M 402 30 Q 476 44 516 56', 0.66))
    add('B', 'M 88 648 Q 149 708 145 603 L 108 39',
        'M 73 658 C 386 804 559 558 212 365 C 569 493 536 83 284 29 Q 179 5 108 39',
        ('M 122 360 Q 172 375 219 367', 0.7))
    add('C', 'M 491 563 C 411 835 117 685 75 363 C 29 3 332 -87 493 162',
        ('M 491 563 L 469 500', 0.78))
    add('D', 'M 87 644 Q 151 704 145 600 L 111 45',
        'M 74 658 C 345 825 563 612 481 304 C 432 71 243 -25 111 45')
    add('E', 'M 94 640 Q 155 703 148 596 L 111 45',
        'M 77 659 Q 248 735 419 680 L 435 626',
        ('M 130 359 Q 253 386 370 379', 0.84),
        'M 112 43 Q 269 12 438 76 L 460 134')
    add('F', 'M 81 642 Q 148 705 142 592 L 108 31',
        'M 65 658 Q 240 739 422 681 L 439 624',
        ('M 127 355 Q 253 387 370 379', 0.8),
        ('M 48 21 Q 120 48 185 33', 0.65))
    add('G', 'M 490 564 C 411 818 121 691 76 367 C 24 3 318 -95 455 165 L 468 326',
        ('M 327 321 Q 428 345 529 326', 0.87))
    add('H', 'M 52 655 Q 150 729 138 604 L 101 26',
        'M 451 686 L 414 107 Q 405 -5 478 52',
        ('M 114 340 Q 250 363 431 353', 0.87))
    add('I', 'M 88 656 Q 153 712 147 601 L 113 68',
        ('M 53 654 Q 155 711 257 684', 0.8),
        ('M 43 31 Q 146 73 232 42', 0.76))
    add('J', 'M 270 674 L 241 175 C 212 -66 36 -79 28 103',
        ('M 143 647 Q 244 712 359 677', 0.8))
    add('K', 'M 61 654 Q 151 726 139 598 L 105 28',
        ('M 460 689 C 379 560 252 385 133 294', 0.88),
        'M 248 400 C 376 401 322 94 456 41 Q 488 25 513 63')
    add('L', 'M 62 653 Q 156 730 143 590 L 108 49',
        'M 109 48 C 246 70 299 -19 451 68 Q 476 83 488 120')
    add('M', ('M 34 30 L 133 682', 0.75),
        'M 135 681 L 268 135',
        ('M 269 136 L 494 684', 0.78),
        'M 494 684 L 510 107 Q 509 9 575 49')
    add('N', ('M 43 34 L 93 680', 0.75),
        'M 73 656 Q 93 702 133 631 L 438 21',
        ('M 438 23 L 490 681', 0.77),
        ('M 434 665 Q 497 700 546 681', 0.65))
    add('O', 'M 299 704 C 125 716 31 437 79 206 C 132 -103 425 -20 476 283 C 524 536 451 704 299 704 Z')
    add('P', 'M 75 646 Q 144 707 140 594 L 106 33',
        'M 60 660 C 296 788 497 662 429 464 C 387 340 252 303 126 346',
        ('M 50 24 Q 129 47 193 33', 0.68))
    add('Q', 'M 299 704 C 125 716 31 437 79 206 C 132 -103 425 -20 476 283 C 524 536 451 704 299 704 Z',
        'M 253 147 C 292 -27 422 -136 565 -82')
    add('R', 'M 70 646 Q 144 707 140 594 L 106 31',
        'M 61 660 C 289 787 487 660 425 473 C 388 360 248 335 128 352',
        'M 251 356 C 346 306 336 101 456 40 Q 488 25 514 62')
    add('S', 'M 443 576 C 410 792 101 717 110 530 C 112 366 430 364 421 177 C 412 -45 126 -51 57 112',
        ('M 57 112 L 69 175', 0.76))
    add('T', 'M 41 616 Q 64 691 152 680 C 302 674 416 728 518 682 L 539 631',
        'M 294 676 L 254 118 Q 238 -9 325 52')
    add('U', 'M 52 653 Q 145 728 132 587 L 100 237 C 74 -70 328 -48 435 216',
        'M 467 690 L 429 108 Q 418 -6 496 53')
    add('V', 'M 52 654 Q 129 718 145 589 L 215 47',
        ('M 215 47 C 339 237 470 511 487 685', 0.84))
    add('W', 'M 41 653 Q 115 721 130 585 L 175 42',
        ('M 175 44 L 370 542', 0.8),
        'M 360 655 L 433 45',
        ('M 433 45 C 558 245 666 524 655 685', 0.81))
    add('X', 'M 50 642 Q 104 729 157 619 L 401 95 Q 440 13 504 63',
        ('M 487 693 C 403 514 219 225 57 25', 0.83))
    add('Y', 'M 40 655 Q 103 713 124 623 L 270 343',
        ('M 479 688 C 430 568 351 429 270 343', 0.82),
        'M 269 343 L 242 33', ('M 172 21 Q 251 49 317 36', 0.72))
    add('Z', 'M 55 618 Q 103 708 192 681 L 463 676 C 317 489 157 251 49 38 Q 276 2 475 67 L 496 122',
        ('M 134 341 Q 280 368 397 358', 0.7))


def numbers_and_symbols():
    add('0', 'M 229 672 C 77 683 38 381 72 177 C 108 -84 310 4 334 276 C 358 517 336 671 229 672 Z')
    add('1', ('M 69 498 Q 164 571 215 666', 0.8), 'M 215 666 L 172 37',
        ('M 81 29 Q 174 51 265 37', 0.7))
    add('2', 'M 69 497 C 83 727 365 735 346 514 C 334 349 142 231 60 48 Q 208 22 345 52 L 368 111')
    add('3', 'M 67 572 C 193 746 409 665 304 479 Q 263 407 172 366',
        'M 172 366 C 421 444 409 133 244 38 Q 106 -28 50 81')
    add('4', ('M 295 673 L 40 246 L 396 260', 0.82), 'M 309 657 L 270 33')
    add('5', 'M 364 671 Q 229 649 113 662 L 82 366 C 314 496 428 211 263 66 Q 136 -41 53 76')
    add('6', 'M 347 647 C 178 759 41 448 65 224 C 81 -8 264 -61 330 123 C 396 304 265 445 86 289')
    add('7', 'M 52 608 Q 86 686 153 661 L 376 652 C 261 454 169 230 132 25',
        ('M 119 339 L 308 350', 0.7))
    add('8', 'M 221 673 C 93 677 51 506 157 413 C 276 312 371 275 330 131 C 286 -41 87 -10 64 146 C 43 288 221 340 301 466 C 381 589 318 675 221 673 Z')
    add('9', 'M 309 384 C 157 215 28 366 79 544 C 130 743 338 711 331 480 C 327 251 222 -51 67 56')
    add('.', dot(60, 35, 0.85), bearing=37)
    add(',', dot(77, 37, 0.82), ('M 79 33 Q 79 -33 34 -70', 0.66), bearing=29)
    add(':', dot(65, 43, 0.8), dot(80, 334, 0.8), bearing=38)
    add(';', dot(71, 334, 0.8), dot(58, 43, 0.8), ('M 59 40 Q 68 -18 19 -69', 0.62), bearing=29)
    add('!', 'M 91 670 L 61 183', dot(47, 40, 0.85), bearing=38)
    add('?', 'M 67 524 C 100 711 329 713 318 550 C 307 413 154 405 149 210', dot(132, 44, 0.85))
    add('-', ('M 35 270 Q 124 286 222 276', 0.8), bearing=39)
    add('_', ('M 22 -77 L 377 -77', 0.73))
    add('/', ('M 38 -104 L 314 735', 0.71), bearing=28)
    add('\\', ('M 31 733 L 285 -108', 0.7), bearing=28)
    add('|', ('M 83 -128 L 83 737', 0.68), bearing=54)
    add('(', ('M 214 753 C 43 575 -4 191 125 -126', 0.84), bearing=22)
    add(')', ('M 70 753 C 244 546 243 191 60 -123', 0.84), bearing=22)
    add('[', ('M 203 743 L 90 739 L 64 -124 L 181 -124', 0.76), bearing=28)
    add(']', ('M 66 743 L 176 739 L 150 -124 L 35 -124', 0.76), bearing=28)
    add('{', ('M 248 747 C 90 762 186 400 69 309 C 170 225 45 -138 216 -128', 0.8), bearing=24)
    add('}', ('M 75 747 C 233 762 120 400 246 309 C 134 225 264 -138 89 -128', 0.8), bearing=24)
    add("'", ('M 64 699 L 50 558', 0.76), bearing=28)
    add('"', ('M 64 699 L 50 558', 0.76), ('M 180 699 L 166 558', 0.76), bearing=28)
    add('`', ('M 50 713 L 125 602', 0.82))
    add('^', ('M 34 545 L 157 694 L 251 545', 0.78))
    add('~', ('M 32 292 C 111 411 197 206 289 321', 0.72))
    add('+', ('M 41 317 L 398 322', 0.7), ('M 232 512 L 208 127', 0.8), bearing=39)
    add('=', ('M 42 419 L 390 425', 0.72), ('M 35 222 L 383 228', 0.72), bearing=39)
    add('<', ('M 307 527 L 57 315 L 289 107', 0.76), bearing=34)
    add('>', ('M 59 527 L 302 315 L 38 107', 0.76), bearing=34)
    add('*', ('M 156 687 L 137 403', 0.63), ('M 23 605 L 264 478', 0.63), ('M 266 617 L 20 470', 0.63))
    add('#', ('M 170 692 L 87 32', 0.75), ('M 358 692 L 275 32', 0.75),
        ('M 37 444 L 431 454', 0.7), ('M 16 237 L 407 247', 0.7))
    add('%', ('M 40 3 L 460 686', 0.65),
        ('M 130 663 C 49 679 38 431 113 427 C 204 422 209 652 130 663 Z', 0.72),
        ('M 379 263 C 297 279 285 25 362 21 C 455 17 459 252 379 263 Z', 0.72))
    add('&', 'M 464 472 C 363 357 282 6 117 20 C -27 33 34 260 173 368 C 321 482 354 694 231 690 C 68 685 135 461 248 300 C 353 144 442 21 514 61',
        ('M 401 471 Q 469 494 533 481', 0.7))
    add('@', 'M 368 337 C 320 460 207 398 192 256 C 174 101 307 87 349 243',
        'M 388 421 L 351 230 C 323 87 483 134 522 337 C 574 646 213 667 104 390 C -13 89 234 -115 486 32')
    add('$', 'M 328 551 C 274 697 79 631 94 487 C 107 369 330 359 317 216 C 301 57 123 79 55 173',
        ('M 248 741 L 169 -42', 0.59))
    add('€', 'M 382 568 C 316 751 90 633 79 348 C 71 93 267 -47 403 143',
        ('M 32 398 L 291 404', 0.64), ('M 26 279 L 266 285', 0.64))
    add('£', 'M 361 568 C 331 729 135 679 126 513 C 118 325 203 171 69 33 Q 190 80 362 30',
        ('M 46 335 L 281 341', 0.72))
    add('¥', 'M 42 662 L 222 350 L 411 671', 'M 222 350 L 198 30',
        ('M 64 328 L 361 333', 0.63), ('M 57 198 L 351 203', 0.63))
    add('¢', 'M 321 424 C 271 541 91 427 82 270 C 65 91 211 40 328 177', ('M 247 658 L 153 11', 0.58))
    add('°', ('M 135 682 C 31 688 16 500 124 493 C 230 487 248 672 135 682 Z', 0.65))
    add('·', dot(62, 312, 0.75), bearing=50)
    add('×', ('M 45 490 L 346 131', 0.74), ('M 366 500 L 42 125', 0.72))
    add('÷', ('M 41 317 L 370 323', 0.72), dot(215, 513, 0.7), dot(194, 133, 0.7))
    add('±', ('M 42 367 L 384 373', 0.7), ('M 226 577 L 210 155', 0.74), ('M 31 43 L 374 49', 0.7))
    add('¬', ('M 42 377 L 384 383 L 371 190', 0.75))
    add('¡', 'M 48 -165 L 78 322', dot(92, 465, 0.85), bearing=38)
    add('¿', 'M 312 -25 C 279 -212 50 -213 61 -51 C 72 86 225 94 230 289', dot(247, 455, 0.85))


ACCENTS = {
    '\u0300': [('M -68 107 L 23 17', 0.84)],
    '\u0301': [('M -31 15 L 64 109', 0.84)],
    '\u0302': [('M -100 18 L 0 118 L 89 19', 0.74)],
    '\u0303': [('M -103 42 C -46 142 22 -3 100 91', 0.69)],
    '\u0304': [('M -93 59 L 96 62', 0.68)],
    '\u0306': [('M -91 100 Q -3 -24 88 100', 0.67)],
    '\u0307': [dot(0, 57, 0.79)],
    '\u0308': [dot(-64, 60, 0.7), dot(64, 60, 0.7)],
    '\u030a': [('M 5 121 C -80 121 -80 0 0 0 C 85 0 85 121 5 121 Z', 0.57)],
    '\u030b': [('M -87 14 L -12 112', 0.66), ('M 25 14 L 100 112', 0.66)],
    '\u030c': [('M -95 117 L 0 17 L 89 117', 0.74)],
    '\u0327': [('M 16 -13 L -7 -68 C 106 -88 44 -181 -38 -145', 0.62)],
    '\u0328': [('M 33 6 C -52 -88 -35 -169 62 -117', 0.65)],
}


def extend_alphabet():
    # A dotless i is used beneath accents so dots never collide with accents.
    add('ı', 'M 57 435 Q 119 480 111 398 L 83 109 C 70 -13 119 15 161 74')
    add('ȷ', 'M 92 434 Q 151 477 146 396 L 103 -43 C 81 -241 -32 -251 -42 -126')
    shapes['ȷ'] = Shape(translate(shapes['ȷ'].geometry, xoff=-135), 243, 'j')
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
    for char, base in [('đ', 'd'), ('Đ', 'D'), ('ð', 'o')]:
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
        y = 757 if base.isupper() else 540
        if base in 'bdfhkl':
            y = 782
        if mark in ('\u0327', '\u0328'):
            y = -15
        x = original.advance / 2 + (28 if y > 0 else 0)
        accent = translate(accent_geometry[mark], xoff=x, yoff=y)
        shapes[char] = Shape(unary_union([original.geometry, accent]), original.advance, base)
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
    for char, base in [('¹', '1'), ('²', '2'), ('³', '3'), ('ª', 'a'), ('º', 'o')]:
        g = shapes[base]
        shapes[char] = Shape(translate(scale(g.geometry, xfact=0.58, yfact=0.58, origin=(0, 0)), yoff=340), round(g.advance*0.58), base)
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
    add('§', 'M 302 630 C 210 766 55 615 137 508 L 289 291 C 395 137 139 116 93 272 C 48 427 287 471 329 338',
        'M 106 492 C -14 382 138 225 244 148 C 347 66 221 -48 116 28')
    add('¶', 'M 260 672 C 22 759 12 363 251 398', 'M 271 675 L 235 -76', 'M 378 676 L 342 -76')
    add('¤', ('M 205 488 C 23 484 24 164 202 166 C 382 168 391 490 205 488 Z', 0.7),
        ('M 61 512 L 354 139', 0.56), ('M 360 517 L 52 135', 0.56))
    # Standalone diacritics, required for complete Latin-1 coverage.
    for char, combining in [('¨', '\u0308'), ('¯', '\u0304'), ('´', '\u0301'), ('¸', '\u0327')]:
        y = 530 if char != '¸' else -5
        shapes[char] = Shape(translate(accent_geometry[combining], xoff=145, yoff=y), 290, char)
    g = shapes['|']
    from shapely.geometry import box
    shapes['¦'] = Shape(g.geometry.difference(box(-100, 275, 400, 370)), g.advance, '¦')
    for char, width in [(' ', 248), ('\u00a0', 248), ('\u2009', 145), ('\u202f', 145), ('\u2002', 500), ('\u2003', 1000)]:
        shapes[char] = Shape(Polygon(), width, char)
    shapes['\u200b'] = Shape(Polygon(), 0, '\u200b')


def glyph_name(char):
    if len(char) > 1:
        return char
    return UV2AGL.get(ord(char), f'uni{ord(char):04X}')


def glyph_outline(geometry):
    pen = TTGlyphPen(None)
    if geometry.is_empty:
        return pen.glyph()
    geometry = geometry.buffer(0).simplify(0.48, preserve_topology=True)
    polygons = [geometry] if geometry.geom_type == 'Polygon' else list(geometry.geoms)
    for polygon in polygons:
        if polygon.area < 0.75:
            continue
        polygon = orient(polygon, sign=-1)
        for ring in [polygon.exterior] + list(polygon.interiors):
            coords = [(round(x), round(y)) for x, y in ring.coords[:-1]]
            coords = [p for i, p in enumerate(coords) if i == 0 or p != coords[i-1]]
            if len(coords) < 3:
                continue
            pen.moveTo(coords[0])
            for p in coords[1:]:
                pen.lineTo(p)
            pen.closePath()
    return pen.glyph()


KERN_PAIRS = {
    ('A','V'):-52, ('A','W'):-36, ('A','Y'):-44, ('A','T'):-28,
    ('V','A'):-46, ('W','A'):-28, ('Y','A'):-42, ('T','A'):-32,
    ('T','a'):-53, ('T','e'):-44, ('T','o'):-48, ('T','u'):-28, ('T','r'):-18,
    ('V','a'):-42, ('V','e'):-39, ('V','o'):-45, ('V','u'):-29,
    ('W','a'):-28, ('W','e'):-27, ('W','o'):-30,
    ('Y','a'):-48, ('Y','e'):-47, ('Y','o'):-47, ('Y','u'):-32,
    ('F','a'):-22, ('F','o'):-26, ('P','a'):-21,
    ('L','T'):-26, ('L','V'):-34, ('L','W'):-25, ('L','Y'):-34,
    ('r','a'):-12, ('r','e'):-11, ('r','o'):-13,
    ('v','a'):-12, ('v','e'):-12, ('v','o'):-14,
    ('w','a'):-10, ('w','o'):-10,
}


def build():
    OUT.mkdir(exist_ok=True)
    alphabet()
    numbers_and_symbols()
    extend_alphabet()
    # Each glyph was constructed above. No external font is opened here.
    missing_latin1 = [chr(cp) for cp in range(32, 256) if cp not in range(127, 160) and chr(cp) not in shapes]
    assert not missing_latin1, missing_latin1
    fb = FontBuilder(UPM, isTTF=True)
    order = ['.notdef'] + [glyph_name(c) for c in shapes]
    assert len(order) == len(set(order))
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({ord(c): glyph_name(c) for c in shapes})
    from shapely.geometry import box
    missing = box(40, 0, 430, 670).difference(box(77, 37, 393, 633))
    glyphs = {'.notdef': glyph_outline(missing)}
    metrics = {'.notdef': (470, 40)}
    for char, shape in shapes.items():
        name = glyph_name(char)
        glyph = glyph_outline(shape.geometry)
        glyphs[name] = glyph
        metrics[name] = (shape.advance, glyph.xMin if hasattr(glyph, 'xMin') else 0)
    fb.setupGlyf(glyphs)
    # Bounds are computed by setupGlyf, so record true side bearings now.
    for char, shape in shapes.items():
        name = glyph_name(char)
        metrics[name] = (shape.advance, getattr(fb.font['glyf'][name], 'xMin', 0))
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=990, descent=-290, lineGap=0, caretSlopeRise=1000, caretSlopeRun=105)
    fb.setupNameTable({
        'familyName': FAMILY, 'styleName': 'Regular', 'typographicFamily': FAMILY,
        'typographicSubfamily': 'Regular', 'uniqueFontIdentifier': f'CartaRinascente-Regular-{VERSION}',
        'fullName': FAMILY + ' Regular', 'psName': 'CartaRinascente-Regular',
        'version': 'Version ' + VERSION, 'copyright': COPYRIGHT,
        'designer': 'Created for nahime with OpenAI Codex',
        'description': 'An original readable Renaissance-inspired pen design. Experimental first release. Independently authored paths; no third-party font outlines.',
        'licenseDescription': 'Licensed under the SIL Open Font License, Version 1.1. No Reserved Font Names. See OFL.txt.',
        'licenseInfoURL': 'https://openfontlicense.org',
    })
    fb.setupOS2(version=4, sTypoAscender=990, sTypoDescender=-290, sTypoLineGap=0,
                usWinAscent=990, usWinDescent=290, sxHeight=470, sCapHeight=700,
                usWeightClass=400, usWidthClass=5, fsType=0, fsSelection=0xC0,
                achVendID='CRIN')
    fb.setupPost(italicAngle=-6, underlinePosition=-95, underlineThickness=37)
    fb.setupMaxp()
    fb.font['head'].fontRevision = 0.1
    # Fixed timestamp makes two builds in the same environment byte reproducible.
    fb.font['head'].created = fb.font['head'].modified = 3874348800
    fb.font.recalcTimestamp = False
    features = ['languagesystem DFLT dflt;', 'languagesystem latn dflt;', 'feature kern {']
    all_pairs = {}
    for (left, right), value in KERN_PAIRS.items():
        lefts = [c for c, s in shapes.items() if s.base == left and len(c) == 1 and c.isalpha()]
        rights = [c for c, s in shapes.items() if s.base == right and len(c) == 1 and c.isalpha()]
        for a in lefts:
            for b in rights:
                all_pairs[glyph_name(a), glyph_name(b)] = value
    for (left, right), value in all_pairs.items():
        features.append(f'  pos {left} {right} {value};')
    features.append('} kern;')
    top_marks = [c for c in ACCENTS if c not in ('\u0327', '\u0328')]
    for c in top_marks:
        features.append(f'markClass {glyph_name(c)} <anchor 0 0> @TOP;')
    for c in ('\u0327', '\u0328'):
        features.append(f'markClass {glyph_name(c)} <anchor 0 0> @BOTTOM;')
    features.append('feature mark {')
    for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzı':
        shape = shapes[c]
        y = 757 if c.isupper() else (782 if c in 'bdfhkl' else 540)
        features.append(f'  pos base {glyph_name(c)} <anchor {round(shape.advance/2+28)} {y}> mark @TOP <anchor {round(shape.advance/2)} -15> mark @BOTTOM;')
    features.append('} mark;')
    addOpenTypeFeaturesFromString(fb.font, '\n'.join(features))
    # Grayscale rasterization at every size; no invented TrueType hint program.
    gasp = newTable('gasp')
    gasp.gaspRange = {65535: 15}
    fb.font['gasp'] = gasp
    ttf = OUT / 'CartaRinascente-Regular.ttf'
    fb.save(ttf)
    web = TTFont(ttf, recalcTimestamp=False)
    web.flavor = 'woff2'
    web.save(OUT / 'CartaRinascente-Regular.woff2')
    metadata = {
        'family': FAMILY, 'version': VERSION, 'style': 'Regular',
        'glyphs': len(order), 'encoded_characters': len(shapes),
        'kerning_pairs': len(all_pairs), 'units_per_em': UPM,
        'characters': ''.join(sorted(shapes, key=ord)),
        'codepoints': [f'U+{ord(c):04X}' for c in sorted(shapes, key=ord)],
        'source': 'Independent pen paths in build_font.py; no input font.',
        'license': 'SIL Open Font License 1.1; no Reserved Font Names',
    }
    # JSON uses ASCII escapes to keep invisible characters explicit.
    (OUT / 'metadata.json').write_text(json.dumps(metadata, ensure_ascii=True, indent=2) + '\n')
    print(json.dumps({k: v for k, v in metadata.items() if k not in ('characters', 'codepoints')}, indent=2))
    for path in (ttf, OUT / 'CartaRinascente-Regular.woff2'):
        print(f'{path.name}: {path.stat().st_size:,} bytes')


if __name__ == '__main__':
    build()
