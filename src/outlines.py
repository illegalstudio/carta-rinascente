"""Convert original polygon geometry into correctly wound TrueType contours.

Copyright (c) 2026, Carta Rinascente contributors.
SPDX-License-Identifier: OFL-1.1
"""

from fontTools.agl import UV2AGL
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._g_l_y_f import Glyph
from shapely.geometry.base import BaseGeometry
from shapely.geometry.polygon import orient


def glyph_name(char: str) -> str:
    return UV2AGL.get(ord(char), f"uni{ord(char):04X}")


def glyph_outline(geometry: BaseGeometry) -> Glyph:
    pen = TTGlyphPen(None)
    if geometry.is_empty:
        return pen.glyph()
    geometry = geometry.buffer(0).simplify(0.48, preserve_topology=True)
    polygons = [geometry] if geometry.geom_type == "Polygon" else list(geometry.geoms)
    for polygon in polygons:
        if polygon.area < 0.75:
            continue
        if polygon.geom_type != "Polygon":
            raise ValueError(f"Unexpected outline geometry: {polygon.geom_type}")
        polygon = orient(polygon, sign=-1)
        for ring in [polygon.exterior, *polygon.interiors]:
            coordinates = [(round(x), round(y)) for x, y in ring.coords[:-1]]
            coordinates = [point for index, point in enumerate(coordinates)
                           if index == 0 or point != coordinates[index - 1]]
            if len(set(coordinates)) < 3:
                continue
            pen.moveTo(coordinates[0])
            for point in coordinates[1:]:
                pen.lineTo(point)
            pen.closePath()
    return pen.glyph()
