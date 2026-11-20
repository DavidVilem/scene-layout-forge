import unittest,math,numpy as np
from render_scene import Mesh,build,Renderer
from industrial_fixture import elbow,fixture

class CurveTests(unittest.TestCase):
    def test_folded_elbow_rejected_before_any_faces_are_added(self):
        points=elbow((1,2,3),.2,0,math.pi/2)
        for radius in [.2,.25]:
            mesh=Mesh()
            with self.assertRaisesRegex(ValueError,'Tube folds'):mesh.sweep(points,radius)
            self.assertEqual(mesh.faces,[])
        self.assertGreater(len(Mesh().sweep(points,.08)),2)

    def test_curvature_guard_is_scale_and_orientation_independent(self):
        from sweep_geometry import check_tube_curvature
        points=elbow((0,0,0),.2,0,math.pi/2)
        for scale in [.001,1,1000]:
            transformed=[[p[2]*scale+4,p[0]*scale-2,p[1]*scale+8] for p in points]
            check_tube_curvature(transformed,.08*scale)
            with self.assertRaisesRegex(ValueError,'Tube folds'):check_tube_curvature(transformed,.25*scale)

    def test_folded_connection_is_rejected_by_scene_validation(self):
        from scene_model import make_part,validate
        route=[list(p) for p in elbow((0,0,0),.2,0,math.pi/2)]
        data={'units':'m','parts':[
            make_part('a','column',[0,0,0],[1,1,1],ports={'out':route[0]}),
            make_part('b','column',[0,0,0],[1,1,1],ports={'in':route[-1]})],
            'connections':[{'from':'a:out','to':'b:in','route':route,'radius':.25}]}
        self.assertTrue(any('Tube folds' in error for error in validate(data)))
        data['connections'][0]['radius']=.08
        self.assertEqual(validate(data),[])

    def test_sweep_radius(self):
        m=Mesh();points=[[0,0,0],[0,0,3]];rings=m.sweep(points,.3)
        for p,ring in zip(points,rings):
            for v in ring:self.assertAlmostEqual(np.linalg.norm(v-p),.3)
    def test_elbow_endpoints_and_radius(self):
        pts=elbow((1,2,3),.5,0,math.pi/2)
        np.testing.assert_allclose(pts[0],[1,2.5,3]);np.testing.assert_allclose(pts[-1],[1,2,3.5])
        for p in pts:self.assertAlmostEqual(math.dist(p,(1,2,3)),.5)
    def test_invalid_sweep(self):
        with self.assertRaises(ValueError):Mesh().sweep([[0,0,0],[0,0,0]],.2)
        for points in [[[0,0,0],[1,0,0],[0,0,0]],[[0,0,0],[float('nan'),0,0]]]:
            with self.assertRaises(ValueError):Mesh().sweep(points,.2)
    def test_flange_arbitrary_axis(self):
        m=Mesh();m.flange([1,2,3],[1,2,-3],.2)
        vertices=np.array([p for f,_ in m.faces for p in f])
        self.assertTrue(np.isfinite(vertices).all())
        np.testing.assert_allclose((vertices.min(0)+vertices.max(0))/2,[1,2,3],atol=.01)
    def test_industrial_render(self):
        m=build(fixture());r=Renderer(m,600,500);im=r.draw(m)
        self.assertEqual(im.size,(600,500));self.assertGreater(np.isfinite(r.z).sum(),20000)

if __name__=='__main__':unittest.main()
