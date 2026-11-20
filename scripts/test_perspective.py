import unittest,numpy as np
from render_scene import Mesh,Renderer,build
from connected_plant import fixture

class PerspectiveTests(unittest.TestCase):
    def mesh(self):
        m=Mesh();m.box((0,0,0),(2,2,3));return m
    def test_projection_roundtrip(self):
        for mode in ['orthographic','perspective']:
            r=Renderer(self.mesh(),500,600,projection=mode)
            for point in [[0,0,0],[2,2,3],[.5,1.3,2.4]]:
                x,y,z=r.project(point);np.testing.assert_allclose(r.unproject(x,y,z),point,atol=1e-12)
    def test_reconstructed_depth_lies_on_box_surface(self):
        m=self.mesh();r=Renderer(m,500,600,projection='perspective');r.draw(m)
        y,x=np.where(np.isfinite(r.z));world=r.unproject(x+.5,y+.5,r.z[y,x])
        distances=np.minimum(abs(world),abs(world-[2,2,3])).min(axis=1)
        self.assertLess(distances.max(),1e-10)
    def test_nearer_equal_segments_look_larger(self):
        r=Renderer(self.mesh(),500,600,projection='perspective');target=r.target@r.basis
        right=r.basis[0];view=r.basis[2]
        def length(center):return np.linalg.norm(r.project(center+right*.2)[:2]-r.project(center-right*.2)[:2])
        self.assertGreater(length(target+view),length(target-view))
    def test_hidden_geometry_stays_hidden(self):
        m=self.mesh();a=np.array(Renderer(m,400,500,projection='perspective').draw(m))
        m.box((.5,.5,.5),(.4,.4,.4));b=np.array(Renderer(m,400,500,projection='perspective').draw(m))
        np.testing.assert_array_equal(a,b)
    def test_plant_with_shadows_and_target_ownership(self):
        m=build(fixture());r=Renderer(m,700,600,projection='perspective',shadows=True);im=r.draw(m)
        self.assertEqual(im.size,(700,600))
        for name in ['tank-0','tank-1','pump','stairs','inspector','operator']:
            self.assertGreater((r.owner==r.part_ids[name]).sum(),0,name)
        _,labels=r.label(im,[{'target':'tank-0','text':'STORAGE VESSEL','position':[.03,.03]}])
        x,y=labels[0]['anchor'];self.assertEqual(r.owner[y,x],r.part_ids['tank-0'])

if __name__=='__main__':unittest.main()
