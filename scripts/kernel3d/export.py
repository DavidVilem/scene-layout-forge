"""GLB 2.0 export of compiled geometry, materials, names and provenance scope."""
import json,struct
import numpy as np
from registered_geometry import arrays

def export_glb(scene,path):
 doc={'asset':{'version':'2.0','generator':'scene-layout-forge independent 3D kernel'},'scene':0,'scenes':[{'nodes':[]}],'nodes':[],'meshes':[],'materials':[],'bufferViews':[],'accessors':[]}
 blob=bytearray()
 def accessor(a,typ):
  a=np.asarray(a,dtype='<f4');start=len(blob);blob.extend(a.tobytes());blob.extend(b'\0'*((-len(blob))%4));vi=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':a.nbytes,'target':34962});ai=len(doc['accessors']);doc['accessors'].append({'bufferView':vi,'componentType':5126,'count':len(a),'type':typ,'min':a.min(axis=0).tolist(),'max':a.max(axis=0).tolist()});return ai
 for p in scene['parts']:
  v,f=arrays(p['parameters']);v+=np.asarray(p['origin']);tri=v[f].reshape(-1,3,3)
  # Z-up model -> glTF Y-up, preserving handedness.
  tri=tri[:,:,[0,2,1]];tri[:,:,2]*=-1
  normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
  pos=accessor(tri.reshape(-1,3),'VEC3');norm=accessor(np.repeat(normals,3,axis=0),'VEC3')
  app=p.get('appearance',{});color=app.get('color','#a8b5b4');rgb=[int(color[i:i+2],16)/255 for i in (1,3,5)];alpha=app.get('opacity',1)
  material={'name':p['id'],'pbrMetallicRoughness':{'baseColorFactor':rgb+[alpha],'metallicFactor':0,'roughnessFactor':.85},'doubleSided':True}
  if alpha<1:material['alphaMode']='BLEND'
  mid=len(doc['materials']);doc['materials'].append(material);mesh=len(doc['meshes']);doc['meshes'].append({'name':p['id'],'primitives':[{'attributes':{'POSITION':pos,'NORMAL':norm},'material':mid}]});node=len(doc['nodes']);doc['nodes'].append({'name':p['id'],'mesh':mesh});doc['scenes'][0]['nodes'].append(node)
 doc['buffers']=[{'byteLength':len(blob)}];j=json.dumps(doc,separators=(',',':')).encode();j+=b' '*((-len(j))%4)
 data=struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(blob))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(blob),0x004e4942)+blob
 with open(path,'xb') as out:out.write(data)
 return {'bytes':len(data),'meshes':len(doc['meshes']),'scope':'Real compiled surfaces; conceptual inference, not recovered measured geometry'}
