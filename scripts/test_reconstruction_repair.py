import copy,tempfile,unittest,json
from pathlib import Path
from PIL import Image
from test_reconstruction_kernel import fixture
from reconstruction_kernel import build
from reconstruction_repair import revise

class RepairTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name)
  image=self.root/'source.png';Image.new('RGB',(16,16),'blue').save(image)
  self.spec=fixture();self.run,_,_=build(self.root,self.spec,image,'Reconstruct source',operation='reconstruct',reuse_reason='Reconstruct source')
  self.issue=dict(id='upper_shape',components=['upper'],observed='Wrong top height',target='Taller top above same contact',action='Extend upper mesh',verification='Front and contact close view')
 def tearDown(self):self.t.cleanup()
 def revised(self):
  s=copy.deepcopy(self.spec);s['components'][1]['shapes'][0]['size'][2]=1.5;return s
 def test_geometry_repair_builds_preserves_source_and_requires_review(self):
  audit,run,job,html=revise(self.root,self.run,self.revised(),[self.issue],'Repair current model')
  self.assertTrue(html.exists());self.assertTrue((job/'pending-repairs.json').exists())
  self.assertEqual((run/'source.png').read_bytes(),(self.run/'source.png').read_bytes())
  self.assertEqual(json.loads((audit/'geometry-diff.json').read_text())['changed_components'],['upper'])
  self.assertFalse((self.root/'explorador.html').exists())
 def test_unreviewed_repair_cannot_be_accepted(self):
  from reconstruction_repair import validate_review
  _,_,job,_=revise(self.root,self.run,self.revised(),[self.issue],'Repair')
  with self.assertRaisesRegex(ValueError,'current candidate'):validate_review(job,None)
 def test_notes_only_cannot_resolve_geometry(self):
  s=copy.deepcopy(self.spec);s['components'][1]['evidence']='Now fixed'
  with self.assertRaisesRegex(ValueError,'No geometry change'):revise(self.root,self.run,s,[self.issue],'Repair')
 def test_unrelated_change_cannot_resolve_issue(self):
  i=dict(self.issue,components=['base'])
  with self.assertRaisesRegex(ValueError,'No geometry change'):revise(self.root,self.run,self.revised(),[i],'Repair')
 def test_broken_contact_remains_rejected(self):
  s=self.revised();s['components'][1]['shapes'][0]['at'][2]=1.2
  with self.assertRaises(ValueError):revise(self.root,self.run,s,[self.issue],'Repair')
  self.assertTrue(list((self.root/'output/history').glob('geometry-repair-*/failure.json')))
 def test_cannot_remove_contact_to_pass(self):
  s=self.revised();s['contacts']=[]
  with self.assertRaisesRegex(ValueError,'drop existing contacts'):revise(self.root,self.run,s,[self.issue],'Repair')
 def test_changed_source_rejected(self):
  Image.new('RGB',(16,16),'red').save(self.run/'source.png')
  with self.assertRaisesRegex(ValueError,'source changed'):revise(self.root,self.run,self.revised(),[self.issue],'Repair')
 def test_opacity_change_counts_but_color_only_does_not(self):
  from reconstruction_repair import changes
  a={'parts':[{'id':'glass','appearance':{'opacity':1,'color':'white'}}]}
  b=copy.deepcopy(a);b['parts'][0]['appearance']['color']='blue'
  self.assertEqual(changes(a,b),[])
  b['parts'][0]['appearance']['opacity']=.25
  self.assertEqual(changes(a,b),['glass'])
if __name__=='__main__':unittest.main()
