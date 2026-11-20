import copy
import unittest
from unittest.mock import patch
from architecture_stages import digest,report,record_stage,records_errors

def fixture():
    def p(k,o,size,kind='slab'):return dict(id=k,origin=o,size=size,kind=kind)
    parts=[p('terrain',[-8,-8,-1],[16,16,1],'footing'),p('floor',[0,0,0],[8,6,.2]),p('approach',[-4,1,0],[4,2,.2]),
           p('roof',[0,0,3],[8,6,.2]),p('wall-a',[0,0,.2],[8,.2,2.8],'wall'),p('wall-b',[0,5.8,.2],[8,.2,2.8],'wall'),
           p('fixture',[2,2,.2],[1,1,1],'cabinet'),p('drive',[4,3,.2],[1,1,1],'cabinet'),p('entry-frame',[0,1,.2],[.2,.2,2.8],'column')]
    s={'workflow_version':4,'parts':parts,'access_roots':['outside'],'access_nodes':[{'id':k,'position':v} for k,v in [('outside',[-2,2,1.2]),('entry',[.5,2,1.2]),('room',[3,2,1.2])]],
       'access_volumes':[dict(id='arrival',**{'from':'outside','to':'entry'}),dict(id='internal',**{'from':'entry','to':'room'})],
       'openings':[dict(id='door',origin=[0,1,.2],size=[.2,2,2.8])],
       'bearings':[dict(part='roof',on=k) for k in ('wall-a','wall-b')]+[dict(part='drive',on='fixture')]}
    alt=[dict(id=str(i),volumes=[dict(size=[8+i,6,3+i],roof='flat' if i==0 else 'shed')],arrival='west',tradeoff='compact vs stepped') for i in range(3)]
    alt[0].update(realized_by=['roof'],geometry_sha256=digest([parts[3]]))
    alt[0]['volumes'][0].update(size=[8,6,.2],parts=['roof'])
    s['architecture_contract']={'version':1,'mode':'building','site':dict(terrain=['terrain'],placement_reason='bench follows contour',operating_direction='south',approach=dict(root='outside',entry='entry',surfaces=['approach'])),
      'spaces':[dict(id='room',activity='maintenance',area_reason='bench and working aisle',access_node='room',bounds=dict(min=[0,0,.2],max=[8,6,3]),fixtures=['fixture'],doors=['door'])],
      'occupied_floors':['floor'],'alternatives':alt,'selected':'0','envelope':dict(roofs=['roof']),
      'roof_supports':[dict(roof='roof',supports=['wall-a','wall-b'])],
      'required_systems':['machine'],'systems':[dict(id='machine',members=['fixture','drive'],links=[['fixture','drive']],limits='contact only')],
      'witnesses':[dict(id=r,role=r,parts=[k]) for r,k in [('arrival','approach'),('entrance','entry-frame'),('envelope','roof'),('operation','drive'),('context','terrain')]]}
    view={'projection_review':{'components':{p['id']:{'area_fraction':.01} for p in parts}}}
    return s,view

