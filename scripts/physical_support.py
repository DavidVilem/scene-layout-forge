"""Surface/contact witnesses and support topology. No strength or stability solver."""
import math
import numpy as np

EPS=1e-6
PLANAR={'wall','slab','footing','column','beam','cabinet','landing','paving'}


def surface_normals(part,point):
    """Normals at a world point on supported actual surfaces; [] means no contact.

    None means the geometry adapter is unsupported, distinct from no contact.
    """
    q=np.asarray(point,float)-np.asarray(part['origin'],float);size=part['size'];kind=part['kind']
    if kind in PLANAR:
        if any(q[k]<-EPS or q[k]>size[k]+EPS for k in range(3)):return []
        out=[]
        for k in range(3):
            for sign,v in ((-1,0),(1,size[k])):
                if abs(q[k]-v)<=EPS:n=[0.,0.,0.];n[k]=sign;out.append(n)
        return out
    if kind=='custom':
        from registered_geometry import arrays,on_triangle
        verts,faces=arrays(part['parameters']);out=[]
        for face in faces:
            for i in range(1,len(face)-1):
                a,b,c=verts[[face[0],face[i],face[i+1]]]
                if on_triangle(q,a,b,c,tol=EPS):
                    n=np.cross(b-a,c-a);n=n/np.linalg.norm(n);out.append(n.tolist())
        return out
    if kind in {'vessel','manifold','pump'}:
        from typed_interfaces import surface
        w,d,h=size
        if kind=='vessel':axis=2;center=[w/2,d/2,h/12]
        elif kind=='manifold':axis=0;center=[0,d/2,h/2]
        else:axis=1;center=[w*.25,d*.25,h*.5]
        radial=q-np.asarray(center);radial[axis]=0;norm=np.linalg.norm(radial);normals=[]
        if norm>EPS:normals.append((radial/norm).tolist())
        for sign in (-1,1):n=[0,0,0];n[axis]=sign;normals.append(n)
        return [n for n in normals if surface(part,q.tolist(),n)]
    if kind=='ramp':
        x,y,z=q;w,d,h=size;rev=part.get('parameters',{}).get('reverse',False);slope=(-1 if rev else 1)*h/d;top=h+slope*y if rev else slope*y
        if min(x,y,z)<-EPS or x>w+EPS or y>d+EPS or z>top+EPS:return []
        normals=[]
        if abs(z)<EPS:normals.append([0,0,-1])
        if abs(z-top)<EPS:n=np.array([0,-slope,1]);normals.append((n/np.linalg.norm(n)).tolist())
        for k,limit in ((0,w),(1,d)):
            for sign,value in ((-1,0),(1,limit)):
                if abs(q[k]-value)<EPS:n=[0,0,0];n[k]=sign;normals.append(n)
        return normals
    if kind=='stair':
        from access_geometry import _solids
        normals=[]
        for lo,hi in _solids(part):
            box={'kind':'slab','origin':lo,'size':[b-a for a,b in zip(lo,hi)]}
            normals.extend(surface_normals(box,point))
        return normals
    return None


def contact_patch_status(scene,contact):
    parts={p['id']:p for p in scene['parts']}
    try:
        a=parts[contact['part']];b=parts[contact['on']];points=np.asarray(contact['points'],float)
        if points.ndim!=2 or points.shape[1]!=3 or len(points)<3 or not np.isfinite(points).all():return 'failed','At least three finite contact points required'
        if np.linalg.matrix_rank(points-points[0],tol=EPS)<2:return 'unsupported','Contact patch has no supported area'
        normals=contact.get('normals')
        if normals is not None and (len(normals)!=len(points) or any(abs(np.linalg.norm(n)-1)>EPS for n in normals)):return 'failed','Unit support normals required per contact point'
        samples=list(points)
        # Flat patches include interior samples so corners cannot bridge a hole.
        # A curved patch instead declares normals per surface sample explicitly.
        if np.linalg.matrix_rank(points-points[0],tol=EPS)==2:
            samples+=list((points+np.roll(points,1,axis=0))/2)+[points.mean(axis=0)]
        for index,point in enumerate(samples):
            na=surface_normals(a,point);nb=surface_normals(b,point)
            if na is None or nb is None:return 'unsupported','No exact surface adapter for contact pair'
            if not na or not nb:return 'failed','Contact patch misses an actual component surface'
            candidates=nb if normals is None or index>=len(points) else [normals[index]]
            if not any(any(math.dist(n,m)<EPS for m in nb) and any(math.dist([-v for v in n],m)<EPS for m in na) for n in candidates):return 'failed','Contact normals are not opposed on actual surfaces'
        return 'passed','Sampled contact patch and opposed surface normals verified'
    except (KeyError,ValueError,TypeError,IndexError) as exc:return 'failed','Invalid contact patch: '+str(exc)


