import unittest
import numpy as np
from render_scene import Mesh,Renderer,build
from scene_model import Part,make_part,validate
from surface_details import vessel_marks


class SurfaceDetailTests(unittest.TestCase):
    def test_all_marks_follow_shell_at_varied_dimensions(self):
        for size in [[1.7,1.7,3.6],[.3,1,2],[3,2,.5]]:
            part=Part.from_data(make_part('tank','vessel',[1,2,3],size,
                               parameters={'inspection_hatch':True,'seam_bolts':16}))
            mesh=Mesh();vessel_marks(mesh,part)
            points=np.array([p for edge in mesh.edges for p in edge])
            center=np.array([1+size[0]/2,2+size[1]/2])
            np.testing.assert_allclose(np.linalg.norm(points[:,:2]-center,axis=1),min(size[:2])/2)
            self.assertGreater(points[:,2].min(),3+size[2]/12)
            self.assertLess(points[:,2].max(),3+size[2]*35/36)
            self.assertTrue(all(np.linalg.norm(b-a)>1e-10 for a,b in mesh.edges))

    def test_marks_change_lines_without_changing_depth_or_ownership(self):
        raw=make_part('tank','vessel',[0,0,0],[1.7,1.7,3.6])
        plain=build({'units':'m','parts':[raw]})
        raw['parameters']={'inspection_hatch':True,'seam_bolts':16}
        detailed=build({'units':'m','parts':[raw]})
        a=Renderer(plain,400,500);b=Renderer(detailed,400,500)
        im_a=np.array(a.draw(plain));im_b=np.array(b.draw(detailed))
        np.testing.assert_array_equal(a.z,b.z)
        np.testing.assert_array_equal(a.owner,b.owner)
        self.assertGreater(np.count_nonzero(im_a!=im_b),100)

    def test_invalid_detail_settings_rejected_before_render(self):
        for params in [{'seam_bolts':True},{'seam_bolts':-1},{'seam_bolts':65},{'inspection_hatch':'yes'}]:
            scene={'units':'m','parts':[make_part('tank','vessel',[0,0,0],[1,1,2],parameters=params)]}
            self.assertTrue(validate(scene))
            with self.assertRaises(ValueError):build(scene)


if __name__=='__main__':unittest.main()
