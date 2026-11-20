"""Domain-independent registered meshes for the optional image reconstruction kernel.

No pixel detector or hidden-surface estimator: the agent authors a visual specification.
"""
import math,re
import numpy as np
from render_scene import Mesh
from registered_geometry import arrays


def vector(v):
    a=np.asarray(v,dtype=float)
    if a.shape!=(3,) or not np.isfinite(a).all():raise ValueError('Finite XYZ required')
    return a


def indexed(vertices,faces):
    v,f=arrays({'vertices':vertices,'faces':faces})
    m=Mesh()
    for face in f:m.faces.append(([v[i] for i in face],0))
    return m


def grid_surface(points):
    a=np.asarray(points,float)
    if a.ndim!=3 or a.shape[2]!=3 or min(a.shape[:2])<2 or not np.isfinite(a).all():raise ValueError('Surface needs finite rectangular rows of XYZ')
    rows,cols=a.shape[:2];faces=[]
    for j in range(rows-1):
        for i in range(cols-1):
            k=j*cols+i;faces.extend([[k,k+1,k+cols+1],[k,k+cols+1,k+cols]])
    return indexed(a.reshape(-1,3).tolist(),faces)


def profile_surface(profile,start=0,end=360,segments=40):
    if not 3<=segments<=256 or not 0<end-start<=360:raise ValueError('Invalid revolution sweep')
    p=np.asarray(profile,float)
    if p.ndim!=2 or p.shape[1]!=2 or len(p)<2 or not np.isfinite(p).all() or np.any(p[:,0]<=0):raise ValueError('Profile is positive radius / height pairs; use a small explicit apex or mesh')
    angles=np.linspace(math.radians(start),math.radians(end),segments+1)
    return grid_surface([[[r*math.cos(a),r*math.sin(a),z] for a in angles] for r,z in p])


def loft(rings,caps=True):
    """Join corresponding convex planar rings; authors control silhouette and twist."""
    a=np.asarray(rings,float)
    if a.ndim!=3 or a.shape[2]!=3 or a.shape[0]<2 or a.shape[1]<3 or not np.isfinite(a).all():
        raise ValueError('Loft needs finite equal-length rings of XYZ')
    rows,n,_=a.shape
    if rows*n>65536:raise ValueError('Loft vertex budget exceeded')
    faces=[];vertices=a.reshape(-1,3).tolist()
    for ring in a:
        normal=np.cross(ring[1]-ring[0],ring[2]-ring[0]);length=np.linalg.norm(normal)
        if length<1e-9:raise ValueError('Degenerate loft ring')
        normal/=length
        if max(abs((ring-ring[0])@normal))>1e-5:raise ValueError('Loft rings must be planar')
        if any(np.dot(np.cross(ring[(j+1)%n]-ring[j],ring[(j+2)%n]-ring[(j+1)%n]),normal)<-1e-8 for j in range(n)):
            raise ValueError('Loft rings must be convex and ordered consistently')
    for r in range(rows-1):
        for j in range(n):
            x=r*n+j;y=r*n+(j+1)%n
            faces.extend([[x,y,y+n],[x,y+n,x+n]])
    if caps:
        for r in (0,rows-1):
            center=len(vertices);vertices.append(a[r].mean(axis=0).tolist())
            for j in range(n):
                face=[center,r*n+j,r*n+(j+1)%n]
                faces.append(face[::-1] if r==0 else face)
    return indexed(vertices,faces)


def mesh_for(shape):
    kind=shape['type'];m=Mesh()
    if kind=='box':
        size=vector(shape['size'])
        if min(size)<=0:raise ValueError('Positive box size required')
        m.box([0,0,0],size)
    elif kind=='ellipsoid':m.ellipsoid([0,0,0],shape['radii'],int(shape.get('segments',24)),int(shape.get('rows',12)))
    elif kind=='sweep':m.sweep(shape['points'],float(shape['radius']),int(shape.get('segments',16)),caps=shape.get('caps',True))
    elif kind=='revolve':m=profile_surface(shape['profile'],shape.get('start',0),shape.get('end',360),shape.get('segments',40))
    elif kind=='surface':m=grid_surface(shape['points'])
    elif kind=='loft':m=loft(shape['rings'],shape.get('caps',True))
    elif kind=='mesh':
        if any(len(f)!=3 for f in shape['faces']):raise ValueError('Custom meshes require explicit triangles, not ambiguous polygon fans')
        m=indexed(shape['vertices'],shape['faces'])
    else:raise ValueError('Unsupported form; author an indexed mesh instead: '+str(kind))
    angles=np.radians(vector(shape.get('rotation',[0,0,0])));x,y,z=angles
    rx=np.array([[1,0,0],[0,math.cos(x),-math.sin(x)],[0,math.sin(x),math.cos(x)]])
    ry=np.array([[math.cos(y),0,math.sin(y)],[0,1,0],[-math.sin(y),0,math.cos(y)]])
    rz=np.array([[math.cos(z),-math.sin(z),0],[math.sin(z),math.cos(z),0],[0,0,1]])
    scale=vector(shape.get('scale',[1,1,1]));offset=vector(shape.get('at',[0,0,0]))
    if min(scale)<=0:raise ValueError('Positive scale required')
    matrix=rz@ry@rx
    return [[(matrix@(np.asarray(v)*scale)+offset).tolist() for v in face] for face,_ in m.faces]


def component(part):
    """Compile arbitrary composed forms into the existing registered geometry contract."""
    faces=[]
    for shape in part['shapes']:faces.extend(mesh_for(shape))
    if not faces:raise ValueError('Empty component')
    vertices=[];indices=[]
    for face in faces:
        # Store explicit triangles; no concave polygon fan assumption in custom meshes.
        for i in range(1,len(face)-1):
            idx=len(vertices);vertices.extend([face[0],face[i],face[i+1]]);indices.append([idx,idx+1,idx+2])
    a=np.asarray(vertices,float);lo=a.min(axis=0);size=np.maximum(a.max(axis=0)-lo,1e-5)
    local=a-lo
    params={'adapter':'reconstruction-composed-mesh','vertices':local.tolist(),'faces':indices,
            'limitations':'Image-derived conceptual geometry; hidden shape and dimensions are inferred, not engineering measurements.'}
    arrays(params)
    color=part.get('color','#a8b5b4')
    if not isinstance(color,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',color):raise ValueError('Component color must be #RRGGBB')
    opacity=part.get('opacity',1)
    if type(opacity) not in (int,float) or not math.isfinite(opacity) or not 0<opacity<=1:raise ValueError('Opacity must be positive and at most one')
    return dict(id=part['id'],kind='custom',origin=lo.tolist(),size=size.tolist(),parameters=params,appearance={'color':color,'opacity':opacity},
                ports={name:(vector(value)-lo).tolist() for name,value in part.get('anchors',{}).items()})