def support_checks(scene):
    """Additional geometry evidence, with explicit legacy ground-plane semantics."""
    parts={p['id']:p for p in scene['parts']};out=[];graph={p:[] for p in parts}
    def add(status,message,ids,source):out.append(dict(check='support_contact',status=status,message=message,parts=ids,critical=True,source=source))
    for field in ('bearings','mounts','custom_contacts','surface_contacts'):
        for index,c in enumerate(scene.get(field,[])):
            if c.get('part') in graph:graph[c['part']].append(c.get('on'))
            if field=='surface_contacts':
                status,message=contact_patch_status(scene,c);add(status,message,[c.get('part'),c.get('on')],f'{field}[{index}]')
            elif field=='bearings' and c.get('part') in parts and c.get('on') in parts:
                a,b=parts[c['part']],parts[c['on']];alo,ahi=a['origin'],[x+y for x,y in zip(a['origin'],a['size'])];blo,bhi=b['origin'],[x+y for x,y in zip(b['origin'],b['size'])]
                if abs(alo[2]-bhi[2])>EPS:add('failed','Bearing contact height mismatch',[a['id'],b['id']],f'{field}[{index}]');continue
                lo=[max(alo[k],blo[k]) for k in (0,1)];hi=[min(ahi[k],bhi[k]) for k in (0,1)]
                if min(hi[k]-lo[k] for k in (0,1))<=EPS:add('failed','Bearing has no positive-area intersection',[a['id'],b['id']],f'{field}[{index}]');continue
                # Existing non-box adapters retain their stated conceptual-footprint
                # coverage. For registered terrain, verify the actual triangles.
                if b['kind']=='custom':
                    points=[[lo[0]+(hi[0]-lo[0])*u,lo[1]+(hi[1]-lo[1])*v,alo[2]] for u,v in ((.1,.1),(.9,.1),(.9,.9),(.1,.9),(.5,.5))]
                    ok=all(any(n[2]>.999 for n in (surface_normals(b,p) or [])) for p in points)
                    add('passed' if ok else 'failed','Bearing samples must touch actual terrain triangles',[a['id'],b['id']],f'{field}[{index}]')
    # Cycles are explicit, root-reaching and justified, never mistaken for ground.
    approved=scene.get('support_cycles',[]);cycles=set()
    def visit(key,path):
        if key in path:
            cycles.add(frozenset(path[path.index(key):]));return
        if len(path)>len(parts):return
        for nxt in graph.get(key,[]):visit(nxt,path+[key])
    # A DFS color map avoids exponential traversal on shared support chains.
    colors={};stack=[]
    def walk(key):
        if colors.get(key)==1:cycles.add(frozenset(stack[stack.index(key):]));return
        if colors.get(key)==2:return
        colors[key]=1;stack.append(key)
        for nxt in graph.get(key,[]):walk(nxt)
        stack.pop();colors[key]=2
    for key in graph:walk(key)
    for cyc in cycles:
        ok=any(set(c.get('members',[]))==set(cyc) and isinstance(c.get('reason'),str) and c['reason'].strip() for c in approved)
        add('passed' if ok else 'failed','Support cycle requires an explicit bounded justification; root reachability remains required',sorted(cyc),'support_cycles')
    # New ground contact contract is opt-in and versioned. Legacy v2 explicitly
    # means an infinite conceptual plane z=0 meeting the declared roots' tops.
    version=scene.get('support_contract_version',0)
    if version not in (0,1):add('unsupported','Unknown support contract version',[],'support_contract_version');return out
    surfaces={s['id']:s for s in scene.get('ground_surfaces',[])}
    records=scene.get('ground_contacts',[])
    for key in scene.get('grounded',[]):
        if version==0:continue
        matches=[c for c in records if c.get('part')==key]
        if not matches:add('failed','Explicit ground contact missing',[key],'ground_contacts');continue
        for c in matches:
            try:
                s=surfaces[c['surface']];p=parts[key];points=np.asarray(c['points'],float)
                if s['type']!='plane':add('unsupported','Unknown ground surface adapter',[key],'ground_contacts');continue
                normal=np.asarray(s['normal'],float);origin=np.asarray(s['point'],float)
                if abs(np.linalg.norm(normal)-1)>EPS:raise ValueError('unit ground normal required')
                if len(points)<3 or points.shape[1]!=3 or not np.isfinite(points).all() or np.linalg.matrix_rank(points-points[0],tol=EPS)<2:raise ValueError('positive-area ground contact patch required')
                for point in points:
                    if abs(np.dot(point-origin,normal))>EPS:raise ValueError('ground patch is detached from plane')
                    if any(point[k]<s['bounds']['min'][k]-EPS or point[k]>s['bounds']['max'][k]+EPS for k in range(3)):raise ValueError('ground patch lies outside registered surface bounds')
                    normals=surface_normals(p,point)
                    if normals is None:add('unsupported','Unknown root surface adapter',[key],'ground_contacts');break
                    if not any(math.dist(n,(-normal).tolist())<EPS for n in normals):raise ValueError('ground contact misses root surface or opposing normal')
                else:add('passed','Explicit plane, positive-area root contact and opposed normals verified',[key],'ground_contacts')
            except (KeyError,ValueError,TypeError,IndexError) as exc:add('failed',str(exc),[key],'ground_contacts')
    return out
