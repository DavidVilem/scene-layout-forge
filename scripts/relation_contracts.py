"""Versioned typed physical relations and localized camera witnesses.

Existing v2 bearing/mount/access records receive deterministic relation IDs.
New relation declarations require actual geometry evidence; names and nearby
screen owners cannot supply a missing connection. This is not a dynamics solver.
"""
import math
from physical_support import surface_normals,contact_patch_status

TYPES={'fluid_port','shaft_bearing','rigid_mount','hinge','sliding_support','wall_opening','stair_landing','flexible_anchor'}
EPS=1e-6


def _region(points,tol=EPS):
    return {'min':[min(p[k] for p in points)-tol for k in range(3)],'max':[max(p[k] for p in points)+tol for k in range(3)]}


def _bounds(part):return part['origin'],[x+y for x,y in zip(part['origin'],part['size'])]


def relation_shape_errors(scene):
    errors=[]
    if scene.get('relation_contract_version',1)!=1:errors.append('unsupported relation_contract_version')
    relations=scene.get('relations',[])
    if not isinstance(relations,list):return errors+['relations: array required']
    ids=set()
    for rel in relations:
        if not isinstance(rel,dict):errors.append('relation: object required');continue
        rid=rel.get('id')
        if not isinstance(rid,str) or not rid or rid in ids:errors.append('relation: unique nonempty ID required')
        else:ids.add(rid)
        if not isinstance(rel.get('type'),str):errors.append('relation: type required')
        tolerance=rel.get('tolerance',EPS)
        if type(tolerance) not in (int,float) or not math.isfinite(tolerance) or not 0<tolerance<=1e-4:errors.append('relation: tolerance must be positive and at most 0.0001 m')
        if 'critical' in rel and type(rel['critical'])!=bool:errors.append('relation: critical must be boolean')
    return errors


def _legacy_relations(scene):
    """Adapt existing evidence without rewriting or upgrading its scope."""
    parts={p['id']:p for p in scene.get('parts',[])};out=[]
    def add(rid,kind,owners,status,message,region):out.append(dict(relation_id=rid,type=kind,owners=owners,status=status,message=message,region=region,critical=True,compatibility='v2-declared-contact'))
    for field in ('bearings','mounts'):
        for c in scene.get(field,[]):
            a,b=c.get('part'),c.get('on');rid=('bearing:'+str(a)+'->'+str(b)) if field=='bearings' else 'mount:'+str(a)+'->'+str(b)+':'+str(c.get('axis'))+':'+str(c.get('side'))
            try:
                pa,pb=parts[a],parts[b];alo,ahi=_bounds(pa);blo,bhi=_bounds(pb)
                axis=2 if field=='bearings' else 'xyz'.index(c['axis']);side=1 if field=='bearings' else c['side']
                plane=bhi[axis] if side==1 else blo[axis];face=alo[axis] if side==1 else ahi[axis]
                lo=[max(alo[k],blo[k]) for k in range(3)];hi=[min(ahi[k],bhi[k]) for k in range(3)];lo[axis]=hi[axis]=plane
                ok=abs(plane-face)<=EPS and all(hi[k]-lo[k]>EPS for k in range(3) if k!=axis)
                if not ok:raise ValueError('contact plane/footprint mismatch')
                # The region comes from geometry, never a user-sized skip box.
                add(rid,'rigid_mount',[a,b],'passed','Declared planar contact verified within adapter scope',_region([lo,hi]))
            except (KeyError,TypeError,ValueError):add(rid,'rigid_mount',[a,b],'failed','Invalid declared contact',None)
    for c in scene.get('stair_access',[])+scene.get('ramp_access',[]):
        a=c.get('stair',c.get('ramp'));b=c.get('landing');rid='stair_landing:'+str(a)+'->'+str(b)
        try:
            p,q=parts[a],parts[b];lo,hi=_bounds(p);ql,qh=_bounds(q);rev=p.get('parameters',{}).get('reverse',False)
            y=lo[1] if rev else hi[1];target=qh[1] if rev else ql[1]
            if p['kind'] not in ('stair','ramp') or q['kind'] not in ('slab','landing') or abs(y-target)>EPS or abs(hi[2]-qh[2])>EPS or lo[0]<ql[0]-EPS or hi[0]>qh[0]+EPS:raise ValueError('landing mismatch')
            add(rid,'stair_landing',[a,b],'passed','Flight reaches its declared landing edge',_region([[lo[0],y,hi[2]],[hi[0],y,hi[2]]]))
        except (KeyError,TypeError,ValueError):add(rid,'stair_landing',[a,b],'failed','Invalid stair landing geometry',None)
    for c in scene.get('shaft_bearings',[]):
        from mechanical_checks import shaft_bearing_errors
        a,b=c.get('shaft'),c.get('bearing');rid='shaft_bearing:'+str(a)+'->'+str(b)
        errors=shaft_bearing_errors(dict(parts=scene.get('parts',[]),shaft_bearings=[c]))
        region=None if errors else _region(_bounds(parts[b]))
        add(rid,'shaft_bearing',[a,b],'failed' if errors else 'passed','; '.join(errors) if errors else 'Straight shaft axis fits annular bearing aperture',region)
    return out


