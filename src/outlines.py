"""Convert original polygon geometry into smooth, correctly wound TrueType contours.

The drawing code produces dense polygons. Each ring is divided at its real
corners and long straight edges, then the curved runs between them are fitted
with a few cubic segments and exported as quadratic splines.

Copyright (c) 2026, Carta Rinascente contributors.
SPDX-License-Identifier: OFL-1.1
"""

import math

from fontTools.agl import UV2AGL
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._g_l_y_f import Glyph
from shapely.geometry.base import BaseGeometry
from shapely.geometry.polygon import orient

type Point = tuple[float, float]
type Cubic = tuple[Point, Point, Point, Point]

# Design units. The fit stays well below one exported unit of the drawn shape.
FIT_TOLERANCE = 0.42
CORNER_DEGREES = 26.0
STRAIGHT_LENGTH = 34.0
_REDUCTION = 0.06


def glyph_name(char: str) -> str:
    return UV2AGL.get(ord(char), f"uni{ord(char):04X}")


def _sub(a: Point, b: Point) -> Point:
    return (a[0] - b[0], a[1] - b[1])


def _unit(vector: Point) -> Point:
    length = math.hypot(*vector)
    return (vector[0] / length, vector[1] / length) if length else (0.0, 0.0)


def _dot(a: Point, b: Point) -> float:
    return a[0] * b[0] + a[1] * b[1]


def _bezier(curve: Cubic, t: float) -> Point:
    s = 1 - t
    a, b, c, d = s * s * s, 3 * s * s * t, 3 * s * t * t, t * t * t
    return (a * curve[0][0] + b * curve[1][0] + c * curve[2][0] + d * curve[3][0],
            a * curve[0][1] + b * curve[1][1] + c * curve[2][1] + d * curve[3][1])


def _chord_parameters(points: list[Point]) -> list[float]:
    values = [0.0]
    for a, b in zip(points, points[1:]):
        values.append(values[-1] + math.dist(a, b))
    return [value / values[-1] for value in values]


def _generate(points: list[Point], u: list[float], t1: Point, t2: Point) -> Cubic:
    """Least-squares cubic with fixed end points and tangent directions."""
    first, last = points[0], points[-1]
    c00 = c01 = c11 = x0 = x1 = 0.0
    for point, t in zip(points, u):
        s = 1 - t
        b1, b2 = 3 * s * s * t, 3 * s * t * t
        a1 = (t1[0] * b1, t1[1] * b1)
        a2 = (t2[0] * b2, t2[1] * b2)
        c00 += _dot(a1, a1)
        c01 += _dot(a1, a2)
        c11 += _dot(a2, a2)
        b0, b3 = s * s * s + b1, t * t * t + b2
        rest = (point[0] - first[0] * b0 - last[0] * b3, point[1] - first[1] * b0 - last[1] * b3)
        x0 += _dot(a1, rest)
        x1 += _dot(a2, rest)
    determinant = c00 * c11 - c01 * c01
    chord = math.dist(first, last)
    if abs(determinant) > 1e-12:
        alpha1 = (x0 * c11 - x1 * c01) / determinant
        alpha2 = (c00 * x1 - c01 * x0) / determinant
    else:
        alpha1 = alpha2 = 0.0
    if alpha1 < chord * 1e-3 or alpha2 < chord * 1e-3 or max(alpha1, alpha2) > chord * 4:
        alpha1 = alpha2 = chord / 3
    return (first, (first[0] + t1[0] * alpha1, first[1] + t1[1] * alpha1),
            (last[0] + t2[0] * alpha2, last[1] + t2[1] * alpha2), last)


def _reparameterize(curve: Cubic, points: list[Point], u: list[float]) -> list[float]:
    """One Newton step toward each point's closest curve parameter."""
    d1 = [(3 * (b[0] - a[0]), 3 * (b[1] - a[1])) for a, b in zip(curve, curve[1:])]
    d2 = [(2 * (b[0] - a[0]), 2 * (b[1] - a[1])) for a, b in zip(d1, d1[1:])]
    result = []
    for point, t in zip(points, u):
        s = 1 - t
        position = _bezier(curve, t)
        first = (s * s * d1[0][0] + 2 * s * t * d1[1][0] + t * t * d1[2][0],
                 s * s * d1[0][1] + 2 * s * t * d1[1][1] + t * t * d1[2][1])
        second = (s * d2[0][0] + t * d2[1][0], s * d2[0][1] + t * d2[1][1])
        delta = _sub(position, point)
        denominator = _dot(first, first) + _dot(delta, second)
        result.append(min(1.0, max(0.0, t - _dot(delta, first) / denominator)) if denominator else t)
    return result


def _max_error(curve: Cubic, points: list[Point], u: list[float]) -> tuple[float, int]:
    worst, split = 0.0, len(points) // 2
    for index in range(1, len(points) - 1):
        position = _bezier(curve, u[index])
        distance = (position[0] - points[index][0]) ** 2 + (position[1] - points[index][1]) ** 2
        if distance >= worst:
            worst, split = distance, index
    return worst, split


