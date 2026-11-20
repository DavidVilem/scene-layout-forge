import copy
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from scene_model import make_part
import explorer_workflow as e


def fixture():
    scene={'units':'m','parts':[make_part('base','slab',[0,0,0],[2,2,.2]),make_part('box','cabinet',[.5,.5,.2],[1,1,1])], 'connections':[]}
    groups=[dict(id=name,label=name,members=[name],offset=[0,0,0] if name=='base' else [0,0,2],fixed=name=='base',
                 provenance='modeled',evidence='Synthetic model',separation_note='Explanatory') for name in ('base','box')]
    return scene,dict(title='Synthetic fixture',assemblies=groups,limitations=['No engineering claim'],quality={'features':[{'id':'body','critical':True}]})


class ExplorerTests(unittest.TestCase):
    def test_standalone_source_is_retained(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);source=root/'photo.jpg';Image.new('RGB',(18,12),'blue').save(source)
            s,c=fixture();j=e.prepare(root,s,c,'Reconstruct external source',source_image=source);e.render(j)
            before=e.digest(source);target=root/'delivered/explorador.html'
            e.accept(j,self.review(),self.browser(j),destination=target,**self.fidelity(j))
            self.assertEqual(before,e.digest(source));self.assertEqual(before,e.digest(target.parent/'source.jpg'))
            self.assertTrue(target.is_file())
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.pair=self.root/'output/sample-01';self.pair.mkdir(parents=True)
        for name,color in [('ilustrada.png','gray'),('coloreada.png','steelblue')]:Image.new('RGB',(24,16),color).save(self.pair/name)
    def tearDown(self):self.tmp.cleanup()
    def job(self,scene=None,config=None):
        s,c=fixture();return e.prepare(self.root,scene or s,config or c,'Inspect fixture',pair=self.pair)
    def fidelity(self,j):
        from fidelity_review import render_comparison,AXES
        comparison=render_comparison(j,{'projection':'perspective','eye':[5,-7,4],'target':[1,1,.6],'rationale':'Synthetic fixture camera'})
        checks={k:{'status':'matched','source_evidence':'Synthetic fixture, not actual image review','model_evidence':'Synthetic fixture, not actual image review'} for k in AXES}
        return {'comparison':comparison,'feature_review':{'body':{'status':'visible','notes':'Synthetic fixture','fidelity':checks}}}
    def review(self):return {k:{'status':'passed','notes':'Synthetic workflow fixture only'} for k in e.KEYS}
    def browser(self,j):return dict(candidate_sha256=e.digest(j/'candidate.html'),errors=[],**{k:True for k in ('webgl','selection','fixed_assemblies','reset','views','section','visibility','keyboard','offline','mobile')})
    def test_geometry_and_owner_retained(self):
        s,c=fixture();p=e.compile_scene(s,c);self.assertEqual({x['id'] for x in p['parts']},{'base','box'})
        self.assertEqual(p['bounds'],[[0.,0.,0.],[2.,2.,1.2]])
    def test_bad_ownership(self):
        for mutate in (lambda c:c['assemblies'][1]['members'].append('base'),lambda c:c['assemblies'][1].update(members=[]),lambda c:c['assemblies'][1].update(members=['ghost'])):
            s,c=fixture();mutate(c)
            with self.assertRaises(ValueError):e.compile_scene(s,c)
    def test_legacy_motion_cannot_move_groups(self):
        s,c=fixture();c['assemblies'][1].update(offset=[5,2,9],phase=[.8,.2])
        p=e.compile_scene(s,c)
        self.assertTrue(all(g['fixed'] and g['offset']==[0,0,0] for g in p['assemblies']))
        self.assertEqual(c['assemblies'][1]['offset'],[5,2,9])
        self.assertEqual(p['interaction_mode'],'fixed_geometry_visibility_only')
    def test_no_motion_metadata_needed(self):
        s,c=fixture()
        for g in c['assemblies']:
            for k in ('offset','phase','separation_note','fixed'):g.pop(k,None)
        p=e.compile_scene(s,c)
        self.assertTrue(all(g['offset']==[0,0,0] for g in p['assemblies']))
        j=self.job(s,c);out=e.render(j).read_text(encoding='utf-8')
        self.assertNotIn('id="explode"',out);self.assertNotIn('id="toggleExplode"',out)
    def test_missing_pair_cannot_be_real_delivery(self):
        s,c=fixture()
        with self.assertRaises(ValueError):e.prepare(self.root,s,c,'No pair')
    def test_failed_model_retained(self):
        s,c=fixture();s['parts'][0]['size']=[-1,2,.2]
        with self.assertRaises(ValueError):self.job(s,c)
        self.assertEqual(len(list((self.root/'output/history').glob('*/failure.json'))),1)
    def test_history_and_source_tamper(self):
        j=self.job();(j/'scene.json').write_text('{}')
        with self.assertRaises(ValueError):e.render(j)
        j=self.job();Image.new('RGB',(24,16),'black').save(self.pair/'coloreada.png')
        with self.assertRaises(ValueError):e.render(j)
    def test_delivery_keeps_pair_and_rejects_overwrite(self):
        before={p.name:e.digest(p) for p in self.pair.iterdir()};j=self.job();e.render(j)
        out=e.accept(j,self.review(),self.browser(j),**self.fidelity(j));self.assertEqual(out.name,'explorador.html')
        self.assertEqual(before,{p.name:e.digest(p) for p in self.pair.glob('*.png')})
        j=self.job();e.render(j)
        with self.assertRaises(FileExistsError):e.accept(j,self.review(),self.browser(j),**self.fidelity(j))
    def test_missing_browser_evidence(self):
        j=self.job();e.render(j)
        with self.assertRaises(ValueError):e.accept(j,self.review(),{})
    def test_changed_candidate(self):
        j=self.job();e.render(j);b=self.browser(j);(j/'candidate.html').write_text('changed')
        with self.assertRaises(ValueError):e.accept(j,self.review(),b)
    def test_no_markup_injection(self):
        s,c=fixture();c['title']='</script><script>alert(1)</script>';j=self.job(s,c);p=e.render(j)
        self.assertNotIn('</script><script>alert(1)</script>',p.read_text(encoding='utf-8'))
    def test_no_unverified_dimensions(self):
        s,c=fixture();c['dimensions_verified']=True
        with self.assertRaises(ValueError):e.compile_scene(s,c)
    def test_failed_visual_review(self):
        j=self.job();e.render(j);obs=self.review();obs['correspondence']['status']='failed'
        with self.assertRaises(ValueError):e.accept(j,obs,self.browser(j))


if __name__=='__main__':unittest.main()
