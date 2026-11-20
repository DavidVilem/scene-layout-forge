"""Evidence inventory and protected-space checks, not automatic image recognition.

Triangle/box SAT tests actual registered surfaces; bounds are only broad phase.
"""
import math
import numpy as np
from registered_geometry import arrays


def triangle_box(triangle,lo,hi,tol=1e-6):
    center=(lo+hi)/2;half=(hi-lo)/2-tol
    if np.any(half<=0):raise ValueError('Protected space too small')
    v=np.asarray(triangle)-center;edges=[v[1]-v[0],v[2]-v[1],v[0]-v[2]]
    basis=np.eye(3);axes=list(basis)+[np.cross(edges[0],edges[1])]
    axes += [np.cross(e,b) for e in edges for b in basis]
    for axis in axes:
        if np.linalg.norm(axis)<1e-10:continue
        p=v@axis;r=np.dot(half,np.abs(axis))
        if p.min()>r or p.max() < -r:return False
    return True


def closed_mesh(vertices,faces):
    counts={}
    for f in faces:
        for a,b in zip(f,f[1:]+f[:1]):
            key=tuple(sorted((tuple(np.round(vertices[a],7)),tuple(np.round(vertices[b],7)))))
            counts[key]=counts.get(key,0)+1
    return bool(counts) and all(n==2 for n in counts.values())


def inside(point,vertices,faces):
    direction=np.array([1.,.317,.173]);hits=[]
    for f in faces:
        a,b,c=vertices[f];e1=b-a;e2=c-a;h=np.cross(direction,e2);det=np.dot(e1,h)
        if abs(det)<1e-10:continue
        q=point-a;u=np.dot(q,h)/det
        if u<0 or u>1:continue
        r=np.cross(q,e1);v=np.dot(direction,r)/det;t=np.dot(e2,r)/det
        if v>=0 and u+v<=1 and t>1e-7:hits.append(round(float(t),7))
    return len(set(hits))%2==1


def inspect(spec,scene):
    q=spec.get('quality_contract')
    if not q:
        if spec.get('schema_version')==2:raise ValueError('Reconstruction v2 requires quality_contract')
        return {'status':'not_run','reason':'Legacy specification; no detail/access contract. Not a fidelity pass.'}
    parts={p['id']:p for p in scene['parts']};features=q.get('features',[])
    ids=[f.get('id') for f in features]
    if not features or any(not isinstance(i,str) or not i for i in ids) or len(set(ids))!=len(ids):raise ValueError('Unique visual features required')
    for f in features:
        if f.get('level') not in ('primary','secondary','fine') or not f.get('evidence'):raise ValueError('Feature level and source evidence required')
        if f.get('status') not in ('modeled','simplified','omitted'):raise ValueError('Explicit feature status required')
        if f.get('critical') and f['status']!='modeled':raise ValueError('Critical visual feature must be modeled: '+f['id'])
        if f['status']!='omitted' and (not f.get('parts') or set(f['parts'])-set(parts)):raise ValueError('Feature references missing geometry')
        if f['status']!='modeled' and not f.get('reason'):raise ValueError('Simplified/omitted feature needs reason')
    zones=q.get('detail_zones',[])
    if not zones:raise ValueError('Visible detail zones required')
    fmap={f['id']:f for f in features}
    for zone in zones:
        selected=zone.get('features',[])
        if not selected or set(selected)-set(ids):raise ValueError('Detail zone needs known features')
        if {fmap[i]['level'] for i in selected}!={'primary','secondary','fine'}:raise ValueError('Each detail zone needs primary, secondary and fine features')
    landmarks=q.get('landmarks',[])
    if not landmarks or set(landmarks)-set(ids):raise ValueError('Initial-view landmarks must name features')
    if not q.get('access_scope'):raise ValueError('Declare access scope or why not applicable')
    if q['access_scope']!='not_applicable' and not q.get('protected_spaces'):raise ValueError('Applicable access requires protected spaces')
    prepared={}
    for pid,p in parts.items():
        v,faces=arrays(p['parameters']);v+=np.asarray(p['origin']);prepared[pid]=(v,faces,v.min(axis=0),v.max(axis=0))
    openings=[]
    for volume in q.get('protected_spaces',[]):
        lo=np.asarray(volume['min'],float);hi=np.asarray(volume['max'],float)
        if lo.shape!=(3,) or hi.shape!=(3,) or not np.isfinite([lo,hi]).all() or np.any(hi-lo<=2e-6):raise ValueError('Valid protected space required')
        if not volume.get('purpose'):raise ValueError('Protected space purpose required')
        exceptions=volume.get('exceptions',{})
        if set(exceptions)-set(parts) or any(not isinstance(v,str) or not v.strip() for v in exceptions.values()):raise ValueError('Space exceptions require named components and specific reasons')
        hits=[]
        for pid,(v,faces,pmin,pmax) in prepared.items():
            if pid in exceptions or np.any(pmax<=lo) or np.any(pmin>=hi):continue
            if any(triangle_box(v[f],lo,hi) for f in faces) or (closed_mesh(v,faces) and inside((lo+hi)/2,v,faces)):hits.append(pid)
        if hits:raise ValueError('Protected space blocked: '+volume['id']+' by '+', '.join(hits))
        openings.append({'id':volume['id'],'status':'passed','scope':'Declared volume clear of modeled surfaces/closed solids','exceptions':exceptions})
    pairs=[]
    for pair in q.get('overlap_review',[]):
        a,b=pair['parts']
        if a not in parts or b not in parts or a==b:raise ValueError('Overlap review needs two distinct known parts')
        if pair.get('classification') not in ('intended_contact','nested','separate') or not pair.get('reason'):raise ValueError('Classify overlap and provide evidence')
        av,af,alo,ahi=prepared[a];bv,bf,blo,bhi=prepared[b]
        overlap=bool(np.all(np.minimum(ahi,bhi)-np.maximum(alo,blo)>1e-6))
        gap=float(np.linalg.norm(np.maximum(np.maximum(alo-bhi,blo-ahi),0)))
        if pair['classification']=='intended_contact' and gap>1e-5:
            raise ValueError('Declared contact has a geometric gap: '+a+' / '+b)
        if overlap and pair['classification']=='separate':raise ValueError('Unresolved bounds overlap: '+a+' / '+b+'; refine geometry or document actual nesting, do not silently approve')
        pairs.append(dict(pair,bounds_overlap=overlap,scope='Conservative bounds review, not exact mesh collision proof'))
    return {'status':'passed_applicable','features':features,'detail_zones':zones,'landmarks':landmarks,'protected_spaces':openings,'overlap_review':pairs,
            'limitations':['Feature evidence is agent-authored and still requires image/model comparison.','Only declared spaces and pairs are checked; no exhaustive collision, egress or assembly motion certification.']}
