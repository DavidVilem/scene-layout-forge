import unittest,copy
from scene_model import validate,make_part
from render_scene import build

class SchemaTests(unittest.TestCase):
    def base(self):return {'units':'m','parts':[make_part('p','wall',[0,0,0],[1,1,1])]}
    def test_invalid_scene_types_return_errors(self):
        for value in [None,[],4,'scene']:
            self.assertTrue(validate(value))
            with self.assertRaises(ValueError):build(value)
    def test_workflow_and_delivery_contract_shape(self):
        from finish_contract import preflight
        for version in ('3',None,True,4,3.5):
            d=self.base();d['workflow_version']=version
            self.assertTrue(validate(d));self.assertTrue(preflight(d))
        for value in ([],None,{'worker':True},{'level':-1},{'':1}):
            d=self.base();d['delivery_counts']=value;self.assertTrue(preflight(d))
    def test_bad_collections_return_errors(self):
        for field in ['parts','connections','bearings','stair_access','ramp_access','labels','route_obstacles','clearance_pairs','expected_counts']:
            for value in [None,7,'bad']:
                d=self.base();d[field]=value;self.assertTrue(validate(d),(field,value))
    def test_bad_part_payloads(self):
        for key,value in [('parent',{}),('ports',[]),('ports',{'a':[0,float('nan'),1]}),('parameters',[]),('kind',[]),('origin',[True,0,0])]:
            d=self.base();d['parts'][0][key]=value;self.assertTrue(validate(d),(key,value))
    def test_nonfinite_and_boolean_pipe_radius(self):
        for radius in [float('nan'),float('inf'),True,0,-1]:
            d=self.base();d['parts'][0]['ports']={'a':[0,0,0],'b':[1,0,0]}
            d['connections']=[{'from':'p:a','to':'p:b','route':[[0,0,0],[1,0,0]],'radius':radius}]
            self.assertTrue(validate(d),radius)
    def test_invalid_optional_details(self):
        for params in [{'panel_size':[1]},{'grid_spacing':float('nan')},{'axis':[0,0,0]},{'reverse':'false'},{'start':[0,0]}]:
            d=self.base();d['parts'][0]['parameters']=params;self.assertTrue(validate(d))
    def test_invalid_relationship_records(self):
        for field,value in [('connections',[{'from':[]}]),('bearings',[{'part':{},'on':'p'}]),('clearance_pairs',[['p']]),('route_obstacles',[{}]),('labels',[{'target':'p','text':'WALL','position':[2,0]}]),('expected_counts',{'typo':0})]:
            d=self.base();d[field]=value;self.assertTrue(validate(d),field)
    def test_mutated_records_do_not_crash_validator(self):
        values=[None,[],{},True,0,'bad',[1,2],float('inf')]
        for value in values:
            for field in ['id','kind','origin','size','parent','ports','parameters']:
                d=self.base();d['parts'][0][field]=value
                self.assertIsInstance(validate(d),list)
        d=self.base();d['parts'][0]['origin'][0]=10**1000
        self.assertTrue(validate(d))

if __name__=='__main__':unittest.main()
