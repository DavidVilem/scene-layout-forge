import unittest,numpy as np
from highrise import highrise
from scene_model import validate,make_part
from render_scene import build,Renderer

class HighriseTests(unittest.TestCase):
    def test_floor_and_detail_scales(self):
        for floors,bays in [(4,2),(24,3),(60,5)]:self.assertEqual(validate(highrise(floors,bays)),[])
    def test_raised_roof_equipment_fails(self):
        d=highrise(8,2);next(p for p in d['parts'] if p['id']=='roof-service-0')['origin'][2]+=.1
        self.assertTrue(any('bearing height' in e for e in validate(d)))
    def test_wrong_ramp_height_fails(self):
        d=highrise(8,2);next(p for p in d['parts'] if p['id']=='entry-ramp')['size'][2]=.4
        self.assertTrue(any('landing height' in e for e in validate(d)))
    def test_reverse_ramp_high_edge(self):
        m=build({'units':'m','parts':[make_part('r','ramp',[0,0,0],[2,3,.25],parameters={'reverse':True})]})
        points=np.array([v for f,_ in m.faces for v in f]);self.assertTrue(np.all(points[points[:,2]==.25,1]==0))
    def test_detailed_tower_render(self):
        m=build(highrise(12,3));r=Renderer(m,500,800);r.draw(m)
        for name in ['entry-ramp','entry-canopy','roof-service-0']:
            self.assertGreater((r.owner==r.part_ids[name]).sum(),0,name)

if __name__=='__main__':unittest.main()