def _endpoint(parts,record):
    part=parts[record['part']];anchor=record['anchor']
    if not isinstance(anchor,(list,tuple)) or len(anchor)!=3 or any(type(x) not in (int,float) or not math.isfinite(x) for x in anchor):raise ValueError('finite local endpoint anchor required')
    point=[x+y for x,y in zip(part['origin'],anchor)]
    return part,point


def relation_report(scene):
    parts={p['id']:p for p in scene.get('parts',[])};checks=_legacy_relations(scene);seen={c['relation_id'] for c in checks}
    if scene.get('actor_contacts'):
        from actor_plan import contact_checks
        checks.extend(contact_checks(scene));seen.update(c['relation_id'] for c in checks)
    for rel in scene.get('relations',[]):
        rid=rel.get('id');kind=rel.get('type');status='unsupported';message='Unknown relation adapter';owners=[];region=None
        try:
            if rid in seen:raise ValueError('Duplicate relation ID')
            seen.add(rid)
            if kind not in TYPES:pass
            elif kind=='wall_opening':
                from assembly_model import opening_errors
                opening=next(o for o in scene.get('openings',[]) if o['id']==rel['opening'])
                relevant=dict(scene,openings=[opening]);errs=opening_errors(relevant)
                if errs:raise ValueError('; '.join(errs))
                host=next(h for h in scene.get('hosts',[]) if h['id']==opening['host']);owners=list(host['fragments'])
                if rel.get('owners') is not None and set(rel['owners'])!=set(owners):raise ValueError('Opening owners disagree with physical host fragments')
                o=opening['origin'];region=_region([o,[a+b for a,b in zip(o,opening['size'])]])
                status='passed';message='Registered through-opening and host fragments verified'
            elif kind=='stair_landing':
                expected='stair_landing:'+rel['flight']+'->'+rel['landing'];base=next(c for c in checks if c['relation_id']==expected)
                status=base['status'];owners=base['owners'];region=base['region'];message=base['message']
            elif kind=='fluid_port':
                from typed_interfaces import interface_errors
                a,b=rel['from'],rel['to'];owners=[a.split(':')[0],b.split(':')[0]]
                route=next(r for r in scene.get('connections',[]) if r['from']==a and r['to']==b)
                errors=interface_errors(scene)
                if errors:raise ValueError('; '.join(errors))
                end=rel.get('endpoint','from')
                if end not in ('from','to'):raise ValueError('fluid witness endpoint must be from or to')
                point=route['route'][0 if end=='from' else -1];region=_region([point],min(route['radius'],.01));status='passed';message='Typed medium, diameter, direction and endpoint route verified'
            elif kind in ('shaft_bearing','hinge'):
                from mechanical_checks import shaft_bearing_errors
                a,b=rel['a'],rel['b'];pa,aa=_endpoint(parts,a);pb,bb=_endpoint(parts,b);owners=[pa['id'],pb['id']]
                errors=shaft_bearing_errors(dict(parts=list(parts.values()),shaft_bearings=[{'shaft':pa['id'],'bearing':pb['id']}]))
                if errors:raise ValueError('; '.join(errors))
                axis='xyz'.index(pb.get('parameters',{}).get('orientation','y'))
                for endpoint in (a,b):
                    n=endpoint['axis']
                    if len(n)!=3 or abs(abs(n[axis])-1)>EPS or abs(sum(v*v for v in n)-1)>EPS:raise ValueError('Endpoint axis disagrees with actual mechanical axis')
                if math.dist(aa,bb)>rel.get('tolerance',EPS):raise ValueError('Mechanical frame origins disagree')
                blo,bhi=_bounds(pb)
                if any(aa[k]<blo[k]-EPS or aa[k]>bhi[k]+EPS for k in range(3)):raise ValueError('Mechanical frame outside bearing')
                status='passed';message='Coaxial straight shaft and annular bearing geometry; motion and fit are unverified';region=_region([aa],EPS)
            else:
                a,b=rel['a'],rel['b'];pa,aa=_endpoint(parts,a);pb,bb=_endpoint(parts,b);owners=[pa['id'],pb['id']]
                tol=rel.get('tolerance',EPS)
                if math.dist(aa,bb)>tol:raise ValueError('Relation local frames are detached')
                if kind=='flexible_anchor':
                    if pa['kind'] not in ('pipe','conduit'):raise ValueError('Flexible anchor needs a registered routed pipe/conduit')
                    points=pa['parameters']['points']
                    if min(math.dist(aa,points[0]),math.dist(aa,points[-1]))>tol:raise ValueError('Anchor does not match a flexible endpoint')
                    normals=surface_normals(pb,bb)
                    if normals is None:status='unsupported';message='Unsupported anchor host surface'
                    elif not normals:raise ValueError('Flexible endpoint is detached from host surface')
                    else:status='passed';message='Routed flexible endpoint touches host; deformation and stress unverified'
                else:
                    patch={'part':pa['id'],'on':pb['id'],'points':rel['points'],'normals':rel.get('normals')}
                    if patch['normals'] is None:patch.pop('normals')
                    status,message=contact_patch_status(scene,patch)
                    if status=='passed':
                        for endpoint,part,point in ((a,pa,aa),(b,pb,bb)):
                            normal=endpoint['normal'];actual=surface_normals(part,point)
                            if len(normal)!=3 or abs(sum(v*v for v in normal)-1)>EPS or not any(math.dist(normal,n)<EPS for n in actual or []):raise ValueError('Endpoint normal disagrees with actual surface')
                        if math.dist(a['normal'],[-v for v in b['normal']])>EPS:raise ValueError('Endpoint normals must oppose')
                        if kind=='sliding_support':
                            axis=a['axis']
                            if abs(sum(v*v for v in axis)-1)>EPS or abs(sum(x*y for x,y in zip(axis,a['normal'])))>EPS or math.dist(axis,b['axis'])>EPS:raise ValueError('Sliding axes must agree and lie in contact tangent plane')
                    region=_region(rel['points'],tol)
                if region is None:region=_region([aa,bb],tol)
        except (KeyError,ValueError,TypeError,IndexError,StopIteration) as exc:status='failed';message=str(exc) or 'Missing physical relation evidence'
        checks.append(dict(relation_id=rid,type=kind,status=status,owners=owners,region=region,message=message,critical=rel.get('critical',True),compatibility='relation-v1'))
    failed=any(c['status']=='failed' or c['status']=='unsupported' and c['critical'] for c in checks)
    return {'status':'failed' if failed else 'passed','checks':checks,'limits':['Geometric relations only; loads, motion, pressure and rendered visibility are independent']}


