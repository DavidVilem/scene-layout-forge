import unittest
from sweep_geometry import route_pair_conflicts
from scene_model import make_part,validate


class RoutePairTests(unittest.TestCase):
    def test_shared_manifold_excludes_only_its_local_envelope(self):
        routes=[dict(route=[[-1,0,0],[0,0,0]],radius=.1,**{'from':'a:out','to':'hub:in'}),
                dict(route=[[0,0,0],[0,1,0]],radius=.1,**{'from':'hub:side','to':'b:in'})]
        boxes={'hub':([-.2,-.2,-.2],[.2,.2,.2])}
        self.assertEqual(route_pair_conflicts(routes),[(0,1)])
        self.assertEqual(route_pair_conflicts(routes,boxes),[])
        routes[1]['route'] += [[-1,1,0],[-1,-1,0]]
        self.assertEqual(route_pair_conflicts(routes,boxes),[(0,1)])

    def routes(self,height=0):
        return [dict(route=[[-1,0,0],[1,0,0]],radius=.1,**{'from':'a:out','to':'b:in'}),
                dict(route=[[0,-1,height],[0,1,height]],radius=.1,**{'from':'c:out','to':'d:in'})]

    def test_crossing_and_near_pass_fail_but_grade_separation_passes(self):
        self.assertEqual(route_pair_conflicts(self.routes()),[(0,1)])
        self.assertEqual(route_pair_conflicts(self.routes(.15)),[(0,1)])
        self.assertEqual(route_pair_conflicts(self.routes(.3)),[])
        self.assertEqual(route_pair_conflicts(self.routes(.2)),[])

    def test_shared_port_excludes_only_the_meeting_zone(self):
        routes=[dict(route=[[0,0,0],[2,0,0]],radius=.1,**{'from':'hub:out','to':'a:in'}),
                dict(route=[[0,0,0],[0,2,0]],radius=.1,**{'from':'hub:out','to':'b:in'})]
        self.assertEqual(route_pair_conflicts(routes),[])
        routes[1]['route'] += [[1,2,0],[1,-1,0]]
        self.assertEqual(route_pair_conflicts(routes),[(0,1)])

    def test_same_shape_duplicates_fail_even_inside_a_junction_zone(self):
        for reverse in [False,True]:
            points=[[0,0,0],[.1,0,0]]
            routes=[dict(route=points,radius=.1,**{'from':'hub:out','to':'b:in'}),
                    dict(route=points[::-1] if reverse else points,radius=.1,**{'from':'hub:out','to':'b:in'})]
            self.assertEqual(route_pair_conflicts(routes),[(0,1)])

    def test_shared_port_does_not_allow_a_long_overlapping_start(self):
        routes=[dict(route=[[0,0,0],[2,0,0]],radius=.1,**{'from':'hub:out','to':'a:in'}),
                dict(route=[[0,0,0],[1,0,0],[1,1,0]],radius=.1,**{'from':'hub:out','to':'b:in'})]
        self.assertEqual(route_pair_conflicts(routes),[(0,1)])

    def test_parallel_overlap_and_separation(self):
        routes=self.routes()
        routes[1]['route']=[[-.5,.1,0],[2,.1,0]]
        self.assertEqual(route_pair_conflicts(routes),[(0,1)])
        routes[1]['route']=[[-.5,.3,0],[2,.3,0]]
        self.assertEqual(route_pair_conflicts(routes),[])

    def test_scene_validation_reports_crossing_routes(self):
        routes=self.routes();parts=[]
        for route in routes:
            for endpoint,point in [(route['from'],route['route'][0]),(route['to'],route['route'][-1])]:
                name,port=endpoint.split(':')
                parts.append(make_part(name,'column',[0,0,0],[1,1,1],ports={port:point}))
        self.assertTrue(any('Route pair clearance' in e for e in validate({'units':'m','parts':parts,'connections':routes})))


if __name__=='__main__':unittest.main()
