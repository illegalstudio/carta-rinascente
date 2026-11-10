"""Original text roman: modulated strokes, fine bracketed serifs and soft terminals.

Round forms are written with a slightly rotated broad nib, so curves swell and
thin on an inclined axis. Diagonals, arms and serifs are constructed contours
with crisp joints. Every coordinate here is original to this project.

Copyright (c) 2026, Carta Rinascente contributors.
SPDX-License-Identifier: OFL-1.1
"""

import math

from shapely.affinity import scale, translate
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from ..geometry import Drop, FilledPath, GlyphBuilder, PenStroke, Raw, Shape, dot, sample_path

X_HEIGHT = 500
CAP_HEIGHT = 700
ASCENDER = 736
DESCENDER = -212
OVERSHOOT = 10
CAP_WEIGHT = 1.07

# Unload the nib where a branch leaves a stem, then restore the full crown.
SHOULDER = ((0, 0.3), (0.1, 0.5), (0.24, 1), (1, 1))
# Bowls meet their stem lightly at both ends.
BOWL_JOINS = ((0, 0.42), (0.14, 1), (0.7, 1), (0.9, 0.5), (1, 0.32))
LEFT_BOWL_JOINS = ((0, 0.36), (0.13, 1), (0.74, 1), (0.92, 0.62), (1, 0.5))
# The spine of s carries the weight; its arcs and sheared ends stay light.
SPINE = ((0, 0.42), (0.07, 0.8), (0.3, 0.84), (0.5, 1.5), (0.7, 0.84), (0.93, 0.8), (1, 0.42))
# The bowl of a: light where it leaves and rejoins the stem, full on its left side.
A_BOWL = ((0, 0.42), (0.1, 1), (0.78, 1), (0.93, 0.5), (1, 0.32))
# A fine entry that grows out of a teardrop terminal.


class Kit:
    """Weight-aware measures and shared parts for one roman face."""

    def __init__(self, builder: GlyphBuilder):
        self.builder = builder
        self.w = builder.style.pen_scale
        self.s, self.v = builder.roman_nib()
        self.S, self.V = builder.roman_nib(CAP_WEIGHT)
        # Constructed hairlines, thick diagonals and serif proportions.
        self.hair = 23.5 * self.w
        self.thick = 2.16 * self.s
        self.THICK = 2.16 * self.S
        self.reach = 36 * self.w ** 0.5
        self.lip = 11.5 * self.w ** 0.5
        # Pressure in the neck behind a teardrop: heavier faces pinch more, so the head still reads.
        self.neck = 0.62 * (1.3 / self.w) ** 0.6
        # The stroke swells again from the neck to its rounded end, like a drop of ink.
        self.swell = min(0.74, self.neck + 0.12)
        self.from_drop = ((0, self.swell), (0.07, self.neck), (0.24, 1), (1, 1))
        # Centre lines that put round tops and bottoms on their overshoot.
        self.top = X_HEIGHT + OVERSHOOT - self.v
        self.bottom = -OVERSHOOT + self.v
        self.cap_top = CAP_HEIGHT + OVERSHOOT - self.V
        self.cap_bottom = -OVERSHOOT + self.V
        self.figure_top = CAP_HEIGHT + OVERSHOOT - self.v
        # Centre lines of level hairlines lying exactly on a guide line.
        self.cap_high = CAP_HEIGHT - self.V
        self.cap_low = self.V

    def serif(self, x: float, y: float = 0, *, top: bool = False, left: float = 1.0,
              right: float = 1.0, half: float | None = None, lean: float = 0.0) -> FilledPath:
        """A fine level serif with long concave brackets and a faintly cupped base.

        lean is the horizontal run per unit of height of a diagonal stroke; the
        brackets then follow the diagonal instead of an upright stem.
        """
        s = self.s if half is None else half
        direction = -1 if top else 1
        rise = (34 if lean else 56) * self.w ** 0.3
        xl, xr = x - s - self.reach * left, x + s + self.reach * right
        a, m, c = y + direction * self.lip, y + direction * rise * 0.46, y + direction * rise
        # Only a full foot under an upright stem is cupped; small and leaning serifs stay level.
        cup = y + direction * (3 if left and right and not lean and s >= self.s * 0.9 else 0)
        shift = lean * direction * rise
        return FilledPath(
            f"M {xl} {y} Q {x} {cup} {xr} {y} L {xr} {a} "
            f"C {x + s + self.reach * right * 0.5} {a + direction * 2} "
            f"{x + s + shift * 0.46 + self.reach * right * 0.07} {m} {x + s + shift} {c} "
            f"L {x - s + shift} {c} C {x - s + shift * 0.46 - self.reach * left * 0.07} {m} "
            f"{x - s - self.reach * left * 0.5} {a + direction * 2} {xl} {a} Z")

    def head(self, x: float, y: float) -> FilledPath:
        """A wedge entry for lowercase stems: the peak is at the right edge."""
        s = self.s
        flag = 31 * self.w ** 0.5
        tip_x, tip_y = x - s - flag, y - 42
        under = tip_y - self.lip
        return FilledPath(
            f"M {x + s} {y - 96} L {x + s} {y - 7} Q {x + s} {y} {x + s - 9} {y - 1} "
            f"C {x - s * 0.2} {y - 9} {x - s - flag * 0.45} {tip_y + 12} {tip_x} {tip_y} "
            f"L {tip_x} {under} C {x - s - flag * 0.45} {under} {x - s} {under - 12} {x - s} {y - 84} "
            f"L {x - s} {y - 96} Z")

    def terminal(self, x: float, y: float, dx: float, dy: float, side: int,
                 radius: float = 23, neck: float = 16, blend: float = 16) -> Drop:
        """A teardrop closing a stroke that arrives at (x, y) travelling along (dx, dy).

        The round head sits to one side of the stroke (+1 left of travel, -1 right),
        so the stroke's far edge runs into the head and its near edge swells in a fillet.
        """
        # Heavier faces keep the head a little smaller, so it clears nearby strokes.
        radius *= (1.3 / self.w) ** 0.4
        length = math.hypot(dx, dy)
        dx, dy = dx / length, dy / length
        nx, ny = -dy * side, dx * side
        offset, forward = (radius - neck) * 0.25 * self.w, radius * 0.1 * self.w
        cx, cy = x + nx * offset + dx * forward, y + ny * offset + dy * forward
        return Drop(cx, cy, radius, cx, cy, radius, blend)

    def stem(self, x: float, top: float, bottom: float = 0, weight: float = 1.0) -> PenStroke:
        """A stem whose ends hide inside its serifs."""
        return PenStroke(f"M {x} {top - 34} L {x} {bottom + 30}", weight)

    def shoulder(self, x0: float, x1: float, bottom: float = 30) -> PenStroke:
        """An arch branching deep in the left stem and swelling into the right one."""
        d = x1 - x0
        t = self.top
        return PenStroke(
            f"M {x0} 368 C {x0 + 0.09 * d} 448 {x0 + 0.32 * d} {t} {x0 + 0.59 * d} {t} "
            f"C {x1 - 0.1 * d} {t} {x1} 432 {x1} 338 L {x1} {bottom}", pressure=SHOULDER)

    def leg(self, x0: float, y0: float, x1: float, y1: float, width: float) -> Polygon:
        """A diagonal with level ends, centred on both points."""
        h = width / 2
        return Polygon([(x0 - h, y0), (x0 + h, y0), (x1 + h, y1), (x1 - h, y1)])

    def vee(self, xa: float, xb: float, xp: float, y0: float, y1: float,
            wa: float, wb: float, flat: float = 14) -> Polygon:
        """Two diagonals meeting in a narrow vertex at y1, open at y0."""
        la, lb = xp - flat / 2, xp + flat / 2
        # Inner edges are the outer edges moved inward by each stroke's width.
        ta = (la - xa) / (y1 - y0)
        tb = (lb - xb) / (y1 - y0)
        y = y0 + (xb - wb - xa - wa) / (ta - tb)
        crotch = (xa + wa + ta * (y - y0), y)
        return Polygon([(xa, y0), (xa + wa, y0), crotch, (xb - wb, y0), (xb, y0), (lb, y1), (la, y1)])

    def tick(self, x: float, y: float, reach: float = 50) -> FilledPath:
        """Close a middle arm with a small flared serif."""
        h = self.hair / 2
        return FilledPath(
            f"M {x - 58} {y + h} C {x - 30} {y + h} {x - 13} {y + reach * 0.5} {x - 10} {y + reach} "
            f"L {x + 4} {y + reach} L {x + 4} {y - reach} L {x - 10} {y - reach} "
            f"C {x - 13} {y - reach * 0.5} {x - 30} {y - h} {x - 58} {y - h} Z")

    def arm(self, x0: float, x1: float, y: float, *, beak: float = 0,
            thickness: float | None = None) -> Polygon:
        """A level hairline from x0 to x1; a beak rises (+) or hangs (-) at x1.

        Without a beak, y is the arm's centre line. With one, y is its outer edge.
        """
        h = self.hair if thickness is None else thickness
        if not beak:
            return box(min(x0, x1), y - h / 2, max(x0, x1), y + h / 2)
        d = 1 if x1 > x0 else -1
        inner = y + h * (1 if beak > 0 else -1)
        tip = y + beak
        run = min(abs(x1 - x0) * 0.55, abs(beak) * 1.15)
        return Polygon(sample_path(
            f"M {x0} {y} L {x1} {y} L {x1 + d * 5} {tip} L {x1 - d * self.lip * 0.9} {tip} "
            f"C {x1 - d * (self.lip * 0.9 + 3)} {inner + (tip - inner) * 0.42} "
            f"{x1 - d * (self.lip + run * 0.4)} {inner} {x1 - d * (self.lip + run)} {inner} "
            f"L {x0} {inner} Z", 2.0))


