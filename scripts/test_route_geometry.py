import math
import unittest
import numpy as np
from route_geometry import rounded_route
from connected_plant import fixture
from scene_model import validate


class RoundedRouteTests(unittest.TestCase):
    def test_quarter_circle_radius_and_tangent_limits(self):
        pts=np.array(rounded_route([[0,0,0],[2,0,0],[2,2,0]],.5))
        np.testing.assert_array_equal(pts[0],[0,0,0])
        np.testing.assert_array_equal(pts[-1],[2,2,0])
        np.testing.assert_allclose(pts[1],[1.5,0,0],atol=1e-12)
        np.testing.assert_allclose(pts[-2],[2,.5,0],atol=1e-12)
        np.testing.assert_allclose(np.linalg.norm(pts[1:-1]-[1.5,.5,0],axis=1),.5)
        dirs=np.diff(pts,axis=0);dirs/=np.linalg.norm(dirs,axis=1)[:,None]
        self.assertGreater(dirs[0]@dirs[1],math.cos(math.radians(4)))
        self.assertGreater(dirs[-1]@dirs[-2],math.cos(math.radians(4)))

    def test_nonplanar_turns_keep_endpoints_and_smooth_direction(self):
        raw=[[0,0,0],[3,0,0],[3,3,0],[3,3,3],[5,4,3]]
        pts=np.array(rounded_route(raw,.3))
        np.testing.assert_array_equal(pts[[0,-1]],np.array(raw)[[0,-1]])
        dirs=np.diff(pts,axis=0);dirs/=np.linalg.norm(dirs,axis=1)[:,None]
        angles=np.arccos(np.clip(np.sum(dirs[:-1]*dirs[1:],axis=1),-1,1))
        self.assertLessEqual(angles.max(),math.radians(7.5)+1e-10)

    def test_bends_cannot_consume_more_than_segment_length(self):
        for raw,radius in [([[0,0,0],[1,0,0],[1,1,0]],2),
                           ([[0,0,0],[2,0,0],[2,1,0],[4,1,0]],.6)]:
            with self.assertRaisesRegex(ValueError,'does not fit'):rounded_route(raw,radius)

    def test_bad_paths_rejected(self):
        for raw,radius in [([[0,0,0],[1,0,0],[0,0,0]],.2),
                           ([[0,0,0],[0,0,0]],.2),
                           ([[0,0,0],[1,0,0]],float('nan'))]:
            with self.assertRaises(ValueError):rounded_route(raw,radius)

    def test_factory_module_retains_exact_ports(self):
        data=fixture();self.assertEqual(validate(data),[])
        route=next(c['route'] for c in data['connections'] if c['from']=='pump:out')
        self.assertGreater(len(route),5)
        self.assertEqual(route[0],[2.05,4.06,.4])
        self.assertEqual(route[-1],[2.15,5.35,.05])


if __name__=='__main__':unittest.main()
