import copy,unittest
from scene_model import validate,make_part
from typed_interfaces import coverage
from typed_water_plant import scene

class TypedTests(unittest.TestCase):
    def setUp(self):self.d=scene()
    def part(self,name):return next(p for p in self.d['parts'] if p['id']==name)
    def fails(self,text):self.assertTrue(any(text in e for e in validate(self.d)),validate(self.d))
    def test_valid(self):self.assertEqual(validate(self.d),[])
    def test_legacy_reports_partial(self):self.assertEqual(coverage({'parts':[]})['mode'],'legacy-partial')
    def test_floating_beam(self):
        self.d['parts'].append(make_part('floating','beam',(0,0,12),(2,.2,.3)));self.fails('floating: no declared bearing')
    def test_missing_support_relation(self):
        self.d['bearings']=[x for x in self.d['bearings'] if x['part']!='pump'];self.fails('pump: no declared bearing')
    def test_missing_port_type(self):
        del self.part('pump')['interfaces']['in'];self.fails('every port requires')
    def test_internal_anchor(self):
        self.part('tank-0')['interfaces']['out']['anchor'][1]=.85;self.fails('surface')
    def test_bad_normal(self):
        self.part('tank-0')['interfaces']['out']['normal']=[1,0,0];self.fails('surface')
    def test_diameter(self):
        self.part('pump')['interfaces']['in']['diameter']=.2;self.fails('diameter mismatch')
    def test_medium(self):
        self.part('pump')['interfaces']['in']['medium']='electricity';self.fails('incompatible medium')
    def test_roles(self):
        self.part('pump')['interfaces']['in']['role']='outlet';self.fails('reversed flow')
    def test_missing_termination(self):
        del self.part('boundary')['interfaces']['external']['termination'];self.fails('without termination')
    def test_nan_interface(self):
        self.part('pump')['interfaces']['in']['diameter']=float('nan');self.fails('finite number')
    def test_bad_interface_shape(self):
        self.part('pump')['interfaces']={3:None};self.fails('interface')
    def test_bad_ground_shape(self):
        self.d['grounded']=[{}];self.fails('grounded')
    def test_missing_access(self):
        self.d['stair_access']=[];self.fails('access missing')
    def test_wrong_version(self):
        self.d['schema_version']=9;self.fails('Unsupported schema')
    def test_automatic_obstacle_coverage(self):
        self.d['parts'].append(make_part('blocking-wall','wall',(1.8,4.5,0),(.5,.2,2)))
        self.fails('Route clearance')
    def test_missing_column_ground_path(self):
        self.d['bearings']=[x for x in self.d['bearings'] if x['part']!='deck-leg-0'];self.fails('deck-leg-0: no declared bearing')
    def test_wrong_departure_direction(self):
        from typed_interfaces import interface_errors
        self.d['connections'][0]['route'][1][0]+=.2
        self.assertTrue(any('not tangent' in e for e in interface_errors(self.d)))
    def test_blocked_stair_access(self):
        self.d['parts'].append(make_part('blocking-rail','railing',(-1.4,-.025,2.4),(1,.05,1)))
        self.fails('entrance blocked')
    def test_expanded_hall(self):
        from typed_water_hall import scene as hall
        d=hall();self.assertEqual(validate(d),[])
        self.assertEqual(d['expected_counts']['worker'],5)
        self.assertEqual(d['expected_counts']['vessel'],4)
    def test_route_disconnected(self):
        self.d['connections'][0]['route'][0][0]+=.3;self.fails('endpoint mismatch')
    def test_surface_geometry_generated(self):
        from render_scene import build
        m=build(self.d)
        self.assertGreater(sum(v=='pump' for v in m.face_owners.values()),100)

if __name__=='__main__':unittest.main()
