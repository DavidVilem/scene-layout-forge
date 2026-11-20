import unittest
import numpy as np
from render_scene import build
from scene_model import make_part


class EquipmentScaleTests(unittest.TestCase):
    def test_long_pump_has_geometry_across_casing_motor_gap(self):
        mesh=build({'units':'m','parts':[make_part('pump','pump',[0,0,0],[12,2,4])]})
        # This slice was empty above the base in the old long-pump adapter:
        # casing ended before x=4.2 and motor started after it.
        crossing=[face for face,_ in mesh.faces
                  if min(v[0] for v in face)<=4.2<=max(v[0] for v in face)
                  and min(v[2] for v in face)>.75]
        self.assertGreater(len(crossing),0)

    def test_equipment_fits_declared_envelope_at_varied_sizes(self):
        for kind in ['vessel','pump']:
            for size in [[.15,.12,.2],[12,2,4],[.3,2,1],[1.7,1.7,3.6],[1.5,.8,.8]]:
                with self.subTest(kind=kind,size=size):
                    origin=np.array([2.,-3.,1.])
                    mesh=build({'units':'m','parts':[make_part('equipment',kind,origin.tolist(),size)]})
                    vertices=np.array([v for face,_ in mesh.faces for v in face])
                    self.assertTrue(np.isfinite(vertices).all())
                    self.assertTrue(np.all(vertices.min(0)>=origin-1e-9))
                    self.assertTrue(np.all(vertices.max(0)<=origin+size+1e-9))
                    self.assertAlmostEqual(vertices[:,2].min(),origin[2])
                    for face,_ in mesh.faces:
                        self.assertGreater(np.linalg.norm(np.cross(face[1]-face[0],face[2]-face[0])),1e-12)


if __name__=='__main__':unittest.main()
