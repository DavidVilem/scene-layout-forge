import copy
import unittest
from types import SimpleNamespace

import numpy as np

from scene_model import make_part
from render_scene import build, Renderer
from visual_contract import compile_visual_contract, errors, MaterialSpec
from projection_review import rank
from projection_review import review
from camera_geometry import candidates
from drawing_style import surface_coordinates, surface_hatching
from annotation_plan import create as annotations, errors as annotation_errors, route_clear, _box_mask
from context_geometry import add_tree, tree_mass
from registered_geometry import contact_errors


class VisualContractTests(unittest.TestCase):
    def scene(self):
        return {'units': 'm', 'parts': [make_part('body', 'wall', [0, 0, 0], [2, 2, 2]),
                make_part('detail', 'cabinet', [0, 2, 0], [.3, .3, .3])],
                'visual_plan': {'objective': 'Read the access panel and its attachment', 'primary': ['body'], 'readable': ['detail']},
                'context_plan': {'mode': 'isolated'},
                'detail_budget': {'regions': [{'name': 'service', 'primary': ['body'], 'secondary': ['detail']}]},
                'light_material_plan': {'materials': {'body': {'family': 'matte_metal'}}}}

    def test_contract_checks_unknown_ids_and_preserves_quiet_reason(self):
        scene = self.scene()
        self.assertEqual(errors(scene), [])
        scene['detail_budget']['regions'][0].update(secondary=[], quietReason='The cast enclosure is intentionally unadorned', quiet_kind='unadorned_surface')
        report = compile_visual_contract(scene)
        self.assertEqual(report['plans']['detail_budget']['regions'][0]['quietReason'], 'The cast enclosure is intentionally unadorned')
        scene['visual_plan']['primary'] = ['invented']
        self.assertTrue(errors(scene))

    def test_hidden_focus_is_never_admissible(self):
        report = {'components': {'body': {'visible_pixels': 0, 'width_fraction': .9, 'area_fraction': .9}}, 'floor_fraction': 0}
        self.assertFalse(rank({'hidden': report}, [], ['body'])[0]['admissible'])

    def test_common_usage_size_not_supersample_count_controls_gate(self):
        def report(size, normalized_area, span):
            return {'components': {'body': {'visible_pixels': normalized_area*(size/1024)**2,
                    'width_fraction': span/1024, 'height_fraction': span/1024,
                    'area_fraction': normalized_area/1024**2}}, 'image_size': [size, size]}
        for area, span, expected in [(8, 4, False), (40, 1, False), (40, 8, True)]:
            for size in [512, 2048]:
                self.assertEqual(rank({'view': report(size, area, span)}, [], ['body'])[0]['admissible'], expected)

    def test_actual_512_and_2048_camera_share_readability_decision(self):
        for side, expected in [(.05, False), (.7, True)]:
            scene={'units':'m','parts':[make_part('body','wall',[0,0,0],[side,side,side])]}
            mesh=build(scene)
            for size in (512,2048):
                renderer=Renderer(mesh,size,size,hatching=False,projection='perspective',camera_eye=[6,-100,12],camera_target=[0,0,0],fov=50)
                renderer.draw(mesh)
                result=rank({'camera':review(renderer,scene)},[],['body'])
                self.assertEqual(result[0]['admissible'],expected)

    def test_screen_visibility_does_not_override_failed_relation_binding(self):
        report={'components':{'body':{'visible_pixels':100,'width_fraction':.3}},
                'junctions':{'joint':{'visible':True,'required':True,'relation_errors':['point outside actual relation']}}}
        self.assertFalse(rank({'camera':report},[],['body'])[0]['admissible'])

    def test_exact_context_counts_exclusions_and_protected_ids(self):
        scene = self.scene()
        scene['context_plan'] = {'mode': 'isolated', 'entities': [{'id': 'detail', 'role': 'use', 'reason': 'equipment'}]}
        self.assertTrue(errors(scene))
        scene['context_plan'] = {'mode': 'situated', 'exclusions': ['cabinet'], 'exact_counts': {'worker': 1}}
        self.assertEqual(len(errors(scene)), 2)
        scene['context_plan'] = {'mode': 'situated', 'entities': [{'id': 'air', 'role': 'support', 'reason': 'floor', 'physical': False}]}
        self.assertTrue(errors(scene))

    def test_empty_glass_is_conditional_not_generic_bypass(self):
        scene = self.scene()
        scene['detail_budget']['regions'][0].update(secondary=[], quietReason='Clear pane', quiet_kind='clean_glazing')
        self.assertTrue(errors(scene))
        scene['light_material_plan']['materials']['body']['family'] = 'glass'
        self.assertEqual(errors(scene), [])
        scene['detail_budget']['regions'][0]['quiet_kind'] = 'anything'
        self.assertTrue(errors(scene))

    def test_named_microdetail_does_not_replace_visible_secondary(self):
        scene = self.scene()
        scene['detail_budget']['regions'][0]['microdetails'] = ['many bolts']
        report = {'image_size': [1024, 1024], 'components': {'body': {'visible_pixels': 20000, 'width_fraction': .2, 'height_fraction': .2}}}
        result = compile_visual_contract(scene, evidence=report)
        self.assertEqual(result['guide_status'], 'failed')
        self.assertTrue(any('detail lacks usable' in x for x in result['errors']))

    def test_no_plans_is_explicit_legacy(self):
        self.assertEqual(compile_visual_contract({'parts': []})['status'], 'not_run')

    def test_camera_freedom_and_requested_top_view(self):
        scene = self.scene()
        options = candidates(scene)
        self.assertGreater(len({tuple(c.get('camera_eye', [])) for c in options.values()}), 2)
        self.assertEqual(candidates(scene, intent='plan')['plan']['elevation'], 90)
        with self.assertRaises(ValueError): candidates(scene, requested={'projection': 'fisheye'})
        with self.assertRaises(ValueError): candidates(scene, intent='cutaway')
        with self.assertRaises(ValueError): candidates(scene, intent='plan', requested={'projection': 'perspective'})
        mesh = build(scene)
        for option in candidates(scene, intent='elevation', azimuths=[30], elevations=[0]).values():
            renderer = Renderer(mesh, 300, 300, **option)
            renderer.draw(mesh)
            self.assertGreater((renderer.owner > 0).sum(), 0)


