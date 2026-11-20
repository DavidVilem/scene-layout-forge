import copy,unittest
from unittest.mock import patch
from evaluation_fixtures import CASES,load
from evaluate_registered import run,run_case,ablations,properties,physical_identity

class RegisteredEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.result=run(with_guides=False,with_ablations=False)
    def test_six_domains_and_sixteen_actual_positive_negative_cases(self):
        r=self.result
        self.assertEqual(r['status'],'passed')
        self.assertEqual(len(r['cases']),16)
        self.assertEqual(set(r['balance']),{'building','process','mechanism','vehicle','environment','cross-domain'})
        self.assertEqual(r['negative_mutation_misses'],0)
        self.assertEqual(r['critical_failure_rate'],0)
        self.assertTrue(all(c['negative']['errors'] for c in r['cases']))
    def test_legacy_and_unsupported_complete_subjects_never_become_strict_successes(self):
        rows={c['id']:c for c in self.result['cases']}
        for case in ('E04','E08','E10','E15'):
            self.assertEqual(rows[case]['geometry']['coverage_status'],'partial')
            self.assertIn('unsupported',rows[case]['scope'])
        self.assertEqual(rows['E05']['geometry']['coverage_status'],'passed')
        self.assertIn('complete train cabin unsupported',rows['E05']['scope'])
        self.assertTrue(all(c['finished_pixels']['status']=='not_run' for c in rows.values()))
    def test_unrejected_negative_cannot_pass_via_visual_score(self):
        case=next(c for c in CASES if c['id']=='E11')
        with patch('evaluate_registered.mutate',side_effect=lambda scene,kind:copy.deepcopy(scene)):
            result=run_case(case,with_guide=False)
        self.assertEqual(result['regression_status'],'failed')
        self.assertEqual(result['negative']['status'],'missed')
    def test_physical_identity_ignores_style_but_not_new_fixture_or_contact(self):
        scene=load('materials');changed=copy.deepcopy(scene)
        changed['light_material_plan']['ambient']=.1
        self.assertEqual(physical_identity(scene),physical_identity(changed))
        changed['parts'][1]['size'][0]+=.1
        self.assertNotEqual(physical_identity(scene),physical_identity(changed))
        changed=copy.deepcopy(scene);changed['bearings'].pop()
        self.assertNotEqual(physical_identity(scene),physical_identity(changed))
    def test_rigid_properties_and_unknown_case_selection(self):
        self.assertTrue(all(properties().values()))
        with self.assertRaises(ValueError):run(['not-a-case'],False,False)
    def test_fixed_scene_context_detail_light_material_style_and_night_ablations(self):
        rows=ablations()
        self.assertEqual({r['variant'] for r in rows},{'material_off','opposite_light','context_off','detail_off','style_seed','same_pump_plant_night'})
        self.assertTrue(all(r['status']=='passed' and r['physical_geometry_unchanged'] for r in rows))
        for row in rows:
            self.assertEqual(row['visual_preference'],'not_observed')
            if row['variant'] not in ('context_off','detail_off'):
                self.assertTrue(row['depth_unchanged']);self.assertTrue(row['ownership_unchanged'])

if __name__=='__main__':unittest.main()
