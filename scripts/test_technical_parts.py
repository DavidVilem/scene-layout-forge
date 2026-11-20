import copy,unittest
import numpy as np
from technical_parts import KINDS
from scene_model import make_part,validate
from render_scene import build,Renderer

class TechnicalPartsTests(unittest.TestCase):
    def scene(self,kind,**params):return {'units':'m','parts':[make_part('item',kind,[2,3,4],[2,3,2],parameters=params)]}
    def test_new_kinds_have_finite_nondegenerate_bounded_mesh_in_all_axes(self):
        for kind in sorted(KINDS):
            for axis in ['x','y','z']:
                with self.subTest(kind=kind,axis=axis):
                    data=self.scene(kind,orientation=axis);self.assertEqual(validate(data),[])
                    mesh=build(data);vertices=np.array([v for f,_ in mesh.faces for v in f])
                    self.assertTrue(np.isfinite(vertices).all())
                    self.assertTrue(np.all(vertices.min(0)>=[2-1e-8,3-1e-8,4-1e-8]))
                    self.assertTrue(np.all(vertices.max(0)<=[4+1e-8,6+1e-8,6+1e-8]))
                    for face,_ in mesh.faces:self.assertGreater(np.linalg.norm(np.cross(face[1]-face[0],face[2]-face[0])),1e-10)
    def test_ring_and_bulkhead_apertures_really_remain_open(self):
        for kind in ['ring_frame','bulkhead']:
            mesh=build(self.scene(kind));r=Renderer(mesh,320,320,projection='perspective',camera_eye=[3,-5,5],camera_target=[3,4.5,5],fov=40)
            r.draw(mesh);self.assertFalse(np.isfinite(r.z[160,160]))
            self.assertGreater(np.isfinite(r.z).sum(),100)
    def test_shell_cap_and_open_arc_are_distinct(self):
        empty=build(self.scene('shell'));capped=build(self.scene('shell',capped=True));partial=build(self.scene('shell',arc_degrees=220))
        self.assertGreater(len(capped.faces),len(empty.faces))
        self.assertGreater(len(partial.edges),len(empty.edges))
    def test_invalid_parameter_controls(self):
        for params in [{'segments':0},{'segments':True},{'inner_ratio':1},{'inner_ratio':float('nan')},{'arc_degrees':361},{'orientation':'oblique'},{'rows':100000},{'capped':'yes'}]:
            data=self.scene('shell',**params);self.assertTrue(validate(data))
            with self.assertRaises(ValueError):build(data)
    def test_orthographic_plan_has_no_height_parallax(self):
        r=Renderer(build(self.scene('console')),400,400,projection='orthographic',azimuth=90,elevation=90)
        np.testing.assert_allclose(r.project([3,4,4])[:2],r.project([3,4,6])[:2],atol=1e-10)
    def test_structural_attachment_must_match(self):
        data={'units':'m','parts':[make_part('a','truss',[0,0,0],[1,2,1],ports={'end':[.5,2,.5]}),make_part('b','truss',[0,2,0],[1,2,1],ports={'start':[.5,0,.5]})], 'attachments':[{'from':'a:end','to':'b:start'}]}
        self.assertEqual(validate(data),[])
        bad=copy.deepcopy(data);bad['parts'][1]['origin'][1]+=.1;self.assertTrue(validate(bad))
        for badlink in [None,{'from':[],'to':'b:start'},{'from':'a:missing','to':'b:start'}]:
            bad=copy.deepcopy(data);bad['attachments']=[badlink];self.assertTrue(validate(bad))
    def test_worker_helmet_can_be_omitted_without_changing_envelope(self):
        a=build(self.scene('worker'));b=build(self.scene('worker',helmet=False))
        self.assertLess(len(b.faces),len(a.faces))
        vertices=np.array([v for f,_ in b.faces for v in f]);self.assertAlmostEqual(vertices[:,2].max(),6)

if __name__=='__main__':unittest.main()
