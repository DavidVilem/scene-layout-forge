import tempfile,unittest,json
from pathlib import Path
from PIL import Image
import illustration_workflow as w
from history_run import new_run
from creation_identity import pixels,policy,check,pair_evidence
from test_illustration_workflow import plan
from reconstruction_kernel import build

class CreationIdentityTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  self.old=self.root/'output/terminal-01/ilustrada.png';self.old.parent.mkdir(parents=True)
  Image.new('RGB',(24,16),'white').save(self.old)
 def tearDown(self): self.tmp.cleanup()
 def test_reencoded_copy_rejected_and_preserved(self):
  a=w.prepare(self.root,'terminal','Draw terminal',plan())
  copy=self.root/'copy.png'
  with Image.open(self.old) as im: im.save(copy,compress_level=0)
  self.assertEqual(pixels(copy),pixels(self.old))
  with self.assertRaisesRegex(ValueError,'reused previous pixels'):w.retain(a,copy,w.read(a/'request.json'))
  self.assertEqual(len(list(a.glob('result-*/rejected.json'))),1)
  self.assertEqual(len(list(a.glob('result-*/original.png'))),1)
 def test_old_guide_rejected(self):
  with self.assertRaisesRegex(ValueError,'reused previous pixels'):w.prepare(self.root,'terminal','Draw terminal',plan(),guide=self.old)
 def test_repeated_brief_is_new_run_and_fresh_pixels_allowed(self):
  a=w.prepare(self.root,'terminal','Draw terminal',plan());b=w.prepare(self.root,'terminal','Draw terminal',plan())
  self.assertNotEqual(a.parent.parent,b.parent.parent)
  fresh=self.root/'fresh.png';Image.new('RGB',(24,16),'blue').save(fresh)
  self.assertTrue(w.retain(b,fresh,w.read(b/'request.json')).exists())
 def test_explicit_edit_allows_identified_source(self):
  run=new_run(self.root,'repair','Repair previous terminal',operation='edit',reuse_reason='Repair previous terminal')
  a=w.prepare(self.root,'repair','Repair previous terminal',plan(),run=run,guide=self.old)
  self.assertTrue((a/'guide.png').exists())
 def test_reuse_requires_reason(self):
  with self.assertRaises(ValueError):policy(self.root,'edit')
 def test_old_pair_cannot_start_new_reconstruction(self):
  with self.assertRaisesRegex(ValueError,'current illustration_attempt'):build(self.root,{},self.old,'Draw a terminal')
  self.assertTrue(list((self.root/'output/history').glob('reconstruction-*/failure.json')))
 def test_current_attempt_without_color_delivery_rejected(self):
  a=w.prepare(self.root,'terminal','Draw terminal',plan())
  with self.assertRaisesRegex(ValueError,'not the colored delivery'):pair_evidence(a,self.old,'Draw terminal')
 def test_other_brief_cannot_bind_attempt(self):
  a=w.prepare(self.root,'terminal','Draw terminal',plan())
  with self.assertRaisesRegex(ValueError,'brief must match'):pair_evidence(a,self.old,'Other request')
class PairBindingTests(unittest.TestCase):
 def test_real_coloring_delivery_binds_and_changed_source_fails(self):
  from test_color_workflow import ColorTests
  import color_workflow as c
  t=ColorTests();t.setUp()
  try:
   job=t.job();rv=t.reviewed(job);d=c.accept(job,rv)
   evidence=pair_evidence(t.attempt,d['coloreada'],'Draw a scene.')
   self.assertEqual(evidence['attempt'],str(t.attempt.resolve()))
   from test_reconstruction_kernel import fixture
   run, explorer, candidate = build(t.root,fixture(),d['coloreada'],'Draw a scene.',pair=t.illustrated.parent,illustration_attempt=t.attempt)
   self.assertTrue(candidate.is_file())
   self.assertEqual(json.loads((run/'reconstruction-route.json').read_text())['mode'], 'image_first')
   self.assertFalse((run/'spatial-design.json').exists())
   Image.new('RGB',(24,16),'red').save(d['coloreada'])
   with self.assertRaises(ValueError):pair_evidence(t.attempt,d['coloreada'],'Draw a scene.')
  finally:t.tearDown()
if __name__=='__main__':unittest.main()

