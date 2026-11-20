"""Circulation-core integration and deliberate physical failure fixtures."""
import unittest
from bunker_access import build_access_core
from assembly_model import opening_errors
from scene_model import validate


class AccessCoreTests(unittest.TestCase):
    def test_six_levels_have_real_openings_and_strict_connected_access(self):
        scene=build_access_core()
        self.assertEqual(validate(scene),[])
        self.assertEqual(opening_errors(scene),[])
        self.assertEqual(len(scene['core_levels']),6)
        self.assertEqual(len(scene['openings']),5)
        self.assertEqual(len(scene['core_vertical_edges']),5)

    def test_support_removed_is_not_silently_accepted(self):
        scene=build_access_core(2)
        scene['mounts']=[m for m in scene['mounts'] if m['part']!='core-stair-0']
        self.assertTrue(any('bearing path' in e or 'support path' in e for e in validate(scene)))

    def test_reversing_one_flight_breaks_landing_and_headroom_contract(self):
        scene=build_access_core(3)
        stair=next(p for p in scene['parts'] if p['id']=='core-stair-1')
        stair['parameters']['reverse']=True
        self.assertTrue(any('landing' in e for e in validate(scene)))

    def test_filling_stairwell_creates_obstruction(self):
        scene=build_access_core(2)
        opening=scene['openings'][0]
        scene['parts'].append({'id':'bad-infill','kind':'wall','origin':opening['origin'],'size':opening['size']})
        scene['bearings'].append({'part':'bad-infill','on':'core-ground'})
        self.assertTrue(validate(scene))


if __name__=='__main__':unittest.main()