def _clip(geometry, low: float = -2000, high: float = 2000):
    return geometry.intersection(box(-3000, low, 5000, high))


def draw(builder: GlyphBuilder) -> None:
    add = builder.add
    k = Kit(builder)
    n, sw = k.neck, k.swell
    serif, head, stem, shoulder = k.serif, k.head, k.stem, k.shoulder
    s, v, S, hair = k.s, k.v, k.S, k.hair
    T, B = k.top, k.bottom
    xh, cap, asc, desc = X_HEIGHT, CAP_HEIGHT, ASCENDER, DESCENDER
    peak = xh + 8

    # ---- lowercase -------------------------------------------------------
    lift = 398 + 34 * (k.w - 1.3)
    add('a', PenStroke(f'M 94 {lift} C 96 {lift + 70} 148 {T} 222 {T} C 306 {T} 356 454 356 362 '
                       f'L 356 96 C 356 38 388 {B + 8} 436 44',
                       pressure=((0, sw), (0.06, n), (0.2, 1), (0.9, 1), (1, 0.62))),
        k.terminal(94, lift, -2, -70, 1),
        PenStroke(f'M 356 292 C 290 300 210 298 152 276 C 100 256 80 208 80 148 '
                  f'C 80 56 132 {B} 208 {B} C 272 {B} 326 30 356 86', pressure=A_BOWL))
    add('b', PenStroke(f'M 112 {asc - 34} L 112 44'), Raw(box(112 - s, 0, 112 + s, 60)), head(112, asc),
        PenStroke(f'M 112 366 C 150 448 226 {T} 298 {T} C 398 {T} 460 398 460 250 '
                  f'C 460 102 392 {B} 292 {B} C 218 {B} 156 42 112 104', pressure=LEFT_BOWL_JOINS))
    add('c', PenStroke(f'M 424 388 C 412 458 352 {T} 272 {T} C 152 {T} 78 394 78 250 '
                       f'C 78 104 152 {B} 274 {B} C 350 {B} 404 40 440 104',
                       pressure=((0, sw), (0.06, n), (0.17, 1), (0.92, 1), (1, 0.55))),
        k.terminal(424, 388, 12, -70, -1))
    add('d', PenStroke(f'M 424 388 C 380 456 310 {T} 240 {T} C 140 {T} 76 394 76 250 '
                       f'C 76 104 140 {B} 236 {B} C 312 {B} 376 50 424 132', pressure=BOWL_JOINS),
        stem(424, asc), head(424, asc), serif(424, left=0))
    add('e', PenStroke(f'M 84 292 L 446 292 C 446 420 378 {T} 264 {T} C 146 {T} 76 392 76 250 '
                       f'C 76 102 150 {B} 276 {B} C 352 {B} 410 38 448 102',
                       pressure=((0, 1), (0.93, 1), (1, 0.55))))
    f_top = asc + 14 - v
    # The heavier hook reaches further, so its terminal clears the stem.
    reach = 46 * (k.w - 1.3)
    add('f', PenStroke(f'M 138 30 L 138 566 C 138 678 196 {f_top} {266 + reach} {f_top} C {302 + reach} {f_top} {326 + reach} 728 {338 + reach} 702',
                       pressure=((0, 1), (0.89, 1), (0.955, n), (1, sw))),
        k.terminal(338 + reach, 702, 12, -26, -1, 22),
        Raw(k.arm(54, 306, xh - hair / 2)), serif(138))
    loop = desc + v
    add('g', f'M 232 {T} C 142 {T} 86 432 86 340 C 86 248 142 184 232 184 '
             f'C 322 184 378 248 378 340 C 378 432 322 {T} 232 {T} Z',
        PenStroke(f'M 336 454 C 366 484 404 {T + 2} 446 {T - 2}', 0.62),
        k.terminal(446, T - 2, 40, -8, -1, 19, 6, 8),
        PenStroke('M 190 200 C 140 182 110 150 120 118 C 130 86 192 70 258 70', 0.86,
                  pressure=((0, 0.6), (0.3, 1), (1, 1))),
        f'M 258 70 C 384 70 448 22 448 -62 C 448 -148 366 {loop} 248 {loop} '
        f'C 128 {loop} 60 -158 60 -98 C 60 -22 134 70 258 70 Z')
    add('h', stem(112, asc), head(112, asc), serif(112), shoulder(112, 441), serif(441))
    stem_i = (stem(112, peak), head(112, peak), serif(112))
    add('i', *stem_i, dot(112, 668, 1.22), bearing=61)
    add('ı', *stem_i, bearing=61)
    low = desc - 4 + v
    stem_j = (PenStroke(f'M 112 {peak - 34} L 112 -62 C 112 -152 62 {low} 6 {low} C -24 {low} -46 -196 -58 -172',
                        pressure=((0, 1), (0.89, 1), (0.955, n), (1, sw))),
              k.terminal(-58, -172, -12, 24, -1, 22), head(112, peak))
    add('j', *stem_j, dot(112, 668, 1.22))
    add('ȷ', *stem_j)
    add('k', stem(112, asc), head(112, asc), serif(112),
        Raw(k.leg(414, xh, 146, 226, hair * 1.42)),
        Raw(k.leg(240, 360, 458, 0, k.thick * 1.12).difference(
            Polygon([(146 + hair * 0.7, 226), (414 + hair * 0.7, xh), (-400, xh), (-400, 226)]))),
        serif(414, xh, top=True, half=hair * 0.5, left=0.8, right=0.8, lean=(414 - 146) / (xh - 226)),
        serif(458, half=s * 1.05, left=0.8, right=0.8, lean=(240 - 458) / 360))
    add('l', stem(112, asc), head(112, asc), serif(112), bearing=61)
    add('m', stem(112, peak), head(112, peak), serif(112), shoulder(112, 402), serif(402),
        shoulder(402, 706), serif(706))
    add('n', stem(112, peak), head(112, peak), serif(112), shoulder(112, 445), serif(445))
    add('o', f'M 267 {T} C 152 {T} 76 394 76 250 C 76 106 152 {B} 267 {B} '
             f'C 382 {B} 458 106 458 250 C 458 394 382 {T} 267 {T} Z')
    add('p', stem(112, peak, desc), head(112, peak), serif(112, desc),
        PenStroke(f'M 112 366 C 150 448 226 {T} 298 {T} C 398 {T} 460 398 460 250 '
                  f'C 460 102 392 {B} 292 {B} C 218 {B} 156 42 112 104', pressure=LEFT_BOWL_JOINS))
    add('q', PenStroke(f'M 424 388 C 380 456 310 {T} 240 {T} C 140 {T} 76 394 76 250 '
                       f'C 76 104 140 {B} 236 {B} C 312 {B} 376 50 424 132', pressure=BOWL_JOINS),
        PenStroke(f'M 424 {xh - v + 4} L 424 {desc + 30}'), serif(424, desc))
    add('r', stem(112, peak), head(112, peak), serif(112),
        PenStroke(f'M 112 366 C 146 446 212 {T} 286 {T} C 328 {T} 352 482 364 456',
                  pressure=((0, 0.3), (0.12, 0.5), (0.3, 1), (0.78, 1), (0.93, n), (1, sw))),
        k.terminal(364, 456, 12, -26, -1))
    add('s', PenStroke(f'M 394 378 C 362 444 318 {T} 238 {T} C 154 {T} 98 452 98 384 '
                       f'C 98 300 172 276 244 250 C 318 224 388 198 388 124 '
                       f'C 388 46 324 {B} 232 {B} C 150 {B} 96 60 62 122',
                       nib_depth=11, pressure=SPINE))
    add('t', PenStroke(f'M 150 {642 - v} L 150 118 C 150 36 196 {B} 250 {B} C 294 {B} 326 28 346 66',
                       pressure=((0, 1), (0.9, 1), (1, 0.55))),
        Raw(k.arm(54, 312, xh - hair / 2)))
    add('u', PenStroke(f'M 112 {peak - 34} L 112 152 C 112 52 166 {B} 242 {B} C 330 {B} 400 60 440 142',
                       pressure=((0, 1), (0.62, 1), (0.84, 0.6), (1, 0.34))),
        head(112, peak), stem(440, peak), head(440, peak), serif(440, left=0))
    feet = dict(top=True, left=0.82, right=0.82)
    add('v', Raw(k.vee(44, 458, 252, xh, -8, k.thick, hair * 1.08)),
        serif(44 + k.thick / 2, xh, half=k.thick / 2, lean=-0.33, **feet),
        serif(458 - hair * 0.54, xh, half=hair * 0.54, lean=0.38, **feet))
    add('w', Raw(_clip(unary_union([k.vee(44, 420, 228, xh, -8, k.thick, hair * 1.08),
                                    k.vee(336, 748, 544, xh, -8, k.thick, hair * 1.08)]), high=xh)),
        serif(44 + k.thick / 2, xh, half=k.thick / 2, lean=-0.29, **feet),
        serif(748 - hair * 0.54, xh, half=hair * 0.54, lean=0.38, **feet))
    add('x', Raw(k.leg(86, xh, 420, 0, k.thick * 1.12)), Raw(k.leg(414, xh, 80, 0, hair * 1.3)),
        serif(86, xh, half=s, lean=-0.668, **feet), serif(414, xh, half=hair * 0.5, lean=0.668, **feet),
        serif(80, half=hair * 0.5, left=0.82, right=0.82, lean=0.668),
        serif(420, half=s, left=0.82, right=0.82, lean=-0.668))
    tail = k.leg(444, xh, 196, -118, hair * 1.08)
    add('y', Raw(k.leg(88, xh, 276, 12, k.thick).difference(
            Polygon([(444 + hair * 0.54, xh), (196 + hair * 0.54, -118), (900, -118), (900, xh)]))),
        Raw(tail),
        PenStroke(f'M 204 -100 C 180 -160 142 {low} 92 {low} C 62 {low} 44 -196 34 -176',
                  0.44, pressure=((0, 0.3), (0.16, 0.86), (1, 1))),
        k.terminal(34, -176, -10, 20, -1, 22),
        serif(88, xh, half=k.thick / 2, lean=-0.385, **feet), serif(444, xh, half=hair * 0.54, lean=0.40, **feet))
    slope = k.thick * 1.08
    add('z', Raw(k.arm(432, 86, xh, beak=-78)),
        Raw(Polygon([(432, xh), (432 - slope, xh), (74, 0), (74 + slope, 0)])),
        Raw(k.arm(74, 446, 0, beak=88)))

    # ---- capitals --------------------------------------------------------
    W = CAP_WEIGHT
    CT, CB, CH, CL = k.cap_top, k.cap_bottom, k.cap_high, k.cap_low
    TH, hw = k.THICK, hair * 1.1

    def cap_stem(x: float, top: float = cap, bottom: float = 0) -> PenStroke:
        return stem(x, top, bottom, W)

    def cap_serif(x: float, y: float = 0, **options) -> FilledPath:
        return serif(x, y, half=S, **options)

    add('A', Raw(k.vee(44, 640, 340, 0, cap + 10, hw, TH)),
        Raw(box(176, 236, 520, 236 + hair)),
        serif(44 + hw / 2, half=hw / 2, lean=0.40), serif(640 - TH / 2, half=TH / 2, lean=-0.36))
    add('B', cap_stem(127), cap_serif(127, cap, top=True, right=0), cap_serif(127, right=0),
        PenStroke(f'M 127 {CH} L 300 {CH} C 426 {CH} 506 632 506 534 C 506 442 424 374 300 374 L 127 374', W),
        PenStroke(f'M 300 374 C 456 374 564 304 564 194 C 564 84 452 {CL} 310 {CL} L 127 {CL}', W))
    add('C', PenStroke(f'M 616 514 C 598 636 494 {CT} 372 {CT} C 202 {CT} 88 562 88 350 '
                       f'C 88 140 202 {CB} 376 {CB} C 484 {CB} 568 58 626 150', W,
                       pressure=((0, 0.3), (0.13, 1), (0.9, 1), (1, 0.5))))
    add('D', cap_stem(127), cap_serif(127, cap, top=True, right=0), cap_serif(127, right=0),
        PenStroke(f'M 127 {CH} L 310 {CH} C 524 {CH} 652 562 652 350 C 652 138 524 {CL} 310 {CL} L 127 {CL}', W))
    add('E', cap_stem(127), cap_serif(127, cap, top=True, right=0), cap_serif(127, right=0),
        Raw(k.arm(127, 574, cap, beak=-92)), Raw(k.arm(127, 456, 362)),
        k.tick(456, 362),
        Raw(k.arm(127, 598, 0, beak=104)))
    add('F', cap_stem(127), cap_serif(127, cap, top=True, right=0), cap_serif(127),
        Raw(k.arm(127, 574, cap, beak=-92)), Raw(k.arm(127, 450, 362)),
        k.tick(450, 362))
    add('G', PenStroke(f'M 612 520 C 594 638 492 {CT} 372 {CT} C 202 {CT} 89 562 89 350 '
                       f'C 89 140 202 {CB} 378 {CB} C 500 {CB} 606 60 606 196 L 606 298', W,
                       pressure=((0, 0.3), (0.11, 1), (1, 1))),
        cap_serif(606, 332, top=True, left=0.95, right=0.7))
    add('H', cap_stem(127), cap_stem(617), Raw(k.arm(127, 617, 360)),
        cap_serif(127), cap_serif(617), cap_serif(127, cap, top=True), cap_serif(617, cap, top=True))
    add('I', cap_stem(127), cap_serif(127), cap_serif(127, cap, top=True), bearing=73)
    add('J', PenStroke(f'M 377 {cap - 34} L 377 164 C 377 60 322 {CB} 242 {CB} C 176 {CB} 122 44 100 104', W,
                       pressure=((0, 1), (0.78, 1), (0.92, n), (1, sw))),
        k.terminal(100, 104, -22, 60, -1, 24), cap_serif(377, cap, top=True))
    add('K', cap_stem(127), cap_serif(127), cap_serif(127, cap, top=True),
        Raw(k.leg(588, cap, 150, 318, hw * 1.5)),
        Raw(k.leg(292, 480, 622, 0, TH * 1.16).difference(
            Polygon([(150 + hw * 0.74, 318), (588 + hw * 0.74, cap), (-400, cap), (-400, 318)]))),
        serif(588, cap, top=True, half=hw * 0.55, left=0.85, right=0.85, lean=(588 - 150) / (cap - 318)),
        serif(622, half=S * 1.1, left=0.85, right=0.85, lean=(292 - 622) / 480))
    add('L', cap_stem(127), cap_serif(127, cap, top=True), cap_serif(127, right=0),
        Raw(k.arm(127, 586, 0, beak=112)))
    add('M', Raw(box(106, 0, 106 + hw, cap)),
        Raw(k.vee(106, 714, 412, cap, 0, TH, hw, flat=10)), cap_stem(714),
        serif(106 + hw / 2, half=hw / 2), cap_serif(714),
        serif(106 + hw / 2, cap, top=True, half=hw / 2, right=0), cap_serif(714, cap, top=True, left=0))
    add('N', Raw(box(110, 0, 110 + hw, cap)), Raw(box(648 - hw, 0, 648, cap)),
        Raw(Polygon([(110, cap), (110 + TH * 1.16, cap), (648, 0), (648 - TH * 1.16, 0)])),
        serif(110 + hw / 2, half=hw / 2), serif(648 - hw / 2, cap, top=True, half=hw / 2),
        serif(110 + hw / 2, cap, top=True, half=hw / 2, right=0))
    oval = (f'M 355 {CT} C 202 {CT} 82 562 82 350 C 82 138 202 {CB} 355 {CB} '
            f'C 508 {CB} 628 138 628 350 C 628 562 508 {CT} 355 {CT} Z')
    add('O', (oval, W))
    add('P', cap_stem(127), cap_serif(127), cap_serif(127, cap, top=True, right=0),
        PenStroke(f'M 127 {CH} L 310 {CH} C 452 {CH} 544 622 544 520 C 544 418 452 344 310 344 L 127 344', W))
    add('Q', (oval, W),
        PenStroke(f'M 318 {CB} C 380 -60 486 -122 668 -88', 0.96,
                  pressure=((0, 0.3), (0.3, 1), (0.7, 1), (1, 0.4))))
    add('R', cap_stem(127), cap_serif(127), cap_serif(127, cap, top=True, right=0),
        PenStroke(f'M 127 {CH} L 310 {CH} C 446 {CH} 532 628 532 532 C 532 436 446 362 310 362 L 127 362', W),
        FilledPath(f'M {300 - TH * 0.5} 358 L {300 + TH * 0.5} 358 '
                   f'L {590 + TH * 0.5} 52 C {602 + TH * 0.5} 30 {620 + TH * 0.5} 16 {646 + TH * 0.5} 12 '
                   f'L {646 + TH * 0.5} 0 L {590 - TH * 0.52} 0 Z'))
    add('S', PenStroke(f'M 562 522 C 522 626 452 {CT} 340 {CT} C 214 {CT} 118 640 118 536 '
                       f'C 118 418 232 384 340 350 C 452 314 556 280 556 176 '
                       f'C 556 62 462 {CB} 328 {CB} C 206 {CB} 122 82 70 178', W,
                       nib_depth=11, pressure=SPINE))
    add('T', cap_stem(359), cap_serif(359),
        Raw(k.arm(359, 674, cap, beak=-96)), Raw(k.arm(359, 44, cap, beak=-96)))
    add('U', PenStroke(f'M 127 {cap - 34} L 127 244 C 127 92 222 {CB} 362 {CB} C 502 {CB} 600 92 600 244 '
                       f'L 600 {cap - 30}', W, pressure=((0, 1), (0.5, 1), (0.66, 0.36), (1, 0.36))),
        cap_serif(127, cap, top=True), serif(600, cap, top=True, half=S * 0.36))
    add('V', Raw(k.vee(44, 668, 356, cap, -8, TH, hw)),
        serif(44 + TH / 2, cap, top=True, half=TH / 2, lean=-0.40), serif(668 - hw / 2, cap, top=True, half=hw / 2, lean=0.43))
    add('W', Raw(_clip(unary_union([k.vee(44, 560, 302, cap, -8, TH, hw),
                                    k.vee(454, 970, 712, cap, -8, TH, hw)]), high=cap)),
        serif(44 + TH / 2, cap, top=True, half=TH / 2, lean=-0.31), serif(970 - hw / 2, cap, top=True, half=hw / 2, lean=0.36))
    add('X', Raw(k.leg(96, cap, 614, 0, TH * 1.14)), Raw(k.leg(606, cap, 88, 0, hw * 1.3)),
        serif(96, cap, top=True, half=S, lean=-0.74), serif(606, cap, top=True, half=hw * 0.55, lean=0.74),
        serif(88, half=hw * 0.55, lean=0.74), serif(614, half=S, lean=-0.74))
    add('Y', Raw(k.vee(38, 676, 357, cap, 318, TH, hw, flat=2 * S)), PenStroke('M 357 330 L 357 30', W),
        serif(38 + TH / 2, cap, top=True, half=TH / 2, lean=-0.72), serif(676 - hw / 2, cap, top=True, half=hw / 2, lean=0.80),
        cap_serif(357))
    add('Z', Raw(k.arm(630, 86, cap, beak=-92)),
        Raw(Polygon([(630, cap), (630 - TH * 1.12, cap), (80, 0), (80 + TH * 1.12, 0)])),
        Raw(k.arm(80, 640, 0, beak=104)))

    extra = 17 if builder.style.weight == 700 else 0
    builder.set_spacing('f', 0, 348 + extra)
    for char in ('j', 'ȷ'):
        builder.set_spacing(char, -126, 257 + extra)


