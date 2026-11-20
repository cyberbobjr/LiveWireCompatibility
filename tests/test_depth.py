"""Offline tests of tools/build_artel_depth.py (ADR-003): engine projection and encoding, box fit
on a synthetic sprite, no drawn pixel without depth. No Workshop copy needed.
Run: python tests/test_artel_depth.py
"""
import os
import sys
import unittest

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build_artel_depth as bad  # noqa: E402


def project(wx, wy, wz):
    """Screen position of a world point in a 128 x 256 cell (wz in levels)."""
    return 64 * (wx - wy) + 64, 32 * (wx + wy) + 192 - 192 * wz


def box_sprite(x0, x1, y0, y1, h):
    """Alpha of a solid box rendered with the engine projection (pixel centres inside its silhouette)."""
    alpha = np.zeros((256, 128), dtype=np.uint8)
    ys, xs = np.mgrid[0:256, 0:128]
    px, py = xs.ravel().astype(float), ys.ravel().astype(float)
    lo, hi = bad.s_interval(px, py, x0, x1, y0, y1)
    ok = (lo <= hi) & (bad.wz_of(hi, py) >= 0) & (bad.wz_of(lo, py) <= h)
    alpha.ravel()[ok] = 255
    return alpha


class Projection(unittest.TestCase):
    def test_floor_corners_and_height(self):
        self.assertAlmostEqual(bad.depth_at(0.0, 0.0), 1.0)    # far (NW) floor corner
        self.assertAlmostEqual(bad.depth_at(1.0, 0.0), 0.75)   # tile centre
        self.assertAlmostEqual(bad.depth_at(2.0, 0.0), 0.5)    # near (SE) floor corner
        self.assertAlmostEqual(bad.depth_at(1.0, 1.0), 0.25)   # one level above the centre

    def test_screen_mapping_matches_the_floor_diamond(self):
        self.assertEqual(project(0, 0, 0), (64, 192))
        self.assertEqual(project(1, 0, 0), (128, 224))
        self.assertEqual(project(1, 1, 0), (64, 256))
        self.assertEqual(project(0, 1, 0), (0, 224))
        self.assertEqual(project(0, 0, 1), (64, 0))

    def test_ray_height_is_back_to_zero_on_the_floor(self):
        # the pixel of the tile centre on the floor: wz(s = 1) = 0
        self.assertAlmostEqual(bad.wz_of(1.0, 224 - 0.5), 0.0)


class Fit(unittest.TestCase):
    def test_box_of_a_box_sprite_is_found_and_every_pixel_has_depth(self):
        alpha = box_sprite(0.2, 0.8, 0.2, 0.8, 0.5)
        depth, box, left = bad.tile_depth(alpha)
        self.assertEqual(left, 0)
        x0, x1, y0, y1, h = box
        self.assertLessEqual(abs(x0 - 0.2) + abs(x1 - 0.8) + abs(y0 - 0.2) + abs(y1 - 0.8), 0.1)
        self.assertAlmostEqual(h, 0.5, delta=0.05)
        drawn = alpha > 0
        self.assertTrue((~np.isnan(depth) == drawn).all())

    def test_front_face_is_nearer_than_the_back_floor(self):
        alpha = box_sprite(0.2, 0.8, 0.2, 0.8, 0.5)
        depth, _box, _left = bad.tile_depth(alpha)
        ys, xs = np.nonzero(alpha)
        top = depth[ys.min(), int(xs.mean())]
        bottom = depth[ys.max(), int(xs.mean())]
        self.assertLess(bottom, 0.75)          # near bottom corner of the box, in front of the centre
        self.assertGreater(top, 0.0)
        self.assertTrue(((depth[alpha > 0] >= 0) & (depth[alpha > 0] <= 1)).all())

    def test_module_against_a_wall_still_gets_a_depth_everywhere(self):
        alpha = box_sprite(0.0, 0.15, 0.3, 0.7, 0.6)
        depth, box, left = bad.tile_depth(alpha)
        self.assertEqual(left, 0)
        self.assertAlmostEqual(box[0] + box[1], 1.0)   # square, centred on the tile
        self.assertTrue((~np.isnan(depth) == (alpha > 0)).all())

    def test_piece_drawn_over_its_neighbours_is_covered(self):
        alpha = box_sprite(-0.3, 1.0, 0.2, 0.8, 0.5)
        _depth, box, left = bad.tile_depth(alpha)
        self.assertEqual(left, 0)
        self.assertLessEqual(box[0], 0.0)

    def test_stray_pixel_takes_a_neighbour_depth(self):
        alpha = box_sprite(0.2, 0.8, 0.2, 0.8, 0.5)
        ys, xs = np.nonzero(alpha)
        alpha[ys.min() - 1, int(xs.mean())] = 255   # an antialiased edge pixel above the box
        _depth, _box, left = bad.tile_depth(alpha)
        self.assertEqual(left, 0)


if __name__ == "__main__":
    unittest.main()
