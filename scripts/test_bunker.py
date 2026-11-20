import copy,unittest
from build_bunker import build_scene
from scene_model import validate,validation_report
from design_variants import verify_selection
from assembly_model import compile_cutaway,opening_errors
from design_realization import edge_id,realization_errors

class BunkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.scene=build_scene(seed=1,family='hub')
    def test_physical_scene_passes_strict(self):
        self.assertEqual(validate(self.scene),[])
        self.assertEqual(validation_report(self.scene)['status'],'passed')
    def test_selected_graph_really_materialized(self):
        s=self.scene;e=s['design_selection'];selected=verify_selection(s['design_intent'],e['candidates'],e)
        self.assertEqual(len({n['level'] for n in selected['nodes']}),6)
        self.assertEqual(set(s['materialized_design']['nodes']),{n['id'] for n in selected['nodes']})
        self.assertEqual(set(s['materialized_design']['edges']),{edge_id(x) for x in selected['edges']})
        self.assertEqual(realization_errors(s),[])
        by={p['id']:p for p in s['parts']}
        for n in selected['nodes']:
            if n['role']=='circulation':continue
            floor=by[n['id']+'/floor']
            for axis in (0,1):self.assertAlmostEqual(floor['origin'][axis]+floor['size'][axis]/2,n['center'][axis]*4)
    def test_seed_reproducible(self):self.assertEqual(self.scene,build_scene(seed=1,family='hub'))
    def test_real_openings_and_unique_stair_chain(self):
        self.assertEqual(opening_errors(self.scene),[])
        self.assertGreater(len(self.scene['openings']),24)
        self.assertEqual(sum(p['kind']=='stair' for p in self.scene['parts']),5)
    def test_cut_is_representation_not_physical_mutation(self):
        before=copy.deepcopy(self.scene);display=compile_cutaway(self.scene,hide_ids=self.scene['display_hidden'])
        self.assertEqual(self.scene,before)
        self.assertLess(len(display['parts']),len(before['parts']))
        self.assertEqual(display['representation']['type'],'cutaway')
    def test_no_unknown_materialized_references(self):
        ids={p['id'] for p in self.scene['parts']};walk={v['id'] for v in self.scene['access_volumes']}
        for values in self.scene['materialized_design']['nodes'].values():self.assertTrue(set(values)<=ids)
        for values in self.scene['materialized_design']['edges'].values():self.assertTrue(set(values)<=walk)
    def test_unsupported_materializer_never_silently_reuses_hub(self):
        for family in ('ring','stepped'):
            with self.assertRaisesRegex(ValueError,'unsupported'):build_scene(seed=2,family=family)
    def test_automatic_selection_does_not_invent_a_user_family_constraint(self):
        automatic=build_scene(seed=1)
        self.assertNotIn('layout_family',automatic['design_intent']['constraints'])
        evidence=automatic['design_selection']
        self.assertEqual({c['family'] for c in evidence['candidates']},{'hub','branched','stepped','spine','ring'})
    def test_mountain_is_a_physical_enclosure_with_a_separate_display_cut(self):
        s=self.scene;by={p['id']:p for p in s['parts']};terrain=s['terrain_contract']
        self.assertEqual(terrain['type'],'heightfield_with_cavity')
        for side in ('north','south','east','west'):self.assertIn('mountain/inner-'+side,by)
        self.assertEqual(len([k for k in by if k.startswith('mountain/crown-')]),4)
        self.assertIn('mountain/crown-0',s['display_hidden'])
        self.assertNotIn('mountain/crown-3',s['display_hidden'])
        self.assertTrue(any(k.startswith('mountain/slope-') for k in by))
    def test_building_foundations_contact_the_visible_subsurface(self):
        s=self.scene;by={p['id']:p for p in s['parts']}
        self.assertEqual(len(s['foundation_contacts']),9)
        self.assertEqual(len([p for p in s['parts'] if p.get('semantic_role')=='continuous_foundation_contact']),8)
        for contact in s['foundation_contacts']:
            self.assertNotIn(contact['slab'],s['grounded'])
            upper=by[contact['slab']];lower=by[contact['on']]
            self.assertAlmostEqual(upper['origin'][2],lower['origin'][2]+lower['size'][2])
            if 'geology' in contact:
                geo=by[contact['geology']]
                self.assertAlmostEqual(lower['origin'][2],geo['origin'][2]+geo['size'][2])
    def test_foundation_contact_gap_is_rejected(self):
        bad=copy.deepcopy(self.scene)
        footing=next(p for p in bad['parts'] if p['id']=='L0Z4/floor/foundation-contact')
        footing['size'][2]-=.1
        self.assertTrue(any('L0Z4/floor' in e for e in validate(bad)))
        self.assertEqual(validation_report(bad)['status'],'failed')
    def test_stair_hole_cannot_be_filled(self):
        bad=copy.deepcopy(self.scene)
        from scene_model import make_part
        bad['parts'].append(make_part('blocked-opening','slab',[-.05,-3,3.3],[1.7,6,.2]))
        bad['expected_counts']['slab']+=1
        bad['mounts'].append({'part':'blocked-opening','on':'core-floor-1/cell-1','axis':'x','side':1})
        self.assertTrue(any('occupied walking envelope' in e for e in validate(bad)))
        self.assertEqual(validation_report(bad)['status'],'failed')
    def test_doorway_cannot_be_closed_by_unrelated_box(self):
        bad=copy.deepcopy(self.scene);door=next(o for o in bad['openings'] if o['id']=='L0Z4/doorway')
        from scene_model import make_part
        bad['parts'].append(make_part('blocked-door','cabinet',door['origin'],door['size']))
        bad['expected_counts']['cabinet']+=1
        bad['bearings'].append({'part':'blocked-door','on':'L0Z4/floor'})
        self.assertTrue(any('occupied walking envelope' in e for e in validate(bad)))
        self.assertEqual(validation_report(bad)['status'],'failed')
    def test_missing_column_support_is_not_transferred_to_other_columns(self):
        bad=copy.deepcopy(self.scene)
        bad['bearings']=[b for b in bad['bearings'] if b['part']!='L0Z4/post-0']
        self.assertTrue(any('bearing path' in e for e in validate(bad)))
    def test_detached_materialization_route_is_detected(self):
        bad=copy.deepcopy(self.scene);edge=next(k for k in bad['materialized_design']['edges'] if 'L0Z0->L0Z4' in k)
        bad['materialized_design']['edges'][edge]=bad['materialized_design']['edges'][edge][-1:]
        self.assertTrue(realization_errors(bad))

if __name__=='__main__':unittest.main()
