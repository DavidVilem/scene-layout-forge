"""Immutable two-mode reconstruction sessions. Each snapshot keeps an actual scene and camera."""
import json,hashlib,tempfile,shutil
from pathlib import Path
from PIL import Image

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,v):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def start(project,mode,brief,source=None):
 if mode not in ('design_first','single_image'):raise ValueError('Choose design_first or single_image')
 if (mode=='single_image')!=(source is not None):raise ValueError('Only single_image starts from an existing image')
 history=Path(project)/'output/history';history.mkdir(parents=True,exist_ok=True)
 run=Path(tempfile.mkdtemp(prefix='kernel3d-',dir=history));record={'mode':mode,'brief':brief}
 if source:
  with Image.open(source) as im:im.load();record['source_size']=list(im.size)
  target=run/('source'+Path(source).suffix);shutil.copyfile(source,target);record['source']=target.name;record['source_sha256']=sha(target)
 save(run/'session.json',record);return run

def snapshot(run,spec,camera,evidence,previous=None):
 from reconstruction_kernel import compile_spec
 from .guide import render
 from .export import export_glb
 run=Path(run);session=read(run/'session.json')
 if session.get('source') and sha(run/session['source'])!=session['source_sha256']:raise ValueError('Source changed')
 if camera.get('projection')!='perspective' or not camera.get('rationale'):raise ValueError('Explicit perspective camera and rationale required')
 if not evidence or not isinstance(evidence,dict) or not evidence.get('visible') or not evidence.get('inferred'):raise ValueError('Record visible targets and inferred hidden regions')
 scene,config,checks=compile_spec(spec)
 folder=Path(tempfile.mkdtemp(prefix='snapshot-',dir=run))
 save(folder/'specification.json',spec);save(folder/'scene.json',scene);save(folder/'config.json',config);save(folder/'checks.json',checks);save(folder/'camera.json',camera);save(folder/'evidence.json',evidence)
 aspect=camera.get('aspect',1.5)
 if not .25<=aspect<=4:raise ValueError('Guide aspect must be between .25 and 4')
 render(scene,camera).save(folder/'geometry-guide.png');export_glb(scene,folder/'model.glb')
 save(folder/'receipt.json',{'specification':canonical(spec),'previous':str(previous) if previous else None,'files':{p.name:sha(p) for p in folder.iterdir() if p.is_file()}})
 return folder

def verify(folder):
 folder=Path(folder);r=read(folder/'receipt.json')
 for n,h in r['files'].items():
  if sha(folder/n)!=h:raise ValueError('Frozen 3D snapshot changed: '+n)
 return r

def bind_request(folder,attempt):
 folder=Path(folder).resolve();attempt=Path(attempt).resolve();verify(folder)
 if read(folder.parent/'session.json')['mode']!='design_first':raise ValueError('Only design_first binds an illustration request')
 if not (attempt/'guide.png').is_file() or sha(attempt/'guide.png')!=sha(folder/'geometry-guide.png'):raise ValueError('Illustration must use the actual frozen geometry guide')
 if list(attempt.glob('result-*')):raise ValueError('Bind geometry before image generation, not afterward')
 save(attempt/'spatial-design.json',{'snapshot':str(folder),'receipt_sha256':sha(folder/'receipt.json')})
 return folder

def check_binding(folder,attempt,spec):
 folder=Path(folder).resolve();verify(folder);record=read(Path(attempt)/'spatial-design.json')
 if record['snapshot']!=str(folder) or record['receipt_sha256']!=sha(folder/'receipt.json'):raise ValueError('Different frozen design')
 if canonical(spec)!=read(folder/'receipt.json')['specification']:raise ValueError('Image and explorer must derive from the same frozen design; reconcile differences explicitly')
 if sha(Path(attempt)/'guide.png')!=sha(folder/'geometry-guide.png'):raise ValueError('Different illustration guide')
 return record

def reconstruct(run,folder):
 from reconstruction_kernel import build
 run=Path(run);folder=Path(folder);verify(folder);s=read(run/'session.json')
 if s['mode']!='single_image':raise ValueError('Use bound image creation for design_first')
 if sha(run/s['source'])!=s['source_sha256']:raise ValueError('Source changed')
 return build(run.parents[2],read(folder/'specification.json'),run/s['source'],s['brief'],parent_history=folder,operation='reconstruct',reuse_reason=s['brief'])

def calibrate(run,world,image,initial,aspect=None):
 from .camera import fit
 run=Path(run);session=read(run/'session.json')
 if aspect is None:
  size=session.get('source_size')
  if not size:raise ValueError('Provide aspect for a design without an existing image')
  aspect=size[0]/size[1]
 result=fit(world,image,initial,aspect)
 folder=Path(tempfile.mkdtemp(prefix='calibration-',dir=run))
 save(folder/'fit.json',{'world':world,'image':image,'initial':initial,'aspect':aspect,'result':result})
 return folder,result


def deliver_glb(folder,explorer_job):
 folder=Path(folder);job=Path(explorer_job);verify(folder)
 delivered=read(job/'delivered.json')
 if sha(delivered['path'])!=delivered['sha256']:raise ValueError('Delivered HTML changed')
 if canonical(read(folder/'scene.json'))!=canonical(read(job/'scene.json')):raise ValueError('GLB and delivered explorer have different geometry')
 target=Path(delivered['path']).with_name('modelo.glb')
 with target.open('xb') as f:f.write((folder/'model.glb').read_bytes())
 save(job/'glb-delivered.json',{'path':str(target),'sha256':sha(target),'snapshot':str(folder)})
 return target
