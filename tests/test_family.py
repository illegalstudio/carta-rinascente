"""Composition and release checks that guard multi-style font regressions.

SPDX-License-Identifier: OFL-1.1
"""

from pathlib import Path
import unittest
from unittest.mock import patch

from shapely.affinity import translate
from shapely.geometry import LineString, box

from src.anchors import mark_anchor
from src.build import build_family
from src.composition import _accented_letters, _additional_symbols
from src.config import STYLES
from src.design import roman
from src.features import kerning_pairs
from src.geometry import GlyphBuilder, Shape


class OutlineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.roman_builders = []
        for style in (STYLES[0], STYLES[2]):
            builder = GlyphBuilder(style)
            roman.draw(builder)
            roman.draw_numerals(builder)
            cls.roman_builders.append((style, builder))

    def test_roman_stems_stay_inside_flat_serif_feet(self):
        for style, builder in self.roman_builders:
            # Round bowls, bare terminals and flared feet have their own overshoot.
            for char in 'AdfhiklmnrxHIKMPRTXY14':
                with self.subTest(style=style.name, char=char):
                    self.assertGreaterEqual(builder.glyphs[char].geometry.bounds[1], -0.1)
            for char in 'pq':
                with self.subTest(style=style.name, char=char):
                    self.assertGreaterEqual(builder.glyphs[char].geometry.bounds[1], -212.1)

    def test_curved_r_leg_has_no_inward_spur_above_the_baseline(self):
        for style, builder in self.roman_builders:
            glyph = builder.glyphs['R']
            edges = [glyph.geometry.intersection(LineString(
                [(glyph.advance * 0.45, y), (glyph.advance, y)])).bounds[0]
                for y in range(2, 100, 2)]
            for lower, upper in zip(edges, edges[1:]):
                with self.subTest(style=style.name):
                    self.assertGreaterEqual(lower, upper - 0.5)

    def test_pilcrow_stems_remain_separate_below_the_bowl(self):
        for style in STYLES:
            builder = GlyphBuilder(style)
            _additional_symbols(builder)
            glyph = builder.glyphs['¶']
            section = glyph.geometry.intersection(LineString([(0, 100), (glyph.advance, 100)]))
            with self.subTest(style=style.name):
                self.assertEqual(section.geom_type, 'MultiLineString')
                self.assertEqual(len(section.geoms), 2)
                self.assertGreater(section.geoms[0].distance(section.geoms[1]), 20)


class CompositionTests(unittest.TestCase):
    def test_contextual_commas_remain_clear_of_the_base(self):
        for style in STYLES:
            with self.subTest(style=style.name):
                builder = GlyphBuilder(style)
                for char in 'dltg':
                    height = 500 if char == 'g' else 700
                    builder.glyphs[char] = Shape(box(30, 0, 300, height), 336, char)
                _accented_letters(builder)
                for base, composed in (('d', 'ď'), ('l', 'ľ'), ('t', 'ť'), ('g', 'ģ')):
                    original = builder.glyphs[base].geometry
                    modified = builder.glyphs[composed]
                    mark = modified.geometry.difference(original)
                    self.assertGreater(mark.distance(original), 10)
                    if base == 'g':
                        self.assertGreater(mark.bounds[1], original.bounds[3])
                    else:
                        self.assertGreater(mark.bounds[0], original.bounds[2])
                        self.assertGreater(modified.advance, builder.glyphs[base].advance)

    def test_composed_accent_uses_the_same_anchor_as_gpos(self):
        for style in STYLES:
            with self.subTest(style=style.name):
                builder = GlyphBuilder(style)
                builder.glyphs['a'] = Shape(box(30, 0, 230, 450), 261, 'a')
                _accented_letters(builder)
                x, y = mark_anchor(builder.glyphs['a'], 'a', '\u0301', style)
                expected = builder.glyphs['a'].geometry.union(
                    translate(builder.glyphs['\u0301'].geometry, xoff=x, yoff=y))
                self.assertTrue(expected.equals(builder.glyphs['á'].geometry))
                self.assertEqual(builder.glyphs['á'].advance, 261)

    def test_kerning_propagates_to_accented_bases(self):
        glyphs = {'A': Shape(box(0, 0, 10, 10), 100, 'A'),
                  'À': Shape(box(0, 0, 10, 10), 100, 'A'),
                  'V': Shape(box(0, 0, 10, 10), 100, 'V')}
        pairs = kerning_pairs(glyphs, STYLES[0])
        self.assertLess(pairs['A', 'V'], 0)
        self.assertEqual(pairs['Agrave', 'V'], pairs['A', 'V'])

    def test_punctuation_kerning_keeps_accented_letter_variants(self):
        glyphs = {'[': Shape(box(0, 0, 10, 10), 100, '['),
                  'j': Shape(box(0, 0, 10, 10), 100, 'j'),
                  'ĵ': Shape(box(0, 0, 10, 10), 100, 'j'),
                  'd': Shape(box(0, 0, 10, 10), 100, 'd'),
                  'ď': Shape(box(0, 0, 10, 10), 100, 'd'),
                  "'": Shape(box(0, 0, 10, 10), 100, "'")}
        for style in (STYLES[0], STYLES[2]):
            with self.subTest(style=style.name):
                pairs = kerning_pairs(glyphs, style)
                self.assertGreater(pairs['bracketleft', 'j'], 0)
                self.assertEqual(pairs['bracketleft', 'jcircumflex'], pairs['bracketleft', 'j'])
        for style in (STYLES[1], STYLES[3]):
            with self.subTest(style=style.name):
                pairs = kerning_pairs(glyphs, style)
                self.assertGreater(pairs['d', 'quotesingle'], 0)
                self.assertEqual(pairs['dcaron', 'quotesingle'], pairs['d', 'quotesingle'])


class ReleaseTests(unittest.TestCase):
    def test_failed_build_does_not_publish_partial_fonts(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory(prefix='.build-test-', dir=Path.cwd()) as temporary:
            output = Path(temporary) / 'dist'
            output.mkdir()
            original = output / 'CartaRinascente-Regular.ttf'
            original.write_bytes(b'previous release')

            def fail(style, staging):
                (staging / 'CartaRinascente-Regular.ttf').write_bytes(b'incomplete')
                raise ValueError('intentional build failure')

            with patch('src.build.compile_style', side_effect=fail):
                with self.assertRaisesRegex(ValueError, 'intentional build failure'):
                    build_family(output)
            self.assertEqual(original.read_bytes(), b'previous release')
            self.assertEqual(list(Path(temporary).iterdir()), [output])


if __name__ == '__main__':
    unittest.main()