class ArchitectureTests(unittest.TestCase):
    def setUp(self):self.s,self.v=fixture()
    def errors(self,stage):return report(self.s,self.v)[stage]['errors']
    def test_valid_all_seven(self):
        self.assertTrue(all(v['status']=='passed' for k,v in report(self.s,self.v).items() if k!='finish'))
    def test_root_inside(self):
        self.s['access_roots']=['room'];self.s['architecture_contract']['site']['approach']['root']='room'
        self.assertTrue(self.errors('site'))
    def test_arrival_is_not_a_name(self):
        self.s['access_nodes'][0]['position']=[-7,2,1.2]
        self.assertTrue(self.errors('site'))
    def test_missing_approach_connection(self):
        self.s['access_volumes'].pop(0);self.assertTrue(self.errors('site'))
    def test_empty_room(self):
        self.s['architecture_contract']['spaces'][0]['fixtures']=[];self.assertTrue(self.errors('program'))
    def test_relocated_variants_are_duplicates(self):
        a=self.s['architecture_contract']['alternatives']
        for c in a:c['volumes']=copy.deepcopy(a[0]['volumes'])
        self.assertTrue(self.errors('massing'))
    def test_stale_massing(self):
        self.s['parts'][3]['size'][0]+=1;self.assertTrue(self.errors('massing'))
    def test_volume_must_match_geometry(self):
        self.s['architecture_contract']['alternatives'][0]['volumes'][0]['size']=[500,300,150]
        self.assertTrue(self.errors('massing'))
    def test_negative_visibility_threshold(self):
        self.s['architecture_contract']['witnesses'][0]['min_area_fraction']=-1
        self.assertTrue(self.errors('representation'))
    def test_single_roof_support(self):
        self.s['architecture_contract']['roof_supports'][0]['supports']=['wall-a'];self.assertTrue(self.errors('structure'))
    def test_roof_contact_removed(self):
        self.s['bearings'].pop(0);self.assertTrue(self.errors('structure'))
    def test_missing_door(self):
        self.s['openings']=[];self.assertTrue(self.errors('levels'))
    def test_gap_between_approach_and_floor(self):
        self.s['parts'][2]['size'][0]=3
        self.assertTrue(self.errors('levels'))
    def test_door_not_on_route(self):
        self.s['openings'][0]['origin'][1]=4;self.assertTrue(self.errors('levels'))
    def test_function_cannot_be_omitted(self):
        self.s['architecture_contract']['systems']=[];self.assertTrue(self.errors('systems'))
    def test_disconnected_function(self):
        self.s['bearings'].pop();self.assertTrue(self.errors('systems'))
    def test_cut_erases_identity(self):
        self.v['projection_review']['components']['roof']['area_fraction']=0
        self.assertTrue(self.errors('representation'))
    def test_eight_stage_chain_and_invalidation(self):
        self.s['validation_policy']='strict'
        records=[]
        with patch('scene_model.validate',return_value=[]):
            for n in range(1,8):records.append(record_stage(self.s,n,records,self.v,note='inspected fixture'))
        self.assertFalse(records_errors(self.s,records,7,self.v))
        self.s['parts'][0]['size'][0]+=1
        self.assertTrue(records_errors(self.s,records,7,self.v))
    def test_cannot_skip_stage(self):
        with self.assertRaises(ValueError):record_stage(self.s,3,[],self.v,note='skip')
    def test_stage_seven_rejects_occluded_detail(self):
        self.s['validation_policy']='strict';self.s['visual_plan']={};records=[]
        with patch('scene_model.validate',return_value=[]):
            for n in range(1,7):records.append(record_stage(self.s,n,records,self.v,note='inspected fixture'))
        with patch('visual_contract.compile_visual_contract',return_value={'errors':['hidden toolboard'],'guide_status':'failed'}):
            with self.assertRaisesRegex(ValueError,'hidden toolboard'):record_stage(self.s,7,records,self.v,note='must fail')
    def test_pixel_observations_need_localized_architecture(self):
        obs=[dict(target='architecture:'+w['id'],state='visible_correct',note='observed',region=[.1,.1,.3,.3]) for w in self.s['architecture_contract']['witnesses']]
        self.assertEqual(report(self.s,self.v,obs)['finish']['status'],'passed')
        obs[0]['state']='uncertain'
        self.assertEqual(report(self.s,self.v,obs)['finish']['status'],'failed')
    def test_missing_contract_fails_closed(self):
        del self.s['architecture_contract'];self.assertTrue(self.errors('site'))
    def test_physical_failure_cannot_gain_stage_approval(self):
        self.s['validation_policy']='strict';records=[]
        for n in range(1,4):records.append(record_stage(self.s,n,records,self.v,note='inspected'))
        with patch('scene_model.validate',return_value=['disconnected actual geometry']):
            with self.assertRaisesRegex(ValueError,'disconnected'):record_stage(self.s,4,records,self.v,note='try')

if __name__=='__main__':unittest.main()
