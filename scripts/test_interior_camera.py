import unittest
import numpy as np
from render_scene import Mesh,Renderer,build
from scene_model import make_part
from camera_geometry import clip_polygon,clip_segment,clip_screen_line


class InteriorCameraTests(unittest.TestCase):
    def renderer(self,mesh,**kwargs):
        return Renderer(mesh,400,300,projection='perspective',camera_eye=[0,0,0],camera_target=[0,1,0],near=.2,**kwargs)

    def test_target_is_center_and_roundtrip_is_exact(self):
        m=Mesh();m.box([-1,1,-1],[2,2,2]);r=self.renderer(m)
        np.testing.assert_allclose(r.project([0,2,0])[:2],[200,150])
        for point in [[.3,1,.5],[-2,4,-1],[0,.2,0]]:
            x,y,d=r.project(point);np.testing.assert_allclose(r.unproject(x,y,d),point,atol=1e-12)

    def test_near_plane_clips_without_moving_retained_vertices(self):
        pts=[[-1,-1,0],[1,1,0],[-1,1,0]]
        clipped=clip_polygon(pts,np.zeros(3),np.array([0,1,0]),.2)
        self.assertEqual(len(clipped),4)
        self.assertTrue(all(p[1]>=.2-1e-12 for p in clipped))
        self.assertTrue(any(np.array_equal(p,[1,1,0]) for p in clipped))
        a,b=clip_segment([0,-1,0],[0,1,0],np.zeros(3),np.array([0,1,0]),.2)
        np.testing.assert_allclose(a,[0,.2,0]);np.testing.assert_array_equal(b,[0,1,0])

    def test_straddling_box_renders_and_behind_object_is_hidden(self):
        scene={'units':'m','parts':[
            make_part('near','wall',[-1,-.2,-1],[2,2,2]),
            make_part('behind','wall',[3,-4,-1],[1,1,1])]}
        mesh=build(scene);r=self.renderer(mesh,finish='graphite',shadows=True);im=r.draw(mesh)
        self.assertEqual(im.size,(400,300))
        self.assertGreater(np.isfinite(r.z).sum(),1000)
        self.assertFalse(np.any(r.owner==r.part_ids['behind']))
        yy,xx=np.where(np.isfinite(r.z));world=r.unproject(xx+.5,yy+.5,r.z[yy,xx])
        self.assertTrue(np.all(world[:,1]>=.2-1e-8))

    def test_screen_clipping_bounds_huge_line_and_interpolates_depth(self):
        a,b=clip_screen_line(np.array([-1e9,150,1]),np.array([1e9,150,3]),400,300)
        self.assertAlmostEqual(a[0],0,places=5);self.assertAlmostEqual(b[0],399,places=5)
        self.assertAlmostEqual(a[2],2)
        self.assertIsNone(clip_screen_line([0,-1,1],[200,-1,1],400,300))

    def test_route_endpoint_behind_camera_reports_zero_without_projecting_it(self):
        scene={'units':'m','parts':[
            make_part('back','column',[0,-1,0],[.2,.2,.2],ports={'port':[.1,.1,.1]}),
            make_part('front','column',[0,2,0],[.2,.2,.2],ports={'port':[.1,.1,.1]})],
            'connections':[{'from':'back:port','to':'front:port','radius':.03,
                            'route':[[.1,-.9,.1],[.1,2.1,.1]]}]}
        mesh=build(scene);r=self.renderer(mesh);r.draw(mesh)
        report=r.connection_visibility(mesh,scene)[0]
        self.assertEqual(report['endpoint_neighborhood_pixels'][0],0)
        self.assertGreater(report['visible_pixels'],0)

    def test_camera_configuration_errors(self):
        m=Mesh();m.box([0,1,0],[1,1,1])
        for kw in [dict(camera_eye=[0,0,0]),dict(camera_eye=[0,0,0],camera_target=[0,0,0]),
                   dict(camera_eye=[0,0,0],camera_target=[0,1,0],near=0),
                   dict(camera_eye=[0,0,0],camera_target=[0,1,0],fov=180)]:
            with self.assertRaises(ValueError):Renderer(m,projection='perspective',**kw)


if __name__=='__main__':unittest.main()
