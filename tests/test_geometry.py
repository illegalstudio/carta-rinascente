"""Regression tests for path parsing and independent per-style drawing state.

SPDX-License-Identifier: OFL-1.1
"""

import unittest

from shapely.geometry import Polygon, box

from src.config import STYLES
from src.geometry import FilledPath, GlyphBuilder, raise_italic_body, sample_path, sweep


class PathTests(unittest.TestCase):
    def test_curves_and_closure_preserve_endpoints(self):
        points = sample_path("M 0 0 Q 10 20 20 0 C 30 -20 40 -20 50 0 L 60 0 Z")
        self.assertEqual(points[0], (0, 0))
        self.assertEqual(points[-1], (0, 0))
        self.assertIn((20, 0), points)
        self.assertIn((50, 0), points)
        self.assertTrue(any(y > 0 for x, y in points))
        self.assertTrue(any(y < 0 for x, y in points))

    def test_malformed_paths_fail_instead_of_silently_losing_data(self):
        for path in ("", "M 0 0", "L 2 3", "M 0 0 C 1 2", "M 0 0 H 20",
                     "M 0 0 L 10 20 garbage", "M 0 0 M 1 2", "M 0 0 L 0 0",
                     "M 0 0 L 1 2 Z L 3 4", "M 0 0 L nan 4"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                sample_path(path)

    def test_closed_counter_remains_open(self):
        outline = sweep("M 100 0 C -50 0 -50 400 100 400 C 250 400 250 0 100 0 Z")
        self.assertTrue(outline.is_valid)
        self.assertEqual(len(outline.interiors), 1)


class BuilderTests(unittest.TestCase):
    def test_filled_contours_join_strokes_without_filling_counters(self):
        builder = GlyphBuilder(STYLES[0])
        builder.add("b", "M 0 0 L 0 400", FilledPath("M -80 0 L 80 0 L 80 20 L -80 20 Z"),
                    "M 0 50 C 300 50 300 350 0 350")
        geometry = builder.glyphs["b"].geometry
        self.assertEqual(geometry.geom_type, "Polygon")
        self.assertTrue(geometry.is_valid)
        self.assertEqual(len(geometry.interiors), 1)

    def test_invalid_filled_contours_are_rejected(self):
        builder = GlyphBuilder(STYLES[0])
        for path in ("M 0 0 L 20 0 L 20 20", "M 0 0 L 20 20 L 0 20 L 20 0 Z",
                     "M 0 0 L 20 0 L 40 0 Z"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                builder.add("x", FilledPath(path))

    def test_italic_body_enlargement_preserves_ascenders_and_descenders(self):
        body = raise_italic_body(box(0, 0, 300, 470))
        self.assertEqual(body.bounds, (0, 0, 300, 500))
        outline = Polygon([(0, -220), (300, -220), (300, 470), (200, 700), (0, 760)])
        raised = raise_italic_body(outline)
        self.assertEqual(raised.bounds, outline.bounds)
        self.assertTrue(raised.is_valid)

    def test_face_state_does_not_leak_between_builds(self):
        regular = GlyphBuilder(STYLES[0])
        bold = GlyphBuilder(STYLES[2])
        regular.add("l", "M 80 0 L 80 700")
        bold.add("l", "M 80 0 L 80 700")
        before = regular.glyphs["l"]
        bold.add("x", "M 0 0 L 300 400")
        self.assertEqual(set(regular.glyphs), {"l"})
        self.assertIs(regular.glyphs["l"], before)
        self.assertGreater(bold.glyphs["l"].geometry.area, before.geometry.area * 1.3)

    def test_explicit_zero_advance_survives(self):
        builder = GlyphBuilder(STYLES[0])
        builder.add("\u0301", "M 0 0 L 50 80", advance=0)
        self.assertEqual(builder.glyphs["\u0301"].advance, 0)

    def test_italic_pen_moves_the_ascender_right(self):
        roman = GlyphBuilder(STYLES[0])
        italic = GlyphBuilder(STYLES[1])
        for builder in (roman, italic):
            builder.add("l", "M 80 0 L 80 700")
        self.assertGreater(italic.glyphs["l"].geometry.bounds[2], roman.glyphs["l"].geometry.bounds[2] + 100)


if __name__ == "__main__":
    unittest.main()
