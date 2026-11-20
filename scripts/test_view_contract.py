import copy
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

import numpy as np
from PIL import Image
from view_contract import create, errors


class ViewContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'guide.png'
        Image.new('RGB', (40, 40), 'white').save(self.path)
        self.scene = {'parts': [], 'camera': {'azimuth': 30}, 'callouts': [{'id': 'label', 'target': 'frame', 'text': 'FRAME'}]}
        owner = np.zeros((40, 40), dtype=int)
        owner[10:30, 10:30] = 1
        owner[17:23, 17:23] = 2  # foreground occluder at centroid
        self.renderer = SimpleNamespace(owner=owner, part_ids={'frame': 1}, w=40, h=40)

    def test_anchor_on_actual_visible_surface_not_centroid_occluder(self):
        report = create(self.scene, self.scene, self.renderer, self.path)
        x, y = report['annotations'][0]['tip_xy']
        self.assertEqual(self.renderer.owner[int(y*40), int(x*40)], 1)
        self.assertEqual(errors(self.scene, report, self.path), [])
        self.assertEqual(report['pixel_review'], 'not_run')

    def test_hidden_target_blocks_handoff(self):
        self.renderer.owner[:] = 0
        with self.assertRaisesRegex(ValueError, 'lacks readable'):
            create(self.scene, self.scene, self.renderer, self.path)

    def test_changed_scene_or_guide_invalidates_binding(self):
        report = create(self.scene, self.scene, self.renderer, self.path)
        new = copy.deepcopy(self.scene); new['camera']['azimuth'] = 60
        self.assertTrue(errors(new, report))
        Image.new('RGB', (40, 40), 'black').save(self.path)
        self.assertIn('guide pixels differ from bound evidence', errors(self.scene, report, self.path))

    def test_missing_or_wrong_arrow_evidence_fails(self):
        report = create(self.scene, self.scene, self.renderer, self.path)
        report['annotations'][0]['target'] = 'neighbour'
        self.assertTrue(errors(self.scene, report))
        report['annotations'] = []
        self.assertTrue(errors(self.scene, report))

    def test_wrong_physical_cut_source_fails(self):
        display = {'representation': {'type': 'cutaway', 'physical_sha256': 'stale'}}
        with self.assertRaisesRegex(ValueError, 'different physical'):
            create(self.scene, display, self.renderer, self.path)


if __name__ == '__main__': unittest.main()
