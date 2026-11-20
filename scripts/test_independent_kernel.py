import unittest,tempfile,json,struct
from pathlib import Path
import numpy as np
from PIL import Image
from kernel3d.camera import fit,project
from kernel3d.workflow import start,snapshot,verify,bind_request,check_binding,reconstruct
from test_reconstruction_kernel import fixture
class IndependentKernelTests(unittest.TestCase):
 def test_bound_design_survives_complete_synthetic_image_pair(self):
  import illustration_workflow as w,color_workflow as c
  from test_illustration_workflow import plan
  from reconstruction_kernel import build
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);run,snap=self.scenario(root,'design_first')
   a=w.prepare(root,'scene','Draw a scene.',plan(),guide=snap/'geometry-guide.png');bind_request(snap,a)
   src=root/'generated.png';Image.new('RGB',(24,16),'gray').save(src)
   im=w.retain(a,src,w.read(a/'request.json'))
   rv=w.review(a,im,{k:{'status':'visible_correct','notes':'Synthetic integration fixture only'} for k in (*w.BASE_REVIEW,'wall_mount')})
   target=root/'output/scene-01/ilustrada.png';w.accept(a,im,rv,target)
   job=c.prepare(a,target);Image.new('RGB',(24,16),'steelblue').save(src);c.retain(job,src,w.read(job/'request.json'))
   rv=c.review(job,{k:{'status':'preserved','notes':'Synthetic fixture, not fidelity approval'} for k in c.KEYS});d=c.accept(job,rv)
   _,_,candidate=build(root,fixture(),d['coloreada'],'Draw a scene.',pair=target.parent,illustration_attempt=a,spatial_snapshot=snap)
   self.assertTrue(candidate.exists())
 def test_camera_fit_held_out(self):
  points=np.array([[x,y,z] for x in (0,1) for y in (0,1) for z in (0,1)],float)
  truth={'eye':[5,-7,4],'target':[.5,.5,.5],'fov':43}
  uv=project(points,truth,1.5)
  result=fit(points,uv,{'eye':[6,-8,5],'target':[.4,.6,.4],'fov':48},1.5)
  self.assertLess(result['rms_after'],1e-5)
  held=[[.2,.3,.7],[.8,.4,.1]]
  self.assertLess(np.max(abs(project(held,truth,1.5)-project(held,result['camera'],1.5))),1e-4)
 def test_planar_camera_not_falsely_solved(self):
  with self.assertRaisesRegex(ValueError,'Depth'):fit([[x,y,0] for x in (0,1,2) for y in (0,1)],[[.2,.3]]*6,{'eye':[5,-7,4],'target':[0,0,0],'fov':40},1.5)
 def test_degenerate_camera(self):
  with self.assertRaises(ValueError):project([[1,2,3]],{'eye':[0,0,0],'target':[0,0,1],'fov':40},1)
 def scenario(self,root,mode):
  source=root/'input.png';Image.new('RGB',(120,80),'white').save(source)
  run=start(root,mode,'Test reconstruction',source if mode=='single_image' else None)
  cam={'projection':'perspective','eye':[5,-6,4],'target':[.5,.5,1],'fov':40,'rationale':'Test source camera'}
  snap=snapshot(run,fixture(),cam,{'visible':['two blocks'],'inferred':['back faces']})
  return run,snap
 def test_single_image_builds_actual_html_and_glb(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);run,snap=self.scenario(root,'single_image');a,b,c=reconstruct(run,snap)
   self.assertTrue(c.exists());data=(snap/'model.glb').read_bytes();magic,version,total=struct.unpack('<III',data[:12]);self.assertEqual((magic,version,total),(0x46546c67,2,len(data)))
   n,tag=struct.unpack('<II',data[12:20]);doc=json.loads(data[20:20+n]);self.assertEqual(len(doc['meshes']),2)
   self.assertTrue(all('POSITION' in m['primitives'][0]['attributes'] for m in doc['meshes']))
 def test_design_binding_rejects_different_model_or_guide(self):
  import shutil
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);run,snap=self.scenario(root,'design_first');attempt=root/'attempt';attempt.mkdir();shutil.copyfile(snap/'geometry-guide.png',attempt/'guide.png')
   bind_request(snap,attempt);check_binding(snap,attempt,fixture())
   s=fixture();s['components'][0]['shapes'][0]['size'][0]=2
   with self.assertRaisesRegex(ValueError,'same frozen design'):check_binding(snap,attempt,s)
   (attempt/'guide.png').write_bytes(b'changed')
   with self.assertRaises(ValueError):check_binding(snap,attempt,fixture())
 def test_cannot_bind_retroactively(self):
  import shutil
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);run,snap=self.scenario(root,'design_first');a=root/'attempt';a.mkdir();shutil.copyfile(snap/'geometry-guide.png',a/'guide.png');(a/'result-1').mkdir()
   with self.assertRaisesRegex(ValueError,'before image'):bind_request(snap,a)
 def test_changed_snapshot_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   _,snap=self.scenario(Path(t),'design_first');(snap/'camera.json').write_text('{}')
   with self.assertRaises(ValueError):verify(snap)
