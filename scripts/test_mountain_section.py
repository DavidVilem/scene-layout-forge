import copy
import unittest
from mountain_section import build_mountain_section
from assembly_model import compile_cutaway
from scene_model import validate


class MountainSectionTests(unittest.TestCase):
    def test_complete_mountain_passes_applicable_strict_geometry(self):
        scene=build_mountain_section()
        self.assertEqual(validate(scene),[])
        self.assertTrue(any('/crown-' in p['id'] for p in scene['parts']))
        self.assertTrue(any('/slope-' in p['id'] for p in scene['parts']))

    def test_cavity_really_does_not_intersect_building_envelope(self):
        scene=build_mountain_section();lo=[-16.3,-16.3,-.4];hi=[16.3,16.3,21]
        for p in scene['parts']:
            end=[p['origin'][k]+p['size'][k] for k in range(3)]
            self.assertFalse(all(min(hi[k],end[k])-max(lo[k],p['origin'][k])>1e-6 for k in range(3)),p['id'])

    def test_section_preserves_source_and_roof_and_exposes_front(self):
        scene=build_mountain_section();original=copy.deepcopy(scene)
        display=compile_cutaway(scene,scene['display_hidden'])
        self.assertEqual(scene,original)
        self.assertEqual(validate(display),[])
        ids={p['id'] for p in display['parts']}
        self.assertNotIn('mountain/inner-east',ids)
        self.assertNotIn('mountain/inner-south',ids)
        self.assertIn('mountain/crown-3',ids)
        self.assertIn('mountain/inner-west',ids)

    def test_removed_contact_fails_validation(self):
        scene=build_mountain_section()
        scene['custom_contacts']=[c for c in scene['custom_contacts'] if c['part']!='mountain/crown-0']
        self.assertTrue(any('contact' in e or 'support' in e for e in validate(scene)))

    def test_invalid_extent_rejected(self):
        with self.assertRaises(ValueError):build_mountain_section(extent=20)

    def test_subsurface_has_exact_geometric_contacts_without_foundation_claim(self):
        scene=build_mountain_section()
        band=next(p for p in scene['parts'] if p['id']=='mountain/subsurface-upper')
        self.assertAlmostEqual(band['origin'][2]+band['size'][2],-.4)
        self.assertTrue(any('room foundations' in text for text in scene['terrain_contract']['limits']))
        self.assertTrue(any(m['part']=='mountain/subsurface-lower' for m in scene['mounts']))
        self.assertEqual(validate(scene),[])


if __name__=='__main__':unittest.main()
