"""Registered indexed geometry, sampled contact checks and render integrity.

Checks geometric evidence only; no structural stability or load analysis.
"""
import hashlib,json
import numpy as np

def arrays(params):
    vertices=np.asarray(params['vertices'],float)
    if vertices.ndim!=2 or vertices.shape[1]!=3 or len(vertices)<3 or not np.isfinite(vertices).all():
        raise ValueError('vertices require finite Nx3 coordinates')
    faces=params['faces']
    if not isinstance(faces,list) or not faces:raise ValueError('faces required')
    for face in faces:
        if not isinstance(face,list) or len(face)<3 or any(type(i)!=int or i<0 or i>=len(vertices) for i in face):raise ValueError('invalid face indices')
        if len(set(face))!=len(face):raise ValueError('repeated face vertex')
        points=vertices[face]
        for i in range(1,len(points)-1):
            if np.linalg.norm(np.cross(points[i]-points[0],points[i+1]-points[0]))<1e-9:raise ValueError('degenerate triangle')
    return vertices,faces

def errors(part):
    try:
        params=part['parameters'];v,f=arrays(params)
        if not isinstance(params.get('adapter'),str) or not params['adapter'].strip():raise ValueError('named adapter required')
        if not isinstance(params.get('limitations'),str) or not params['limitations'].strip():raise ValueError('adapter limitations required')
        size=np.asarray(part['size'])
        if np.any(v< -1e-6) or np.any(v>size+1e-6):raise ValueError('vertices outside declared component bounds')
        for edge in params.get('edges',[]):
            if not isinstance(edge,list) or len(edge)!=2 or any(type(i)!=int or i<0 or i>=len(v) for i in edge):raise ValueError('invalid edge indices')
        return []
    except (ValueError,TypeError,KeyError,IndexError) as e:return [part['id']+': '+str(e)]

def render(mesh,part):
    v,faces=arrays(part['parameters']);v=v+np.asarray(part['origin'])
    for face in faces:mesh.faces.append(([p for p in v[face]],0))
    for a,b in part['parameters'].get('edges',[]):mesh.edges.append((v[a],v[b]))

def on_triangle(point,a,b,c,tol=1e-5):
    v0=b-a;v1=c-a;v2=point-a;n=np.cross(v0,v1);length=np.linalg.norm(n)
    if length<1e-10 or abs(np.dot(v2,n)/length)>tol:return False
    d00=np.dot(v0,v0);d01=np.dot(v0,v1);d11=np.dot(v1,v1)
    d20=np.dot(v2,v0);d21=np.dot(v2,v1);den=d00*d11-d01*d01
    u=(d11*d20-d01*d21)/den;v=(d00*d21-d01*d20)/den
    return u>=-tol and v>=-tol and u+v<=1+tol

def contact_errors(data):
    parts={p['id']:p for p in data['parts']};result=[]
    for index,c in enumerate(data.get('custom_contacts',[])):
        try:
            p=parts[c['part']];s=parts[c['on']]
            if p['kind']!='custom':raise ValueError('custom contact requires custom upper component')
            points=np.asarray(c['points'],float)
            if points.ndim!=2 or points.shape[1]!=3 or len(points)<3 or not np.isfinite(points).all():raise ValueError('finite contact patch of at least three points required')
            if np.linalg.matrix_rank(points-points[0],tol=1e-7)<2:raise ValueError('contact patch must have area')
            lo=np.asarray(s['origin']);hi=lo+np.asarray(s['size'])
            if s['kind'] not in {'footing','slab','landing','beam','column'}:raise ValueError('unsupported lower contact surface')
            if np.any(abs(points[:,2]-hi[2])>1e-5) or np.any(points[:,:2]<lo[:2]-1e-5) or np.any(points[:,:2]>hi[:2]+1e-5):raise ValueError('contact patch misses support top')
            vertices,faces=arrays(p['parameters']);vertices+=np.asarray(p['origin'])
            # Vertices, edge midpoints and centroid give local contact evidence.
            samples=list(points)+list((points+np.roll(points,1,axis=0))/2)+[points.mean(axis=0)]
            for point in samples:
                if not any(on_triangle(point,vertices[f[0]],vertices[f[i]],vertices[f[i+1]]) for f in faces for i in range(1,len(f)-1)):
                    raise ValueError('contact patch misses registered surface')
        except (ValueError,TypeError,KeyError,IndexError) as e:result.append(f'custom_contact[{index}]: {e}')
    return result

def mount_errors(data):
    parts={p['id']:p for p in data['parts']};result=[]
    for i,c in enumerate(data.get('mounts',[])):
        try:
            p=parts[c['part']];s=parts[c['on']];axis={'x':0,'y':1,'z':2}[c['axis']];side=c['side']
            if side not in (-1,1):raise ValueError('mount side must be -1 or 1')
            if s['kind'] not in {'wall','cabinet','beam','column','slab','landing'}:raise ValueError('mount needs a supported planar adapter')
            lo=np.asarray(p['origin']);hi=lo+np.asarray(p['size']);slo=np.asarray(s['origin']);shi=slo+np.asarray(s['size'])
            plane=shi[axis] if side==1 else slo[axis];end=lo[axis] if side==1 else hi[axis]
            if abs(plane-end)>1e-6:raise ValueError('mount surface gap or penetration')
            if any(min(hi[j],shi[j])-max(lo[j],slo[j])<=1e-6 for j in range(3) if j!=axis):raise ValueError('mount footprints do not overlap')
        except (ValueError,TypeError,KeyError) as e:result.append(f'mount[{i}]: {e}')
    return result

def signature(mesh):
    values={'faces':[[[np.asarray(p).tolist() for p in face],tone] for face,tone in mesh.faces],
            'edges':[[np.asarray(a).tolist(),np.asarray(b).tolist()] for a,b in mesh.edges],
            'smooth_edges':[[np.asarray(x).tolist() for x in edge] for edge in mesh.smooth_edges],
            'owners':mesh.face_owners}
    return hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest()

def seal(mesh):
    if set(mesh.face_owners)!=set(range(len(mesh.faces))):raise ValueError('unregistered rendered faces')
    mesh.registry_signature=signature(mesh)

def assert_integrity(mesh):
    if hasattr(mesh,'registry_signature') and mesh.registry_signature!=signature(mesh):
        raise ValueError('geometry changed after registry validation; register components and rebuild')
