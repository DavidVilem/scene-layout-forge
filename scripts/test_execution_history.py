"""History/tamper tests use synthetic locks; physical revalidation is separately tested.
Only freeze is isolated here; production preserve calls the real geometry gate.
"""
import copy,tempfile,unittest,json
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from finish_contract import digest
from history_run import new_run
from annotation_policy import configure
from execution_history import preserve,errors,retain_attempt,current_errors
from run_manifest import sha
from accept_delivery import accept

class ExecutionHistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.brief='Draw a vehicle in terrain.';self.run=new_run(self.root,'vehicle',self.brief)
        self.guide=self.root/'guide.png';Image.new('RGB',(24,16),'white').save(self.guide)
        self.source=self.root/'scene_builder.py';self.source.write_text('# synthetic history fixture')
        s=configure({'schema_version':2,'workflow_version':3,'validation_policy':'strict','registered_geometry':True,'parts':[]})
        v={'version':2,'guide_sha256':sha(self.guide),'scene_sha256':digest(s)}
        self.lock={'version':3,'scene':s,'scene_sha256':digest(s),'view':v,'view_sha256':digest(v)}
    def tearDown(self):self.tmp.cleanup()
    def prepare(self):
        with patch('execution_history.freeze') as physical, patch('finish_contract.compile_handoff',return_value={'scope':'synthetic history test'}):
            folder=preserve(self.lock,self.run,self.guide,self.brief,'Draw no annotations.',sources=[self.source])
            physical.assert_called_once()
        return folder
    def test_default_history_contains_original_brief(self):
        self.assertEqual((self.run/'01-site/brief.txt').read_text(),self.brief)
    def test_preparation_copies_sources_and_guide(self):
        f=self.prepare();self.assertFalse(errors(self.lock,self.run))
        self.assertEqual((f/'guide.png').read_bytes(),self.guide.read_bytes());self.assertTrue(list((f/'sources').iterdir()))
    def test_missing_history_blocks_direct_image_delivery(self):
        with self.assertRaisesRegex(ValueError,'prepared history'):accept(self.lock,self.guide,{},self.run,self.root/'final.png')
        self.assertFalse((self.root/'final.png').exists())
    def test_no_lock_is_diagnostic(self):self.assertTrue(errors(None,self.run))
    def test_vehicle_cannot_downgrade_to_legacy(self):
        self.lock['scene']['workflow_version']=2;self.assertTrue(current_errors(self.lock))
    def test_building_cannot_use_vehicle_shortcut(self):
        self.lock['scene']['design_intent']={'domain':'building'};self.assertTrue(current_errors(self.lock))
    def test_missing_annotation_policy_rejected(self):
        self.lock['scene'].pop('annotation_policy');self.assertTrue(current_errors(self.lock))
    def test_changed_prompt_is_rejected(self):
        f=self.prepare();(f/'finishing-prompt.txt').write_text('changed');self.assertTrue(errors(self.lock,self.run))
    def test_removed_guide_is_rejected(self):
        f=self.prepare();(f/'guide.png').unlink();self.assertTrue(errors(self.lock,self.run))
    def test_changed_original_brief_rejected(self):
        self.prepare();(self.run/'01-site/brief.txt').write_text('different');self.assertTrue(errors(self.lock,self.run))
    def test_originals_and_repeated_attempts_are_preserved(self):
        a=self.prepare();b=self.prepare();self.assertNotEqual(a,b);self.assertTrue(a.exists())
        x=retain_attempt(self.run,self.guide,{'prompt':'first'});y=retain_attempt(self.run,self.guide,{'prompt':'second'})
        self.assertNotEqual(x,y);self.assertEqual(x.read_bytes(),self.guide.read_bytes())
    def test_failed_physical_gate_cannot_prepare(self):
        with patch('execution_history.freeze',side_effect=ValueError('unsupported contact')):
            with self.assertRaisesRegex(ValueError,'unsupported contact'):preserve(self.lock,self.run,self.guide,self.brief,'draw',sources=[self.source])
        self.assertFalse(list((self.run/'08-finish').glob('attempt-*')))

if __name__=='__main__':unittest.main()
