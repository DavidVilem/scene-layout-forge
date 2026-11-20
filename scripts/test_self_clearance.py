import math,unittest
from sweep_geometry import segment_distance,check_route_self_clearance
from route_geometry import rounded_route


class SelfClearanceTests(unittest.TestCase):
    def test_scene_validator_rejects_a_self_crossing_connection(self):
        from scene_model import make_part,validate
        route=[[-2,0,0],[2,0,0],[2,2,0],[0,2,0],[0,-2,0]]
        data={'units':'m','parts':[
            make_part('a','column',[0,0,0],[1,1,1],ports={'out':route[0]}),
            make_part('b','column',[0,0,0],[1,1,1],ports={'in':route[-1]})],
            'connections':[{'from':'a:out','to':'b:in','route':route,'radius':.1}]}
        self.assertTrue(any('self-clearance' in error for error in validate(data)))

    def test_distance_for_crossing_skew_parallel_and_clamped_segments(self):
        cases=[(([0,0,0],[2,0,0],[1,-1,0],[1,1,0]),0),
               (([0,0,0],[2,0,0],[1,-1,3],[1,1,3]),3),
               (([0,0,0],[2,0,0],[1,1,0],[3,1,0]),1),
               (([0,0,0],[1,0,0],[2,1,0],[2,2,0]),math.sqrt(2))]
        for points,expected in cases:
            self.assertAlmostEqual(segment_distance(*points)[0],expected)
            self.assertAlmostEqual(segment_distance(*points[2:],*points[:2])[0],expected)

    def test_crossing_and_close_parallel_return_are_rejected(self):
        for points in [ [[-2,0,0],[2,0,0],[2,2,0],[0,2,0],[0,-2,0]],
                        [[0,0,0],[4,0,0],[4,2,0],[0,2,0],[0,.15,0],[3,.15,0]] ]:
            with self.assertRaisesRegex(ValueError,'self-clearance'):check_route_self_clearance(points,.1)

    def test_elevated_crossing_and_dense_ordinary_elbow_are_allowed(self):
        check_route_self_clearance([[-2,0,0],[2,0,0],[2,2,1],[0,2,1],[0,-2,1]],.1)
        for samples in [4,12,64]:
            check_route_self_clearance(rounded_route([[0,0,0],[2,0,0],[2,2,0]],.4,samples),.1)

    def test_closed_circle_seam_is_not_a_remote_collision(self):
        points=[[math.cos(i*math.tau/64),math.sin(i*math.tau/64),0] for i in range(65)]
        check_route_self_clearance(points,.1)


if __name__=='__main__':unittest.main()