def draw_extended(builder: GlyphBuilder) -> None:
    """Keep less frequent Latin letters consistent with the upright alphabet."""
    add = builder.add
    k = Kit(builder)
    n, sw = k.neck, k.swell
    serif, head, stem = k.serif, k.head, k.stem
    s, v, S = k.s, k.v, k.S
    T, B = k.top, k.bottom
    peak = X_HEIGHT + 8
    eszett_top = ASCENDER + 14 - v
    add('ß', PenStroke(f'M 112 30 L 112 520 C 112 660 176 {eszett_top} 256 {eszett_top} '
                       f'C 336 {eszett_top} 388 692 388 610 C 388 500 252 470 252 390 '
                       f'C 252 300 470 300 470 150 C 470 60 400 {B} 312 {B} C 276 {B} 252 10 236 30',
                       pressure=((0, 1), (0.9, 1), (1, 0.4))), serif(112))
    add('µ', stem(112, peak, DESCENDER), head(112, peak), serif(112, DESCENDER),
        PenStroke(f'M 112 300 L 112 152 C 112 52 166 {B} 242 {B} C 330 {B} 400 60 440 142',
                  pressure=((0, 1), (0.4, 1), (0.75, 0.6), (1, 0.34))),
        stem(440, peak), head(440, peak), serif(440, left=0))
    add('þ', stem(112, ASCENDER, DESCENDER), head(112, ASCENDER), serif(112, DESCENDER),
        PenStroke(f'M 112 366 C 150 448 226 {T} 298 {T} C 398 {T} 460 398 460 250 '
                  f'C 460 102 392 {B} 292 {B} C 218 {B} 156 42 112 104', pressure=LEFT_BOWL_JOINS))
    add('Þ', stem(127, CAP_HEIGHT, 0, CAP_WEIGHT), serif(127, CAP_HEIGHT, top=True, half=S),
        serif(127, half=S),
        PenStroke(f'M 127 {540 - k.V} L 296 {540 - k.V} C 440 {540 - k.V} 536 468 536 362 '
                  f'C 536 256 440 {176 + k.V} 296 {176 + k.V} L 127 {176 + k.V}', CAP_WEIGHT))
    add('ð', f'M 267 {T - 24} C 152 {T - 24} 76 386 76 244 C 76 104 152 {B} 267 {B} '
             f'C 382 {B} 458 104 458 244 C 458 386 382 {T - 24} 267 {T - 24} Z',
        PenStroke(f'M 458 252 C 458 430 380 596 146 {ASCENDER - 6}',
                  pressure=((0, 1), (0.5, 1), (1, 0.55))),
        Raw(k.leg(352, 700, 262, 596, k.hair * 1.5)))
    long_top = ASCENDER + 14 - v
    add('ſ', PenStroke(f'M 138 30 L 138 566 C 138 678 196 {long_top} 266 {long_top} C 302 {long_top} 326 728 338 702',
                       pressure=((0, 1), (0.89, 1), (0.955, n), (1, sw))),
        k.terminal(338, 702, 12, -26, -1, 22), Raw(k.arm(54, 138, X_HEIGHT - k.hair / 2)), serif(138))
    builder.set_spacing('ſ', 0, 348 + (17 if builder.style.weight == 700 else 0))
    hair = k.hair
    # One stem serves both the bowl of a and the eye of e.
    lift = 398 + 34 * (k.w - 1.3)
    add('æ', PenStroke(f'M 84 {lift} C 86 {lift + 70} 140 {T} 212 {T} C 300 {T} 334 448 334 362 L 334 {v}',
                       pressure=((0, sw), (0.07, n), (0.22, 1), (1, 1))),
        k.terminal(84, lift, -2, -70, 1),
        PenStroke(f'M 334 292 C 272 300 198 298 146 276 C 98 256 78 208 78 148 '
                  f'C 78 56 128 {B} 198 {B} C 258 {B} 306 30 334 86', pressure=A_BOWL),
        PenStroke(f'M 334 292 L 650 292 C 650 420 590 {T} 498 {T} C 420 {T} 362 452 334 380',
                  pressure=((0, 1), (0.82, 1), (1, 0.36))),
        PenStroke(f'M 334 300 C 334 110 400 {B} 506 {B} C 572 {B} 620 38 654 102',
                  pressure=((0, 0.5), (0.12, 1), (0.92, 1), (1, 0.55))))
    o, e = builder.glyphs['o'], builder.glyphs['e']
    factor = 0.9
    offset = (o.geometry.bounds[2] - e.geometry.bounds[0]) * factor - 58 * builder.style.pen_scale / 1.3
    builder.glyphs['œ'] = Shape(
        unary_union([scale(o.geometry, xfact=factor, yfact=1, origin=(0, 0)),
                     translate(scale(e.geometry, xfact=factor, yfact=1, origin=(0, 0)), xoff=offset)]),
        round(offset + e.advance * factor), 'œ')
    cap, S, hw = CAP_HEIGHT, k.S, k.hair * 1.1
    add('Æ', Raw(k.leg(430 - hw * 0.6, cap, 50 + hw * 0.6, 0, hw * 1.2)),
        serif(50 + hw * 0.6, half=hw * 0.6, lean=(430 - 50) / cap),
        stem(470, cap, 0, CAP_WEIGHT), serif(470, half=S, left=0.5, right=0),
        Raw(k.arm(418, 800, cap, beak=-92)), Raw(k.arm(470, 688, 362)), k.tick(688, 362),
        Raw(k.arm(470, 824, 0, beak=104)), Raw(box(238, 232, 470, 232 + hair)))


