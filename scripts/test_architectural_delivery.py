"""I/O identity tests use synthetic pixels, not evidence of visual design quality."""
import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from test_architecture_stages import fixture
from architecture_stages import digest,record_stage,save_record
from pixel_review import requirements,create_review
from accept_delivery import accept

class DeliveryTests(unittest.TestCase):
    def setUp(self):
        # These tiny synthetic fixtures isolate stage-8/I-O checks. The real
        # history preflight is exercised without mocks in test_execution_history.
        self.history_patch=patch('execution_history.errors',return_value=[])
        self.history_patch.start();self.addCleanup(self.history_patch.stop)
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        (self.root/'08-finish').mkdir();self.image=self.root/'08-finish'/'generated.png'
        Image.new('RGB',(32,32),'white').save(self.image)
        s,v=fixture();s['validation_policy']='strict';records=[]
        with patch('scene_model.validate',return_value=[]):
            for n in range(1,8):records.append(record_stage(s,n,records,v,note='synthetic gate fixture'))
        self.lock={'scene':s,'scene_sha256':digest(s),'view':v,'view_sha256':digest(v),'architecture_stages':records,'architecture_stages_sha256':digest(records)}
        self.obs=[dict(target=k,state='visible_correct',note='synthetic review identity fixture',region=[.1,.1,.9,.9]) for k in requirements(self.lock)]
    def tearDown(self):self.tmp.cleanup()
    def review(self):return create_review(self.lock,self.image,self.obs,'synthetic test reviewer')
    def test_keeps_source_and_stages_and_copies_exact_pixels(self):
        out=self.root/'delivery'/'final.png';accept(self.lock,self.image,self.review(),self.root,out)
        self.assertEqual(out.read_bytes(),self.image.read_bytes());self.assertTrue(list((self.root/'08-finish').glob('approval-*.json')))
    def test_missing_or_uncertain_entrance_blocks(self):
        next(o for o in self.obs if o['target']=='architecture:entrance')['state']='uncertain'
        with self.assertRaises(ValueError):accept(self.lock,self.image,self.review(),self.root,self.root/'final.png')
    def test_changed_png_rejects_stale_review(self):
        review=self.review();Image.new('RGB',(32,32),'black').save(self.image)
        with self.assertRaises(ValueError):accept(self.lock,self.image,review,self.root,self.root/'final.png')
    def test_no_overwrite(self):
        out=self.root/'final.png';out.write_bytes(b'keep')
        with self.assertRaises(FileExistsError):accept(self.lock,self.image,self.review(),self.root,out)
        self.assertEqual(out.read_bytes(),b'keep')
    def test_same_stage_preserves_previous_approval(self):
        record=self.lock['architecture_stages'][0]
        a=save_record(self.root,record);b=save_record(self.root,record)
        self.assertNotEqual(a,b);self.assertEqual(a.read_bytes(),b.read_bytes())

if __name__=='__main__':unittest.main()
