"""Strict path sampling, broad-nib geometry and per-face glyph construction.

Copyright (c) 2026, Carta Rinascente contributors.
SPDX-License-Identifier: OFL-1.1
"""

from dataclasses import dataclass, replace
import math
import re

from shapely import transform
from shapely.affinity import affine_transform, translate
from shapely.geometry import LineString, MultiPoint, Point as GeometryPoint, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from .config import DESIGN_CAP_HEIGHT, DESIGN_X_HEIGHT, Style

type Point = tuple[float, float]
type Tips = tuple[float, float]
type PressureProfile = tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class FilledPath:
    """An original closed contour, used for bracketed serifs and terminals."""

    path: str


@dataclass(frozen=True)
class RoundDot:
    """A round ink mark, independent of the broad nib's angle."""

    x: float
    y: float
    weight: float = 1.0


@dataclass(frozen=True)
class Drop:
    """A teardrop terminal: a round head drawn out into a hairline tail.

    Radii are in pen units and scale with the style's weight.
    """

    x: float
    y: float
    radius: float
    tail_x: float
    tail_y: float
    tail_radius: float = 7.0
    # Radius, in pen units, of the fillet that melts the head into its stroke.
    blend: float = 0.0


@dataclass(frozen=True)
class Raw:
    """Finished geometry in design coordinates, for constructed diagonals and arms."""

    geometry: BaseGeometry


@dataclass(frozen=True)
class PenStroke:
    """A nib-depth override and smooth pressure stops along normalized path distance.

    Depth strengthens a hairline without widening a vertical stem. Pressure
    scales the whole nib locally and multiplies the style's terminal taper.
    """

    path: str
    weight: float = 1.0
    nib_depth: float | None = None
    pressure: PressureProfile = ()
    tips: Tips | None = None


type Stroke = (str | tuple[str, float] | tuple[str, float, Tips] | FilledPath | RoundDot | PenStroke
               | Drop | Raw)

_TOKEN = re.compile(r"[MLCQZ]|[+-]?(?:\d+(?:\.\d*)?|\.\d+)")
_ARITY = {"M": 2, "L": 2, "Q": 4, "C": 6, "Z": 0}
_ITALIC_PATH_X_HEIGHT = 470
# The roman pen is held almost level: a slight rotation gives an inclined
# stress, and a shallow nib gives fine hairlines beside full stems.
ROMAN_NIB_ANGLE = 10.0
ROMAN_NIB_DEPTH = 9.0
ROMAN_CORNER_RADIUS = 4.0
ITALIC_CORNER_RADIUS = 7.0
ITALIC_CORNER_TRIM = 3.0
ITALIC_NIB_DEPTH = 8.5
# Italic strokes enter and leave on a fine point instead of a blunt nib cut.
ITALIC_TIPS = (0.34, 0.16)
# An italic stroke end this close to another stroke's centre line is a junction.
JUNCTION_REACH = 24.0
RULE_NIB_DEPTH = 19.0
NIB_SEGMENTS = 96


def raise_italic_body(geometry: BaseGeometry) -> BaseGeometry:
    """Enlarge the italic lowercase body while preserving its vertical extremes."""
    def body_y(y: float) -> float:
        if 0 < y <= _ITALIC_PATH_X_HEIGHT:
            return y * DESIGN_X_HEIGHT / _ITALIC_PATH_X_HEIGHT
        if _ITALIC_PATH_X_HEIGHT < y < DESIGN_CAP_HEIGHT:
            fraction = (y - _ITALIC_PATH_X_HEIGHT) / (DESIGN_CAP_HEIGHT - _ITALIC_PATH_X_HEIGHT)
            return DESIGN_X_HEIGHT + fraction * (DESIGN_CAP_HEIGHT - DESIGN_X_HEIGHT)
        return y

    return transform(geometry, lambda x, y: (x, [body_y(value) for value in y]), interleaved=False)


def sample_path(path: str, step_size: float = 3.5) -> list[Point]:
    """Sample one absolute M/L/Q/C/Z contour; reject unsupported or malformed data."""
    return [point for point, _, _ in _sample_with_tangents(path, step_size)]


