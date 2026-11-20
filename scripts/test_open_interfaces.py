import unittest
import numpy as np
from render_scene import Mesh
from typed_interfaces import add_interface,render_interfaces
from scene_model import make_part

class OpenInterfacesTests(unittest.TestCase):
    def centered_face(self,mesh,x):
        # A filled end disc spans the axis; annular quads and bolts do not.
        return any(all(abs(v[0]-x)<1e-7 for v in face) and
                   np.linalg.norm(np.mean(face,axis=0)[1:])<1e-7 for face,_ in mesh.faces)
    def test_flange_bore_leaves_axis_open(self):
        m=Mesh();m.flange([0,0,0],[1,0,0],1,bore=.85)
        self.assertFalse(self.centered_face(m,.22))
        self.assertFalse(self.centered_face(m,-.22))
        closed=Mesh();closed.flange([0,0,0],[1,0,0],1)
        self.assertTrue(self.centered_face(closed,.22))
    def test_external_and_sealed_interfaces_differ(self):
        for termination,closed in [('external',False),('cap',True)]:
            p=make_part('p','manifold',[0,-1,-1],[4,2,2])
            add_interface(p,'end',[4,1,1],[1,0,0],2,'outlet',termination=termination)
            m=Mesh();render_interfaces(m,p)
            self.assertEqual(self.centered_face(m,4.12),closed)
    def test_sweep_can_cap_only_one_end(self):
        m=Mesh();m.sweep([[0,0,0],[2,0,0]],1,caps=(True,False))
        self.assertTrue(self.centered_face(m,0));self.assertFalse(self.centered_face(m,2))
    def test_bad_caps_rejected(self):
        with self.assertRaises(ValueError):Mesh().sweep([[0,0,0],[2,0,0]],1,caps=[1,0])

if __name__=='__main__':unittest.main()
