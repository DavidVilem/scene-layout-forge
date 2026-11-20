"""Continuous declared walking centerlines supported by actual mesh triangles.
No accessibility code or load certification. Clearance uses protected_spaces separately.
"""
import numpy as np
from registered_geometry import arrays

def interval(p,q,tri):
    a,b,c=tri;u=b-a;v=c-a;n=np.cross(u,v);length=np.linalg.norm(n)
    if length<1e-10 or abs(n[2])/length<.35:return None
    if max(abs(np.dot(p-a,n)),abs(np.dot(q-a,n)))/length>1e-5:return None
    uv=np.column_stack((u,v));x=np.linalg.lstsq(uv,p-a,rcond=None)[0];y=np.linalg.lstsq(uv,q-a,rcond=None)[0]
    start=np.array([x[0],x[1],1-x.sum()]);end=np.array([y[0],y[1],1-y.sum()]);lo,hi=0.,1.
    for value,delta in zip(start,end-start):
        if abs(delta)<1e-12:
            if value < -1e-7:return None
        elif delta>0:lo=max(lo,(-1e-7-value)/delta)
        else:hi=min(hi,(-1e-7-value)/delta)
    return (lo,hi) if lo<=hi else None

def inspect(network,scene):
    if network is None:return {'status':'not_run','scope':'No walking network supplied'}
    nodes=network.get('nodes',[]);by={n['id']:np.asarray(n['point'],float) for n in nodes}
    if not nodes or len(by)!=len(nodes) or any(p.shape!=(3,) or not np.isfinite(p).all() for p in by.values()):raise ValueError('Unique finite access nodes required')
    entry=network.get('entry');targets=network.get('targets',[])
    if entry not in by or not targets or set(targets)-set(by):raise ValueError('Access entry and known destinations required')
    parts={p['id']:p for p in scene['parts']};graph={k:set() for k in by};checked=[]
    for link in network.get('links',[]):
        a,b=link['from'],link['to'];support=link.get('supports',[])
        if a not in by or b not in by or a==b or not support or set(support)-set(parts):raise ValueError('Access link needs endpoints and known floor supports')
        points=np.asarray(link.get('points',[by[a].tolist(),by[b].tolist()]),float)
        if points.ndim!=2 or points.shape[1]!=3 or len(points)<2 or not np.isfinite(points).all():raise ValueError('Finite route polyline required')
        if not np.allclose(points[0],by[a],atol=1e-6) or not np.allclose(points[-1],by[b],atol=1e-6):raise ValueError('Route endpoint mismatch')
        triangles=[]
        for name in support:
            p=parts[name];v,f=arrays(p['parameters']);v=v+np.asarray(p['origin']);triangles.extend(v[f])
        for p,q in zip(points,points[1:]):
            if np.linalg.norm(q-p)<1e-8:raise ValueError('Zero-length route segment')
            intervals=sorted(i for tri in triangles if (i:=interval(p,q,tri)) is not None)
            covered=0.
            for lo,hi in intervals:
                if lo>covered+1e-6:break
                covered=max(covered,hi)
            if covered<1-1e-6:raise ValueError('Unsupported walking segment: '+a+' -> '+b)
        graph[a].add(b);graph[b].add(a);checked.append([a,b])
    reached={entry};pending=[entry]
    while pending:
        for n in graph[pending.pop()]-reached:reached.add(n);pending.append(n)
    if set(targets)-reached:raise ValueError('Unreachable destinations: '+', '.join(sorted(set(targets)-reached)))
    return {'status':'passed','links':checked,'destinations':targets,'scope':'Declared centerlines continuously supported by mesh triangles; no width, obstacle, accessibility or load claim. Use protected spaces and visual review for clearance.'}