def draw_numerals(builder: GlyphBuilder) -> None:
    """Lining figures at capital height, written with the same pen as the letters."""
    add = builder.add
    k = Kit(builder)
    n, sw = k.neck, k.swell
    s, v, hair = k.s, k.v, k.hair
    NT, NB = k.figure_top, k.bottom
    cap = CAP_HEIGHT
    end = ((0, 1), (0.8, 1), (0.93, n), (1, sw))
    add('0', f'M 250 {NT} C 142 {NT} 72 548 72 350 C 72 152 142 {NB} 250 {NB} '
             f'C 358 {NB} 428 152 428 350 C 428 548 358 {NT} 250 {NT} Z')
    add('1', PenStroke(f'M 250 {cap - 58} L 250 30'), k.serif(250),
        FilledPath(f'M {250 + s} {cap + 4} L {250 + s} {cap - 100} L {250 - s} {cap - 100} L {250 - s} {cap - 78} '
                   f'C {250 - s - 40} {cap - 104} {250 - s - 78} {cap - 124} {250 - s - 112} {cap - 132} '
                   f'L {250 - s - 116} {cap - 132 + k.lip * 1.5} C {250 - s - 50} {cap - 96} {250 + s - 40} {cap - 40} {250 + s} {cap + 4} Z'))
    add('2', PenStroke(f'M 84 532 C 90 640 162 {NT} 248 {NT} C 338 {NT} 404 640 404 536 '
                       f'C 404 372 190 250 76 {hair * 0.6}', pressure=k.from_drop),
        k.terminal(84, 532, -6, -108, 1),
        Raw(k.arm(70, 432, 0, beak=96, thickness=hair * 1.15)))
    add('3', PenStroke(f'M 88 590 C 108 664 168 {NT} 244 {NT} C 330 {NT} 392 652 392 562 '
                       f'C 392 456 312 392 208 388', pressure=((0, sw), (0.07, n), (0.24, 1), (0.8, 1), (1, 0.45))),
        k.terminal(88, 590, -20, -74, 1, 22),
        PenStroke(f'M 208 388 C 334 388 428 318 428 198 C 428 82 342 {NB} 236 {NB} '
                  f'C 152 {NB} 92 44 66 106', pressure=((0, 0.4), (0.1, 1), (0.77, 1), (0.88, n), (1, sw))),
        k.terminal(66, 106, -26, 62, -1))
    add('4', Raw(_clip(unary_union([k.leg(338 + s - hair * 0.7, cap + 20, 40 + hair * 0.7, 196, hair * 1.4),
                                    box(338 - s, 30, 338 + s, cap + 20)]), high=cap)),
        Raw(box(40, 196, 478, 196 + hair * 1.1)), k.serif(338))
    add('5', Raw(k.arm(122, 404, cap, beak=0, thickness=hair * 1.5).intersection(box(0, cap - hair * 1.5, 900, cap))),
        Raw(box(122, cap - hair * 1.5, 404, cap)), Raw(k.leg(122 + hair * 0.6, cap, 104 + hair * 0.6, 396, hair * 1.2)),
        PenStroke(f'M 108 388 C 160 428 212 450 264 450 C 362 450 428 362 428 232 C 428 92 342 {NB} 236 {NB} '
                  f'C 152 {NB} 92 44 66 106', pressure=((0, 0.45), (0.1, 0.8), (0.2, 1), (0.8, 1), (0.9, n), (1, sw))),
        k.terminal(66, 106, -26, 62, -1))
    # 6 and 9 are a closed bowl with a stem that leaves it and thins into its terminal.
    stem_out = ((0, 1), (0.74, 1), (0.9, n), (1, sw))
    add('6', f'M 250 {NB} C 350 {NB} 430 100 430 224 C 430 348 350 436 250 436 '
             f'C 150 436 68 348 68 224 C 68 100 150 {NB} 250 {NB} Z',
        PenStroke(f'M 68 224 C 64 452 124 {NT} 262 {NT} C 330 {NT} 380 670 398 612', pressure=stem_out),
        k.terminal(398, 612, 18, -58, -1, 22))
    add('7', Raw(k.arm(452, 70, cap, beak=-88, thickness=hair * 1.15)),
        Raw(Polygon([(452, cap), (452 - k.thick * 0.9, cap), (164, 0), (164 + k.thick * 1.12, 0)])))
    add('8', f'M 250 {NT} C 162 {NT} 102 642 102 552 C 102 384 428 400 428 190 C 428 82 352 {NB} 250 {NB} '
             f'C 148 {NB} 72 82 72 190 C 72 400 398 384 398 552 C 398 642 338 {NT} 250 {NT} Z')
    add('9', f'M 250 {NT} C 150 {NT} 70 602 70 476 C 70 352 150 264 250 264 '
             f'C 350 264 432 352 432 476 C 432 602 350 {NT} 250 {NT} Z',
        PenStroke(f'M 432 476 C 436 248 376 {NB} 238 {NB} C 170 {NB} 120 30 102 88', pressure=stem_out),
        k.terminal(102, 88, -18, 58, -1, 22))


