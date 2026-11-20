import copy
import math
import unittest
from dataclasses import asdict
import numpy as np

from actor_plan import ActorPlan,contact_checks,scene_errors
from worker_pose import make_worker_pose,contact_anchors,collision_status
from worker_pose_examples import seated_scene,leaning_scene,contact_atlas_scene
from scene_model import validate,make_part
from render_scene import build,Mesh
from registered_geometry import on_triangle
from relation_contracts import witness_errors


class SituatedPoseTests(unittest.TestCase):
    def test_both_original_situated_fixtures_pass_strict(self):
        for factory in (seated_scene,leaning_scene,contact_atlas_scene):
            scene=factory();before=copy.deepcopy(scene)
            self.assertEqual(validate(scene),[])
            self.assertTrue(all(c['status']=='passed' for c in contact_checks(scene)))
            self.assertEqual(scene,before)

    def test_missing_seat_rejected(self):
        s=seated_scene();s['parts']=[p for p in s['parts'] if p['id']!='seat'];s['bearings']=[b for b in s['bearings'] if b['part']!='seat']
        self.assertTrue(scene_errors(s));self.assertTrue(validate(s))

    def test_changed_seat_height_does_not_leave_pelvis_floating(self):
        s=seated_scene();seat=next(p for p in s['parts'] if p['id']=='seat');seat['size'][2]-=.1
        self.assertTrue(any('pelvis' in e and 'detached' in e for e in scene_errors(s)))

    def test_seat_moved_to_neighboring_figure_is_not_a_witness(self):
        s=seated_scene();next(p for p in s['parts'] if p['id']=='seat')['origin'][0]+=1
        self.assertTrue(any('pelvis' in e for e in scene_errors(s)))

    def test_hand_hovering_over_lowered_worktop_fails(self):
        s=leaning_scene();next(p for p in s['parts'] if p['id']=='bench/top')['origin'][2]-=.025
        self.assertTrue(any('left_hand' in e and 'detached' in e for e in scene_errors(s)))

    def test_foot_target_on_another_floor_is_rejected(self):
        s=seated_scene();floor=next(p for p in s['parts'] if p['id']=='floor');floor['origin'][2]-=.1
        self.assertTrue(any('foot' in e and 'detached' in e for e in scene_errors(s)))

    def test_each_required_pose_contact_is_explicit(self):
        s=seated_scene();s['actor_contacts']=[c for c in s['actor_contacts'] if c['anchor']!='pelvis']
        self.assertTrue(any('missing' in e for e in scene_errors(s)))

    def test_contact_name_cannot_substitute_for_geometry(self):
        s=leaning_scene();s['actor_contacts'][-1]['target']='floor'
        self.assertTrue(any('differs from situated task' in e for e in scene_errors(s)))

    def test_contacts_reject_stale_world_points(self):
        s=seated_scene();s['actor_contacts'][0]['point'][0]+=.1
        self.assertTrue(any('stale' in e for e in scene_errors(s)))

    def test_duplicate_contact_is_rejected(self):
        s=seated_scene();s['actor_contacts'].append(copy.deepcopy(s['actor_contacts'][0]))
        self.assertTrue(any('Duplicate' in e for e in scene_errors(s)))

    def test_nonfinite_contact_cannot_silently_pass(self):
        for field in ('point','normal'):
            s=seated_scene();s['actor_contacts'][0][field][0]=float('nan')
            self.assertTrue(any('finite coordinates' in e for e in scene_errors(s)))

    def test_exact_actor_count_stays_separate_from_pose_height(self):
        s=contact_atlas_scene();self.assertEqual(s['expected_counts']['worker'],2)
        self.assertEqual(s['actor_plan']['exact_count'],2)
        for a in s['actor_plan']['actors']:
            p=next(p for p in s['parts'] if p['id']==a['id'])
            self.assertEqual(a['physical_height'],1.8);self.assertLess(p['size'][2],a['physical_height'])
        s['actor_plan']['exact_count']=3;self.assertTrue(scene_errors(s))

    def test_changing_stature_without_regenerating_pose_fails(self):
        s=seated_scene();s['actor_plan']['actors'][0]['physical_height']=2.1
        self.assertTrue(any('stature' in e for e in scene_errors(s)))

    def test_seated_label_does_not_convert_standing_geometry(self):
        s=seated_scene();p=next(p for p in s['parts'] if p['id']=='seated-operator');p['parameters']={}
        self.assertTrue(any('pose differs' in e for e in scene_errors(s)))

    def test_pose_cannot_omit_plan(self):
        s=leaning_scene();s.pop('actor_plan')
        self.assertTrue(any('ActorPlan version 2' in e for e in validate(s)))

    def test_unknown_pose_or_unfitted_height_remains_unsupported(self):
        for pose,kw in [('kneeling',{}),('seated',{'seat_height':1.5}),('leaning',{'hand_height':.1})]:
            with self.assertRaises(ValueError):make_worker_pose('x',pose,**kw)

    def test_legacy_standing_worker_geometry_unchanged(self):
        from components import circulation
        from scene_model import Part
        p=Part.from_data(make_part('old','worker',[0,0,0],[.5,.5,1.8]));m=Mesh();circulation(m,p)
        points=np.array([point for face,_ in m.faces for point in face])
        self.assertAlmostEqual(points[:,2].min(),0);self.assertAlmostEqual(points[:,2].max(),1.8)
        self.assertEqual(validate(dict(units='m',parts=[make_part('old','worker',[0,0,0],[.5,.5,1.8])])),[])