class MaterialExecutionTests(unittest.TestCase):
    def test_light_and_material_change_pixels_not_geometry(self):
        scene = {'units': 'm', 'parts': [make_part('body', 'wall', [0, 0, 0], [2, 2, 2])],
                 'light_material_plan': {'key_direction': [1, 0, 1], 'materials': {'body': {'family': 'wood'}}}}
        mesh = build(scene); a = Renderer(mesh, 300, 300, finish='graphite', shadows=True)
        ia = np.asarray(a.draw(mesh))
        scene['light_material_plan']['key_direction'] = [-1, 0, 1]
        scene['light_material_plan']['materials']['body']['family'] = 'glass'
        mesh2 = build(scene); b = Renderer(mesh2, 300, 300, finish='graphite', shadows=True)
        ib = np.asarray(b.draw(mesh2))
        np.testing.assert_array_equal(a.z, b.z); np.testing.assert_array_equal(a.owner, b.owner)
        self.assertGreater(np.count_nonzero(ia != ib), 1000)

    def test_surface_frame_rotates_with_geometry_and_cylinder_seam_agrees(self):
        points = np.array([[[1., 0., .1], [0., 1., .2]], [[-1., 0., .3], [0., -1., .4]]])
        spec = {'family': 'wood', 'mapping': 'cylindrical'}
        before = surface_coordinates(points, spec)
        rotation = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
        moved = points@rotation.T + [4, 3, 2]
        after = surface_coordinates(moved, dict(spec, origin=[4, 3, 2], tangent=[0, 1, 0]))
        np.testing.assert_allclose(before, after)
        seam = np.array([[[-1., 1e-10, .2], [-1., -1e-10, .2]]])
        marks = surface_hatching(seam, dict(spec, mark='axial'), [1, 0, 0], [200, 200, 200])
        self.assertAlmostEqual(float(marks[0, 0]), float(marks[0, 1]), places=4)
        with self.assertRaises(ValueError): MaterialSpec(family='wood', axis=[1, 0, 0], tangent=[1, 0, 0])


