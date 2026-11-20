import copy,math,unittest
from design_intent import DesignIntent,seed_streams
from design_variants import generate_candidates,fingerprint,hard_errors,evaluate_candidates,choose_candidate,verify_selection

def intent(levels=6):
    return DesignIntent.from_data({'subject':'underground research complex',
        'constraints':{'levels':levels,'connected':True,'required_features':['section'],
                       'required_roles':['research']},
        'program_roles':['research','logistics','living'],'features':['section']})

class DesignVariantTests(unittest.TestCase):
    def test_constraints_are_copied_and_not_overridden(self):
        source={'subject':'station','constraints':{'levels':2},'choices':{'levels':7}}
        it=DesignIntent.from_data(source);source['constraints']['levels']=5
        self.assertEqual(it.constraints['levels'],2)
        self.assertTrue(all(c['levels']==2 for c in generate_candidates(it,31)))
    def test_unknown_hard_constraint_is_not_silently_accepted(self):
        with self.assertRaisesRegex(ValueError,'unsupported'):DesignIntent.from_data({'subject':'x','constraints':{'load_capacity':4}})
    def test_reproducible_seed_and_independent_streams(self):
        self.assertEqual(generate_candidates(intent(),42),generate_candidates(intent(),42))
        seeds=seed_streams(42);self.assertEqual(len(set(seeds.values())),4)
        self.assertNotEqual(seed_streams()['root'],seed_streams()['root'])
    def test_different_seed_changes_design_order_not_constraints(self):
        a=generate_candidates(intent(),42);b=generate_candidates(intent(),43)
        self.assertNotEqual([x['family'] for x in a],[x['family'] for x in b])
        self.assertTrue(all(not hard_errors(intent(),x) for x in a+b))
    def test_generates_distinct_topologies_and_records_unbuilt_geometry(self):
        values=generate_candidates(intent(),42,count=5)
        self.assertEqual(len({fingerprint(x) for x in values}),5)
        self.assertTrue(all(x['geometry_status']=='not_built' for x in values))
    def test_any_requested_level_count_is_preserved(self):
        for n in (1,2,8):
            self.assertTrue(all(x['levels']==n and not hard_errors(intent(n),x) for x in generate_candidates(intent(n),3)))
    def test_id_order_translation_rotation_and_scale_are_not_novelty(self):
        x=generate_candidates(intent(),12)[0];y=copy.deepcopy(x)
        names={n['id']:'renamed-'+str(i) for i,n in enumerate(y['nodes'])}
        t=.12
        for n in y['nodes']:
            n['id']=names[n['id']];a,b,z=n['center'];n['center']=[2*(a*math.cos(t)-b*math.sin(t))+19,2*(a*math.sin(t)+b*math.cos(t))-9,2*z+3]
        for e in y['edges']:e['from']=names[e['from']];e['to']=names[e['to']]
        y['nodes'].reverse();y['edges'].reverse();y['family']='renamed';y['camera_seed']=0
        self.assertEqual(fingerprint(x),fingerprint(y))
    def test_small_metric_change_not_sold_as_new_design(self):
        x=generate_candidates(intent(),12)[0];y=copy.deepcopy(x)
        for n in y['nodes']:n['extent']=[v*1.02 for v in n['extent']]
        self.assertEqual(fingerprint(x),fingerprint(y))
    def test_invalid_candidate_never_gets_quality_score(self):
        values=generate_candidates(intent(),12);bad=values[0];bad['levels']=7
        result=evaluate_candidates(intent(),values)[0]
        self.assertFalse(result['valid']);self.assertNotIn('quality',result)
    def test_disconnected_graph_rejected_before_novelty(self):
        x=generate_candidates(intent(),12)[0];x['edges']=[e for e in x['edges'] if e['kind']!='vertical_access']
        self.assertIn('disconnected circulation graph',hard_errors(intent(),x))
    def test_required_program_and_feature_checked(self):
        x=generate_candidates(intent(),12)[0];x['features']=[]
        self.assertIn('required feature absent: section',hard_errors(intent(),x))
        for node in x['nodes']:node['role']='other';node['program']='other'
        self.assertIn('required role absent: research',hard_errors(intent(),x))
    def test_semantic_duplicate_removed_even_with_new_name(self):
        a=generate_candidates(intent(),12)[0];b=copy.deepcopy(a);b['id']='new-name'
        reports=evaluate_candidates(intent(),[a,b]);self.assertTrue(reports[1]['duplicate'])
    def test_selection_evidence_recomputed(self):
        candidates=generate_candidates(intent(),12);selected,evidence=choose_candidate(intent(),candidates)
        self.assertEqual(verify_selection(intent(),candidates,evidence),selected)
        evidence['reports'][0]['valid']=False
        with self.assertRaisesRegex(ValueError,'stale'):verify_selection(intent(),candidates,evidence)
    def test_tampered_candidate_rejected(self):
        candidates=generate_candidates(intent(),12);_,evidence=choose_candidate(intent(),candidates)
        candidates[0]['nodes'][0]['center'][0]+=1
        with self.assertRaisesRegex(ValueError,'snapshot'):verify_selection(intent(),candidates,evidence)
    def test_all_duplicates_require_redesign(self):
        candidates=generate_candidates(intent(),12)
        with self.assertRaisesRegex(ValueError,'distinct'):choose_candidate(intent(),candidates,[fingerprint(x) for x in candidates])
    def test_explicit_family_not_lost_to_candidate_sampling(self):
        data=intent().to_data();data['constraints']['layout_family']='spine'
        it=DesignIntent.from_data(data)
        for seed in range(4):
            chosen,_=choose_candidate(it,generate_candidates(it,seed,count=3))
            self.assertEqual(chosen['family'],'spine')
    def test_single_level_zone_programs_are_all_preserved(self):
        it=DesignIntent.from_data({'subject':'machine','constraints':{'levels':1,'required_roles':['drive','drum','brake','services']},
            'program_roles':['drive','drum','brake','services'],'choices':{'program_assignment':'zone'}})
        self.assertTrue(all(not hard_errors(it,x) for x in generate_candidates(it,12)))

    def test_circulation_core_is_not_programmed_as_a_furnished_room(self):
        for assignment in ['level', 'zone']:
            data=intent().to_data();data.setdefault('choices',{})['program_assignment']=assignment
            for candidate in generate_candidates(DesignIntent.from_data(data),12):
                cores=[node for node in candidate['nodes'] if node['role']=='circulation']
                self.assertEqual(len(cores),candidate['levels'])
                self.assertTrue(all(node['program']=='circulation' for node in cores))

if __name__=='__main__':unittest.main()
