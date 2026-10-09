"""Family-wide metrics and explicit static style definitions.

Copyright (c) 2026, Carta Rinascente contributors.
SPDX-License-Identifier: OFL-1.1
"""

from dataclasses import dataclass
import math
from pathlib import Path

from . import __version__

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "dist"
FAMILY = "Carta Rinascente"
VERSION = __version__
COPYRIGHT = "Copyright (c) 2026, Carta Rinascente contributors."
UNITS_PER_EM = 1000
ASCENT = 1050
DESCENT = -320
X_HEIGHT = 470
CAP_HEIGHT = 700
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
        return -10.0 if self.italic else 0.0

    @property
    def slant(self) -> float:
        return math.tan(math.radians(-self.angle))

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
    Style("Regular"),
    Style("Italic", italic=True, side_bearing=29),
    Style("Bold", weight=700, pen_scale=1.48, side_bearing=35),
    Style("Bold Italic", weight=700, italic=True, pen_scale=1.48, side_bearing=32),
)
