import copy,unittest
from build_bunker import build_scene
from domain_grammar import BUNKER_FAMILIES
from design_variants import verify_selection
from evaluate_designs import topology_signature
from scene_model import validate,validation_report
from design_realization import realization_report
from assembly_model import storage_rack,compose_assembly,RigidTransform

class MaterializedFamilyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.scenes={f:build_scene(seed=27,family=f) for f in BUNKER_FAMILIES}
    def test_every_declared_family_passes_strict_and_realization(self):
        signatures=set()
        for f,s in self.scenes.items():
            with self.subTest(family=f):
                self.assertEqual(validate(s),[]);self.assertEqual(validation_report(s)['status'],'passed')
                self.assertEqual(realization_report(s)['status'],'passed')
                self.assertEqual(s['delivery_counts'],{'level':6,'stair':5})
                self.assertEqual(s['workflow_version'],3);self.assertEqual(s['support_contract_version'],1)
                self.assertEqual({c['part'] for c in s['ground_contacts']},set(s['grounded']))
                selected=verify_selection(s['design_intent'],s['design_selection']['candidates'],s['design_selection'])
                self.assertEqual(selected['family'],f);signatures.add(topology_signature(selected))
                self.assertEqual(set(s['materialized_design']['requirements']),set(s['materialized_design']['edges']))
        self.assertEqual(len(signatures),3)
    def test_non_six_level_request_is_preserved(self):
        for family in BUNKER_FAMILIES:
            s=build_scene(seed=8,levels=3,family=family)
            self.assertEqual(s['delivery_counts'],{'level':3,'stair':2});self.assertEqual(validate(s),[])
    def test_supported_geometry_is_not_shared_unchanged_between_families(self):
        floors=[]
        for s in self.scenes.values():
            floors.append(tuple(tuple(p['origin']) for p in s['parts'] if p['id'].endswith('/floor')))
        self.assertEqual(len(set(floors)),3)
    def test_each_family_rejects_closed_door(self):
        for family,s in self.scenes.items():
            bad=copy.deepcopy(s);door=next(o for o in bad['openings'] if '/doorway' in o['id'])
            bad['parts'].append({'id':'door-obstruction','kind':'cabinet','origin':door['origin'],'size':door['size']})
            bad['expected_counts']['cabinet']=bad['expected_counts'].get('cabinet',0)+1
            bad['bearings'].append({'part':'door-obstruction','on':door['id'].split('/')[0]+'/floor'})
            self.assertTrue(validate(bad),family)
    def test_storage_is_constructed_as_racks_with_supported_crates(self):
        for s in self.scenes.values():
            racks=[a for a in s['assemblies'] if a['role']=='storage_rack']
            self.assertTrue(racks);self.assertTrue(all(len(a['members'])>=13 for a in racks))
    def test_rack_placement_retains_mounts_and_ground_contacts(self):
        rack=storage_rack('rack');placed=compose_assembly(rack,RigidTransform((2,3,0)),prefix='room/')
        self.assertEqual(len(placed['mounts']),12)
        self.assertTrue(all(x.startswith('room/rack/') for x in placed['assembly']['ground_contacts']))
    def test_missing_geological_ground_patch_is_rejected(self):
        bad=copy.deepcopy(self.scenes['hub']);bad['ground_contacts'].pop()
        self.assertEqual(validation_report(bad)['status'],'failed')

if __name__=='__main__':unittest.main()
