"""Neutral structural guide with crease edges, using the calibrated camera convention."""
import copy
import numpy as np
from PIL import Image
from registered_geometry import arrays
from render_scene import build,Renderer

def render(scene,camera):
 display=copy.deepcopy(scene)
 for part in display['parts']:
  v,faces=arrays(part['parameters']);edges={}
  for face in faces:
   normal=np.cross(v[face[1]]-v[face[0]],v[face[2]]-v[face[0]]);normal/=np.linalg.norm(normal)
   for a,b in zip(face,face[1:]+face[:1]):
    key=tuple(sorted((tuple(np.round(v[a],8)),tuple(np.round(v[b],8)))))
    edges.setdefault(key,[]).append((a,b,normal))
  part['parameters']['edges']=[[items[0][0],items[0][1]] for items in edges.values() if len(items)==1 or any(abs(float(items[0][2]@item[2]))<.98 for item in items[1:])]
 mesh=build(display);aspect=camera.get('aspect',1.5)
 r=Renderer(mesh,960,round(960/aspect),projection='perspective',camera_eye=camera['eye'],camera_target=camera['target'],fov=camera['fov'],hatching=False)
 # Legacy renderer uses mirrored horizontal camera basis. Match standard
 # right-handed camera.project and the browser instead for this independent path.
 r.basis[0]*=-1;r.target=np.asarray(camera['target'])@r.basis.T
 r.rgb[:]=250
 result=np.asarray(r.draw(mesh)).copy()
 return Image.fromarray(result)
