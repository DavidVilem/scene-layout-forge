import copy
import tempfile
import unittest
from pathlib import Path
from PIL import Image
import illustration_workflow as w
from tunnel_guide import layout,check

def plan():
    return dict(subject='unfamiliar gallery',view='oblique',setting='enclosed',composition='deep',
                detail=['frames','fixings','distant rhythm'],relationships={'wall_mount':'rack fixed to wall'},
                annotations=[],stages=[dict(status='planned',reason='represented scope') for _ in range(8)])

class IllustrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.png=self.root/'generated.png';Image.new('RGB',(24,16),'white').save(self.png)
    def tearDown(self):self.tmp.cleanup()
    def prepare(self):return w.prepare(self.root,'gallery','Draw a gallery.',plan())
    def observations(self):return {k:dict(status='visible_correct',notes='Synthetic workflow fixture, not visual evaluation') for k in (*w.BASE_REVIEW,'wall_mount')}
    def test_missing_adapter_allows_honest_illustration(self):
        a=self.prepare();self.assertEqual(w.read(a/'coverage.json')['status'],'limited')
        im=w.retain(a,self.png,w.read(a/'request.json'));rev=w.review(a,im,self.observations())
        result=w.accept(a,im,rev,self.root/'final.png')
        self.assertTrue(result['limitations']);self.assertTrue((a.parent.parent/'01-site/brief.txt').exists())
    def test_tampered_plan_rejected(self):
        a=self.prepare();(a/'plan.json').write_text('{}')
        with self.assertRaises(ValueError):w.verify(a)
    def test_changed_request_rejected(self):
        a=self.prepare()
        with self.assertRaises(ValueError):w.retain(a,self.png,{'prompt':'other'})
    def test_missing_relationship_review_rejected(self):
        a=self.prepare();im=w.retain(a,self.png,w.read(a/'request.json'));obs=self.observations();obs.pop('wall_mount')
        with self.assertRaises(ValueError):w.review(a,im,obs)
    def test_changed_reviewed_pixels_rejected(self):
        a=self.prepare();im=w.retain(a,self.png,w.read(a/'request.json'));rev=w.review(a,im,self.observations())
        Image.new('RGB',(24,16),'black').save(im)
        with self.assertRaises(ValueError):w.accept(a,im,rev,self.root/'final.png')
    def test_detected_model_error_is_not_waived(self):
        bad={'schema_version':2,'validation_policy':'strict','units':'m','parts':[{'id':'bad','kind':'pipe','origin':[0,0,0],'size':[-1,1,1]}],'connections':[]}
        self.assertEqual(w.assess(bad)['status'],'failed')
        with self.assertRaises(ValueError):w.prepare(self.root,'broken','Draw.',plan(),scene=bad)
        self.assertTrue(list((self.root/'output/history').rglob('failure.json')))
    def test_no_model_downgrade(self):
        with self.assertRaises(ValueError):w.assess({'parts':[]})
    def test_unsupported_stays_limited_but_strict_still_rejects(self):
        from test_coherence import fixture
        from scene_model import make_part,validate
        data=fixture();data['parts'].append(make_part('rotor','rotor',[8,8,4],[1,1,1]))
        report=w.assess(data)
        self.assertEqual(report['status'],'limited')
        self.assertTrue(any(c['status']=='unsupported' for c in report['checks']))
        self.assertTrue(validate(data))
    def test_missing_support_still_fails(self):
        from test_coherence import fixture
        data=fixture();data['bearings']=[]
        self.assertEqual(w.assess(data)['status'],'failed')
    def test_correction_sequence_and_budget(self):
        a=self.prepare();im=w.retain(a,self.png,w.read(a/'request.json'));rev=w.review(a,im,self.observations())
        r=w.correction(a,im,rev,'Repair bracket contact')
        with self.assertRaises(ValueError):w.correction(a,im,rev,'Skip preceding result')
        im2=w.retain_correction(a,self.png,r);rev2=w.review(a,im2,self.observations())
        r2=w.correction(a,im2,rev2,'Refine same bracket')
        im3=w.retain_correction(a,self.png,r2);rev3=w.review(a,im3,self.observations())
        with self.assertRaises(ValueError):w.correction(a,im3,rev3,'Third attempt')
    def test_observed_error_requires_correction(self):
        a=self.prepare();im=w.retain(a,self.png,w.read(a/'request.json'));obs=self.observations()
        obs['wall_mount']={'status':'visible_error','notes':'Floating rack'};rev=w.review(a,im,obs)
        with self.assertRaises(ValueError):w.accept(a,im,rev,self.root/'final.png')
    def test_no_overwrite(self):
        a=self.prepare();im=w.retain(a,self.png,w.read(a/'request.json'));rev=w.review(a,im,self.observations())
        with self.assertRaises(FileExistsError):w.accept(a,im,rev,self.png)
    def test_tunnel_failure_probes(self):
        data=layout();self.assertEqual(check(data)['status'],'passed')
        bad=copy.deepcopy(data);bad['pipes'][0]['x']=0
        self.assertTrue(check(bad)['errors'])
        bad=copy.deepcopy(data);bad['brackets'][0]['z']+=.3
        self.assertTrue(check(bad)['errors'])
        bad=copy.deepcopy(data);bad['pipes'][1].update(x=bad['pipes'][0]['x'],z=bad['pipes'][0]['z'])
        self.assertTrue(check(bad)['errors'])

if __name__=='__main__':unittest.main()
