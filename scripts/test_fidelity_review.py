import copy,tempfile,unittest
from pathlib import Path
from PIL import Image
import explorer_workflow as e
from fidelity_review import render_comparison,validate,AXES
from test_explorer_workflow import fixture

class FidelityTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name)
        pair=self.root/'output/pair';pair.mkdir(parents=True)
        for n in ['ilustrada.png','coloreada.png']:Image.new('RGB',(24,16),'gray').save(pair/n)
        old=self.root/'output/previous';old.mkdir();(old/'coloreada.png').write_bytes((pair/'coloreada.png').read_bytes())
        s,c=fixture();self.j=e.prepare(self.root,s,c,'Synthetic fidelity test',pair=pair);e.render(self.j)
        self.record=render_comparison(self.j,{'projection':'perspective','eye':[5,-7,4],'target':[1,1,.6],'rationale':'Test only'})
        self.f=[{'id':'body','critical':True}]
        self.r={'body':{'status':'visible','notes':'Synthetic','fidelity':{a:{'status':'matched','source_evidence':'Synthetic source','model_evidence':'Synthetic model'} for a in AXES}}}
    def tearDown(self):self.t.cleanup()
    def check(self):return validate(self.j,self.f,self.r,self.record)
    def test_complete_evidence(self):self.check()
    def test_browser_capture_binding(self):
        from fidelity_review import record_browser_comparison,sha
        folder=self.j/'browser-fixture';folder.mkdir()
        Image.new('RGB',(300,200),'white').save(folder/'model.png')
        evidence={'candidate_sha256':sha(self.j/'candidate.html'),'model_sha256':sha(folder/'model.png'),'errors':[],
          'requested_camera':{'projection':'perspective','eye':[5,-7,4],'target':[1,1,.6],'rationale':'Synthetic binding test only'}}
        e.save(folder/'capture.json',evidence)
        record=record_browser_comparison(self.j,folder);validate(self.j,self.f,self.r,record)
        (folder/'capture.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'capture evidence changed'):validate(self.j,self.f,self.r,record)
    def test_presence_alone_rejected(self):
        self.r['body'].pop('fidelity')
        with self.assertRaisesRegex(ValueError,'Presence'):self.check()
    def test_flat_roof_instead_of_sloped_rejected(self):
        self.r['body']['fidelity']['shape']['status']='mismatch'
        with self.assertRaisesRegex(ValueError,'mismatch'):self.check()
    def test_unknown_yaw_of_critical_part_rejected(self):
        self.r['body']['fidelity']['orientation']['status']='uncertain'
        with self.assertRaisesRegex(ValueError,'unresolved'):self.check()
    def test_hidden_noncritical_uncertainty_allowed(self):
        self.f[0]['critical']=False;self.r['body']['fidelity']['orientation']['status']='uncertain';self.check()
    def test_shape_cannot_be_exempted(self):
        self.r['body']['fidelity']['shape'].update(status='not_applicable',reason='simplified')
        with self.assertRaises(ValueError):self.check()
    def test_modified_comparison_rejected(self):
        (self.record.parent/'model.png').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'changed'):self.check()
    def test_old_candidate_rejected(self):
        (self.j/'candidate.html').write_text('changed')
        with self.assertRaisesRegex(ValueError,'different geometry'):self.check()
    def test_reused_pixels_disclosed(self):
        r=e.read(self.j/'image-lineage.json')['coloreada.png']
        self.assertTrue(r['identical_existing_outputs']);self.assertIn('not an image correction',r['action'])
    def test_declared_contact_gap_rejected(self):
        from test_maquette_quality import MaquetteTests
        from reconstruction_kernel import compile_spec
        s=MaquetteTests().spec();s['contacts']=[];s['components'][1]['shapes'][0]['at']=[0,0,8]
        s['quality_contract']['overlap_review']=[{'parts':['base','upper'],'classification':'intended_contact','reason':'Supposed contact'}]
        with self.assertRaisesRegex(ValueError,'geometric gap'):compile_spec(s)

if __name__=='__main__':unittest.main()
