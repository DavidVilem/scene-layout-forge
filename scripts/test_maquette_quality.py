import unittest,copy
from test_reconstruction_kernel import fixture
from reconstruction_kernel import compile_spec
from maquette_quality import triangle_box
import numpy as np
import tempfile
from pathlib import Path
from PIL import Image

def quality():
    return dict(features=[dict(id=i,level=level,status='modeled',parts=['base'],evidence='Source observation',critical=level=='primary') for i,level in [('body','primary'),('joint','secondary'),('seam','fine')]],detail_zones=[{'id':'body','features':['body','joint','seam']}],landmarks=['body'],access_scope='not_applicable',protected_spaces=[],overlap_review=[])

class MaquetteTests(unittest.TestCase):
    def spec(self):
        s=fixture();s['schema_version']=2;s['quality_contract']=quality();return s
    def test_requires_contract(self):
        s=self.spec();del s['quality_contract']
        with self.assertRaisesRegex(ValueError,'quality_contract'):compile_spec(s)
    def test_legacy_not_fidelity_pass(self):self.assertEqual(compile_spec(fixture())[2]['quality']['status'],'not_run')
    def test_required_detail_cannot_disappear(self):
        s=self.spec();s['quality_contract']['features'][0]['status']='omitted'
        with self.assertRaisesRegex(ValueError,'Critical'):compile_spec(s)
    def test_missing_detail_tier(self):
        s=self.spec();s['quality_contract']['detail_zones'][0]['features']=['body','joint']
        with self.assertRaisesRegex(ValueError,'primary, secondary and fine'):compile_spec(s)
    def test_solid_containment(self):
        s=self.spec();s['quality_contract']['protected_spaces']=[dict(id='door',purpose='Entrance',min=[.2,.2,.2],max=[.8,.8,.8])]
        with self.assertRaisesRegex(ValueError,'blocked'):compile_spec(s)
    def test_crossing_surface(self):
        s=self.spec();s['quality_contract']['protected_spaces']=[dict(id='door',purpose='Entrance',min=[.2,.2,.8],max=[.8,.8,1.2])]
        with self.assertRaisesRegex(ValueError,'blocked'):compile_spec(s)
    def test_clear_space_and_boundary_contact(self):
        s=self.spec();s['quality_contract']['protected_spaces']=[dict(id='passage',purpose='Passage',min=[1,0,0],max=[2,1,2])]
        self.assertEqual(compile_spec(s)[2]['quality']['protected_spaces'][0]['status'],'passed')
    def test_access_missing_volume(self):
        s=self.spec();s['quality_contract']['access_scope']='Building entrance'
        with self.assertRaisesRegex(ValueError,'protected spaces'):compile_spec(s)
    def test_unknown_exemption(self):
        s=self.spec();s['quality_contract']['protected_spaces']=[dict(id='door',purpose='Door',min=[1,0,0],max=[2,1,2],exceptions={'ghost':'ignore'})]
        with self.assertRaises(ValueError):compile_spec(s)
    def test_overlapping_separate_parts_fail(self):
        s=self.spec();s['contacts']=[];s['components'][1]['shapes'][0]['at']=[0,0,.5]
        s['quality_contract']['overlap_review']=[dict(parts=['base','upper'],classification='separate',reason='Should be clear')]
        with self.assertRaisesRegex(ValueError,'Unresolved bounds overlap'):compile_spec(s)
    def test_nonintersecting_triangle_despite_bounds(self):
        self.assertFalse(triangle_box([[0,0,0],[3,0,0],[0,3,0]],np.array([2.,2.,-.1]),np.array([2.2,2.2,.1])))
    def test_finite_camera_required(self):
        from explorer_workflow import compile_scene
        a,b,c=compile_spec(self.spec());b['presentation']={'direction':[0,0,0]}
        with self.assertRaises(ValueError):compile_scene(a,b)
    def test_accept_requires_independent_critical_feature_review(self):
        import explorer_workflow as e
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);pair=root/'pair';pair.mkdir()
            for name in ('ilustrada.png','coloreada.png'):Image.new('RGB',(12,12)).save(pair/name)
            a,b,c=compile_spec(self.spec());job=e.prepare(root,a,b,'Synthetic acceptance test',pair=pair);e.render(job)
            browser=dict(candidate_sha256=e.digest(job/'candidate.html'),errors=[],**{k:True for k in ('webgl','selection','fixed_assemblies','reset','views','section','visibility','keyboard','offline','mobile')})
            obs={k:dict(status='passed',notes='Synthetic acceptance test, not actual visual validation') for k in e.KEYS}
            review={id:dict(status='unverified',notes='Deliberately not reviewed') for id in ('body','joint','seam')}
            with self.assertRaisesRegex(ValueError,'Critical feature not visually confirmed'):e.accept(job,obs,browser,feature_review=review)
            self.assertFalse((pair/'explorador.html').exists())

if __name__=='__main__':unittest.main()