def _sample_with_tangents(path: str, step_size: float) -> list[tuple[Point, Point, Point]]:
    """Sample a contour with the exact direction arriving at and leaving each point."""
    if step_size <= 0:
        raise ValueError("Path sampling step must be positive")
    if _TOKEN.sub("", path).strip(" ,\t\n\r"):
        raise ValueError(f"Unsupported path syntax: {path!r}")
    tokens = _TOKEN.findall(path)
    samples: list[tuple[Point, Point, Point]] = []
    cursor = 0
    closed = False
    while cursor < len(tokens):
        command = tokens[cursor]
        cursor += 1
        if command not in _ARITY or closed:
            raise ValueError(f"Expected a path command before {command!r}")
        count = _ARITY[command]
        values = tokens[cursor:cursor + count]
        if len(values) != count or any(value in _ARITY for value in values):
            raise ValueError(f"Incomplete {command} command in {path!r}")
        coordinates = list(map(float, values))
        cursor += count
        if command == "M":
            if samples:
                raise ValueError("Use separate strokes for separate contours")
            samples.append(((coordinates[0], coordinates[1]), (0.0, 0.0), (0.0, 0.0)))
            continue
        if not samples:
            raise ValueError("A stroke must start with M")
        if command == "Z":
            controls = [samples[-1][0], samples[0][0]]
            closed = True
        else:
            controls = [samples[-1][0], *zip(coordinates[::2], coordinates[1::2])]
        length = sum(math.dist(a, b) for a, b in zip(controls, controls[1:]))
        if length == 0:
            continue
        steps = max(3, math.ceil(length / step_size))

        def direction(t: float) -> Point:
            curve = controls
            while len(curve) > 2:
                curve = [(a[0] * (1 - t) + b[0] * t, a[1] * (1 - t) + b[1] * t)
                         for a, b in zip(curve, curve[1:])]
            dx, dy = curve[1][0] - curve[0][0], curve[1][1] - curve[0][1]
            size = math.hypot(dx, dy)
            if size < 1e-9:
                # A control point on its end point: fall back to the chord.
                dx, dy = controls[-1][0] - controls[0][0], controls[-1][1] - controls[0][1]
                size = math.hypot(dx, dy) or 1.0
            return (dx / size, dy / size)

        point, arriving, _ = samples[-1]
        samples[-1] = (point, arriving, direction(0.0))
        for step in range(1, steps + 1):
            t = step / steps
            curve = controls
            while len(curve) > 1:
                curve = [(a[0] * (1 - t) + b[0] * t, a[1] * (1 - t) + b[1] * t)
                         for a, b in zip(curve, curve[1:])]
            heading = direction(t)
            samples.append((curve[0], heading, heading))
    if len(samples) < 2 or all(sample[0] == samples[0][0] for sample in samples):
        raise ValueError("A stroke must have nonzero length")
    point, _, leaving = samples[0]
    samples[0] = (point, leaving, leaving)
    return samples


