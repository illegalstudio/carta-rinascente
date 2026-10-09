"""Compile a deterministic, style-linked TTF and WOFF2 family.

Copyright (c) 2026, Carta Rinascente contributors.
SPDX-License-Identifier: OFL-1.1
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.ttLib import TTFont, newTable
from shapely.geometry import box

from .config import (ASCENT, BUILD_TIMESTAMP, CAP_HEIGHT, COPYRIGHT, DESCENT,
                     FAMILY, ROOT, STYLES, UNITS_PER_EM, VERSION, X_HEIGHT, Style)
from .design import build_glyphs
from .features import feature_source
from .outlines import glyph_name, glyph_outline


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def compile_style(style: Style, output: Path) -> dict:
    """Construct one face without opening any input font."""
    shapes = build_glyphs(style)
    expected = {*range(32, 127), *range(160, 256)}
    missing = expected - {ord(char) for char in shapes}
    if missing:
        raise ValueError(f"Missing required characters: {sorted(missing)}")
    chars = sorted(shapes, key=ord)
    order = [".notdef", *map(glyph_name, chars)]
    if len(set(order)) != len(order):
        raise ValueError("Duplicate glyph names")
    builder = FontBuilder(UNITS_PER_EM, isTTF=True)
    builder.setupGlyphOrder(order)
    builder.setupCharacterMap({ord(char): glyph_name(char) for char in chars})
    missing_box = box(40, 0, 430, 670).difference(box(77, 37, 393, 633))
    glyphs = {".notdef": glyph_outline(missing_box)}
    glyphs.update({glyph_name(char): glyph_outline(shapes[char].geometry) for char in chars})
    builder.setupGlyf(glyphs)
    metrics = {".notdef": (470, 40)}
    metrics.update({glyph_name(char): (shapes[char].advance,
                    getattr(glyphs[glyph_name(char)], "xMin", 0)) for char in chars})
    builder.setupHorizontalMetrics(metrics)
    builder.setupHorizontalHeader(ascent=ASCENT, descent=DESCENT, lineGap=0,
                                  caretSlopeRise=1000, caretSlopeRun=round(style.slant * 1000))
    builder.setupNameTable({
        "familyName": FAMILY,
        "styleName": style.name,
        "typographicFamily": FAMILY,
        "typographicSubfamily": style.name,
        "uniqueFontIdentifier": f"{style.filename}-{VERSION}",
        "fullName": f"{FAMILY} {style.name}",
        "psName": style.filename,
        "version": f"Version {VERSION}",
        "copyright": COPYRIGHT,
        "designer": "nahime / illegal studio, with OpenAI Codex assistance",
        "vendorURL": "https://illegal.studio",
        "description": "Original Renaissance-inspired typeface created for Ariadne. "
                       "Independent pen paths; no third-party font outlines.",
        "licenseDescription": "SIL Open Font License 1.1. No Reserved Font Names. See OFL.txt.",
        "licenseInfoURL": "https://openfontlicense.org",
    })
    builder.setupOS2(version=4, sTypoAscender=ASCENT, sTypoDescender=DESCENT,
                     sTypoLineGap=0, usWinAscent=ASCENT, usWinDescent=-DESCENT,
                     sxHeight=X_HEIGHT, sCapHeight=CAP_HEIGHT, usWeightClass=style.weight,
                     usWidthClass=5, fsType=0, fsSelection=style.selection, achVendID="CRIN")
    builder.setupPost(italicAngle=style.angle, underlinePosition=-95,
                      underlineThickness=round(37 * style.pen_scale))
    builder.setupMaxp()
    builder.font["head"].macStyle = style.mac_style
    builder.font["head"].fontRevision = float(VERSION)
    builder.font["head"].created = builder.font["head"].modified = BUILD_TIMESTAMP
    builder.font.recalcTimestamp = False
    features, pair_count = feature_source(shapes, style)
    addOpenTypeFeaturesFromString(builder.font, features)
    gasp = newTable("gasp")
    gasp.gaspRange = {65535: 15}
    builder.font["gasp"] = gasp
    ttf = output / f"{style.filename}.ttf"
    builder.save(ttf)
    with TTFont(ttf, recalcTimestamp=False) as web:
        web.flavor = "woff2"
        web.save(output / f"{style.filename}.woff2")
    builder.font.close()
    return {
        "style": style.name, "weight": style.weight, "italic": style.italic,
        "italic_angle": style.angle, "glyphs": len(order), "encoded_characters": len(chars),
        "kerning_pairs": pair_count, "files": [f"{style.filename}.ttf", f"{style.filename}.woff2"],
        "codepoints": [f"U+{ord(char):04X}" for char in chars],
    }


def build_family(output: Path) -> dict:
    """Stage and validate all faces before replacing any released font files."""
    from .validation import validate_family

    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".build-family-", dir=output.parent) as temporary:
        staging = Path(temporary)
        faces = []
        for style in STYLES:
            print(f"Building {style.name}...", flush=True)
            faces.append(compile_style(style, staging))
        repertoire = faces[0]["codepoints"]
        if any(face["codepoints"] != repertoire for face in faces[1:]):
            raise ValueError("Family members must have identical character coverage")
        for face in faces:
            del face["codepoints"]
        metadata = {
            "family": FAMILY, "version": VERSION, "units_per_em": UNITS_PER_EM,
            "encoded_characters": len(repertoire), "glyphs_per_style": len(repertoire) + 1,
            "styles": faces, "codepoints": repertoire,
            "source": "Independent paths in src/design; no input font.",
            "license": "SIL Open Font License 1.1; no Reserved Font Names",
        }
        write_json(staging / "metadata.json", metadata)
        (staging / "OFL.txt").write_bytes((ROOT / "OFL.txt").read_bytes())
        validate_family(staging)
        for path in sorted(staging.iterdir()):
            path.replace(output / path.name)
    return metadata
