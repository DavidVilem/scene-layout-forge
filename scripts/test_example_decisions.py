import copy,json,unittest
from run_example import load_example,ROOT
from check_examples import decision_errors

class ExampleDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scene,cls.recipe=load_example('supported-drive')
        cls.record=json.loads((ROOT/'examples/supported-drive/decision-contract.json').read_text(encoding='utf-8'))
    def test_original_decision_contract_matches_actual_fixture(self):
        self.assertEqual(decision_errors(self.scene,self.recipe,self.record),[])
    def test_legacy_coverage_cannot_be_promoted_by_documentation(self):
        record=copy.deepcopy(self.record);record['coverage_status']='passed'
        self.assertTrue(any('promote' in e for e in decision_errors(self.scene,self.recipe,record)))
    def test_wrong_adapter_and_missing_negative_are_rejected(self):
        record=copy.deepcopy(self.record);record['adapter_kinds'].append('invented');record['negative_command']=''
        errors=decision_errors(self.scene,self.recipe,record)
        self.assertTrue(any('adapter inventory' in e for e in errors));self.assertTrue(any('negative_command' in e for e in errors))
    def test_lost_count_invariant_is_rejected(self):
        record=copy.deepcopy(self.record);record['invariants']['recipe_counts']['worker']=3
        self.assertTrue(any('invariants' in e for e in decision_errors(self.scene,self.recipe,record)))

if __name__=='__main__':unittest.main()
