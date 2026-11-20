import unittest
import numpy as np
from render_scene import build,Renderer
from connected_plant import fixture
from scene_model import tower
from drawing_style import graphite_hatching


class DrawingStyleTests(unittest.TestCase):
    def test_hatching_respects_tone_and_plane_without_winding_seams(self):
        yy,xx=np.mgrid[:180,:240]
        bright=graphite_hatching(xx,yy,1,[0,0,1],[240,235,224])
        dark=graphite_hatching(xx,yy,1,[0,0,1],[214,209,198])
        reverse=graphite_hatching(xx,yy,1,[0,0,-7],[214,209,198])
        wall=graphite_hatching(xx,yy,1,[1,0,0],[214,209,198])
        np.testing.assert_array_equal(dark,reverse)
        self.assertGreater(dark.mean(),bright.mean()*4)
        self.assertGreater(np.mean(np.abs(dark-wall)),1)
        self.assertTrue(np.isfinite(dark).all())
        curved=graphite_hatching(xx,yy,1,[.6,.8,0],[214,209,198])
        np.testing.assert_array_equal(wall,curved)

    def test_graphite_preserves_depth_ownership_and_route_visibility(self):
        data=fixture();mesh=build(data)
        a=Renderer(mesh,500,420,projection='perspective',finish='technical',shadows=True)
        b=Renderer(mesh,500,420,projection='perspective',finish='graphite',shadows=True)
        plain=np.array(a.draw(mesh));styled=np.array(b.draw(mesh))
        np.testing.assert_array_equal(a.z,b.z)
        np.testing.assert_array_equal(a.owner,b.owner)
        self.assertEqual(a.connection_visibility(mesh,data),b.connection_visibility(mesh,data))
        self.assertGreater(np.count_nonzero(plain!=styled),10000)
        self.assertGreater(np.std(styled[~np.isfinite(b.z),0]),1)

    def test_finish_is_repeatable_on_a_building(self):
        mesh=build(tower(4,2))
        a=Renderer(mesh,300,500,finish='graphite')
        b=Renderer(mesh,300,500,finish='graphite')
        np.testing.assert_array_equal(np.array(a.draw(mesh)),np.array(b.draw(mesh)))

    def test_graphite_has_neutral_ink_and_subtle_paper_tint(self):
        mesh=build(tower(2,1))
        renderer=Renderer(mesh,300,350,finish='graphite')
        image=np.array(renderer.draw(mesh)).astype(float)
        paper=image[~np.isfinite(renderer.z)]
        surfaces=image[np.isfinite(renderer.z)]
        self.assertGreater(paper.mean(),240)
        self.assertLess(np.max(np.ptp(paper,axis=1)),7)
        self.assertLess(np.max(np.ptp(surfaces,axis=1)),7)
        ink=surfaces[surfaces.mean(axis=1)<130]
        self.assertGreater(len(ink),100)
        self.assertLess(np.max(np.ptp(ink,axis=1)),2)

    def test_unknown_finish_rejected(self):
        with self.assertRaises(ValueError):Renderer(build(tower(1,1)),finish='undefined')


if __name__=='__main__':unittest.main()