def sweep(path: str, weight: float = 1.0, tips: Tips = (0.75, 0.6),
          *, nib_angle: float = 18, nib_depth: float = 8.5,
          path_width_scale: float = 1.0, pressure_profile: PressureProfile = ()) -> BaseGeometry:
    """Sweep a rounded broad nib with terminal taper and optional local pressure."""
    if weight <= 0 or min(tips) <= 0 or path_width_scale <= 0 or nib_depth <= 0:
        raise ValueError("Pen weight, terminal pressure, path width and nib depth must be positive")
    if pressure_profile and (
        len(pressure_profile) < 2 or pressure_profile[0][0] != 0 or pressure_profile[-1][0] != 1
        or any(not math.isfinite(t) or not math.isfinite(p) or p <= 0 for t, p in pressure_profile)
        or any(a[0] >= b[0] for a, b in zip(pressure_profile, pressure_profile[1:]))
    ):
        raise ValueError("Pressure profiles need increasing positions from 0 to 1 and positive pressures")
    def widened(vector: Point) -> Point:
        x, y = vector[0] * path_width_scale, vector[1]
        size = math.hypot(x, y) or 1.0
        return (x / size, y / size)

    # (point, direction arriving, direction leaving), in the widened frame.
    samples = []
    for (x, y), arriving, leaving in _sample_with_tangents(path, 3.5):
        point = (x * path_width_scale, y)
        if samples and math.dist(point, samples[-1][0]) <= 1e-6:
            samples[-1] = (samples[-1][0], samples[-1][1], widened(leaving))
            continue
        samples.append((point, widened(arriving), widened(leaving)))
    points = [sample[0] for sample in samples]
    distances = [0.0]
    for a, b in zip(points, points[1:]):
        distances.append(distances[-1] + math.dist(a, b))
    closed = math.dist(points[0], points[-1]) < 1
    slopes = _profile_slopes(pressure_profile) if pressure_profile else []
    pressures = []
    for distance in distances:
        position = distance / distances[-1]
        pressure = 1.0 if closed else min(terminal_pressure(position, tips[0]),
                                           terminal_pressure(1 - position, tips[1]))
        if pressure_profile:
            pressure *= _profile_pressure(pressure_profile, slopes, position)
        pressures.append(pressure * weight)
    nib = _Nib(nib_angle, nib_depth)

    def turn(first: Point, second: Point) -> float:
        return abs(math.atan2(first[0] * second[1] - first[1] * second[0],
                              first[0] * second[0] + first[1] * second[1]))

    # Divide the path where its direction really breaks, so each run is smooth.
    cuts = [0]
    for index in range(1, len(points) - 1):
        if turn(samples[index][1], samples[index][2]) > _CORNER_TURN:
            cuts.append(index)
    cuts.append(len(points) - 1)
    smooth_loop = closed and len(cuts) == 2 and turn(samples[-1][1], samples[0][2]) <= _CORNER_TURN
    pieces = []
    for start, end in zip(cuts, cuts[1:]):
        left, right = [], []
        for index in range(start, end + 1):
            _, arriving, leaving = samples[index]
            if index == start and not smooth_loop:
                dx, dy = leaving
            elif index == end and not smooth_loop:
                dx, dy = arriving
            else:
                if smooth_loop and index in (start, end):
                    arriving, leaving = samples[end][1], samples[start][2]
                dx, dy = arriving[0] + leaving[0], arriving[1] + leaving[1]
            length = math.hypot(dx, dy)
            x, y = points[index]
            ox, oy = nib.support(-dy / length, dx / length)
            left.append((x + ox * pressures[index], y + oy * pressures[index]))
            right.append((x - ox * pressures[index], y - oy * pressures[index]))
        for index in range(len(left) - 1):
            pieces.append(MultiPoint([left[index], left[index + 1],
                                      right[index + 1], right[index]]).convex_hull)
        if not smooth_loop:
            for index in (start, end):
                pieces.append(nib.stamp(points[index], pressures[index]))
    swept = unary_union([piece for piece in pieces if piece.geom_type == "Polygon"])
    # Coincident quad edges can leave hairline holes along a seam.
    parts = [swept] if swept.geom_type == "Polygon" else list(swept.geoms)
    return unary_union([Polygon(part.exterior, [hole for hole in part.interiors if Polygon(hole).area > 0.5])
                        for part in parts])


def _profile_slopes(profile: PressureProfile) -> list[float]:
    """Monotone cubic slopes: pressure passes through a stop without pausing on it."""
    secants = [(b[1] - a[1]) / (b[0] - a[0]) for a, b in zip(profile, profile[1:])]
    slopes = [0.0]
    for before, after in zip(secants, secants[1:]):
        slopes.append(0.0 if before * after <= 0 else 2 * before * after / (before + after))
    slopes.append(0.0)
    return slopes


def _profile_pressure(profile: PressureProfile, slopes: list[float], position: float) -> float:
    for index, ((start, first), (end, last)) in enumerate(zip(profile, profile[1:])):
        if position <= end:
            span = end - start
            t = (position - start) / span
            return ((2 * t ** 3 - 3 * t ** 2 + 1) * first + (t ** 3 - 2 * t ** 2 + t) * span * slopes[index]
                    + (-2 * t ** 3 + 3 * t ** 2) * last + (t ** 3 - t ** 2) * span * slopes[index + 1])
    return profile[-1][1]


_CORNER_TURN = math.radians(35)
# A rounded rectangle between an ellipse and a box, as cut on a broad pen.
_NIB_POWER = 2 / 0.72


