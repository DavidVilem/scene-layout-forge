import copy
from types import SimpleNamespace
import unittest

import numpy as np

from projection_review import choose, rank, review

class ProjectionTests(unittest.TestCase):
    def test_missing_subject_rejected_despite_large_focus(self):
        reports={'close':{'components':{'pump':{'visible_pixels':100,'width_fraction':.9}},'floor_fraction':.1},
                 'wide':{'components':{'pump':{'visible_pixels':50,'width_fraction':.2},'worker':{'visible_pixels':4,'width_fraction':.01}},'floor_fraction':.3}}
        self.assertEqual(choose(reports,['pump','worker'],['pump']),'wide')
    def test_no_visible_candidate_requires_redesign(self):
        with self.assertRaises(ValueError):choose({'a':{'components':{},'floor_fraction':0}},['worker'],['pump'])
    def test_clipped_access_is_not_complete(self):
        r={'a':{'components':{'stairs':{'visible_pixels':20,'width_fraction':.2,'fully_in_frame':False}},'floor_fraction':.1}}
        with self.assertRaises(ValueError):choose(r,['stairs'],['stairs'],full=['stairs'])
    def test_readable_focal_assembly_preferred(self):
        reports={name:{'components':{'pump':{'visible_pixels':100,'width_fraction':w}},'floor_fraction':.2} for name,w in [('a',.1),('b',.3)]}
        self.assertEqual(choose(reports,['pump'],['pump']),'b')

    def test_larger_focal_width_cannot_compensate_hidden_junction(self):
        reports = {name: {'components': {'pump': {'visible_pixels': 200, 'width_fraction': width}},
                         'floor_fraction': 0, 'junctions': {'shaft': {'required': True, 'visible': visible}}}
                   for name, width, visible in [('large', .8, False), ('oblique', .2, True)]}
        self.assertEqual(choose(reports, ['pump'], ['pump']), 'oblique')
        ranked = rank(reports, ['pump'], ['pump'])
        self.assertFalse(ranked[1]['admissible'])
        self.assertIn('shaft', ranked[1]['failures'][0])

    def test_missing_junction_evidence_is_not_a_pass(self):
        report = {'components': {'pump': {'visible_pixels': 20, 'width_fraction': .2}}, 'floor_fraction': 0}
        with self.assertRaisesRegex(ValueError, 'junctions'):
            choose({'camera': report}, ['pump'], ['pump'], critical_junctions=['shaft'])
        other = copy.deepcopy(report)
        other['junctions'] = {'shaft': {'required': True, 'visible': True}}
        self.assertEqual(choose({'missing': report, 'measured': other}, ['pump'], ['pump']), 'measured')

    def test_owned_area_beats_long_thin_silhouette_and_empty_floor(self):
        reports = {name: {'components': {'pump': {'visible_pixels': pixels, 'width_fraction': width,
                                                 'area_fraction': area}}, 'floor_fraction': floor}
                   for name, pixels, width, area, floor in [('thin', 200, .9, .0002, 0),
                                                           ('readable', 20000, .25, .02, .5)]}
        self.assertEqual(choose(reports, ['pump'], ['pump']), 'readable')

    def test_detail_distribution_beats_single_enlarged_focus(self):
        def report(hidden):
            components = {'assembly': {'visible_pixels': 3000, 'width_fraction': .6, 'area_fraction': .03}}
            for key in ['joint-a', 'joint-b', 'services']:
                components[key] = {'visible_pixels': 0 if hidden and key != 'joint-a' else 300,
                                   'width_fraction': .05, 'area_fraction': 0 if hidden and key != 'joint-a' else .005}
            return {'components': components, 'floor_fraction': .2,
                    'regions': [{'name': key, 'visible_secondary': [] if components[key]['visible_pixels'] == 0 else [key],
                                 'hidden_secondary': [key] if components[key]['visible_pixels'] == 0 else []}
                                for key in ['joint-a', 'joint-b', 'services']]}
        reports = {'uneven': report(True), 'distributed': report(False)}
        self.assertEqual(choose(reports, ['assembly'], ['assembly']), 'distributed')
        self.assertGreater(rank(reports, ['assembly'], ['assembly'])[0]['metrics']['detail_balance'], 0)

    def test_requested_readability_is_a_gate(self):
        r = {'components': {'worker': {'visible_pixels': 1, 'width_fraction': .02}}, 'floor_fraction': 0}
        with self.assertRaises(ValueError):
            choose({'tiny': r}, ['worker'], ['worker'], readable=['worker'])

    def test_no_angle_or_projection_type_is_privileged(self):
        for angle, projection in [(17, 'perspective'), (180, 'orthographic'), (307, 'perspective')]:
            good = {'components': {'pump': {'visible_pixels': 100, 'width_fraction': .2}},
                    'floor_fraction': .2, 'camera': {'azimuth': angle, 'projection': projection}}
            bad = copy.deepcopy(good); bad['components']['pump']['visible_pixels'] = 0
            self.assertEqual(choose({'chosen': good, 'other': bad}, ['pump'], ['pump']), 'chosen')


class ProjectionWitnessTests(unittest.TestCase):
    def setUp(self):
        owner = np.zeros((100, 100), dtype=int)
        owner[45:55, 45:50] = 1; owner[45:55, 50:55] = 2
        self.renderer = SimpleNamespace(owner=owner, part_ids={'shaft': 1, 'bearing': 2}, w=100, h=100,
                                        project=lambda p: np.asarray(p, dtype=float))
        self.scene = {'parts': [{'id': key, 'kind': 'machine', 'origin': [x, 45, 0], 'size': [5, 10, 1]}
                                for key, x in [('shaft', 45), ('bearing', 50)]],
                      'camera_junctions': [{'id': 'shaft-bearing', 'point': [50, 50, 0],
                                            'owners': ['shaft', 'bearing'], 'radius_fraction': .05}]}

    def test_local_surface_ownership_witness(self):
        report = review(self.renderer, self.scene)
        self.assertTrue(report['junctions']['shaft-bearing']['visible'])
        self.assertAlmostEqual(report['components']['shaft']['area_fraction'], .005)
        self.assertEqual(report['components']['shaft']['visible_pixels'], 50)

    def test_component_visible_elsewhere_does_not_prove_junction_visible(self):
        self.renderer.owner[45:55, 50:55] = 3
        self.renderer.owner[70:80, 70:80] = 2
        report = review(self.renderer, self.scene)
        self.assertGreater(report['components']['bearing']['visible_pixels'], 0)
        self.assertFalse(report['junctions']['shaft-bearing']['visible'])
        with self.assertRaises(ValueError):
            choose({'hidden': report}, ['shaft', 'bearing'], ['shaft'])

    def test_off_frame_and_unknown_owner_fail_witness(self):
        for point, owners in [([-10, 50, 0], ['shaft', 'bearing']), ([50, 50, 0], ['shaft', 'unknown'])]:
            self.scene['camera_junctions'][0].update(point=point, owners=owners)
            self.assertFalse(review(self.renderer, self.scene)['junctions']['shaft-bearing']['visible'])

    def test_malformed_witness_not_silently_accepted(self):
        self.scene['camera_junctions'][0]['owners'] = ['shaft']
        with self.assertRaises(ValueError):
            review(self.renderer, self.scene)
