import copy
import unittest
from design_variants import generate_candidates, choose_candidate
from design_realization import edge_id, realization_errors, realization_report


def example():
    intent={'subject':'multifunction scientific station',
            'constraints':{'levels':1,'connected':True,'layout_family':'hub'},
            'program_roles':['workshop','living','water','control'],
            'choices':{'program_assignment':'zone','zones_per_level':5}}
    candidates=generate_candidates(intent,seed=2,count=4);selected,evidence=choose_candidate(intent,candidates)
    scene={'units':'m','design_intent':intent,'design_selection':evidence,'parts':[],
           'access_nodes':[],'access_volumes':[],
           'materialized_design':{'nodes':{},'edges':{},'zones':{},'topology_transform':{'translation':[0,0,0],'scale_xy':4}}}
    m=scene['materialized_design']
    for n in selected['nodes']:
        x,y,z=n['center'];x*=4;y*=4;name='part-'+n['id'];aid='access-'+n['id']
        scene['parts'].append({'id':name,'kind':'slab','origin':[x-.3,y-.3,z],
            'size':[.6,.6,.9],'design_program':n['program'],'semantic_role':'circulation_landing' if n['program']=='access' else n['program']+'_station'})
        scene['access_nodes'].append({'id':aid,'position':[x,y,z+1.2]})
        m['nodes'][n['id']]=[name]
        m['zones'][n['id']]={'program':n['program'],'anchor':[x,y,z],
            'min':[x-2,y-2,z],'max':[x+2,y+2,z+3],'access_node':aid,'program_evidence':[name]}
    nodes={a['id']:a['position'] for a in scene['access_nodes']}
    for i,e in enumerate(selected['edges']):
        a='access-'+e['from'];b='access-'+e['to'];pa,pb=nodes[a],nodes[b];vid='route-'+str(i)
        scene['access_volumes'].append({'id':vid,'from':a,'to':b,
            'min':[min(pa[k],pb[k])-.3 for k in range(3)],'max':[max(pa[k],pb[k])+.3 for k in range(3)]})
        m['edges'][edge_id(e)]=[vid]
    return scene


class DesignRealizationTests(unittest.TestCase):
    def test_complete_selected_graph_is_realized(self):
        s=example();original=copy.deepcopy(s)
        self.assertEqual(realization_errors(s),[])
        self.assertEqual(realization_report(s)['status'],'passed')
        self.assertEqual(s,original)

    def test_legacy_is_explicitly_not_applicable(self):
        self.assertEqual(realization_report({'parts':[]})['status'],'not_applicable')
        self.assertTrue(realization_errors({'design_intent':{}}))

    def test_stale_part_id_rejected(self):
        s=example();s['parts'].pop()
        self.assertTrue(any('absent/stale' in x for x in realization_errors(s)))

    def test_wrong_program_rejected(self):
        s=example();s['parts'][1]['design_program']='unrelated'
        self.assertTrue(any('wrong program' in x for x in realization_errors(s)))

    def test_generic_cabinet_label_is_not_semantic_evidence(self):
        s=example();s['parts'][1]['semantic_role']='cabinet'
        self.assertTrue(any('specific semantic' in x for x in realization_errors(s)))

    def test_changing_labels_does_not_realize_new_topology(self):
        s=example();z=s['materialized_design']['zones']['L0Z1'];z['anchor'][0]+=2
        self.assertTrue(any('selected topology transform' in x for x in realization_errors(s)))

    def test_unchanged_actual_geometry_fails_new_zone_allocation(self):
        s=example();s['parts'][1]['origin']=[99,99,0]
        self.assertTrue(any('outside allocated zone' in x for x in realization_errors(s)))

    def test_missing_selected_route_rejected(self):
        s=example();s['access_volumes'].pop()
        self.assertTrue(any('access volume ID is absent/stale' in x for x in realization_errors(s)))

    def test_unrelated_route_does_not_connect_selected_endpoints(self):
        s=example();s['access_volumes'][0]['to']='access-L0Z0'
        self.assertTrue(any('do not connect' in x for x in realization_errors(s)))

    def test_detached_access_volume_rejected(self):
        s=example();s['access_volumes'][0]['min']=[100,100,100];s['access_volumes'][0]['max']=[101,101,101]
        self.assertTrue(any('detached' in x for x in realization_errors(s)))

    def test_missing_node_mapping_rejected(self):
        s=example();del s['materialized_design']['nodes']['L0Z1']
        self.assertTrue(any('nodes: missing' in x for x in realization_errors(s)))

    def test_selection_hash_and_reports_recomputed(self):
        s=example();s['design_selection']['reports'][0]['valid']=False
        self.assertTrue(any('selection evidence' in x for x in realization_errors(s)))


if __name__=='__main__':unittest.main()
