import copy
import unittest
from bunker_access import build_access_core
from design_realization import edge_id
from requirement_contracts import requirement_checks,program_checks


def fixture():
    s=build_access_core(3);edge=dict(kind='vertical_access',from_='lower',to='upper',requires=['supported_flight','landing','headroom','opening'])
    edge['from']=edge.pop('from_');key=edge_id(edge);landing=s['stair_access'][0]['landing']
    s['materialized_design']=dict(edges={key:s['core_vertical_edges']['0']},zones={'lower':dict(anchor=[0,0,0]),'upper':dict(anchor=[0,0,3.5])},
        requirements={key:dict(supported_flight=dict(parts=['core-stair-0']),landing=dict(parts=[landing]),
            headroom=dict(access_volumes=s['core_vertical_edges']['0']),opening=dict(openings=['core-opening-1']))})
    return s,dict(edges=[edge]),key


class RequirementTests(unittest.TestCase):
    def test_every_requirement_has_physical_result(self):
        s,selected,_=fixture();rows=requirement_checks(s,selected)
        self.assertEqual(len(rows),4);self.assertEqual({r['status'] for r in rows},{'passed'})
        self.assertTrue(all(r['validators'] and r['evidence'] for r in rows))

    def test_empty_connected_volume_does_not_supply_flight(self):
        s,selected,key=fixture();s['materialized_design']['requirements'][key]['supported_flight']['parts']=[]
        self.assertEqual(requirement_checks(s,selected)[0]['status'],'failed')

    def test_deleted_opening_is_detected_with_same_access_graph(self):
        s,selected,_=fixture();s['openings']=[o for o in s['openings'] if o['id']!='core-opening-1']
        rows=requirement_checks(s,selected);self.assertEqual(next(r for r in rows if r['requirement']=='opening')['status'],'failed')

    def test_witness_from_another_level_is_rejected(self):
        s,selected,key=fixture();s['materialized_design']['requirements'][key]['supported_flight']['parts']=['core-stair-1']
        self.assertEqual(requirement_checks(s,selected)[0]['status'],'failed')

    def test_low_headroom_is_not_accepted_by_connectivity(self):
        s,selected,key=fixture();vid=s['materialized_design']['edges'][key][0];v=next(v for v in s['access_volumes'] if v['id']==vid)
        v['body_above']=.2
        rows=requirement_checks(s,selected);self.assertEqual(next(r for r in rows if r['requirement']=='headroom')['status'],'failed')

    def test_required_witness_must_cover_every_mapped_volume(self):
        s,selected,key=fixture();s['materialized_design']['requirements'][key]['headroom']['access_volumes']=[]
        rows=requirement_checks(s,selected);self.assertEqual(next(r for r in rows if r['requirement']=='headroom')['status'],'failed')

    def test_floating_walk_path_cannot_claim_a_nearby_flight(self):
        s,selected,key=fixture()
        for v in s['access_volumes']:
            if v['id'] in s['materialized_design']['edges'][key]:v['walking_offset']=.5
        rows=requirement_checks(s,selected)
        self.assertEqual(rows[0]['status'],'failed');self.assertIn('detached',rows[0]['message'])

    def test_unknown_requirement_is_unsupported_not_ignored(self):
        s,selected,key=fixture();selected['edges'][0]['requires'].append('operational_elevator')
        s['materialized_design']['requirements'][key]['operational_elevator']={}
        self.assertEqual(requirement_checks(s,selected)[-1]['status'],'unsupported')

    def test_displaced_landing_invalidates_physical_requirement(self):
        s,selected,_=fixture();landing=s['stair_access'][0]['landing'];next(p for p in s['parts'] if p['id']==landing)['origin'][1]+=.2
        self.assertTrue(any(r['requirement']=='landing' and r['status']=='failed' for r in requirement_checks(s,selected)))

    def test_legacy_partial_graph_is_reported_explicitly(self):
        s,selected,_=fixture();s.pop('validation_policy');s['materialized_design'].pop('requirements')
        self.assertEqual({r['status'] for r in requirement_checks(s,selected)},{'not_run'})

    def test_semantic_labels_are_separate_from_program_adapter(self):
        s={'parts':[dict(id='box',kind='cabinet')],'materialized_design':dict(nodes={'z':['box']},zones={'z':dict(program='sleeping',program_contract=dict(adapter='component_set',required_kinds=['seat']))})}
        self.assertEqual(program_checks(s)[0]['status'],'failed')


if __name__=='__main__':unittest.main()
