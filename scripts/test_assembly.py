import unittest,numpy as np
from connected_plant import fixture
from scene_model import validate
from render_scene import build,Renderer
class AssemblyTests(unittest.TestCase):
    def test_connected_ports(self):self.assertEqual(validate(fixture()),[])
    def test_platform_does_not_cut_into_vessels(self):
        data=fixture()
        deck=next(p for p in data['parts'] if p['id']=='deck')
        for tank in (p for p in data['parts'] if p['kind']=='vessel'):
            self.assertLessEqual(deck['origin'][1]+deck['size'][1],tank['origin'][1])
        deck['size'][1]+=.2
        self.assertTrue(any('Bounding-box penetration: deck' in e for e in validate(data)))
    def test_moved_equipment_breaks_connection(self):
        data=fixture();next(p for p in data['parts'] if p['id']=='pump')['origin'][0]+=.5
        self.assertTrue(any('mismatch' in e for e in validate(data)))
    def test_worker_support(self):
        data=fixture();next(p for p in data['parts'] if p['id']=='inspector')['origin'][2]+=.1
        self.assertTrue(any('feet' in e for e in validate(data)))
    def test_full_render(self):
        mesh=build(fixture());r=Renderer(mesh,700,600);im=r.draw(mesh)
        self.assertEqual(im.size,(700,600));self.assertGreater(np.isfinite(r.z).sum(),40000)
if __name__=='__main__':unittest.main()
