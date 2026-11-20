import copy,unittest
from scene_model import make_part,validate,validation_report
from coherence_validation import coherence_report
from typed_interfaces import add_interface

def fixture():
    return {'units':'m','schema_version':2,'validation_policy':'strict','grounded':['floor'],
        'parts':[make_part('floor','slab',[0,0,-.2],[10,10,.2]),make_part('cabinet','cabinet',[2,2,0],[1,1,2])],
        'bearings':[{'part':'cabinet','on':'floor'}]}

class CoherenceTests(unittest.TestCase):
    def test_positive_supported_scene(self):
        self.assertEqual(validate(fixture()),[])
        self.assertEqual(coherence_report(fixture())['status'],'passed')
    def test_legacy_is_explicitly_partial(self):
        d=fixture();d.pop('validation_policy');report=coherence_report(d)
        self.assertEqual(report['status'],'partial');self.assertEqual(report['checks'][0]['status'],'not_run')
    def test_coincident_cabinets_rejected_without_clearance_pairs(self):
        d=fixture();d['parts'].append(make_part('duplicate','cabinet',[2,2,0],[1,1,2]));d['bearings'].append({'part':'duplicate','on':'floor'})
        self.assertTrue(any('penetration' in e for e in validate(d)))
        d.pop('validation_policy');self.assertEqual(validate(d),[])
    def test_wall_blocks_walk_volume(self):
        d=fixture();d['parts'].append(make_part('wall','wall',[4,1,0],[.2,3,3]));d['bearings'].append({'part':'wall','on':'floor'})
        d['access_nodes']=[{'id':'entry','position':[3.5,2.5,1]},{'id':'service','position':[5,2.5,1]}];d['access_roots']=['entry']
        d['access_volumes']=[{'id':'walk','min':[3.4,2.2,.01],'max':[5.1,2.8,2],'from':'entry','to':'service'}]
        errors=validate(d);self.assertTrue(any('occupied walking' in e for e in errors));self.assertTrue(any('Unreachable' in e for e in errors))
    def test_unreachable_clear_route_rejected(self):
        d=fixture();d['access_nodes']=[{'id':'entry','position':[1,1,1]},{'id':'service','position':[9,9,1]}];d['access_roots']=['entry']
        self.assertTrue(any('Unreachable' in e for e in validate(d)))
    def test_clear_navigation_passes(self):
        d=fixture();d['access_nodes']=[{'id':'entry','position':[3.5,2.5,1]},{'id':'service','position':[5,2.5,1]}];d['access_roots']=['entry']
        d['access_volumes']=[{'id':'walk','min':[3.4,2.2,.01],'max':[5.1,2.8,2],'from':'entry','to':'service'}]
        self.assertEqual(validate(d),[])
    def test_floating_duct_rejected(self):
        d=fixture();d['parts'].append(make_part('duct','duct',[0,0,100],[1,1,1]))
        self.assertTrue(any('No declared support' in e for e in validate(d)))
    def test_oversized_nozzle_rejected(self):
        d=fixture();p=make_part('header','manifold',[4,4,0],[3,.24,.24]);add_interface(p,'out',[3,.12,.12],[1,0,0],20,'outlet',termination='external')
        d['parts'].append(p);d['bearings'].append({'part':'header','on':'floor'})
        self.assertTrue(any('nozzle bore' in e for e in validate(d)))
    def test_missing_pump_ports_rejected(self):
        d=fixture();d['parts'].append(make_part('pump','pump',[5,5,0],[2,1,1]));d['bearings'].append({'part':'pump','on':'floor'})
        d['functional_contracts']=[{'part':'pump','role':'installed_pump'}]
        self.assertTrue(any('requires inlet and outlet' in e for e in validate(d)))
    def test_stored_pump_exemption(self):
        d=fixture();d['parts'].append(make_part('pump','pump',[5,5,0],[2,1,1]));d['bearings'].append({'part':'pump','on':'floor'})
        d['functional_contracts']=[{'part':'pump','role':'stored'}]
        self.assertEqual(validate(d),[])
    def test_critical_unsupported_blocks_acceptance(self):
        d=fixture();d['parts'].append(make_part('rotor','rotor',[8,8,4],[1,1,1]))
        report=coherence_report(d);self.assertEqual(report['status'],'failed')
        self.assertTrue(any(c['status']=='unsupported' for c in report['checks']))
        d['parts'][-1]['validation_critical']=False
        self.assertEqual(coherence_report(d)['status'],'passed')
    def test_contact_exception_is_bounded(self):
        d=fixture();d['parts'].append(make_part('c2','cabinet',[2.9,2,0],[1,1,2]));d['bearings'].append({'part':'c2','on':'floor'})
        d['contact_exceptions']=[{'a':'cabinet','b':'c2','relation':'joint','reason':'declared shared joint','region':{'min':[2.9,2,0],'max':[3,3,2]}}]
        self.assertEqual(validate(d),[])
        d['contact_exceptions'][0]['region']['max']=[100,100,100]
        self.assertTrue(any('extends beyond' in e for e in validate(d)))
    def test_invalid_contract_shape_is_reported(self):
        d=fixture();d['access_volumes']='wrong'
        self.assertTrue(any('access_volumes' in e for e in validate(d)))
        self.assertEqual(coherence_report(d)['status'],'failed')
    def test_stair_exit_blocked_by_wall(self):
        d=fixture();d['parts']+= [make_part('stair','stair',[4,1,0],[1,2,1],parameters={'steps':6}),
            make_part('landing','landing',[4,3,.8],[1,1,.2]),
            make_part('c1','column',[4,3,0],[.2,.2,.8]),make_part('c2','column',[4.8,3.8,0],[.2,.2,.8])]
        d['bearings'] += [{'part':key,'on':'floor'} for key in ('stair','c1','c2')]+[{'part':'landing','on':key} for key in ('c1','c2')]
        d['stair_access']=[{'stair':'stair','landing':'landing'}]
        d['access_nodes']=[{'id':'a','position':[4.5,2.85,1.5]},{'id':'b','position':[4.5,3.55,1.5]}];d['access_roots']=['a']
        d['access_volumes']=[{'id':'stair-exit','min':[4.1,2.8,1.01],'max':[4.9,3.6,2.8],'from':'a','to':'b'}]
        self.assertEqual(validate(d),[])
        d['parts'].append(make_part('blocking-wall','wall',[4,2.9,0],[1,.2,3]));d['bearings'].append({'part':'blocking-wall','on':'floor'})
        self.assertTrue(any('stair-exit: occupied walking' in e for e in validate(d)))
    def test_access_cannot_exempt_a_wall(self):
        d=fixture();d['access_nodes']=[{'id':'a','position':[2,2,1]},{'id':'b','position':[3,3,1]}];d['access_roots']=['a']
        d['access_volumes']=[{'id':'bad','min':[1,1,.01],'max':[4,4,2.5],'from':'a','to':'b','traversable_parts':['cabinet']}]
        self.assertTrue(any('traversable exclusions' in e for e in validate(d)))
    def test_traversable_bridge_cannot_intersect_walking_body(self):
        d=fixture();d['parts'] += [make_part('post','column',[4,4,0],[.2,.2,1]),make_part('bridge','slab',[4,4,1],[2,2,.2])]
        d['bearings'] += [{'part':'post','on':'floor'},{'part':'bridge','on':'post'}]
        d['access_nodes']=[{'id':'a','position':[4.5,4.5,1.5]},{'id':'b','position':[5.5,5.5,1.5]}];d['access_roots']=['a']
        d['access_volumes']=[{'id':'bridge-walk','min':[4.3,4.3,.9],'max':[5.7,5.7,2.5],'from':'a','to':'b','traversable_parts':['bridge']}]
        self.assertTrue(any('must remain below' in e for e in validate(d)))
        d['access_volumes'][0]['min'][2]=1.2
        self.assertEqual(validate(d),[])
    def test_invalid_traversable_shape_reports_instead_of_crashing(self):
        d=fixture();d['access_volumes']=[{'id':'bad','min':[1,1,0],'max':[2,2,2],'from':'a','to':'b','traversable_parts':None}]
        self.assertTrue(any('traversable_parts' in e for e in validate(d)))
    def test_combined_report_does_not_hide_base_geometry_failure(self):
        d=fixture();d['parts'][1]['origin'][2]=1
        report=validation_report(d)
        self.assertEqual(report['status'],'failed')
        self.assertTrue(any(c['status']=='not_run' for c in report['checks']))
    def test_combined_report_keeps_legacy_partial(self):
        d=fixture();d.pop('validation_policy')
        self.assertEqual(validation_report(d)['status'],'partial')
    def test_endpoint_component_is_not_globally_exempt(self):
        d=fixture();a=make_part('a','manifold',[4,4,0],[2,.4,.4]);b=make_part('b','manifold',[7,4,0],[2,.4,.4])
        add_interface(a,'out',[2,.2,.2],[1,0,0],.2,'outlet');add_interface(b,'in',[0,.2,.2],[-1,0,0],.2,'inlet')
        d['parts']+=[a,b];d['bearings']+=[{'part':k,'on':'floor'} for k in ('a','b')]
        d['connections']=[{'from':'a:out','to':'b:in','radius':.1,'route':[[6.12,4.2,.2],[6.5,4.2,.2],[6.88,4.2,.2]]}]
        self.assertEqual(validate(d),[])
        # Independent endpoint gate on a deliberately intrusive polyline; base
        # route curvature validation is tested elsewhere and must also run.
        d['connections'][0]['route']=[[6.12,4.2,.2],[6.5,4.2,.2],[5,4.2,.2],[6.88,4.2,.2]]
        report=coherence_report(d)
        self.assertTrue(any(c['check']=='endpoint_clearance' and c['status']=='unsupported' for c in report['checks']))
    def test_malformed_nozzle_does_not_crash_public_report(self):
        d=fixture();p=make_part('header','manifold',[4,4,0],[3,.24,.24]);add_interface(p,'out',[3,.12,.12],[1,0,0],.2,'outlet',termination='external')
        p['interfaces']['out']['diameter']='invalid';d['parts'].append(p)
        self.assertEqual(coherence_report(d)['status'],'failed')

if __name__=='__main__':unittest.main()
