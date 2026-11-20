"""Drawing construction invariants using the actual guide renderer, not ImageGen."""
import unittest

import numpy as np

from render_scene import Mesh, Renderer


def image_line(renderer, start, direction):
    start = np.asarray(start, dtype=float)
    a = np.r_[renderer.project(start)[:2], 1.]
    b = np.r_[renderer.project(start + direction)[:2], 1.]
    line = np.cross(a, b)
    return line / np.linalg.norm(line[:2])


def line_intersection(line_a, line_b):
    intersection = np.cross(line_a, line_b)
    return intersection / np.linalg.norm(intersection)


class DrawingProjectionTests(unittest.TestCase):
    def mesh(self):
        mesh = Mesh()
        mesh.box([-2, -1, 0], [4, 5, 3])
        return mesh

    def perspective(self, eye, target):
        return Renderer(self.mesh(), 640, 480, projection='perspective',
                        camera_eye=eye, camera_target=target, fov=55, near=.1)

    def finite_vanishing_point(self, renderer, direction):
        # The directional limit of the existing pinhole camera. No scene point
        # needs to be placed at infinity or behind the camera.
        x, y, z = np.asarray(direction) @ renderer.basis.T
        self.assertGreater(abs(z), 1e-8)
        return np.array([-renderer.scale*x/z + renderer.w/2,
                          renderer.scale*y/z + renderer.h/2])

    def assert_converges(self, renderer, direction):
        lines = [image_line(renderer, point, direction)
                 for point in [[-1, 1, 0], [1.2, 3.1, 2], [-1.5, 2, 2.5]]]
        vp = self.finite_vanishing_point(renderer, direction)
        for line in lines:
            self.assertAlmostEqual(float(line @ np.r_[vp, 1.]), 0, places=7)
        point = line_intersection(lines[0], lines[1])
        self.assertGreater(abs(point[2]), 1e-10)
        np.testing.assert_allclose(point[:2] / point[2], vp, atol=1e-6)

    def assert_stays_parallel(self, renderer, direction):
        a = image_line(renderer, [-1, 1, 0], direction)
        b = image_line(renderer, [1.2, 3.1, 2], direction)
        self.assertAlmostEqual(float(a[0]*b[1]-a[1]*b[0]), 0, places=9)
        self.assertAlmostEqual(float(line_intersection(a, b)[2]), 0, places=9)

    def test_one_point_orientation_only_depth_family_converges(self):
        r = self.perspective([0, -10, 1.6], [0, 0, 1.6])
        self.assert_converges(r, [0, 1, 0])
        self.assert_stays_parallel(r, [1, 0, 0])
        self.assert_stays_parallel(r, [0, 0, 1])

    def test_two_point_level_view_verticals_remain_parallel(self):
        r = self.perspective([8, -10, 1.6], [0, 0, 1.6])
        self.assert_converges(r, [1, 0, 0])
        self.assert_converges(r, [0, 1, 0])
        self.assert_stays_parallel(r, [0, 0, 1])

    def test_three_point_tilted_view_verticals_converge_too(self):
        r = self.perspective([8, -10, 7], [0, 0, 1.6])
        for direction in np.eye(3):
            self.assert_converges(r, direction)
        a = image_line(r, [-1, 1, 0], [0, 0, 1])
        b = image_line(r, [1.2, 3.1, 2], [0, 0, 1])
        self.assertGreater(abs(float(a[0]*b[1]-a[1]*b[0])), .001)

    def test_orthographic_parallel_families_have_no_finite_vanishing_point(self):
        r = Renderer(self.mesh(), 640, 480, projection='orthographic', azimuth=31, elevation=35)
        for direction in np.eye(3):
            self.assert_stays_parallel(r, direction)

    def test_equal_world_segments_shrink_with_perspective_depth(self):
        r = self.perspective([0, -10, 1.6], [0, 0, 1.6])
        def width(depth):
            return np.linalg.norm(r.project([.5, depth, 1])[:2] - r.project([-.5, depth, 1])[:2])
        near, far = width(0), width(10)
        self.assertGreater(near, far)
        self.assertAlmostEqual(near/far, 2, places=9)

    def test_orthographic_size_is_invariant_under_depth_translation(self):
        r = Renderer(self.mesh(), 640, 480, projection='orthographic', azimuth=31, elevation=35)
        a, b = np.array([0., 0., 0.]), np.array([0., 0., 1.8])
        delta = 20 * r.basis[2]
        near = r.project(b)[:2] - r.project(a)[:2]
        far = r.project(b+delta)[:2] - r.project(a+delta)[:2]
        np.testing.assert_allclose(near, far, atol=1e-10)

    def test_world_height_and_foot_contact_are_preserved_at_multiple_depths(self):
        r = self.perspective([0, -10, 1.6], [0, 0, 1.6])
        heights = []
        for depth in [0, 4, 10]:
            foot = np.array([.8, depth, 0.])
            head = foot + [0, 0, 1.8]
            support_surface = np.array([.8, depth, 0.])
            self.assertAlmostEqual(float(np.linalg.norm(head-foot)), 1.8)
            np.testing.assert_allclose(r.project(foot), r.project(support_surface))
            heights.append(np.linalg.norm(r.project(head)[:2]-r.project(foot)[:2]))
        self.assertGreater(heights[0], heights[1])
        self.assertGreater(heights[1], heights[2])

    def test_common_head_screen_height_is_not_a_rule_for_tilt_or_different_levels(self):
        level = self.perspective([0, -10, 1.8], [0, 0, 1.8])
        # Equal heads share a horizon only in this special level-camera setup.
        self.assertAlmostEqual(level.project([0, 0, 1.8])[1], level.project([0, 10, 1.8])[1])
        tilted = self.perspective([0, -10, 5], [0, 0, 1.8])
        self.assertGreater(abs(tilted.project([0, 0, 1.8])[1]-tilted.project([0, 10, 1.8])[1]), 10)
        self.assertGreater(abs(level.project([0, 0, 1.8])[1]-level.project([0, 0, 4.8])[1]), 10)

    def test_special_effects_are_not_silently_treated_as_linear_perspective(self):
        for mode in ['fisheye', 'droste']:
            with self.assertRaisesRegex(ValueError, 'Unknown projection'):
                Renderer(self.mesh(), 640, 480, projection=mode)


if __name__ == '__main__':
    unittest.main()
