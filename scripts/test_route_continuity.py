import copy,json,tempfile,unittest
from pathlib import Path
from PIL import Image
from route_continuity import inspect,REVIEW_KEYS
from tunnel_guide import layout,route_contract
import illustration_workflow as w
from test_illustration_workflow import plan

def fixture():
    return {'version':1,'inventory':['main-in','main-out','branch'],
     'nodes':{
      'source':{'kind':'frame_exit','description':'behind camera','continues_to':'upstream utility network','position':[0,0,0]},
      'tee':{'kind':'junction','description':'three-port tee','position':[1,0,0]},
      'far':{'kind':'wall_passage','description':'rear wall','continues_to':'same pipe beyond wall','cue':'sleeve around pipe','position':[2,0,0]},
      'cap':{'kind':'cap','description':'inspection stub','cue':'closed blind flange','position':[1,1,0]}},
     'routes':[
      {'id':'main-in','from':'source','to':'tee','trace':'straight main','points':[[0,0,0],[1,0,0]]},
      {'id':'main-out','from':'tee','to':'far','trace':'same main beyond tee','points':[[1,0,0],[2,0,0]]},
      {'id':'branch','from':'tee','to':'cap','trace':'short branch ending at cap','points':[[1,0,0],[1,1,0]]}],
     'crossings':[{'routes':['main-in','branch'],'kind':'joined','node':'tee'}],
     'occlusions':[{'route':'main-out','behind':'foreground panel','continuation':'continues straight through rear wall sleeve'}]}

class RouteTests(unittest.TestCase):
    def ok(self,c):self.assertEqual(inspect(c)['status'],'passed',inspect(c))
    def bad(self,c):self.assertEqual(inspect(c)['status'],'failed',inspect(c))
    def test_connected_tee_and_cap(self):self.ok(fixture())
    def test_all_tunnel_routes_have_coordinate_bound_ends(self):
        c=route_contract(layout());self.ok(c);self.assertEqual(len(c['routes']),43)
        self.assertIn('86 coordinate-bound endpoint contacts',inspect(c)['checked'])
    def test_descriptions_without_cad_are_allowed(self):
        c=fixture()
        for n in c['nodes'].values():n.pop('position')
        for r in c['routes']:r.pop('points')
        self.ok(c);self.assertTrue(any('descriptive' in x for x in inspect(c)['limits']))
    def test_missing_endpoint(self):
        c=fixture();c['routes'][0]['to']='nowhere';self.bad(c)
    def test_free_termination_not_hidden(self):
        c=fixture();c['nodes']['cap']['kind']='occluded';self.bad(c)
    def test_separate_crossing_keeps_two_independent_routes(self):
        c=route_contract(layout())
        c['crossings']=[{'routes':['ceiling-0','back--1-0'],'kind':'separate','cue':'Ceiling route is above and behind the side bank in this view'}]
        self.ok(c)
    def test_incomplete_tee(self):
        c=fixture();c['routes'].pop();c['inventory'].pop();c['nodes'].pop('cap');c['crossings']=[];self.bad(c)
    def test_boundary_without_destination(self):
        c=fixture();c['nodes']['far'].pop('continues_to');self.bad(c)
    def test_cap_without_visible_closure(self):
        c=fixture();c['nodes']['cap'].pop('cue');self.bad(c)
    def test_duplicate_inventory(self):
        c=fixture();c['inventory'].append('branch');self.bad(c)
    def test_missing_inventoried_route(self):
        c=fixture();c['inventory'].append('new-hidden-pipe');self.bad(c)
    def test_detached_endpoint(self):
        c=fixture();c['routes'][2]['points'][-1]=[1,1.2,0];self.bad(c)
    def test_false_join_at_crossing(self):
        c=fixture();c['crossings'][0]['node']='cap';self.bad(c)
    def test_crossing_cannot_be_separate_and_joined(self):
        c=fixture();c['crossings'][0].update(kind='separate',cue='front');self.bad(c)
    def test_occlusion_needs_continuation(self):
        c=fixture();c['occlusions'][0].pop('continuation');self.bad(c)
    def test_multiple_pipes_cannot_share_blind_cap(self):
        c=fixture();c['routes'][1]['to']='cap';c['routes'][1].pop('points');self.bad(c)
    def test_invalid_numeric_inputs(self):
        for value in (float('nan'),float('inf'),True):
            c=fixture();c['nodes']['source']['position'][0]=value;self.bad(c)
    def test_repeated_path_point(self):
        c=fixture();c['routes'][0]['points']=[[0,0,0],[0,0,0],[1,0,0]];self.bad(c)
    def test_unknown_optional_structure_is_reported(self):
        c=fixture();c['occlusions']=[None];self.bad(c)

class WorkflowContinuityTests(unittest.TestCase):
    def test_persistence_and_pixel_review_are_separate(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);p=plan();p.update(route_scope='present',continuity=fixture())
            a=w.prepare(root,'routes','Draw pipes.',p)
            self.assertEqual(w.read(a/'continuity.json')['status'],'passed')
            src=root/'synthetic.png';Image.new('RGB',(24,16),'white').save(src)
            original=w.retain(a,src,w.read(a/'request.json'))
            obs={k:{'status':'visible_correct','notes':'Synthetic test only'} for k in set(w.BASE_REVIEW)|set(p['relationships'])}
            with self.assertRaises(ValueError):w.review(a,original,obs)
            for key in REVIEW_KEYS:obs[key]={'status':'uncertain','notes':'Synthetic test does not claim pixel continuity'}
            rv=w.review(a,original,obs);result=w.accept(a,original,rv,root/'final.png')
            self.assertTrue(any('continuity:ends' in x for x in result['limitations']))
    def test_missing_contract_requires_simple_plan_not_adapter(self):
        p=plan();p['route_scope']='present'
        with self.assertRaisesRegex(ValueError,'no numerical adapter'):w.validate_plan(p)
    def test_failed_continuity_retains_history(self):
        with tempfile.TemporaryDirectory() as t:
            p=plan();p['continuity']=fixture();p['continuity']['routes'][0]['to']='missing'
            with self.assertRaises(ValueError):w.prepare(Path(t),'bad','Draw.',p)
            self.assertTrue(list(Path(t).rglob('failure.json')))
    def test_correction_preserves_route_rules(self):
        p=plan();p['continuity']=fixture()
        self.assertIn('Occlusion hides a continuous route',w.compile_prompt(p,'Draw.'))

if __name__=='__main__':unittest.main()