class _Nib:
    """A smooth broad nib; support() gives its contact point for an outward normal."""

    def __init__(self, angle: float, depth: float):
        self.cos, self.sin = math.cos(math.radians(angle)), math.sin(math.radians(angle))
        self.width, self.depth = 32.0, depth

    def support(self, nx: float, ny: float) -> Point:
        u, v = nx * self.cos + ny * self.sin, -nx * self.sin + ny * self.cos
        a, b = abs(self.width * u), abs(self.depth * v)
        ratio = _NIB_POWER / (_NIB_POWER - 1)
        scale = (a ** ratio + b ** ratio) ** (1 / _NIB_POWER)
        exponent = 1 / (_NIB_POWER - 1)
        x = math.copysign(self.width * a ** exponent / scale, u) if a else 0.0
        y = math.copysign(self.depth * b ** exponent / scale, v) if b else 0.0
        return (x * self.cos - y * self.sin, x * self.sin + y * self.cos)

    def stamp(self, center: Point, pressure: float) -> Polygon:
        contour = []
        for segment in range(NIB_SEGMENTS):
            a = segment * math.tau / NIB_SEGMENTS
            u, v = math.cos(a), math.sin(a)
            u = math.copysign(abs(u) ** 0.72, u) * self.width * pressure
            v = math.copysign(abs(v) ** 0.72, v) * self.depth * pressure
            contour.append((center[0] + self.cos * u - self.sin * v,
                            center[1] + self.sin * u + self.cos * v))
        return Polygon(contour)


def terminal_pressure(position: float, tip: float) -> float:
    """Ease into full pressure without a slope discontinuity at the taper join."""
    if tip >= 1:
        return 1.0
    fraction = min(1.0, position * 5 / (1 - tip))
    return tip + (1 - tip) * fraction * fraction * (3 - 2 * fraction)


def dot(x: float, y: float, weight: float = 1.0) -> RoundDot:
    return RoundDot(x, y, weight)


def soften_corners(geometry: BaseGeometry, radius: float = 5.0,
                   trim: float | None = None) -> BaseGeometry:
    """Round abrupt joins and terminal corners without changing glyph spacing.

    radius fills notches at joins; trim rounds outer corners and must stay below
    half the finest hairline, or it would erase the hairline itself.
    """
    trim = radius if trim is None else trim
    rounded = geometry.buffer(radius, quad_segs=8).buffer(-radius, quad_segs=8)
    rounded = rounded.buffer(-trim, quad_segs=8).buffer(trim, quad_segs=8)
    if rounded.is_empty:
        raise ValueError("Corner refinement removed a glyph")
    return rounded


@dataclass(frozen=True)
class Shape:
    geometry: BaseGeometry
    advance: int
    base: str = ""