def draw_symbols(builder: GlyphBuilder) -> None:
    """Upright punctuation and signs that share the roman's stems and hairlines."""
    add = builder.add
    rule = builder.rule
    shapes = builder.glyphs
    k = Kit(builder)
    n, sw = k.neck, k.swell
    s, hair = k.s, k.hair
    FT, NB = k.figure_top, k.bottom
    even = hair * 1.3
    mark = 1.35
    from_drop = ((0, sw), (0.07, n), (0.2, 1), (1, 1))

    add('!', FilledPath(f'M {90 - s * 0.92} 690 Q 90 716 {90 + s * 0.92} 690 '
                        f'L {90 + hair * 0.3} 196 L {90 - hair * 0.3} 196 Z'), dot(90, 38, mark), bearing=52)
    add('?', PenStroke(f'M 70 540 C 76 646 140 {FT} 222 {FT} C 312 {FT} 372 646 372 556 '
                       f'C 372 428 222 404 222 262 L 222 200',
                       pressure=((0, sw), (0.07, n), (0.2, 1), (0.72, 1), (0.9, 0.5), (1, 0.4))),
        k.terminal(70, 540, -6, -106, 1), dot(222, 38, mark))
    curve = ((0, 0.5), (0.25, 1), (0.75, 1), (1, 0.5))
    add('(', PenStroke('M 236 770 C 96 600 96 50 236 -140', 0.84, pressure=curve), bearing=42)
    add(')', PenStroke('M 60 770 C 200 600 200 50 60 -140', 0.84, pressure=curve), bearing=42)
    add('[', Raw(unary_union([box(70, -130, 70 + even, 760), box(70, 760 - hair, 232, 760),
                              box(70, -130, 232, -130 + hair)])), bearing=58)
    add(']', Raw(unary_union([box(232 - even, -130, 232, 760), box(70, 760 - hair, 232, 760),
                              box(70, -130, 232, -130 + hair)])), bearing=36)
    add('{', PenStroke('M 250 760 C 160 760 172 650 172 520 C 172 400 150 330 84 314 '
                       'C 150 298 172 230 172 110 C 172 -20 160 -130 250 -130', 0.74), bearing=34)
    add('}', PenStroke('M 84 760 C 174 760 162 650 162 520 C 162 400 184 330 250 314 '
                       'C 184 298 162 230 162 110 C 162 -20 174 -130 84 -130', 0.74), bearing=34)
    add('|', Raw(box(0, -130, even, 760)), bearing=72)
    tick = (f'M {{x0}} 706 L {{x1}} 706 L {{x3}} 470 L {{x2}} 470 Z')

    def prime(x: float) -> FilledPath:
        return FilledPath(tick.format(x0=x - s * 0.7, x1=x + s * 0.7, x2=x - hair * 0.28, x3=x + hair * 0.28))

    add("'", prime(70), bearing=42)
    add('"', prime(70), prime(70 + s * 1.4 + 58), bearing=42)
    add('/', Raw(k.leg(330, 760, 50, -130, hair * 1.5)), bearing=22)
    add('\\', Raw(k.leg(50, 760, 330, -130, hair * 1.5)), bearing=22)
    add('*', rule('M 160 706 L 160 420', 0.5), rule('M 36 634 L 284 492', 0.5), rule('M 284 634 L 36 492', 0.5))
    add('#', rule('M 196 700 L 136 0', 0.55), rule('M 396 700 L 336 0', 0.55),
        rule('M 40 470 L 490 470', 0.55), rule('M 20 230 L 470 230', 0.55))
    add('+', Raw(unary_union([box(50, 320 - even / 2, 430, 320 + even / 2),
                              box(240 - even / 2, 130, 240 + even / 2, 510)])), bearing=40)
    add('=', Raw(box(50, 400 - even / 2, 430, 400 + even / 2)),
        Raw(box(50, 240 - even / 2, 430, 240 + even / 2)), bearing=40)
    add('-', Raw(box(44, 232, 256, 232 + even * 1.08)), bearing=42)
    add('_', Raw(box(0, -104, 420, -104 + hair)), bearing=0)
    add('<', rule('M 400 520 L 70 320 L 400 120', 0.56), bearing=38)
    add('>', rule('M 70 520 L 400 320 L 70 120', 0.56), bearing=38)
    add('~', rule('M 50 290 C 130 400 230 220 330 330', 0.56))
    add('^', rule('M 60 440 L 215 700 L 370 440', 0.5))
    add('×', rule('M 80 480 L 400 160', 0.56), rule('M 400 480 L 80 160', 0.56))
    add('÷', Raw(box(50, 320 - even / 2, 430, 320 + even / 2)), dot(240, 506, 0.95), dot(240, 134, 0.95),
        bearing=40)
    add('±', Raw(unary_union([box(50, 370 - even / 2, 430, 370 + even / 2),
                              box(240 - even / 2, 196, 240 + even / 2, 544)])),
        Raw(box(50, 40, 430, 40 + even)), bearing=40)
    add('¬', Raw(unary_union([box(50, 380 - even, 430, 380), box(430 - even, 200, 430, 380)])), bearing=40)
    add('%', (f'M 150 {FT} C 92 {FT} 62 632 62 542 C 62 452 92 384 150 384 '
              f'C 208 384 238 452 238 542 C 238 632 208 {FT} 150 {FT} Z', 0.6),
        (f'M 480 316 C 422 316 392 248 392 158 C 392 68 422 {NB} 480 {NB} '
         f'C 538 {NB} 568 68 568 158 C 568 248 538 316 480 316 Z', 0.6),
        Raw(k.leg(506, 712, 124, -12, hair * 1.3)))
    add('&', PenStroke(f'M 612 22 C 500 70 250 430 250 566 C 250 650 292 {FT} 346 {FT} '
                       f'C 400 {FT} 436 656 436 600 C 436 470 96 410 96 196 C 96 82 176 {NB} 296 {NB} '
                       f'C 440 {NB} 530 150 566 344',
                       pressure=((0, 0.45), (0.06, 1), (0.9, 1), (1, 0.7))),
        Raw(box(486, 344, 660, 344 + hair)))
    add('@', ('M 336 478 C 254 478 200 414 200 324 C 200 238 252 180 322 180 '
              'C 394 180 444 242 444 332 C 444 422 404 478 336 478 Z', 0.68),
        PenStroke('M 446 486 L 446 258 C 446 196 482 172 524 182 C 596 200 648 284 648 384 '
                  'C 648 566 524 690 352 690 C 172 690 60 548 60 332 C 60 108 182 -24 364 -24 '
                  'C 446 -24 516 -2 578 40', 0.62))
    add('£', PenStroke(f'M 420 548 C 404 640 356 {FT} 296 {FT} C 216 {FT} 176 640 176 540 '
                       f'L 176 210 C 176 120 140 56 84 30', pressure=from_drop),
        k.terminal(420, 548, 16, -92, -1), Raw(k.arm(60, 452, 0, beak=84, thickness=hair * 1.2)),
        Raw(box(70, 330, 360, 330 + hair)))

    def derived(char: str, base: str, xfact: float, yfact: float, lift: float, extra: list, pad: float = 0) -> None:
        original = shapes[base]
        geometry = translate(scale(original.geometry, xfact=xfact, yfact=yfact, origin=(0, 0)),
                             xoff=pad, yoff=lift)
        x0, _, x1, _ = geometry.bounds
        middle = (x0 + x1) / 2
        parts = [geometry, *(translate(part, xoff=middle) for part in extra)]
        shapes[char] = Shape(unary_union(parts), round(original.advance * xfact + pad * 2), char)

    derived('$', 'S', 0.84, 0.9, 34, [box(-hair / 2, -74, hair / 2, 774)])
    derived('€', 'C', 0.8, 1.0, 0, [box(-262, 396, 60, 396 + hair), box(-262, 286, 30, 286 + hair)], pad=14)
    derived('¥', 'Y', 0.8, 1.0, 0, [box(-170, 300, 170, 300 + hair), box(-170, 186, 170, 186 + hair)])
    derived('¢', 'c', 1.0, 1.0, 0, [box(12 - hair / 2, -84, 12 + hair / 2, 592)])
    for char, base in (('¡', '!'), ('¿', '?')):
        original = shapes[base]
        shapes[char] = Shape(scale(original.geometry, xfact=-1, yfact=-1, origin=(original.advance / 2, 244)),
                             original.advance, char)
