"""Composition and release checks that guard multi-style font regressions.

SPDX-License-Identifier: OFL-1.1
"""

from pathlib import Path
import unittest
from unittest.mock import patch

from shapely.affinity import translate
from shapely.geometry import box

from src.anchors import mark_anchor
from src.build import build_family
from src.composition import _accented_letters
from src.config import STYLES
from src.features import kerning_pairs
from src.geometry import GlyphBuilder, Shape


class CompositionTests(unittest.TestCase):
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
