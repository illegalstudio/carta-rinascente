"""Independent checks of exported files with FontTools, FreeType and HarfBuzz.

Copyright (c) 2026, Carta Rinascente contributors.
SPDX-License-Identifier: OFL-1.1
"""

from io import BytesIO
import hashlib
import json
from pathlib import Path
import unicodedata

from fontTools.ttLib import TTFont
from PIL import ImageFont
from shapely.affinity import translate
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union
import uharfbuzz as hb

from .config import (ASCENT, CAP_HEIGHT, DESCENT, FAMILY, FONT_REVISION, STYLES,
                     UNITS_PER_EM, VERSION, WHITESPACE, X_HEIGHT, Style)

SAMPLES = (
    "Carta Rinascente", "A quiet page, an expressive voice.",
    "The art of a quiet page. A yellow flower, a playful melody.",
    "Perché la città è già più bella? À È É Ì Ò Ù à è é ì ò ù",
    "minimum illimitato fili foglie qui quattro",
    "AVATAR WA VA To Ta Te Yo Wo fi fl ffi ffl",
    "The journey: € 125.90. 09/10/2026 (14:30)",
    "Æ Œ æ œ ð þ Ð Þ µ ß ı ȷ",
)


class FontValidationError(ValueError):
    """An exported font does not meet the family's release contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FontValidationError(message)


def shape(data: bytes, text: str, *, kern: bool = True) -> list[tuple[int, int, int, int, int]]:
    face = hb.Face(data)
    font = hb.Font(face)
    font.scale = (face.upem, face.upem)
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(font, buffer, {"kern": kern})
    return [(info.codepoint, pos.x_advance, pos.y_advance, pos.x_offset, pos.y_offset)
            for info, pos in zip(buffer.glyph_infos, buffer.glyph_positions)]


def _check_style(font: TTFont, style: Style) -> None:
    names = font["name"]
    for name_id, expected in ((1, FAMILY), (2, style.name), (4, f"{FAMILY} {style.name}"),
                              (3, f"{style.filename}-{VERSION}"),
                              (5, f"Version {FONT_REVISION}; release {VERSION}"),
                              (6, style.filename), (16, FAMILY), (17, style.name)):
        require(names.getDebugName(name_id) == expected, f"{style.name}: incorrect name ID {name_id}")
    require(abs(font["head"].fontRevision - float(FONT_REVISION)) <= 1 / 65536,
            f"{style.name}: incorrect font revision")
    require(font["head"].unitsPerEm == UNITS_PER_EM, f"{style.name}: incorrect em scale")
    require(font["OS/2"].sxHeight == X_HEIGHT and font["OS/2"].sCapHeight == CAP_HEIGHT,
            f"{style.name}: incorrect scaled body metrics")
    require(font["OS/2"].usWeightClass == style.weight, f"{style.name}: weight class mismatch")
    require(font["OS/2"].fsSelection == style.selection, f"{style.name}: incorrect OS/2 style flags")
    require(font["head"].macStyle == style.mac_style, f"{style.name}: incorrect head style flags")
    require(font["post"].italicAngle == style.angle, f"{style.name}: incorrect italic angle")
    require(font["hhea"].caretSlopeRise == 1000 and
            font["hhea"].caretSlopeRun == round(style.slant * 1000), f"{style.name}: caret mismatch")
    require(font["hhea"].ascent == ASCENT and font["hhea"].descent == DESCENT,
            f"{style.name}: family line metrics mismatch")
    require(font["OS/2"].sTypoAscender == ASCENT and font["OS/2"].sTypoDescender == DESCENT,
            f"{style.name}: typographic line metrics mismatch")
    require(font["OS/2"].usWinAscent == ASCENT and font["OS/2"].usWinDescent == -DESCENT,
            f"{style.name}: Windows line metrics mismatch")
    require(font["OS/2"].fsType == 0, f"{style.name}: embedding is restricted")
    require("SIL Open Font License" in (names.getDebugName(13) or ""), "Missing embedded license")


def _polygon_outline(font: TTFont, char: str) -> BaseGeometry:
    """Read the exported polygon contours, so spacing checks include quantization."""
    glyph = font['glyf'][font.getBestCmap()[ord(char)]]
    coordinates, ends, flags = glyph.getCoordinates(font['glyf'])
    require(all(flag & 1 for flag in flags), "Polygon proof expects on-curve points")
    outer, holes, start = [], [], 0
    for end in ends:
        contour = Polygon(coordinates[start:end + 1])
        (holes if contour.exterior.is_ccw else outer).append(contour)
        start = end + 1
    return unary_union(outer).difference(unary_union(holes))


def _check_proof_spacing(font: TTFont, data: bytes, style: Style) -> None:
    for pair in ('AV', 'VA', 'WA', 'TA', 'To', 'Ta', 'Te', 'Yo', 'Wo', 'fi', 'fl', 'ff',
                 'fp', 'fy', 'ag', 'pa', 'pg', 'gy', 'yl', 'll', 'ld', 'rn'):
        result = shape(data, pair)
        left, right = (_polygon_outline(font, char) for char in pair)
        overlap = left.intersection(translate(right, xoff=result[0][1])).area
        require(overlap <= 1, f"{style.name}: unintended outline overlap in {pair!r}")


def validate_style(directory: Path, style: Style) -> tuple[dict, tuple[list[str], dict[int, str]]]:
    ttf_path = directory / f"{style.filename}.ttf"
    woff_path = directory / f"{style.filename}.woff2"
    data = ttf_path.read_bytes()
    with TTFont(ttf_path, checkChecksums=2) as font, TTFont(woff_path) as web:
        font.ensureDecompiled()
        web.ensureDecompiled()
        _check_style(font, style)
        _check_style(web, style)
        require(all(table in font for table in ("GPOS", "GDEF", "GSUB")), "Missing layout tables")
        cmap = font.getBestCmap()
        require(font["hmtx"][cmap[0x2003]][0] == UNITS_PER_EM and
                font["hmtx"][cmap[0x2002]][0] == UNITS_PER_EM // 2,
                f"{style.name}: em-space widths were not scaled correctly")
        required = {*range(32, 127), *range(160, 256)}
        require(required <= cmap.keys(), f"{style.name}: incomplete Basic Latin / Latin-1")
        bounds = []
        for codepoint, name in cmap.items():
            glyph = font["glyf"][name]
            require(name != ".notdef", f"U+{codepoint:04X}: maps to missing glyph")
            if codepoint not in WHITESPACE:
                require(glyph.numberOfContours > 0, f"{style.name}: empty U+{codepoint:04X}")
                require(glyph.yMax <= ASCENT and glyph.yMin >= DESCENT,
                        f"{style.name}: clipped U+{codepoint:04X}")
                bounds.append((glyph.yMin, glyph.yMax))
            if unicodedata.combining(chr(codepoint)):
                require(font["hmtx"][name][0] == 0, f"{name}: combining mark must have zero advance")
            elif codepoint != 0x200B:
                require(font["hmtx"][name][0] > 0, f"{name}: invalid advance")
        for text in (*SAMPLES, "".join(map(chr, cmap))):
            require(all(row[0] for row in shape(data, text)), f"{style.name}: shaping produced .notdef")
        for codepoint in cmap:
            text = chr(codepoint)
            decomposed = unicodedata.normalize("NFD", text)
            if len(decomposed) > 1 and all(ord(char) in cmap for char in decomposed):
                require(shape(data, text) == shape(data, decomposed),
                        f"{style.name}: NFC/NFD mismatch for U+{codepoint:04X}")
        require(sum(row[1] for row in shape(data, "AVATAR")) <
                sum(row[1] for row in shape(data, "AVATAR", kern=False)), f"{style.name}: inactive kerning")
        marked = shape(data, "x\u0301")
        require(len(marked) == 2 and marked[1][1] == 0 and marked[1][3:] != (0, 0),
                f"{style.name}: combining mark is not positioned")
        dotless = shape(data, "i\u0307")
        require(dotless[0][0] == font.getGlyphID("dotlessi"), f"{style.name}: dotted-i substitution failed")
        _check_proof_spacing(font, data, style)
        for size in (18, 24, 64):
            rasterizer = ImageFont.truetype(str(ttf_path), size)
            for codepoint in cmap:
                if codepoint in WHITESPACE or codepoint == 0xAD or unicodedata.combining(chr(codepoint)):
                    continue
                require(rasterizer.getmask(chr(codepoint)).getbbox() is not None,
                        f"{style.name}: empty FreeType render U+{codepoint:04X} at {size}px")
        require(web.getBestCmap() == cmap, "WOFF2 character map mismatch")
        require(web["hmtx"].metrics == font["hmtx"].metrics, "WOFF2 metrics mismatch")
        require(web.getGlyphOrder() == font.getGlyphOrder(), "WOFF2 glyph order mismatch")
        for name in font.getGlyphOrder():
            require(web["glyf"][name].getCoordinates(web["glyf"]) ==
                    font["glyf"][name].getCoordinates(font["glyf"]), f"WOFF2 outline mismatch: {name}")
        web.flavor = None
        restored = BytesIO()
        web.save(restored)
        for sample in SAMPLES:
            require(shape(data, sample) == shape(restored.getvalue(), sample), "WOFF2 shaping mismatch")
        return ({
            "style": style.name, "result": "PASS", "glyph_count": len(font.getGlyphOrder()),
            "encoded_characters": len(cmap), "outline_y_min": min(y[0] for y in bounds),
            "outline_y_max": max(y[1] for y in bounds), "style_linking": True,
            "nfc_nfd_equivalence": True, "kerning_active": True, "combining_marks": True,
            "proof_pairs_do_not_overlap": True,
            "woff2_round_trip_equivalent": True,
            "sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in (ttf_path, woff_path)},
        }, (font.getGlyphOrder(), cmap))


def validate_family(directory: Path) -> dict:
    results, repertoires = zip(*(validate_style(directory, style) for style in STYLES))
    require(all(repertoire == repertoires[0] for repertoire in repertoires),
            "Style character maps or glyph orders differ")
    metadata = json.loads((directory / "metadata.json").read_text())
    require(metadata["version"] == VERSION, "Stale metadata version")
    require(metadata["font_revision"] == FONT_REVISION, "Stale metadata font revision")
    require([face["style"] for face in metadata["styles"]] == [style.name for style in STYLES],
            "Incomplete family metadata")
    require(metadata["codepoints"] == [f"U+{cp:04X}" for cp in sorted(repertoires[0][1])],
            "Metadata character coverage does not match the font files")
    for result, face, style in zip(results, metadata["styles"], STYLES):
        require(face["glyphs"] == result["glyph_count"] and
                face["encoded_characters"] == result["encoded_characters"],
                f"{style.name}: metadata glyph counts do not match the font")
        require(face["weight"] == style.weight and face["italic"] == style.italic,
                f"{style.name}: metadata style classification mismatch")
    require((directory / "OFL.txt").is_file(), "The distribution must include OFL.txt")
    report = {
        "result": "PASS", "family": FAMILY, "version": VERSION, "font_revision": FONT_REVISION,
        "engines": ["FontTools", "FreeType via Pillow", "HarfBuzz"],
        "family_metrics": {"ascender": ASCENT, "descender": DESCENT, "line_gap": 0},
        "styles": list(results),
        "scope": "Static family structure, style linking, shaping, coverage and rasterization. "
                 "Application integration requires testing in the target product.",
    }
    (directory / "validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
