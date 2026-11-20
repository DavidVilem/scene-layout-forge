import unittest
import numpy as np
from render_scene import build
from scene_model import make_part,validate

class ServiceGeometryTests(unittest.TestCase):
    def test_tray_orientation_rotates_crossbars_and_stays_in_bounds(self):
        for axis,size in [('x',[6,.4,.2]),('y',[.4,6,.2]),('z',[.4,.2,6])]:
            mesh=build({'units':'m','parts':[make_part('tray','cable_tray',[1,2,3],size,parameters={'orientation':axis})]})
            points=np.array([v for face,_ in mesh.faces for v in face])
            np.testing.assert_allclose(points.min(axis=0),[1,2,3])
            np.testing.assert_allclose(points.max(axis=0),np.array([1,2,3])+size)
            self.assertGreater(len(mesh.faces),80) # repeated crossbars along the long axis
    def test_invalid_orientation_rejected_by_validator(self):
        data={'units':'m','parts':[make_part('tray','cable_tray',[0,0,0],[6,.4,.2],parameters={'orientation':'invalid'})]}
        self.assertTrue(any('orientation' in e for e in validate(data)))
    def test_corbel_has_flat_upper_support_face(self):
        mesh=build({'units':'m','parts':[make_part('seat','corbel',[1,2,3],[.2,.5,.35],parameters={'top_flat':True})]})
        upper=[np.array(face) for face,_ in mesh.faces if all(abs(v[2]-3.35)<1e-8 for v in face)]
        self.assertEqual(len(upper),1)
        np.testing.assert_allclose(upper[0][:,:2].max(axis=0)-upper[0][:,:2].min(axis=0),[.2,.5])

if __name__=='__main__':unittest.main()

