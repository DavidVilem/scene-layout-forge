import copy,itertools,unittest
from design_intent import DesignIntent
from domain_grammar import DOMAINS,BUNKER_FAMILIES
from design_variants import generate_candidates,evaluate_candidates,choose_candidate,fingerprint

class DomainDiversityTests(unittest.TestCase):
    def intent(self,domain='building',**choices):
        return DesignIntent.from_data({'subject':'conceptual subject','domain':domain,'program_roles':['drive','brake'],
            'choices':choices,'constraints':{'connected':True}})
    def test_mechanism_two_components_does_not_invent_rooms(self):
        for c in generate_candidates(self.intent('mechanism',component_count=2),3):
            self.assertEqual(len(c['nodes']),2)
            self.assertEqual({n['entity'] for n in c['nodes']},{'mechanical_component'})
            self.assertEqual({e['kind'] for e in c['edges']},{'transmission'})
            self.assertNotIn('circulation',{n['role'] for n in c['nodes']})
    def test_single_component_is_valid_inventory(self):
        c=generate_candidates(self.intent('mechanism',component_count=1),3)[0]
        self.assertEqual(len(c['nodes']),1);self.assertEqual(c['edges'],[])
    def test_domains_have_different_relation_contracts(self):
        kinds={domain:generate_candidates(self.intent(domain,component_count=3),3)[0]['edges'][0]['kind'] for domain in DOMAINS}
        self.assertEqual(len(set(kinds.values())),5)
        self.assertEqual(kinds['environment'],'site_access')
    def test_unknown_and_curved_capabilities_are_explicit(self):
        data=self.intent('vehicle').to_data();data['features']=['curved_enclosure']
        for c in generate_candidates(data,3):
            self.assertEqual(c['capability']['status'],'unsupported')
            self.assertTrue(any('curved' in r for r in c['capability']['reasons']))
    def test_all_120_orders_preserve_scores_and_selected_fingerprint(self):
        intent=self.intent();candidates=generate_candidates(intent,42,count=5)
        reports=evaluate_candidates(intent,candidates)
        baseline={r['fingerprint']:(r['quality'],r['novelty']) for r in reports}
        chosen=fingerprint(choose_candidate(intent,candidates)[0])
        for order in itertools.permutations(candidates):
            got=evaluate_candidates(intent,list(order))
            self.assertEqual({r['fingerprint']:(r['quality'],r['novelty']) for r in got},baseline)
            self.assertEqual({r['id']:r['duplicate'] for r in got},{r['id']:r['duplicate'] for r in reports})
            self.assertEqual(fingerprint(choose_candidate(intent,list(order))[0]),chosen)
    def test_program_change_has_separate_structural_fingerprint(self):
        c=generate_candidates(self.intent(),42)[0];changed=copy.deepcopy(c)
        changed['nodes'][1]['program']='different functional program'
        self.assertEqual(fingerprint(c,semantic=False),fingerprint(changed,semantic=False))
        self.assertNotEqual(fingerprint(c),fingerprint(changed))
    def test_duplicate_representative_is_order_independent(self):
        it=self.intent();a=generate_candidates(it,3)[0];b=copy.deepcopy(a);b['id']='renamed-copy'
        first={r['id']:r['duplicate'] for r in evaluate_candidates(it,[a,b])}
        self.assertEqual(first,{r['id']:r['duplicate'] for r in evaluate_candidates(it,[b,a])})
    def test_explicit_closed_loop_filters_hub(self):
        data=self.intent().to_data();data['constraints']['closed_loop']=True
        selected,_=choose_candidate(data,generate_candidates(data,9,count=5))
        self.assertEqual(selected['family'],'ring')
    def test_mismatched_seed_is_not_inferred_from_first_candidate(self):
        it=self.intent();c=generate_candidates(it,3);c[1]['seeds']['design']+=1
        with self.assertRaisesRegex(ValueError,'seed streams'):choose_candidate(it,c)
    def test_forged_capability_is_recomputed(self):
        from design_variants import hard_errors
        it=self.intent('vehicle');c=generate_candidates(it,3)[0]
        c['capability']['status']='supported';c['capability']['reasons']=[]
        self.assertIn('materialization capability differs from registered adapter',hard_errors(it,c))
    def bunker_intent(self,**extra):
        return DesignIntent.from_data({'subject':'connected mountain bunker','domain':'building',
            'constraints':{'levels':6,'connected':True},'program_roles':['control','dormitory','storage','workshop','utilities','medical'],
            'choices':dict(zones_per_level=5,materializer='bunker',require_materializable=True,**extra)})
    def test_default_many_seeds_select_multiple_supported_organizations(self):
        intent=self.bunker_intent();families=set();outside_frontier=False
        for seed in range(32):
            chosen,evidence=choose_candidate(intent,generate_candidates(intent,seed,count=5))
            families.add(chosen['family']);self.assertEqual(evidence['selection_policy'],'quality_then_seeded_content')
            self.assertEqual(len(evidence['eligible_ids']),3)
            outside_frontier |= chosen['id'] not in evidence['pareto_ids']
        self.assertGreaterEqual(len(families),2)
        self.assertTrue(families<=set(BUNKER_FAMILIES));self.assertTrue(outside_frontier)
    def test_explicit_travel_quality_has_priority_over_seeded_variety(self):
        intent=self.bunker_intent(quality_objective='shortest_travel')
        for seed in range(6):
            chosen,evidence=choose_candidate(intent,generate_candidates(intent,seed,count=5))
            report=next(r for r in evidence['reports'] if r['id']==chosen['id'])
            self.assertEqual(report['quality'],max(r['quality'] for r in evidence['reports'] if r['valid']))
            self.assertEqual(chosen['family'],'hub')
    def test_maximum_novelty_is_an_explicit_optional_preference(self):
        intent=self.bunker_intent(novelty_objective='maximize')
        chosen,evidence=choose_candidate(intent,generate_candidates(intent,19,count=5))
        report=next(r for r in evidence['reports'] if r['id']==chosen['id'])
        self.assertEqual(evidence['selection_policy'],'quality_then_explicit_max_novelty')
        self.assertEqual(report['novelty'],max(r['novelty'] for r in evidence['reports'] if r['valid']))

if __name__=='__main__':unittest.main()