class PoseGeometryEvidenceTests(unittest.TestCase):
    def test_every_contact_point_lies_on_rendered_actor_and_target(self):
        for factory in (seated_scene,leaning_scene):
            s=factory();mesh=build(s)
            for c in s['actor_contacts']:
                point=np.array(c['point'])
                for owner in (c['actor'],c['target']):
                    faces=[face for i,(face,_) in enumerate(mesh.faces) if mesh.face_owners[i]==owner]
                    self.assertTrue(any(on_triangle(point,np.array(f[0]),np.array(f[i]),np.array(f[i+1])) for f in faces for i in range(1,len(f)-1)),(c['id'],owner))

    def test_posed_mesh_stays_inside_registered_envelope(self):
        from worker_pose import render
        for pose,args in [('seated',dict(seat_height=.468)),('leaning',dict(hand_height=1.008))]:
            for height,yaw in ((1.8,0),(1.8,90),(1.8,37)):
                part=make_worker_pose('person',pose,[3,-2,4],height,yaw,**args);mesh=Mesh();render(mesh,part)
                points=np.array([p for face,_ in mesh.faces for p in face]);lo=np.array(part['origin']);hi=lo+part['size']
                self.assertTrue(np.all(points>=lo-1e-6));self.assertTrue(np.all(points<=hi+1e-6))
                self.assertTrue(all(np.isfinite(points).flat))

    def test_world_frame_transforms_contacts_with_geometry(self):
        from worker_pose import render
        a=make_worker_pose('a','seated',seat_height=.468);b=make_worker_pose('b','seated',[3,4,2],yaw=90,seat_height=.468)
        first,second=contact_anchors(a),contact_anchors(b)
        for name in first:
            x,y,z=first[name]['point'];self.assertTrue(np.allclose(second[name]['point'],[3-y,4+x,2+z]))
        self.assertAlmostEqual(second['left_foot']['point'][2],2)

    def test_supported_stature_variants_remain_grounded(self):
        for h in (1.55,2.05):
            self.assertEqual(validate(seated_scene(h)),[]);self.assertEqual(validate(leaning_scene(h)),[])

    def test_pose_mesh_actually_differs_between_tasks(self):
        a=build(seated_scene());b=build(leaning_scene())
        af=[f for i,(f,_) in enumerate(a.faces) if a.face_owners[i]=='seated-operator']
        bf=[f for i,(f,_) in enumerate(b.faces) if b.face_owners[i]=='leaning-operator']
        self.assertFalse(np.array_equal(np.array(af[0]),np.array(bf[0])))

    def test_added_solid_intersects_body_and_is_not_contact_exempted(self):
        s=seated_scene();p=next(p for p in s['parts'] if p['id']=='seated-operator')
        blocker=make_part('blocker','cabinet',[-.1,-.1,.6],[.2,.2,.3])
        self.assertEqual(collision_status(p,blocker)[0],'failed')

    def test_pose_contact_relations_bind_camera_witness(self):
        s=seated_scene();w=next(w for w in s['camera_junctions'] if w['relation_type']=='seat_support')
        self.assertEqual(witness_errors(s,w),[]);w['point'][2]+=.1
        self.assertTrue(witness_errors(s,w))


if __name__=='__main__':unittest.main()
