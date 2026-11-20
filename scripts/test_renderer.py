import unittest,numpy as np
from render_scene import Mesh,Renderer,build
from scene_model import tower

class RendererTests(unittest.TestCase):
    def test_height_projects_up(self):
        m=Mesh();m.box((0,0,0),(1,1,1));r=Renderer(m,240,240)
        self.assertLess(r.project((0,0,1))[1],r.project((0,0,0))[1])
    def test_hatching_preserves_geometry(self):
        m=Mesh();m.box((0,0,0),(2,2,2))
        a=Renderer(m,320,320,hatching=False);b=Renderer(m,320,320,hatching=True)
        plain=np.array(a.draw(m));hatched=np.array(b.draw(m))
        np.testing.assert_array_equal(a.z,b.z)
        self.assertGreater(np.count_nonzero(plain!=hatched),100)
        np.testing.assert_array_equal(hatched,np.array(Renderer(m,320,320).draw(m)))
    def test_order_independent(self):
        m=Mesh();m.box((0,0,0),(2,2,2));m.box((1,-1,.5),(2,2,1))
        a=np.array(Renderer(m,240,240).draw(m));m.faces.reverse();m.edges.reverse()
        b=np.array(Renderer(m,240,240).draw(m))
        self.assertTrue(np.array_equal(a,b))
    def test_supersampling_preserves_composition(self):
        m=Mesh();m.box((0,0,0),(2,2,2))
        a=Renderer(m,400,300);b=Renderer(m,800,600,pixel_ratio=2)
        for point in [[0,0,0],[2,2,2],[1,.5,.3]]:
            np.testing.assert_allclose(a.project(point)[:2]*2,b.project(point)[:2])
            self.assertAlmostEqual(a.project(point)[2],b.project(point)[2])
    def test_stroke_style_does_not_change_ownership(self):
        m=build(tower(2,1));a=Renderer(m,400,400,hatching=False);b=Renderer(m,400,400,hatching=True)
        a.draw(m);b.draw(m)
        np.testing.assert_array_equal(a.owner,b.owner)
        np.testing.assert_array_equal(a.z,b.z)
    def test_hidden_far_triangle(self):
        m=Mesh();m.box((0,0,0),(1,1,1));r=Renderer(m,240,240)
        near=np.array([[40,40,2],[140,40,2],[40,140,2]],float)
        far=near.copy();far[:,2]=1
        r.triangle(near,(20,30,40));r.triangle(far,(240,230,220))
        self.assertEqual(tuple(r.rgb[60,60]),(20,30,40))
    def test_tower_render(self):
        m=build(tower(8,2));r=Renderer(m,400,600);im=r.draw(m)
        self.assertEqual(im.size,(400,600));self.assertGreater(np.isfinite(r.z).sum(),10000)

if __name__=='__main__':unittest.main()