def witness_errors(scene,witness):
    """Check identity, owners and local region before a camera visibility test."""
    try:
        rid=witness['relation_id'];matches=[r for r in relation_report(scene)['checks'] if r['relation_id']==rid]
        if len(matches)!=1:raise ValueError('Witness must identify one existing physical relation')
        relation=matches[0]
        if relation['status']!='passed':raise ValueError('Physical relation is '+relation['status'])
        if set(witness['owners'])!=set(relation['owners']):raise ValueError('Witness owners disagree with relation')
        point=witness['point'];region=relation['region']
        if not isinstance(point,(list,tuple)) or len(point)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) for v in point):raise ValueError('Finite witness point required')
        if region is None or any(point[k]<region['min'][k]-EPS or point[k]>region['max'][k]+EPS for k in range(3)):raise ValueError('Witness point is outside the verified relation region')
        if relation['type'] in ('rigid_mount','sliding_support'):
            parts={p['id']:p for p in scene.get('parts',[])}
            surfaces=[surface_normals(parts[p],point) for p in relation['owners']]
            if any(n is None for n in surfaces):raise ValueError('Witness contact surface adapter is unsupported')
            if any(not n for n in surfaces):raise ValueError('Witness point misses the actual contact surfaces')
        if witness.get('relation_type',relation['type'])!=relation['type']:raise ValueError('Witness relation type mismatch')
        return []
    except (KeyError,ValueError,TypeError,IndexError) as exc:return [str(exc)]