def fit_cubics(points: list[Point], t1: Point, t2: Point,
               tolerance: float = FIT_TOLERANCE) -> list[Cubic]:
    """Fit a smooth open run; t1 leaves the first point and t2 leaves the last one."""
    if len(points) == 2:
        reach = math.dist(points[0], points[1]) / 3
        return [(points[0], (points[0][0] + t1[0] * reach, points[0][1] + t1[1] * reach),
                 (points[1][0] + t2[0] * reach, points[1][1] + t2[1] * reach), points[1])]
    u = _chord_parameters(points)
    curve = _generate(points, u, t1, t2)
    error, split = _max_error(curve, points, u)
    limit = tolerance * tolerance
    if error < limit:
        return [curve]
    if error < limit * 16:
        for _ in range(6):
            u = _reparameterize(curve, points, u)
            curve = _generate(points, u, t1, t2)
            error, split = _max_error(curve, points, u)
            if error < limit:
                return [curve]
    # Tangent of the circle through the split point and its uneven neighbours.
    before, here, after = points[split - 1], points[split], points[split + 1]
    h1, h2 = math.dist(before, here), math.dist(here, after)
    center = _unit(((before[0] - here[0]) * h2 / h1 + (here[0] - after[0]) * h1 / h2,
                    (before[1] - here[1]) * h2 / h1 + (here[1] - after[1]) * h1 / h2))
    return (fit_cubics(points[:split + 1], t1, center, tolerance)
            + fit_cubics(points[split:], (-center[0], -center[1]), t2, tolerance))


def _end_tangent(a: Point, b: Point, c: Point | None) -> Point:
    """Direction leaving a toward b, corrected for curvature using the next point."""
    h1 = math.dist(a, b)
    first = ((b[0] - a[0]) / h1, (b[1] - a[1]) / h1)
    if c is None:
        return first
    h2 = math.dist(b, c)
    if not h2:
        return first
    second = ((c[0] - b[0]) / h2, (c[1] - b[1]) / h2)
    if _dot(first, second) < math.cos(math.radians(CORNER_DEGREES)):
        return first
    w1, w2 = (2 * h1 + h2) / (h1 + h2), h1 / (h1 + h2)
    return _unit((first[0] * w1 - second[0] * w2, first[1] * w1 - second[1] * w2))


def ring_segments(coordinates: list[Point]) -> list[tuple]:
    """Describe a closed ring as ('line', end) and ('curve', c1, c2, end) segments."""
    points = [coordinates[0]]
    for point in coordinates[1:]:
        if math.dist(point, points[-1]) > 0.02:
            points.append(point)
    if len(points) > 1 and math.dist(points[0], points[-1]) <= 0.02:
        points.pop()
    count = len(points)
    if count < 3:
        return []
    lengths = [math.dist(points[i], points[(i + 1) % count]) for i in range(count)]
    directions = [_unit(_sub(points[(i + 1) % count], points[i])) for i in range(count)]
    threshold = math.cos(math.radians(CORNER_DEGREES))
    corner = [_dot(directions[i - 1], directions[i]) < threshold for i in range(count)]
    straight = [length >= STRAIGHT_LENGTH for length in lengths]
    breaks = [i for i in range(count) if corner[i] or straight[i] or straight[i - 1]]
    if not breaks:
        # A fully smooth ring: open it at its rightmost point.
        start = max(range(count), key=lambda i: points[i])
        breaks = [start]
    segments: list[tuple] = []
    for index, start in enumerate(breaks):
        end = breaks[(index + 1) % len(breaks)]
        span = (end - start) % count or count
        run = [points[(start + offset) % count] for offset in range(span + 1)]
        if span == 1:
            segments.append(('line', run[-1]))
            continue
        chord = _unit(_sub(run[-1], run[0])) if run[-1] != run[0] else (0.0, 0.0)
        if chord != (0.0, 0.0) and all(
                abs((p[0] - run[0][0]) * chord[1] - (p[1] - run[0][1]) * chord[0]) < 0.2 for p in run[1:-1]):
            segments.append(('line', run[-1]))
            continue
        if len(breaks) == 1:
            before, here, after = points[start - 1], points[start], points[(start + 1) % count]
            h1, h2 = math.dist(before, here), math.dist(here, after)
            t1 = _unit(((here[0] - before[0]) * h2 / h1 + (after[0] - here[0]) * h1 / h2,
                        (here[1] - before[1]) * h2 / h1 + (after[1] - here[1]) * h1 / h2))
            t2 = (-t1[0], -t1[1])
        else:
            if not corner[start] and straight[start - 1]:
                t1 = directions[start - 1]
            else:
                t1 = _end_tangent(run[0], run[1], run[2] if len(run) > 2 else None)
            if not corner[end] and straight[end]:
                t2 = (-directions[end][0], -directions[end][1])
            else:
                t2 = _end_tangent(run[-1], run[-2], run[-3] if len(run) > 2 else None)
        for curve in fit_cubics(run, t1, t2):
            segments.append(('curve', curve[1], curve[2], curve[3]))
    return segments


def glyph_outline(geometry: BaseGeometry) -> Glyph:
    pen = TTGlyphPen(None)
    if geometry.is_empty:
        return pen.glyph()
    curves = Cu2QuPen(pen, max_err=0.35, reverse_direction=False)
    geometry = geometry.buffer(0).simplify(_REDUCTION, preserve_topology=True)
    polygons = [geometry] if geometry.geom_type == "Polygon" else list(geometry.geoms)
    for polygon in polygons:
        if polygon.area < 0.75:
            continue
        if polygon.geom_type != "Polygon":
            raise ValueError(f"Unexpected outline geometry: {polygon.geom_type}")
        polygon = orient(polygon, sign=-1)
        for ring in [polygon.exterior, *polygon.interiors]:
            coordinates = [(float(x), float(y)) for x, y in ring.coords[:-1]]
            segments = ring_segments(coordinates)
            if len(segments) < 2 and not any(segment[0] == 'curve' for segment in segments):
                continue
            start = segments[-1][-1]
            curves.moveTo(start)
            for segment in segments:
                if segment[0] == 'line':
                    curves.lineTo(segment[1])
                else:
                    curves.curveTo(*segment[1:])
            curves.closePath()
    return pen.glyph()