class AnnotationRoutingTests(unittest.TestCase):
    def test_leaders_avoid_a_person_and_other_text_and_tip_remains_owned(self):
        owner = np.zeros((300, 400), dtype=np.int32)
        owner[140:240, 250:350] = 1
        owner[40:125, 140:210] = 2
        renderer = SimpleNamespace(owner=owner, part_ids={'machine': 1, 'worker': 2}, w=400, h=300)
        scene = {'parts': [{'id': 'worker', 'kind': 'worker'}], 'callouts': [
            {'id': 'one', 'target': 'machine', 'text': 'MACHINE', 'position': [.03, .05]}]}
        records = annotations(scene, renderer)
        self.assertEqual(annotation_errors(records, renderer), [])
        self.assertTrue(route_clear(records[0]['leader'], renderer, owner == 2))
        records[0]['tip_xy'] = [.4, .3]; records[0]['leader'][-1] = [.4, .3]
        self.assertTrue(annotation_errors(records, renderer))


class SituatedContextTests(unittest.TestCase):
    def test_natural_families_are_bounded_varied_and_really_touch_ground(self):
        scene = {'units': 'm', 'registered_geometry': True, 'parts': [make_part('ground', 'slab', [0, 0, -.3], [12, 5, .3])]}
        for index, family in enumerate(['broadleaf', 'columnar', 'pyramidal']):
            add_tree(scene, 'tree-' + str(index), 'ground', [index*4, 1], [3, 3, 4], family=family, seed=index)
        self.assertEqual(contact_errors(scene), [])
        self.assertNotEqual(scene['parts'][1]['parameters']['vertices'], scene['parts'][2]['parameters']['vertices'])
        mesh = build(scene); renderer = Renderer(mesh, 500, 350)
        renderer.draw(mesh)
        self.assertEqual(sum((renderer.owner == renderer.part_ids['tree-' + str(i)]).any() for i in range(3)), 3)
        scene['parts'][1]['origin'][2] += .1
        self.assertTrue(contact_errors(scene))
        with self.assertRaises(ValueError): add_tree(scene, 'outside', 'ground', [100, 100], [2, 2, 4])

    def test_actor_height_and_real_feet_cannot_be_replaced_by_shadow_or_pose_label(self):
        scene = {'parts': [make_part('ground', 'slab', [0, 0, 0], [4, 4, .2]),
                          make_part('operator', 'worker', [1, 1, .2], [.5, .5, 1.8])],
                 'bearings': [{'part': 'operator', 'on': 'ground'}],
                 'actor_plan': {'actors': [{'id': 'operator', 'task': 'observe gauges', 'physical_height': 1.8, 'support': 'ground'}], 'exact_count': 1}}
        self.assertEqual(errors(scene), [])
        scene['parts'][1]['origin'][2] += .1
        self.assertTrue(any('foot' in item for item in errors(scene)))
        scene['parts'][1]['origin'][2] -= .1
        scene['actor_plan']['actors'][0]['pose'] = 'seated'
        self.assertTrue(any('unsupported pose' in item for item in errors(scene)))
        scene['actor_plan']['actors'][0]['pose'] = 'standing'
        scene['parts'][1]['size'][2] = 2.3
        self.assertTrue(any('height' in item for item in errors(scene)))


if __name__ == '__main__': unittest.main()
