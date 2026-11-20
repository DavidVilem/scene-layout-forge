import copy,unittest
import numpy as np
from dry_dock import scene
from scene_model import validate
from render_scene import build,Renderer
from finish_contract import freeze,check,correction,preflight,handoff
from registered_geometry import errors as mesh_errors

class RegisteredWorkflowTests(unittest.TestCase):
    def setUp(self):self.d=scene()
    def ship(self):return next(p for p in self.d['parts'] if p['id']=='ship')
    def fails(self,text):self.assertTrue(any(text in e for e in validate(self.d)),validate(self.d))
    def test_scene_and_all_faces_registered(self):
        self.assertEqual(validate(self.d),[]);m=build(self.d)
        self.assertEqual(set(m.face_owners),set(range(len(m.faces))))
        self.assertIn('ship',m.face_owners.values())
    def test_unknown_face_rejected_before_render(self):
        m=build(self.d);m.box((0,0,0),(1,1,1))
        with self.assertRaisesRegex(ValueError,'geometry changed'):Renderer(m,200,200)
    def test_vertex_mutation_rejected(self):
        m=build(self.d);m.faces[0][0][0][0]+=.1
        with self.assertRaisesRegex(ValueError,'geometry changed'):Renderer(m,200,200)
    def test_unregistered_edge_rejected(self):
        m=build(self.d);m.edges.append((np.zeros(3),np.ones(3)))
        with self.assertRaisesRegex(ValueError,'geometry changed'):Renderer(m,200,200)
    def test_lifted_hull_breaks_contacts(self):
        self.ship()['origin'][2]+=.1;self.fails('height mismatch')
    def test_contact_patch_not_on_surface(self):
        for point in self.d['custom_contacts'][0]['points']:point[1]+=.5
        self.fails('contact patch misses')
    def test_point_contact_is_not_patch(self):
        self.d['custom_contacts'][0]['points']=[[10,14,1.2]]*3;self.fails('must have area')
    def test_missing_contact_cannot_use_bbox_bearing(self):
        self.d['custom_contacts']=[]
        self.fails('custom surface contact required')
    def test_nonfinite_custom_geometry(self):
        self.ship()['parameters']['vertices'][0][0]=float('nan');self.fails('finite')
    def test_bad_face_index(self):
        self.ship()['parameters']['faces'][0][0]=10000;self.fails('face indices')
    def test_missing_adapter_limits(self):
        del self.ship()['parameters']['limitations'];self.fails('limitations')
    def test_side_mount_gap(self):
        next(p for p in self.d['parts'] if p['id']=='wall-service-0')['origin'][1]-=.1;self.fails('mount surface gap')
    def test_correction_preserves_intake_and_discharge(self):
        lock=freeze(self.d);text=correction(lock,self.d,[{'kind':'annotation','target':'2'}])
        self.assertIn('never reconnect to a dock sump',text)
        self.assertIn('underground intake unmodeled, not discharge',text)
        self.assertIn('NOT a sealed end',text)
    def test_changed_boundary_role_rejected(self):
        lock=freeze(self.d)
        next(p for p in self.d['parts'] if p['id']=='discharge-header')['interfaces']['external']['role']='inlet'
        with self.assertRaisesRegex(ValueError,'scene changed'):correction(lock,self.d,[])
    def test_changed_route_rejected(self):
        lock=freeze(self.d);self.d['connections'][0]['route'][1][0]+=.1
        with self.assertRaisesRegex(ValueError,'scene changed'):check(lock,self.d)
    def test_freeform_topology_correction_rejected(self):
        lock=freeze(self.d)
        with self.assertRaisesRegex(ValueError,'kind and target only'):correction(lock,self.d,[{'kind':'interface_clarity','target':'pump-0','instruction':'send discharge to sump'}])
    def test_corrupted_lock_rejected(self):
        lock=freeze(self.d);lock['scene']['parts'][0]['size'][0]+=1
        with self.assertRaisesRegex(ValueError,'lock itself'):check(lock,self.d)
    def test_missing_detail_components_rejected(self):
        self.d['detail_regions'][0]['secondary'].append('imaginary-assembly')
        self.assertTrue(any('unregistered detail' in x for x in preflight(self.d)))
    def test_empty_secondary_plan_rejected(self):
        self.d['detail_regions'][0]['secondary']=[]
        self.assertTrue(any('secondary assemblies' in x for x in preflight(self.d)))
    def test_old_corrections_do_not_mutate_source(self):
        before=copy.deepcopy(self.d);lock=freeze(self.d)
        correction(lock,self.d,[{'kind':'tone','target':'paper'}]);self.assertEqual(self.d,before)
    def test_malformed_detail_lists_report_error(self):
        for bad in ['ship',None,[{}]]:
            self.d=scene();self.d['detail_regions'][0]['primary']=bad
            self.assertIn('detail component IDs must be lists of strings',preflight(self.d))
    def test_missing_region_name_reported(self):
        del self.d['detail_regions'][0]['name']
        self.assertIn('detail region name required',preflight(self.d))
    def test_handoff_binds_ids_to_shapes_and_camera(self):
        self.d['camera']={'eye':[17,-16,14],'target':[17,10,4],'fov':60}
        text=handoff(freeze(self.d))
        self.assertIn('pump-0: pump, origin=',text)
        self.assertIn('Chosen camera:',text)
    def test_camera_change_requires_new_lock(self):
        self.d['camera']={'eye':[17,-16,14],'target':[17,10,4],'fov':60}
        lock=freeze(self.d);self.d['camera']['fov']=40
        with self.assertRaisesRegex(ValueError,'scene changed'):check(lock,self.d)
    def test_count_repair_uses_registered_instances(self):
        text=correction(freeze(self.d),self.d,[{'kind':'count','target':'footing'}])
        self.assertIn('exactly 6 requested footing',text)
        self.assertIn('never expose physically hidden inventory',text)
        self.assertIn('keel-block-5',text)
        self.assertIn('never reconnect to a dock sump',text)
    def test_count_evidence_rejects_outside_image(self):
        with self.assertRaisesRegex(ValueError,'normalized'):
            correction(freeze(self.d),self.d,[{'kind':'count','target':'footing','extra_at':[2,.5]}])

if __name__=='__main__':unittest.main()
