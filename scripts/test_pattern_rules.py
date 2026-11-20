import ast
import copy
import json
import os
from pathlib import Path
import re
import tempfile
import unittest

from pattern_rules import ROOT,load_catalog,validate_catalog,evidence_confidence,select_patterns

def scene():
    return {'design_intent':{'domain':'building'},'camera':{'projection':'perspective'},
        'visual_plan':{'view_intent':'cutaway'},'context_plan':{'mode':'interior','entities':[]},
        'light_material_plan':{'value_policy':'dark_interior','materials':{}},'parts':[]}

def selected(result):return {r['id'] for r in result['rules']}

class PatternRuleTests(unittest.TestCase):
    def test_catalog_is_original_portable_and_links_existing_evidence(self):
        catalog=load_catalog();self.assertEqual(validate_catalog(catalog),[])
        self.assertEqual(len({r['family'] for r in catalog['patterns']}),6)
        text=json.dumps(catalog)
        self.assertIsNone(re.search(r'I\d{4}|[A-Za-z]:[/\\]|image-study|data:image',text))
        for record in catalog['patterns']:
            self.assertIn(record['mode'],{'operational','comparison','negative_control','scope_limit'})
            self.assertTrue(record['applicability']);self.assertIsInstance(record['exceptions'],list)
            for evidence in record['evidence']:
                filename,name=evidence['source'].split('::');path=ROOT/filename
                tree=ast.parse(path.read_text(encoding='utf-8-sig'))
                self.assertIn(name,{node.name for node in ast.walk(tree) if isinstance(node,ast.FunctionDef)})

    def test_duplicate_evidence_family_never_increases_confidence(self):
        catalog=load_catalog();record=copy.deepcopy(catalog['patterns'][0])
        before=evidence_confidence(record,catalog)
        for index in range(25):
            duplicate=copy.deepcopy(record['evidence'][0]);duplicate['source']='duplicate-procedural-note-'+str(index)
            record['evidence'].append(duplicate)
        self.assertEqual(evidence_confidence(record,catalog),before)

    def test_independent_registered_family_counts_once_and_respects_ceiling(self):
        catalog=load_catalog();record=copy.deepcopy(catalog['patterns'][0]);before=evidence_confidence(record,catalog)
        new={'family':'guide_readability','source':'independent-guide-fixture','scope':'Different question from projection equations.'}
        record['evidence'].extend([new,copy.deepcopy(new)])
        after=evidence_confidence(record,catalog)
        self.assertEqual(after['score'],round(before['score']+catalog['confidence_policy']['per_independent_family'],6))
        record['confidence']['ceiling']=.3
        self.assertEqual(evidence_confidence(record,catalog)['score'],.3)

    def test_dark_interior_is_explicit_exception_to_open_air_rule(self):
        result=select_patterns(scene())
        self.assertIn('light_dark_interior',selected(result));self.assertNotIn('light_open_air',selected(result))
        excluded={v['id']:v['reason'] for v in result['excluded_by_exception']}
        self.assertIn('light_open_air',excluded);self.assertIn('dark interior',excluded['light_open_air'])
        exterior=scene();exterior['light_material_plan']['value_policy']='open_air';exterior['context_plan']['mode']='landscape'
        result=select_patterns(exterior)
        self.assertIn('light_open_air',selected(result));self.assertNotIn('light_dark_interior',selected(result))

    def test_plan_keeps_parallel_projection_and_no_perspective_recipe(self):
        value=scene();value['camera']['projection']='orthographic';value['visual_plan']['view_intent']='plan';value['light_material_plan']['value_policy']='diagram'
        result=select_patterns(value)
        self.assertIn('view_orthographic',selected(result));self.assertNotIn('view_perspective',selected(result));self.assertNotIn('light_open_air',selected(result))
        self.assertEqual(result['conflicts'],[])
        value['camera']['projection']='perspective';result=select_patterns(value)
        self.assertTrue(result['conflicts']);self.assertNotIn('view_perspective',selected(result))
        self.assertNotIn('view_orthographic',selected(result))

    def test_unknown_fields_do_not_invent_domain_or_artistic_claims(self):
        result=select_patterns({'subject':'a machine in a forest','parts':[]})
        self.assertEqual(result['rules'],[]);self.assertNotIn('domain',result['facts'])
        self.assertTrue(result['unknown_facts'])
        value=scene();value['camera']['projection']='fisheye';value['design_intent']['domain']='medical_anatomy'
        result=select_patterns(value)
        self.assertNotIn('domain',result['facts']);self.assertNotIn('projection',result['facts'])
        self.assertNotIn('view_perspective',selected(result))

    def test_organic_guidance_is_nonmedical_and_unknown_adapters_stay_unknown(self):
        value=scene();value['parts']=[{'id':'tree','kind':'custom','parameters':{'adapter':'natural_tree_mass_v1'}}]
        result=select_patterns(value);record=next(r for r in result['rules'] if r['id']=='organic_scope_only')
        self.assertEqual(record['mode'],'scope_limit');self.assertIn('do not establish medical',record['principle'])
        self.assertTrue(any('No medical guidance' in limit for limit in record['limits']))
        value['parts'][0]['parameters']['adapter']='invented_anatomy_adapter'
        self.assertNotIn('organic_scope_only',selected(select_patterns(value)))

    def test_material_rule_requires_real_owner_and_explicit_local_frame(self):
        value=scene();value['parts']=[{'id':'panel','kind':'slab'}]
        value['light_material_plan']['materials']={'absent':{'family':'wood','origin':[0,0,0],'axis':[0,0,1],'tangent':[1,0,0]}}
        self.assertNotIn('material_local_frames',selected(select_patterns(value)))
        value['light_material_plan']['materials']['panel']=value['light_material_plan']['materials'].pop('absent')
        self.assertIn('material_local_frames',selected(select_patterns(value)))
        del value['light_material_plan']['materials']['panel']['tangent']
        self.assertNotIn('material_local_frames',selected(select_patterns(value)))
        value['light_material_plan']['materials']['panel'].update(axis=[0,0,0],tangent=[1,0,0])
        self.assertNotIn('material_local_frames',selected(select_patterns(value)))

    def test_isolation_does_not_select_situated_context_enrichment(self):
        value=scene();value['context_plan']['mode']='isolated';result=select_patterns(value)
        self.assertIn('context_isolated',selected(result));self.assertNotIn('context_with_purpose',selected(result))
        value['context_plan']['entities']=[{'id':'extra-worker'}]
        self.assertTrue(select_patterns(value)['conflicts'])

    def test_selection_is_order_independent_and_preserves_inputs(self):
        value=scene();catalog=load_catalog();before=copy.deepcopy(value);old=copy.deepcopy(catalog)
        first=select_patterns(value,catalog);catalog['patterns'].reverse()
        self.assertEqual(first,select_patterns(value,catalog));self.assertEqual(value,before)
        catalog['patterns'].reverse();self.assertEqual(catalog,old)

    def test_invalid_conditions_or_evidence_do_not_gain_confidence(self):
        for mutation in ('fact','family','confidence','duplicate_id'):
            catalog=load_catalog()
            if mutation=='fact':catalog['patterns'][0]['applicability']={'fact':'invented_medical_canon','eq':True}
            elif mutation=='family':catalog['patterns'][0]['evidence'][0]['family']='renamed_copy_claiming_independence'
            elif mutation=='confidence':catalog['confidence_policy']['baseline']=float('nan')
            else:catalog['patterns'].append(copy.deepcopy(catalog['patterns'][0]))
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):validate_catalog(catalog)

    def test_default_catalog_resolves_from_installation_not_cwd(self):
        before=os.getcwd()
        with tempfile.TemporaryDirectory() as temporary:
            try:
                os.chdir(temporary);self.assertTrue(load_catalog()['patterns'])
            finally:os.chdir(before)

if __name__=='__main__':unittest.main()
