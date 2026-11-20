import copy,unittest
from evaluate_designs import cases,run_matrix,topology_signature,camera_only_duplicate_check,materialization_requirements
from design_variants import generate_candidates

class DesignEvaluationTests(unittest.TestCase):
    def test_six_domains_use_domain_programs_and_not_six_levels_everywhere(self):
        values=cases();self.assertEqual(len(values),6)
        self.assertEqual(next(x for x in values if x['id']=='bunker')['intent']['constraints']['levels'],6)
        self.assertTrue(all(x['intent']['constraints']['levels']==1 for x in values if x['id']!='bunker'))
        self.assertEqual(len({tuple(x['intent']['program_roles']) for x in values}),6)
    def test_matrix_distinguishes_graph_acceptance_from_geometry(self):
        result=run_matrix(case_specs=cases()[:1])
        self.assertEqual(result['design_graph_status'],'passed')
        for run in result['domains'][0]['runs']:
            self.assertEqual(run['geometry_validation'],'not_run');self.assertEqual(run['artistic_validation'],'not_run')
            self.assertTrue(run['prior_exact_fingerprint_excluded'])
    def test_same_seed_list_is_not_a_diversity_experiment(self):
        with self.assertRaises(ValueError):run_matrix([1,1])
    def test_rotated_camera_and_detail_do_not_create_novelty(self):
        candidate=generate_candidates(cases()[0]['intent'],0)[0]
        self.assertTrue(camera_only_duplicate_check(candidate))
    def test_geometry_metric_change_does_not_create_new_topology(self):
        candidate=generate_candidates(cases()[0]['intent'],0)[0];other=copy.deepcopy(candidate)
        for node in other['nodes']:node['center'][0]+=node['level']*4
        self.assertEqual(topology_signature(candidate),topology_signature(other))
    def test_realization_checklist_contains_edges_but_no_pass_claim(self):
        candidate=generate_candidates(cases()[0]['intent'],0)[0];result=materialization_requirements(candidate)
        self.assertEqual(len(result['required_links']),len(candidate['edges']))
        self.assertEqual(result['status'],'unverified_until_realized_geometry_checked')
        self.assertTrue(any('headroom' in e['requires'] for e in result['required_links']))

if __name__=='__main__':unittest.main()
