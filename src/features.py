"""Build kerning, dot removal and mark positioning from the same glyph model.

Copyright (c) 2026, Carta Rinascente contributors.
SPDX-License-Identifier: OFL-1.1
"""

from .anchors import mark_anchor
from .config import BOTTOM_MARKS, Style
from .design.accents import ACCENTS, CONTEXTUAL_ACCENTS
from .design.kerning import KERN_PAIRS
from .geometry import Shape
from .outlines import glyph_name


def kerning_pairs(glyphs: dict[str, Shape], style: Style) -> dict[tuple[str, str], int]:
    pairs = {}
    factor = 0.85 if style.weight == 700 else 1.0
    adjustments = {pair: round(value * factor) for pair, value in KERN_PAIRS.items()}
    # The italic f overhang needs clearance beside dots, loops and descenders.
    # Keep it local to these pairs rather than opening every word containing f.
    if style.italic:
        adjustments.update({('f', 'i'): 22, ('f', 'l'): 74, ('f', 'p'): 42, ('f', 'y'): 42,
                            ('f', 'w'): 90, ('q', 'g'): 54, ('q', 'j'): 59, ('q', 'y'): 54})
    else:
        adjustments.update({('g', 'j'): 47, ('q', 'j'): 34})
        if style.weight == 700:
            adjustments['f', 'l'] = 32
    for (left, right), adjustment in adjustments.items():
        lefts = [char for char, shape in glyphs.items() if shape.base == left and char.isalpha()]
        rights = [char for char, shape in glyphs.items() if shape.base == right and char.isalpha()]
        for a in lefts:
            for b in rights:
                pairs[glyph_name(a), glyph_name(b)] = adjustment
    return pairs


def feature_source(glyphs: dict[str, Shape], style: Style) -> tuple[str, int]:
    pairs = kerning_pairs(glyphs, style)
    top_marks = [mark for mark in ACCENTS if mark not in BOTTOM_MARKS]
    features = ["languagesystem DFLT dflt;", "languagesystem latn dflt;"]
    features += ["@TOP_MARKS = [" + " ".join(map(glyph_name, top_marks)) + "];", "feature ccmp {"]
    for (base, mark), composed in CONTEXTUAL_ACCENTS.items():
        features.append(f"  sub {glyph_name(base)} {glyph_name(mark)} by {glyph_name(composed)};")
    features += ["  sub i' @TOP_MARKS by dotlessi;",
                 "  sub j' @TOP_MARKS by uni0237;",
                 "} ccmp;", "feature kern {", "  lookupflag IgnoreMarks;"]
    features.extend(f"  pos {left} {right} {value};" for (left, right), value in pairs.items())
    features.append("} kern;")
    for mark in ACCENTS:
        group = "BOTTOM" if mark in BOTTOM_MARKS else "TOP"
        features.append(f"markClass {glyph_name(mark)} <anchor 0 0> @{group};")
    features.append("feature mark {")
    for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzıȷ":
        top_x, top_y = mark_anchor(glyphs[char], char, "\u0301", style)
        bottom_x, bottom_y = mark_anchor(glyphs[char], char, "\u0327", style)
        features.append(f"  pos base {glyph_name(char)} <anchor {top_x} {top_y}> mark @TOP "
                        f"<anchor {bottom_x} {bottom_y}> mark @BOTTOM;")
    features.append("} mark;")
    return "\n".join(features), len(pairs)
