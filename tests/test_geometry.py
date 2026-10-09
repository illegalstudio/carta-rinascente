"""Regression tests for path parsing and independent per-style drawing state.

SPDX-License-Identifier: OFL-1.1
"""

import unittest

from shapely.geometry import LineString, Polygon, box

from src.config import STYLES
from src.geometry import (FilledPath, GlyphBuilder, PenStroke, dot, raise_italic_body,
                          sample_path, soften_corners, sweep)


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

    def test_path_expansion_preserves_stroke_weight_and_height(self):
        stem = "M 100 0 L 100 500"
        original = sweep(stem)
        expanded = sweep(stem, path_width_scale=1.25)
        self.assertAlmostEqual(expanded.bounds[2] - expanded.bounds[0],
                               original.bounds[2] - original.bounds[0])
        self.assertEqual(expanded.bounds[1::2], original.bounds[1::2])
        self.assertAlmostEqual(expanded.area, original.area)
        oval = "M 100 0 C -50 0 -50 400 100 400 C 250 400 250 0 100 0 Z"
        before, after = sweep(oval), sweep(oval, path_width_scale=1.25)
        self.assertGreater(after.interiors[0].bounds[2] - after.interiors[0].bounds[0],
                           before.interiors[0].bounds[2] - before.interiors[0].bounds[0])
        self.assertEqual(after.bounds[1::2], before.bounds[1::2])

    def test_nib_depth_strengthens_hairlines_without_widening_stems(self):
        builder = GlyphBuilder(STYLES[0])
        for path, axis in (("M 0 0 L 300 0", 1), ("M 0 0 L 0 300", 0)):
            before = builder.stroke(path)
            after = builder.stroke(PenStroke(path, nib_depth=20))
            old_width = before.bounds[axis + 2] - before.bounds[axis]
            new_width = after.bounds[axis + 2] - after.bounds[axis]
            if axis == 1:
                self.assertGreater(new_width, old_width)
            else:
                self.assertAlmostEqual(new_width, old_width)

    def test_local_pressure_preserves_stem_entry_and_lightens_return(self):
        path = "M 0 500 L 0 0 L 250 0"
        before = sweep(path, tips=(1, 1), nib_angle=0)
        after = sweep(path, tips=(1, 1), nib_angle=0,
                      pressure_profile=((0, 1), (0.6, 1), (1, 0.5)))
        entry = LineString([(-100, 400), (100, 400)])
        return_stroke = LineString([(200, -100), (200, 100)])
        self.assertAlmostEqual(before.intersection(entry).length, after.intersection(entry).length)
        self.assertLess(after.intersection(return_stroke).length,
                        before.intersection(return_stroke).length * 0.6)
        self.assertTrue(after.is_valid)
        self.assertEqual(after.geom_type, "Polygon")

    def test_pressure_depends_on_distance_not_path_command_count(self):
        profile = ((0, 1), (0.5, 0.6), (1, 1))
        sparse = sweep("M 0 0 L 350 0", tips=(1, 1), pressure_profile=profile)
        split = sweep("M 0 0 L 1 0 L 2 0 L 3 0 L 350 0", tips=(1, 1), pressure_profile=profile)
        self.assertLess(sparse.hausdorff_distance(split), 0.02)

    def test_invalid_pressure_profiles_and_depth_fail(self):
        for profile in (((0, 1),), ((0.1, 1), (1, 1)), ((0, 1), (0.9, 1)),
                        ((0, 1), (0.5, 1), (0.5, 0.7), (1, 1)),
                        ((0, 1), (1, 0)), ((0, 1), (1, float("nan")))):
            with self.subTest(profile=profile), self.assertRaises(ValueError):
                sweep("M 0 0 L 100 0", pressure_profile=profile)
        for depth in (0, -1):
            with self.subTest(depth=depth), self.assertRaises(ValueError):
                sweep("M 0 0 L 100 0", nib_depth=depth)


class BuilderTests(unittest.TestCase):
    def test_round_dot_preserves_its_diameter_when_paths_are_widened(self):
        for style in STYLES:
            with self.subTest(style=style.name):
                geometry = GlyphBuilder(style).stroke(dot(100, 600))
                x0, y0, x1, y1 = geometry.bounds
                self.assertAlmostEqual(x1 - x0, y1 - y0)
                self.assertAlmostEqual(geometry.centroid.x, 100 * style.path_width_scale)
                self.assertAlmostEqual(geometry.centroid.y, 600)

    def test_corner_refinement_preserves_counters_and_overall_dimensions(self):
        original = box(0, 0, 100, 400).difference(box(20, 20, 80, 380))
        rounded = soften_corners(original)
        self.assertTrue(rounded.is_valid)
        self.assertEqual(len(rounded.interiors), 1)
        self.assertLess(rounded.hausdorff_distance(original), 3)
        self.assertGreater(rounded.symmetric_difference(original).area, 10)
        for before, after in zip(original.bounds, rounded.bounds):
            self.assertAlmostEqual(before, after, delta=0.1)

    def test_derived_ink_does_not_expand_completed_glyph_coordinates(self):
        builder = GlyphBuilder(STYLES[1])
        stem = builder.ink("M 200 0 L 200 500", path_width_scale=1.0)
        expanded = builder.ink("M 200 0 L 200 500")
        self.assertAlmostEqual(stem.centroid.x, 200, delta=0.1)
        self.assertAlmostEqual(expanded.centroid.x, 200 * STYLES[1].path_width_scale, delta=0.1)
        self.assertAlmostEqual(stem.area, expanded.area)

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
