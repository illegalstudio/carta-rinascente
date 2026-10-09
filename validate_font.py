"""Check exported fonts through FontTools, FreeType and HarfBuzz."""
from io import BytesIO
from pathlib import Path
import hashlib
import json
import unicodedata

from fontTools.ttLib import TTFont
from PIL import ImageFont
import uharfbuzz as hb

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'dist'
TTF = OUT / 'CartaRinascente-Regular.ttf'
WOFF = OUT / 'CartaRinascente-Regular.woff2'


def shape(data, text, kern=True):
    face = hb.Face(data)
    font = hb.Font(face)
    font.scale = (face.upem, face.upem)
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(font, buffer, {'kern': kern})
    return [(i.codepoint, p.x_advance, p.y_advance, p.x_offset, p.y_offset)
            for i, p in zip(buffer.glyph_infos, buffer.glyph_positions)]


def validate():
    data = TTF.read_bytes()
    font = TTFont(TTF, checkChecksums=2)
    font.ensureDecompiled()
    cmap = font.getBestCmap()
    expected = list(range(32, 127)) + list(range(160, 256))
    assert not [cp for cp in expected if cp not in cmap], 'Missing Basic Latin or Latin-1'
    assert all(cp in cmap for cp in map(ord, 'àèéìòùÀÈÉÌÒÙ€‘’“”«»…'))
    assert font['OS/2'].fsType == 0
    assert font['OS/2'].version >= 4
    assert 'GPOS' in font and 'GDEF' in font
    whitespace = {32, 160, 0x2002, 0x2003, 0x2009, 0x200B, 0x202F}
    glyph_bounds = []
    for cp, name in cmap.items():
        g = font['glyf'][name]
        assert name != '.notdef'
        if cp not in whitespace:
            assert g.numberOfContours > 0, f'Empty glyph U+{cp:04X}'
            glyph_bounds.append((g.yMin, g.yMax))
            assert g.yMax <= font['OS/2'].usWinAscent, f'Top clipping U+{cp:04X}'
            assert g.yMin >= -font['OS/2'].usWinDescent, f'Bottom clipping U+{cp:04X}'
    samples = [
        'Carta Rinascente', 'Perché la città è già più bella?',
        'À È É Ì Ò Ù à è é ì ò ù', 'minimum illimitato fili foglie qui quattro',
        'AVATAR WA VA To Ta Te Yo Wo fi fl ffi ffl',
        'Il viaggio: € 125,90. 09/10/2026 (ore 14:30)',
        'Æ Œ æ œ ð þ Ð Þ µ ß ı ȷ',
    ]
    all_text = ''.join(chr(cp) for cp in cmap)
    for sample in samples + [all_text]:
        result = shape(data, sample)
        assert all(row[0] != 0 for row in result), f'HarfBuzz .notdef: {sample!r}'
    for sample in samples[:3]:
        assert shape(data, unicodedata.normalize('NFC', sample)) == shape(data, unicodedata.normalize('NFD', sample)), 'Decomposed accent mismatch'
    assert sum(x[1] for x in shape(data, 'AVATAR')) < sum(x[1] for x in shape(data, 'AVATAR', kern=False)), 'Kerning inactive'
    for cp in cmap:
        if 0x300 <= cp <= 0x36F:
            continue
        # Soft hyphen is intentionally hidden by the layout engine unless
        # a word is broken at a line boundary; its outline is checked above.
        if cp not in whitespace and cp != 0xAD:
            for size in (24, 64):
                ft = ImageFont.truetype(str(TTF), size)
                assert ft.getmask(chr(cp)).getbbox() is not None, f'FreeType empty render U+{cp:04X}'
    web = TTFont(WOFF)
    web.ensureDecompiled()
    assert web.getBestCmap() == cmap
    assert web['hmtx'].metrics == font['hmtx'].metrics
    assert web.getGlyphOrder() == font.getGlyphOrder()
    for name in font.getGlyphOrder():
        assert web['glyf'][name].getCoordinates(web['glyf']) == font['glyf'][name].getCoordinates(font['glyf'])
    web.flavor = None
    restored = BytesIO()
    web.save(restored)
    for sample in samples:
        assert shape(restored.getvalue(), sample) == shape(data, sample), 'WOFF2 round-trip shaping mismatch'
    report = {
        'result': 'PASS',
        'engines': ['FontTools table decoding', 'FreeType via Pillow', 'HarfBuzz'],
        'glyph_count': len(font.getGlyphOrder()), 'encoded_characters': len(cmap),
        'full_basic_latin_and_latin1': True, 'italian_nfc_nfd_equivalence': True,
        'kerning_active': True, 'woff2_round_trip_equivalent': True,
        'outline_y_min': min(x[0] for x in glyph_bounds),
        'outline_y_max': max(x[1] for x in glyph_bounds),
        'windows_metrics': [-font['OS/2'].usWinDescent, font['OS/2'].usWinAscent],
        'sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (TTF, WOFF)},
        'scope': 'File structure, shaping, coverage and rasterization. Browser/native application integration requires project-specific verification.',
    }
    (OUT / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    validate()
