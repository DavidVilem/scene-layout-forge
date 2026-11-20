import unittest
import numpy as np
from scene_model import make_part
from render_scene import build

class DetailTests(unittest.TestCase):
    def mesh(self,kind,size,parameters):return build({'units':'m','parts':[make_part('p',kind,[1,2,3],size,parameters=parameters)]})
    def test_baseplate_stays_in_declared_bounds(self):
        for size in [[.12,.12,2.25],[.3,.4,5]]:
            m=self.mesh('column',size,{'profile':'steel'})
            vertices=np.array([v for f,_ in m.faces for v in f])
            np.testing.assert_allclose(vertices.min(0),[1,2,3])
            np.testing.assert_allclose(vertices.max(0),np.array([1,2,3])+size)
            self.assertGreater(len(m.faces),12)
    def test_wall_joints_lie_on_surface(self):
        m=self.mesh('wall',[6,.2,4],{'panel_size':[2,1.5]})
        self.assertEqual(len(m.edges),16) # box plus two vertical and two horizontal joints
        for a,b in m.edges[12:]:
            self.assertAlmostEqual(a[1],2.2);self.assertAlmostEqual(b[1],2.2)
    def test_grating_keeps_support_height(self):
        m=self.mesh('landing',[3,1,.15],{'surface':'grating','grid_spacing':.2})
        for a,b in m.edges[12:]:
            self.assertAlmostEqual(a[2],3.15);self.assertAlmostEqual(b[2],3.15)
    def test_invalid_density_rejected(self):
        for spacing in [0,float('nan'),1e-9]:
            with self.assertRaises(ValueError):self.mesh('landing',[3,1,.15],{'surface':'grating','grid_spacing':spacing})

if __name__=='__main__':unittest.main()
