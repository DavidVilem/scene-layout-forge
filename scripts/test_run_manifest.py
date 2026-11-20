import copy,json,tempfile,unittest
from pathlib import Path
from PIL import Image
import test_finish_v3 as fixtures
from finish_contract import freeze
from pixel_review import requirements,create_review
from run_manifest import manifest,compare,errors,finalize,digest

class RunManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):fixtures.FinishV3Tests.setUpClass()
    @classmethod
    def tearDownClass(cls):fixtures.FinishV3Tests.tearDownClass()
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        (self.root/'SKILL.md').write_text('revision: "test"',encoding='utf-8')
        self.fixture=fixtures.FinishV3Tests;self.guide=self.fixture.guide
        self.lock=freeze(self.fixture.scene,self.fixture.view)
        self.record=manifest(self.root,self.lock,'test','handoff',self.guide)
        self.review=create_review(self.lock,self.guide,[{'target':k,'state':'uncertain','note':'Synthetic fixture, not approved artistic pixels'} for k in requirements(self.lock)],'test')
    def tearDown(self):self.temp.cleanup()
    def test_empty_records_are_not_equal_evidence(self):
        self.assertFalse(compare({},{})['same_recorded_inputs'])
        self.assertFalse(compare([],None)['same_known_execution'])
    def test_unknown_models_never_establish_known_execution(self):
        report=compare(self.record,self.record)
        self.assertTrue(report['same_recorded_inputs']);self.assertTrue(report['complete_input_evidence'])
        self.assertFalse(report['same_known_execution'])
    def test_client_differences_are_exposed(self):
        altered=copy.deepcopy(self.record);altered['client'].update(surface='vscode',image_model='reported-model')
        self.assertIn('surface',compare(self.record,altered)['execution_differences'])
    def test_host_context_opt_in_stays_runtime_only(self):
        self.assertNotIn('execution',self.record)
        record=manifest(self.root,self.lock,'test','handoff',self.guide,record_host=True)
        self.assertEqual(record['execution']['loaded_skill_root'],str(self.root.resolve()))
    def test_other_guide_cannot_create_manifest(self):
        other=self.root/'other.png';Image.new('RGB',(10,10)).save(other)
        with self.assertRaisesRegex(ValueError,'guide differs'):manifest(self.root,self.lock,'test','handoff',other)
    def test_guide_hash_mismatch_cannot_finalize(self):
        self.record['guide_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'guide differs'):finalize(self.record,self.lock,self.guide,self.review)
    def test_modified_lock_cannot_finalize(self):
        self.lock['scene']['delivery_counts']['slab']=2
        with self.assertRaisesRegex(ValueError,'lock itself was modified'):finalize(self.record,self.lock,self.guide,self.review)
    def test_bad_lock_is_diagnostic(self):
        with self.assertRaisesRegex(ValueError,'finish lock'):finalize(self.record,[],self.guide,self.review)
    def test_source_hash_tampering_invalidates_comparison(self):
        self.record['skill']['files']['SKILL.md']='0'*64
        self.assertFalse(compare(self.record,self.record)['same_recorded_inputs'])
    def test_native_and_uncertainty_preserved(self):
        result=finalize(self.record,self.lock,self.guide,self.review,native_image=self.guide)
        self.assertEqual(errors(result),[]);self.assertEqual(result['outcome']['review_status'],'limited')
        self.assertEqual(result['outcome']['resolution_status'],'native_pixels_preserved')
    def test_no_native_file_means_unverified_native_resolution(self):
        result=finalize(self.record,self.lock,self.guide,self.review)
        self.assertEqual(result['outcome']['resolution_status'],'native_resolution_unverified')
        self.assertEqual(result['outcome']['generation']['model'],'unreported')
    def test_upscaled_export_is_not_native(self):
        resized=self.root/'resized.png'
        with Image.open(self.guide) as im:im.resize((640,480)).save(resized)
        review=create_review(self.lock,resized,self.review['observations'],'test resized')
        result=finalize(self.record,self.lock,resized,review,native_image=self.guide)
        self.assertEqual(result['outcome']['image']['size'],[640,480])
        self.assertEqual(result['outcome']['resolution_status'],'transformed_after_generation')
    def test_changed_pixels_require_new_review(self):
        changed=self.root/'changed.png';Image.new('RGB',(320,240)).save(changed)
        with self.assertRaisesRegex(ValueError,'another PNG'):finalize(self.record,self.lock,changed,self.review)
    def test_forged_outcome_does_not_pass_with_recomputed_digest(self):
        r=copy.deepcopy(self.record);r['outcome']={'image':{'pixel_sha256':'0'*64},'review_status':'passed','resolution_status':'native_pixels_preserved','generated_image':None}
        r['outcome_sha256']=digest(r['outcome'])
        self.assertTrue(errors(r))
    def test_outcome_nan_and_bad_dimensions_are_diagnostic(self):
        r=finalize(self.record,self.lock,self.guide,self.review,native_image=self.guide)
        r['outcome']['image']['size']=[True,float('nan')]
        self.assertTrue(errors(r))
    def test_cannot_silently_infer_generation_facts(self):
        with self.assertRaisesRegex(ValueError,'unsupported generation fact'):
            finalize(self.record,self.lock,self.guide,self.review,generation={'imagined_engine':'model'})
if __name__=='__main__':unittest.main()