class GlyphBuilder:
    """Own one style's geometry; no mutable state survives a build."""

    def __init__(self, style: Style):
        self.style = style
        self.glyphs: dict[str, Shape] = {}

    def ink(self, path: str, weight: float = 1.0, tips: Tips = ITALIC_TIPS,
            *, path_width_scale: float | None = None, nib_depth: float | None = None,
            pressure_profile: PressureProfile = ()) -> BaseGeometry:
        if self.style.italic:
            return sweep(path, weight * self.style.pen_scale, tips, nib_angle=21,
                         nib_depth=ITALIC_NIB_DEPTH if nib_depth is None else nib_depth,
                         path_width_scale=self.style.path_width_scale if path_width_scale is None else path_width_scale,
                         pressure_profile=pressure_profile)
        return sweep(path, weight * self.style.pen_scale, (1, 1), nib_angle=ROMAN_NIB_ANGLE,
                     nib_depth=ROMAN_NIB_DEPTH if nib_depth is None else nib_depth,
                     pressure_profile=pressure_profile)

    def rule(self, path: str, weight: float = 1.0) -> PenStroke:
        """A stroke for signs and dashes: the roman keeps them even, without hairlines."""
        return PenStroke(path, weight, nib_depth=None if self.style.italic else RULE_NIB_DEPTH)

    def roman_nib(self, weight: float = 1.0) -> tuple[float, float]:
        """Half the width of an upright stem and half the depth of a level hairline."""
        nib = _Nib(ROMAN_NIB_ANGLE, ROMAN_NIB_DEPTH)
        scale = weight * self.style.pen_scale
        return nib.support(1, 0)[0] * scale, nib.support(0, 1)[1] * scale

    def stroke(self, path: Stroke, tips: Tips = ITALIC_TIPS) -> BaseGeometry:
        """Draw one stroke; tips applies only where the stroke does not set its own."""
        if isinstance(path, PenStroke):
            return self.ink(path.path, path.weight, tips if path.tips is None else path.tips,
                            nib_depth=path.nib_depth, pressure_profile=path.pressure)
        if isinstance(path, Raw):
            return path.geometry
        if isinstance(path, Drop):
            scale = self.style.pen_scale
            head = GeometryPoint(path.x * self.style.path_width_scale, path.y).buffer(
                path.radius * scale, quad_segs=24)
            tail = GeometryPoint(path.tail_x * self.style.path_width_scale, path.tail_y).buffer(
                path.tail_radius * scale, quad_segs=24)
            return unary_union([head, tail]).convex_hull
        if isinstance(path, RoundDot):
            radius = 24 * path.weight * self.style.pen_scale
            if radius <= 0:
                raise ValueError("Dot weight must be positive")
            return GeometryPoint(path.x * self.style.path_width_scale, path.y).buffer(radius, quad_segs=24)
        if isinstance(path, FilledPath):
            if not path.path.rstrip().endswith("Z"):
                raise ValueError("A filled contour must be explicitly closed")
            contour = Polygon(sample_path(path.path))
            if not contour.is_valid or contour.area == 0:
                raise ValueError("A filled contour must have a valid nonzero area")
            return affine_transform(contour, [self.style.path_width_scale, 0, 0, 1, 0, 0])
        if isinstance(path, str):
            return self.ink(path, tips=tips)
        return self.ink(*path) if len(path) == 3 else self.ink(path[0], path[1], tips)

    def _joined_tips(self, paths: tuple[Stroke, ...]) -> list[Tips]:
        """Taper only free, curved stroke ends; junctions and straight stem ends keep the full nib."""
        lines, straight = [], []
        for path in paths:
            source = path.path if isinstance(path, PenStroke) else (
                path if isinstance(path, str) else path[0] if isinstance(path, tuple) else None)
            lines.append(None if source is None else LineString(sample_path(source, 9.0)))
            commands = [] if source is None else [token for token in _TOKEN.findall(source) if token in _ARITY]
            straight.append((commands[1:2] == ["L"], commands[-1:] == ["L"]))
        result = []
        for index, line in enumerate(lines):
            if line is None:
                result.append(ITALIC_TIPS)
                continue
            others = [other for position, other in enumerate(lines) if other is not None and position != index]
            ends = []
            for point, taper, stem in ((line.coords[0], ITALIC_TIPS[0], straight[index][0]),
                                       (line.coords[-1], ITALIC_TIPS[1], straight[index][1])):
                meets = any(other.distance(GeometryPoint(point)) < JUNCTION_REACH for other in others)
                # A straight end is a stem cut by the nib; only curved entries and exits taper.
                ends.append(1.0 if meets or stem else taper)
            result.append((ends[0], ends[1]))
        return result

    def add(self, char: str, *paths: Stroke, bearing: int | None = None,
            advance: int | None = None) -> None:
        if len(char) != 1 or not paths:
            raise ValueError("A glyph needs one Unicode character and at least one stroke")
        if self.style.italic:
            pieces = [self.stroke(path, tips) for path, tips in zip(paths, self._joined_tips(paths))]
        else:
            pieces = [self.stroke(path) for path in paths]
        geometry = unary_union(pieces)
        for path in paths:
            if isinstance(path, Drop) and path.blend:
                # Fill only the notches between a terminal's head and the stroke that carries it.
                scale = self.style.pen_scale
                centre = GeometryPoint(path.x * self.style.path_width_scale, path.y)
                fillet = path.blend * scale
                nearby = geometry.intersection(centre.buffer(path.radius * scale * 2.3))
                melted = nearby.buffer(fillet, quad_segs=16).buffer(-fillet, quad_segs=16)
                geometry = geometry.union(melted.intersection(centre.buffer(path.radius * scale * 1.9)))
        geometry = geometry.simplify(0.05, preserve_topology=True)
        if self.style.italic and char.islower():
            geometry = raise_italic_body(geometry)
        geometry = affine_transform(geometry, [self.style.width_scale, self.style.slant, 0, 1, 0, 0])
        side = self.style.side_bearing if bearing is None else bearing
        geometry = translate(geometry, xoff=side - geometry.bounds[0])
        width = round(geometry.bounds[2] + side) if advance is None else round(advance * self.style.spacing_scale)
        if width < 0:
            raise ValueError(f"Negative advance for {char!r}")
        if self.style.italic:
            geometry = soften_corners(geometry, ITALIC_CORNER_RADIUS, ITALIC_CORNER_TRIM)
        else:
            geometry = soften_corners(geometry, ROMAN_CORNER_RADIUS)
        self.glyphs[char] = Shape(geometry, width, char)

    def set_spacing(self, char: str, shift: float, advance: int) -> None:
        shape = self.glyphs[char]
        self.glyphs[char] = replace(shape, geometry=translate(shape.geometry, xoff=shift * self.style.spacing_scale),
                                    advance=round(advance * self.style.spacing_scale))
