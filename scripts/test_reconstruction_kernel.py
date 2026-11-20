import copy,unittest,tempfile
from pathlib import Path
from PIL import Image
from reconstruction_geometry import component,mesh_for
from reconstruction_kernel import compile_spec,build


def fixture():
    parts=[];groups=[];targets=[]
    for name,at,anchor in [('base',[0,0,0],[.5,.5,1]),('upper',[0,0,1],[.5,.5,1])]:
        parts.append(dict(id=name,shapes=[dict(type='box',at=at,size=[1,1,1])],anchors={'joint':anchor},provenance='observed',evidence='Visible block',hidden_assumptions='Rear depth inferred',support_note='Shared surface anchor checked'))
        groups.append(dict(id=name,label=name,members=[name],offset=[0,0,0] if name=='base' else [0,0,2],fixed=name=='base',provenance='observed',evidence='Visible block',separation_note='Explanatory'))
        targets.append(dict(parts=[name],image_bbox=[0,0,1,1],evidence='Visible block'))
    return dict(schema_version=1,title='Fixture',camera_notes='Oblique, inferred depth',limitations=['Conceptual'],components=parts,assemblies=groups,correspondence=targets,contacts=[{'from':'base:joint','to':'upper:joint'}])


class ReconstructionTests(unittest.TestCase):
    def test_surface_contact(self):
        scene,config,report=compile_spec(fixture());self.assertEqual(report['contacts'][0]['status'],'passed');self.assertTrue(scene['registered_geometry'])
        from explorer_workflow import compile_scene
        payload=compile_scene(scene,config);self.assertEqual(payload['connections'][0]['id'],'attachment[0]')
    def test_gap_rejected(self):
        s=fixture();s['components'][1]['shapes'][0]['at'][2]=1.2;s['components'][1]['anchors']['joint'][2]=1.2
        with self.assertRaisesRegex(ValueError,'Contact gap'):compile_spec(s)
    def test_floating_anchor_rejected(self):
        s=fixture()
        for p in s['components']:p['anchors']['joint']=[.5,.5,.5]
        with self.assertRaisesRegex(ValueError,'misses actual surface'):compile_spec(s)
    def test_observed_needs_correspondence(self):
        s=fixture();s['correspondence'].pop()
        with self.assertRaisesRegex(ValueError,'missing image correspondence'):compile_spec(s)
    def test_hidden_assumptions_required(self):
        s=fixture();del s['components'][0]['hidden_assumptions']
        with self.assertRaisesRegex(ValueError,'hidden shape assumptions'):compile_spec(s)
    def test_nonfinite_image_bbox(self):
        s=fixture();s['correspondence'][0]['image_bbox'][0]=float('nan')
        with self.assertRaises(ValueError):compile_spec(s)
    def test_generic_shape_families(self):
        shapes=[dict(type='ellipsoid',radii=[1,2,1]),dict(type='revolve',profile=[[1,0],[.7,1],[.02,2]],start=20,end=300),dict(type='sweep',points=[[0,0,0],[0,0,2]],radius=.2),dict(type='surface',points=[[[0,0,0],[1,0,.1]],[[0,1,.2],[1,1,.3]]]),dict(type='mesh',vertices=[[0,0,0],[1,0,0],[0,1,1]],faces=[[0,1,2]])]
        for i,shape in enumerate(shapes):
            with self.subTest(shape=shape['type']):self.assertTrue(component(dict(id=str(i),shapes=[shape]))['parameters']['faces'])
    def test_invalid_mesh(self):
        with self.assertRaises(ValueError):mesh_for(dict(type='mesh',vertices=[[0,0,0],[1,0,0],[2,0,0]],faces=[[0,1,2]]))
    def test_unsupported_not_box(self):
        with self.assertRaisesRegex(ValueError,'Unsupported'):mesh_for(dict(type='dragon'))
    def test_polygon_requires_triangulation(self):
        with self.assertRaisesRegex(ValueError,'explicit triangles'):mesh_for(dict(type='mesh',vertices=[[0,0,0],[1,0,0],[1,1,0],[0,1,0]],faces=[[0,1,2,3]]))
    def test_pipe_endpoint_failure_retained(self):
        s=fixture();s['connections']=[{'from':'base:joint','to':'upper:joint','route':[[0,0,4],[0,0,6]],'radius':.1}]
        with self.assertRaisesRegex(ValueError,'Geometry failed'):compile_spec(s)
    def test_coverage_not_global_approval(self):
        s=fixture();s['contacts']=[]
        a,b,c=compile_spec(s);self.assertEqual(set(c['components_without_checked_contact']),{'base','upper'})
    def test_material_validation(self):
        s=fixture();s['components'][0]['color']='#ffffff';a,b,c=compile_spec(s);self.assertEqual(a['parts'][0]['appearance']['color'],'#ffffff')
        s['components'][0]['color']='javascript:invalid'
        with self.assertRaises(ValueError):compile_spec(s)
    def test_glass_opacity_preserved_in_payload(self):
        from explorer_workflow import compile_scene
        s=fixture();s['components'][1]['opacity']=.22
        scene,config,_=compile_spec(s)
        self.assertEqual(compile_scene(scene,config)['parts'][1]['opacity'],.22)
        for invalid in [0,-1,1.1,float('nan'),True]:
            s['components'][1]['opacity']=invalid
            with self.assertRaises(ValueError):compile_spec(s)
    def test_build_single_image_and_history(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);p=root/'source.jpg';Image.new('RGB',(16,16),'blue').save(p)
            run,job,html=build(root,fixture(),p,'Reconstruct this image',operation='reconstruct',reuse_reason='Reconstruct this image')
            self.assertTrue(html.is_file());self.assertTrue((run/'specification.json').is_file());self.assertTrue((job/'source.jpg').is_file())
    def test_failed_build_retained(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);p=root/'source.png';Image.new('RGB',(16,16)).save(p);s=fixture();s['contacts'][0]['from']='missing:joint'
            with self.assertRaises(ValueError):build(root,s,p,'Invalid fixture',operation='reconstruct',reuse_reason='Reconstruct this image')
            self.assertEqual(len(list((root/'output/history').glob('reconstruction-*/failure.json'))),1)


if __name__=='__main__':unittest.main()
