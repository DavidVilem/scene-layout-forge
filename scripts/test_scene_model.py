import unittest,copy
from scene_model import validate,tower,make_part

class SceneTests(unittest.TestCase):
    def sample(self):
        return {'units':'m','parts':[
            make_part('floor','slab',(0,0,0),(5,5,.2)),
            make_part('person','worker',(1,1,.2),(.4,.4,1.7),parent='floor'),
            make_part('a','vessel',(0,0,.2),(1,1,3),ports={'out':[1,.5,1]}),
            make_part('b','pump',(3,0,.2),(1,1,1),ports={'in':[0,.5,1]})],
            'connections':[{'from':'a:out','to':'b:in','route':[[1,.5,1.2],[3,.5,1.2]],'radius':.1}],
            'clearance_pairs':[['a','b']]}
    def test_valid_scene(self):self.assertEqual(validate(self.sample()),[])
    def test_disconnected_route(self):
        s=self.sample();s['connections'][0]['route'][1][0]=4
        self.assertTrue(any('mismatch' in e for e in validate(s)))
    def test_floating_person(self):
        s=self.sample();s['parts'][1]['origin'][2]=.7
        self.assertTrue(any('feet' in e for e in validate(s)))
    def test_duplicate_and_missing_parent(self):
        s=self.sample();s['parts'].append(copy.deepcopy(s['parts'][0]));s['parts'][1]['parent']='absent'
        e=validate(s);self.assertTrue(any('Duplicate' in x for x in e));self.assertTrue(any('unknown parent' in x for x in e))
    def test_collision(self):
        s=self.sample();s['parts'][3]['origin'][0]=.5
        self.assertTrue(any('penetration' in e for e in validate(s)))
    def test_reject_nan(self):
        s=self.sample();s['parts'][0]['size'][0]=float('nan')
        self.assertTrue(any('finite' in e for e in validate(s)))
    def test_tower_scales(self):
        for f,b in [(1,1),(20,3),(60,5),(100,12)]:
            with self.subTest(floors=f,bays=b):self.assertEqual(validate(tower(f,b)),[])
    def test_tower_limits(self):
        for f,b in [(0,3),(101,3),(4,0)]:
            with self.assertRaises(ValueError):tower(f,b)

if __name__=='__main__':unittest.main()
