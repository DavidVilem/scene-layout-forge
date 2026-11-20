import unittest
import numpy as np
from scene_model import make_part
from render_scene import build,Renderer

class AnnotationTests(unittest.TestCase):
    def scene(self):
        mesh=build({'units':'m','parts':[make_part('shell','wall',[0,0,0],[2,2,2]),make_part('hidden','cabinet',[.5,.5,.5],[.5,.5,.5])]})
        r=Renderer(mesh,700,600);return r,r.draw(mesh)
    def test_anchor_belongs_to_visible_target(self):
        r,im=self.scene();depth=r.z.copy()
        _,notes=r.label(im,[{'target':'shell','text':'WALL','position':[.03,.06]}])
        x,y=notes[0]['anchor'];self.assertEqual(r.owner[y,x],r.part_ids['shell'])
        np.testing.assert_array_equal(depth,r.z)
    def test_hidden_target_rejected(self):
        r,im=self.scene()
        with self.assertRaisesRegex(ValueError,'not sufficiently visible'):
            r.label(im,[{'target':'hidden','text':'CABINET','position':[.03,.06]}])
    def test_overlap_and_bounds(self):
        r,im=self.scene();item={'target':'shell','text':'WALL','position':[.03,.06]}
        with self.assertRaisesRegex(ValueError,'Overlapping'):r.label(im,[item,item])
        with self.assertRaisesRegex(ValueError,'outside'):r.label(im,[{**item,'position':[1.,.06]}])
    def test_multiple_camera_bases(self):
        mesh=build({'units':'m','parts':[make_part('box','wall',[0,0,0],[2,2,2])]})
        for az,el in [(0,15),(90,45),(180,60),(270,80)]:
            r=Renderer(mesh,400,400,azimuth=az,elevation=el)
            np.testing.assert_allclose(r.basis@r.basis.T,np.eye(3),atol=1e-12)
            self.assertLess(r.project([0,0,1])[1],r.project([0,0,0])[1])
            r.draw(mesh);self.assertGreater((r.owner>0).sum(),1000)
    def test_invalid_camera(self):
        mesh=build({'units':'m','parts':[make_part('box','wall',[0,0,0],[1,1,1])]})
        for elevation in [0,91,float('nan')]:
            with self.assertRaises(ValueError):Renderer(mesh,elevation=elevation)

if __name__=='__main__':unittest.main()
