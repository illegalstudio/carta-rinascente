"""Shared anchors keep composed glyphs and OpenType positioning in agreement.

Copyright (c) 2026, Carta Rinascente contributors.
SPDX-License-Identifier: OFL-1.1
"""

from .config import BOTTOM_MARKS, Style
from .geometry import Shape


def mark_anchor(shape: Shape, base: str, mark: str, style: Style) -> tuple[int, int]:
    if mark in BOTTOM_MARKS:
        return round(shape.advance / 2), -15
    height = 757 if base.isupper() else (782 if base in "bdfhkl" else 540)
    offset = 28 if style.italic else 0
    return round(shape.advance / 2 + offset), height
