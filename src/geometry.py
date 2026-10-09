"""Strict path sampling, broad-nib geometry and per-face glyph construction.

Copyright (c) 2026, Carta Rinascente contributors.
SPDX-License-Identifier: OFL-1.1
"""

from dataclasses import dataclass, replace
import math
import re

from shapely import transform
from shapely.affinity import affine_transform, translate
from shapely.geometry import Point as GeometryPoint, Polygon
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
class PenStroke:
    """A nib-depth override and smooth pressure stops along normalized path distance.

    Depth strengthens a hairline without widening a vertical stem. Pressure
    scales the whole nib locally and multiplies the style's terminal taper.
    """

    path: str
    weight: float = 1.0
    nib_depth: float | None = None
    pressure: PressureProfile = ()


type Stroke = str | tuple[str, float] | tuple[str, float, Tips] | FilledPath | RoundDot | PenStroke

_TOKEN = re.compile(r"[MLCQZ]|[+-]?(?:\d+(?:\.\d*)?|\.\d+)")
_ARITY = {"M": 2, "L": 2, "Q": 4, "C": 6, "Z": 0}
_ITALIC_PATH_X_HEIGHT = 470


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


def sample_path(path: str, step_size: float = 7.0) -> list[Point]:
    """Sample one absolute M/L/Q/C/Z contour; reject unsupported or malformed data."""
    if step_size <= 0:
        raise ValueError("Path sampling step must be positive")
    if _TOKEN.sub("", path).strip(" ,\t\n\r"):
        raise ValueError(f"Unsupported path syntax: {path!r}")
    tokens = _TOKEN.findall(path)
    points: list[Point] = []
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
            if points:
                raise ValueError("Use separate strokes for separate contours")
            points.append((coordinates[0], coordinates[1]))
            continue
        if not points:
            raise ValueError("A stroke must start with M")
        if command == "Z":
            controls = [points[-1], points[0]]
            closed = True
        else:
            controls = [points[-1], *zip(coordinates[::2], coordinates[1::2])]
        length = sum(math.dist(a, b) for a, b in zip(controls, controls[1:]))
        steps = max(3, math.ceil(length / step_size))
        for step in range(1, steps + 1):
            t = step / steps
            curve = controls
            while len(curve) > 1:
                curve = [(a[0] * (1 - t) + b[0] * t, a[1] * (1 - t) + b[1] * t)
                         for a, b in zip(curve, curve[1:])]
            points.append(curve[0])
    if len(points) < 2 or all(point == points[0] for point in points):
        raise ValueError("A stroke must have nonzero length")
    return points


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
    points = [(x * path_width_scale, y) for x, y in sample_path(path)]
    distances = [0.0]
    if pressure_profile:
        for a, b in zip(points, points[1:]):
            distances.append(distances[-1] + math.dist(a, b))
    closed = math.dist(points[0], points[-1]) < 1
    angle = math.radians(nib_angle)
    ca, sa = math.cos(angle), math.sin(angle)
    stamps = []
    for index, (x, y) in enumerate(points):
        t = index / (len(points) - 1)
        pressure = 1.0 if closed else min(1, tips[0] + t * 5, tips[1] + (1 - t) * 5)
        if pressure_profile:
            position = distances[index] / distances[-1]
            for (start, first), (end, last) in zip(pressure_profile, pressure_profile[1:]):
                if position <= end:
                    fraction = (position - start) / (end - start)
                    fraction = fraction * fraction * (3 - 2 * fraction)
                    pressure *= first + (last - first) * fraction
                    break
        contour = []
        for segment in range(16):
            a = segment * math.tau / 16
            u, v = math.cos(a), math.sin(a)
            u = math.copysign(abs(u) ** 0.72, u) * 32 * weight * pressure
            v = math.copysign(abs(v) ** 0.72, v) * nib_depth * weight * pressure
            contour.append((x + ca * u - sa * v, y + sa * u + ca * v))
        stamps.append(Polygon(contour))
    return unary_union([a.union(b).convex_hull for a, b in zip(stamps, stamps[1:])])


def dot(x: float, y: float, weight: float = 1.0) -> RoundDot:
    return RoundDot(x, y, weight)


def soften_corners(geometry: BaseGeometry, radius: float = 5.0) -> BaseGeometry:
    """Round abrupt joins and terminal corners without changing glyph spacing."""
    rounded = geometry.buffer(radius, quad_segs=4).buffer(-radius, quad_segs=4)
    rounded = rounded.buffer(-radius, quad_segs=4).buffer(radius, quad_segs=4)
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

    def ink(self, path: str, weight: float = 1.0, tips: Tips = (0.75, 0.6),
            *, path_width_scale: float | None = None, nib_depth: float | None = None,
            pressure_profile: PressureProfile = ()) -> BaseGeometry:
        if self.style.italic:
            return sweep(path, weight * self.style.pen_scale, tips, nib_angle=21,
                         nib_depth=10 if nib_depth is None else nib_depth,
                         path_width_scale=self.style.path_width_scale if path_width_scale is None else path_width_scale,
                         pressure_profile=pressure_profile)
        # Roman strokes keep level terminals and even pressure, with fuller hairlines.
        return sweep(path, weight * self.style.pen_scale, (1, 1), nib_angle=0,
                     nib_depth=15 if nib_depth is None else nib_depth, pressure_profile=pressure_profile)

    def stroke(self, path: Stroke) -> BaseGeometry:
        if isinstance(path, PenStroke):
            return self.ink(path.path, path.weight, nib_depth=path.nib_depth, pressure_profile=path.pressure)
        if isinstance(path, RoundDot):
            radius = 24 * path.weight * self.style.pen_scale
            if radius <= 0:
                raise ValueError("Dot weight must be positive")
            return GeometryPoint(path.x * self.style.path_width_scale, path.y).buffer(radius, quad_segs=12)
        if isinstance(path, FilledPath):
            if not path.path.rstrip().endswith("Z"):
                raise ValueError("A filled contour must be explicitly closed")
            contour = Polygon(sample_path(path.path))
            if not contour.is_valid or contour.area == 0:
                raise ValueError("A filled contour must have a valid nonzero area")
            return affine_transform(contour, [self.style.path_width_scale, 0, 0, 1, 0, 0])
        return self.ink(path) if isinstance(path, str) else self.ink(*path)

    def add(self, char: str, *paths: Stroke, bearing: int | None = None,
            advance: int | None = None) -> None:
        if len(char) != 1 or not paths:
            raise ValueError("A glyph needs one Unicode character and at least one stroke")
        pieces = [self.stroke(path) for path in paths]
        geometry = unary_union(pieces).simplify(0.42, preserve_topology=True)
        if self.style.italic and char.islower():
            geometry = raise_italic_body(geometry)
        geometry = affine_transform(geometry, [self.style.width_scale, self.style.slant, 0, 1, 0, 0])
        side = self.style.side_bearing if bearing is None else bearing
        geometry = translate(geometry, xoff=side - geometry.bounds[0])
        width = round(geometry.bounds[2] + side) if advance is None else round(advance * self.style.spacing_scale)
        if width < 0:
            raise ValueError(f"Negative advance for {char!r}")
        if not self.style.italic:
            geometry = soften_corners(geometry)
        self.glyphs[char] = Shape(geometry, width, char)

    def set_spacing(self, char: str, shift: float, advance: int) -> None:
        shape = self.glyphs[char]
        self.glyphs[char] = replace(shape, geometry=translate(shape.geometry, xoff=shift * self.style.spacing_scale),
                                    advance=round(advance * self.style.spacing_scale))
