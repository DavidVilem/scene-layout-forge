import copy,unittest
from assembly_model import compose_assembly,RigidTransform

def assembly():
    return {'units':'m','parts':[{'id':'base','kind':'slab','origin':[0,0,0],'size':[2,1,.2]},
        {'id':'post','kind':'column','origin':[1,0,.2],'size':[.2,.2,1]}],
        'relations':[{'id':'joint','type':'rigid_mount','a':{'part':'post','anchor':[.1,.1,0],'normal':[0,0,-1],'axis':[1,0,0]},
            'b':{'part':'base','anchor':[1.1,.1,.2],'normal':[0,0,1]},'points':[[1,.0,.2],[1.2,0,.2],[1.2,.2,.2]],'normals':[[0,0,1]]}],
        'surface_contacts':[{'part':'post','on':'base','points':[[1,0,.2],[1.2,0,.2],[1.2,.2,.2]],'normals':[[0,0,1]]}],
        'ground_surfaces':[{'id':'ground','type':'plane','point':[0,0,0],'normal':[0,0,1],'bounds':{'min':[-3,-3,0],'max':[3,3,0]}}],
        'ground_contacts':[{'part':'base','surface':'ground','points':[[0,0,0],[2,0,0],[2,1,0]]}],
        'camera_junctions':[{'id':'witness','relation_id':'joint','owners':['post','base'],'point':[1.1,.1,.2]}],
        'access_nodes':[{'id':'start','position':[0,0,1]},{'id':'end','position':[1,0,1]}],
        'access_volumes':[{'id':'walk','from':'start','to':'end','min':[-.2,-.2,.2],'max':[1.2,.2,2],
            'walking_path':[[0,0,1],[1,0,1]],'traversable_parts':['base']}],'access_roots':['start']}

class AssemblyRelationTests(unittest.TestCase):
    def test_local_anchors_normals_and_world_witnesses_transform_together(self):
        original=assembly();before=copy.deepcopy(original);t=RigidTransform((4,7,2),90)
        result=compose_assembly(original,t,prefix='unit/');parts={p['id']:p for p in result['parts']};r=result['relations'][0]
        self.assertEqual(original,before);self.assertEqual(r['id'],'unit/joint')
        self.assertEqual(r['a']['part'],'unit/post')
        for endpoint in (r['a'],r['b']):
            world=[parts[endpoint['part']]['origin'][k]+endpoint['anchor'][k] for k in range(3)]
            for a,b in zip(world,t.point([1.1,.1,.2])):self.assertAlmostEqual(a,b)
        for a,b in zip(r['a']['axis'],[0,1,0]):self.assertAlmostEqual(a,b)
        w=result['camera_junctions'][0];self.assertEqual(w['relation_id'],'unit/joint');self.assertEqual(w['owners'],['unit/post','unit/base'])
        self.assertEqual(w['point'],t.point([1.1,.1,.2]))
    def test_surfaces_ground_and_access_records_keep_names_and_geometry(self):
        t=RigidTransform((4,7,2),90);r=compose_assembly(assembly(),t,prefix='unit/')
        self.assertEqual(r['surface_contacts'][0]['part'],'unit/post')
        self.assertEqual(r['ground_contacts'][0]['surface'],'unit/ground')
        self.assertEqual(r['ground_surfaces'][0]['point'],[4,7,2])
        self.assertEqual(r['access_roots'],['unit/start']);self.assertEqual(r['access_volumes'][0]['from'],'unit/start')
        self.assertEqual(r['access_volumes'][0]['walking_path'][1],t.point([1,0,1]))
        self.assertEqual(r['access_volumes'][0]['traversable_parts'],['unit/base'])
    def test_legacy_relation_witness_prefixes_both_owners(self):
        a=assembly();a['camera_junctions'][0]['relation_id']='stair_landing:post->base'
        r=compose_assembly(a,prefix='unit/')
        self.assertEqual(r['camera_junctions'][0]['relation_id'],'stair_landing:unit/post->unit/base')

if __name__=='__main__':unittest.main()
