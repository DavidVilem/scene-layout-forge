import unittest
import numpy as np
from render_scene import Mesh,build
from scene_model import make_part

class PeopleTests(unittest.TestCase):
    def test_ellipsoid_surface_and_nondegenerate_faces(self):
        m=Mesh();center=np.array([1,2,3]);radii=np.array([.2,.3,.5]);m.ellipsoid(center,radii)
        for face,_ in m.faces:
            self.assertGreater(np.linalg.norm(np.cross(face[1]-face[0],face[2]-face[0])),1e-9)
            for vertex in face:self.assertAlmostEqual(np.sum(((vertex-center)/radii)**2),1)
        self.assertGreater(len(m.smooth_edges),0)
    def test_worker_stays_in_support_footprint(self):
        for width,depth,height in [(.45,.45,1.7),(.55,.4,1.85)]:
            origin=np.array([3,2,4.])
            m=build({'units':'m','parts':[make_part('worker','worker',origin.tolist(),[width,depth,height])]})
            vertices=np.array([v for f,_ in m.faces for v in f])
            self.assertTrue(np.all(vertices.min(0)>=origin-1e-8))
            self.assertTrue(np.all(vertices.max(0)<=origin+[width,depth,height]+np.array([1e-8]*3)))
            self.assertAlmostEqual(vertices[:,2].min(),origin[2])
            self.assertAlmostEqual(vertices[:,2].max(),origin[2]+height)
    def test_invalid_ellipsoid_rejected(self):
        for radii in [[1,0,1],[1,float('nan'),1]]:
            with self.assertRaises(ValueError):Mesh().ellipsoid([0,0,0],radii)

if __name__=='__main__':unittest.main()
