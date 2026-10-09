"""Family-wide metrics and explicit static style definitions.

Copyright (c) 2026, Carta Rinascente contributors.
SPDX-License-Identifier: OFL-1.1
"""

from dataclasses import dataclass
import math
from pathlib import Path

from . import __font_revision__, __version__

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "dist"
FAMILY = "Carta Rinascente"
VERSION = __version__
FONT_REVISION = __font_revision__
COPYRIGHT = "Copyright (c) 2026, Carta Rinascente contributors."
UNITS_PER_EM = 1000
# Draw on a compact grid, then scale every OpenType table to the standard em.
DESIGN_UNITS_PER_EM = 900
DESIGN_ASCENT = 1050
DESIGN_DESCENT = -320
DESIGN_X_HEIGHT = 500
DESIGN_CAP_HEIGHT = 700
ASCENT = round(DESIGN_ASCENT * UNITS_PER_EM / DESIGN_UNITS_PER_EM)
DESCENT = round(DESIGN_DESCENT * UNITS_PER_EM / DESIGN_UNITS_PER_EM)
X_HEIGHT = round(DESIGN_X_HEIGHT * UNITS_PER_EM / DESIGN_UNITS_PER_EM)
CAP_HEIGHT = round(DESIGN_CAP_HEIGHT * UNITS_PER_EM / DESIGN_UNITS_PER_EM)
BUILD_TIMESTAMP = 3874348800
BOTTOM_MARKS = frozenset({"\u0327", "\u0328"})
WHITESPACE = frozenset({32, 160, 0x2002, 0x2003, 0x2009, 0x200B, 0x202F})


@dataclass(frozen=True)
class Style:
    """A designed face; weight changes the pen before outlines are constructed."""

    name: str
    weight: int = 400
    italic: bool = False
    pen_scale: float = 1.0
    side_bearing: int = 32

    @property
    def slug(self) -> str:
        return self.name.replace(" ", "")

    @property
    def filename(self) -> str:
        return f"CartaRinascente-{self.slug}"

    @property
    def angle(self) -> float:
        return -13.0 if self.italic else 0.0

    @property
    def slant(self) -> float:
        return math.tan(math.radians(-self.angle))

    @property
    def width_scale(self) -> float:
        return 1.08 if self.italic else 1.06

    @property
    def selection(self) -> int:
        # USE_TYPO_METRICS plus the mutually compatible style-linking bits.
        return 0x80 | (0x01 if self.italic else 0) | (0x20 if self.weight == 700 else 0) | (
            0x40 if self.weight == 400 and not self.italic else 0
        )

    @property
    def mac_style(self) -> int:
        return (1 if self.weight == 700 else 0) | (2 if self.italic else 0)


STYLES = (
    Style("Regular", pen_scale=1.3, side_bearing=36),
    Style("Italic", italic=True, pen_scale=1.26, side_bearing=23),
    Style("Bold", weight=700, pen_scale=1.76, side_bearing=38),
    Style("Bold Italic", weight=700, italic=True, pen_scale=1.72, side_bearing=26),
)
