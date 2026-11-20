import copy
import unittest
from run_example import load_example
from scene_model import validate
from render_scene import build

class MechanicalChecks(unittest.TestCase):
    def setUp(self):self.data,_=load_example('supported-drive')
    def part(self,name):return next(p for p in self.data['parts'] if p['id']==name)
    def test_supported_chain_builds(self):
        self.assertEqual(validate(self.data),[])
        self.assertGreater(len(build(self.data).faces),0)
    def test_shifted_bearing_rejected(self):
        self.part('bearing-a')['origin'][0]+=.03
        self.assertTrue(any('centreline' in e for e in validate(self.data)))
    def test_short_shaft_rejected(self):
        self.part('output-shaft')['parameters']['points'][1][1]=4.6
        self.assertTrue(any('thickness' in e for e in validate(self.data)))
    def test_aperture_rejected(self):
        self.part('bearing-a')['parameters']['inner_ratio']=.2
        self.assertTrue(any('aperture' in e for e in validate(self.data)))
    def test_wrong_axis_rejected(self):
        self.part('bearing-a')['parameters']['orientation']='x'
        self.assertTrue(any('parallel' in e for e in validate(self.data)))
    def test_invalid_declarations_return_errors(self):
        for value in [None,{},[None],[{'shaft':'missing','bearing':'bearing-a'}]]:
            data=copy.deepcopy(self.data);data['shaft_bearings']=value
            self.assertTrue(validate(data))

if __name__=='__main__':unittest.main()
