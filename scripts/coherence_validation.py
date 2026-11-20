"""Opt-in conceptual coherence gates; no engineering or raster certification.

Reports distinguish unsupported evidence from a successful check. AABB collision
is exact only for opaque box envelopes; curved/hollow overlap needs another
adapter or an explicitly bounded assembly contact, never a global skip pair.
"""
import math

STATES={'passed','failed','unsupported','not_applicable','not_run'}
BOXES={'wall','slab','footing','column','beam','cabinet','landing','paving'}
SUPPORT_ADAPTERS=BOXES|{'vessel','pump','manifold','stair','ramp','worker','railing','custom','duct','cable_tray','console','seat','corbel','window','door','luminaire','instrument_panel'}

def vec(x):
    return isinstance(x,(list,tuple)) and len(x)==3 and all(type(v) in (int,float) and math.isfinite(v) for v in x)

def bounds(p):
    return p['origin'],[a+b for a,b in zip(p['origin'],p['size'])]

def intersection(a,b):
    lo=[max(x,y) for x,y in zip(a[0],b[0])];hi=[min(x,y) for x,y in zip(a[1],b[1])]
    return (lo,hi) if all(y-x>1e-6 for x,y in zip(lo,hi)) else None

def contains(box,other):
    return all(box[0][i]-1e-6<=other[0][i] and other[1][i]<=box[1][i]+1e-6 for i in range(3))

def segment_clip(a,b,box):
    start,end=0.,1.
    for axis in range(3):
        delta=b[axis]-a[axis]
        if abs(delta)<1e-12:
            if not box[0][axis]<=a[axis]<=box[1][axis]:return None
        else:
            lo,hi=sorted(((box[0][axis]-a[axis])/delta,(box[1][axis]-a[axis])/delta))
            start=max(start,lo);end=min(end,hi)
    if end-start<1e-7:return None
    points=[[a[k]+t*(b[k]-a[k]) for k in range(3)] for t in (start,end)]
    return [min(p[k] for p in points) for k in range(3)],[max(p[k] for p in points) for k in range(3)]

def contract_shape_errors(data):
    errors=[]
    policy=data.get('validation_policy','legacy')
    if policy not in ('legacy','strict'):errors.append('validation_policy must be legacy or strict')
    for field in ('functional_contracts','access_nodes','access_volumes','contact_exceptions'):
        values=data.get(field,[])
        if not isinstance(values,list):errors.append(field+': list required');continue
        for item in values:
            if not isinstance(item,dict):errors.append(field+': object required');continue
            keys={'functional_contracts':('part','role'),'access_nodes':('id',),'access_volumes':('id',),'contact_exceptions':('a','b','relation','reason')}[field]
            for key in keys:
                if not isinstance(item.get(key),str) or not item[key].strip():errors.append(field+': '+key+' required')
            if field=='access_nodes' and not vec(item.get('position')):errors.append('access node: position required')
            if field=='access_volumes':
                for key in ('from','to'):
                    if not isinstance(item.get(key),str) or not item[key].strip():errors.append('access volume: '+key+' node required')
                traversable=item.get('traversable_parts',[])
                if not isinstance(traversable,list) or any(not isinstance(x,str) for x in traversable):errors.append('access volume: traversable_parts must be IDs')
            if field in ('access_volumes','contact_exceptions'):
                box=item.get('region',{}) if field=='contact_exceptions' else item
                if not isinstance(box,dict) or not vec(box.get('min')) or not vec(box.get('max')):errors.append(field+': finite min/max required')
                elif any(y<=x for x,y in zip(box['min'],box['max'])):errors.append(field+': positive volume required')
            if 'critical' in item and type(item['critical'])!=bool:errors.append(field+': critical must be boolean')
    roots=data.get('access_roots',[])
    if not isinstance(roots,list) or any(not isinstance(x,str) for x in roots):errors.append('access_roots: IDs required')
    for part in data.get('parts',[]) if isinstance(data.get('parts',[]),list) else []:
        if not isinstance(part,dict):continue
        if 'validation_critical' in part and type(part['validation_critical'])!=bool:errors.append('part validation_critical must be boolean')
    from relation_contracts import relation_shape_errors
    errors.extend(relation_shape_errors(data))
    for field in ('surface_contacts','ground_contacts','ground_surfaces','support_cycles','route_contracts'):
        items=data.get(field,[])
        if not isinstance(items,list):errors.append(field+': array required');continue
        if any(not isinstance(item,dict) for item in items):errors.append(field+': objects required')
    return errors

def _coherence_report(data):
    if not isinstance(data,dict):
        return {'policy':'legacy','status':'failed','checks':[{'check':'contract_shape','status':'failed','message':'Scene must be an object','parts':[],'critical':True}]}
    strict=data.get('validation_policy')=='strict';checks=[]
    def add(check,status,message,parts=(),critical=True):
        checks.append(dict(check=check,status=status,message=message,parts=list(parts),critical=critical))
    from scene_schema import shape_errors
    from scene_model import KINDS
    shape=shape_errors(data,KINDS)
    if shape:
        for error in shape:add('contract_shape','failed',error)
        return dict(policy='strict' if strict else 'legacy',status='failed',checks=checks)
    if not strict:
        add('coherence','not_run','Legacy validation is partial; functional, circulation and global collision gates not requested.')
        return dict(policy='legacy',status='partial',checks=checks)
    parts={p['id']:p for p in data.get('parts',[])}
    critical=lambda *ids:any(parts[x].get('validation_critical',True) for x in ids)
    from functional_contracts import functional_checks
    from physical_support import support_checks
    from relation_contracts import relation_report
    from route_contracts import route_checks
    checks.extend(functional_checks(data));checks.extend(support_checks(data));checks.extend(route_checks(data))
    for relation in relation_report(data)['checks']:
        checks.append(dict(check='relation',status=relation['status'],message=relation['message'],
            parts=relation['owners'],critical=relation['critical'],relation_id=relation['relation_id'],relation_type=relation['type']))

    # Geometric nozzle footprint, not pressure/weld compatibility.
    nozzles=0
    for key,p in parts.items():
        for name,s in p.get('interfaces',{}).items():
            nozzles+=1;kind=p['kind'];w,d,h=p['size'];a=s['anchor'];n=s['normal'];r=s['diameter']/2
            if kind=='manifold':axis=0;center=[0,d/2,h/2];length=w;radius=min(d,h)/2
            elif kind=='pump':axis=1;center=[w*.25,d*.25,h*.5];length=d*.45;radius=min(h*.3,d*.3,w*.24)
            elif kind=='vessel':axis=2;center=[w/2,d/2,h/12];length=h*35/36-h/12;radius=min(w,d)/2
            else:add('nozzle_footprint','unsupported','No footprint adapter',[key],critical(key));continue
            radial=[i for i in range(3) if i!=axis];rr=math.sqrt(sum((a[i]-center[i])**2 for i in radial))
            if abs(n[axis])>.99:ok=rr+r<=radius+1e-6
            else:ok=r<=radius+1e-6 and center[axis]+r-1e-6<=a[axis]<=center[axis]+length-r+1e-6
            add('nozzle_footprint','passed' if ok else 'failed',name+': nozzle bore must fit component mounting surface',[key],critical(key))
    if not nozzles:add('nozzle_footprint','not_applicable','No interfaces declared')

    # Unlike the legacy obstacle check, exempt only each local endpoint region.
    for route in data.get('connections',[]):
        for ref in (route['from'],route['to']):
            key,name=ref.split(':');p=parts.get(key);s=p.get('interfaces',{}).get(name) if p else None
            if not s:add('endpoint_clearance','failed','Missing typed endpoint for local clearance',[key]);continue
            r=route['radius'];bb=bounds(p);expanded=([x-r for x in bb[0]],[x+r for x in bb[1]])
            anchor=[x+y for x,y in zip(p['origin'],s['anchor'])];tip=[x+y for x,y in zip(p['origin'],p['ports'][name])]
            pad=max(r,s['diameter']*.8)+1e-5
            local=([min(a,b)-pad for a,b in zip(anchor,tip)],[max(a,b)+pad for a,b in zip(anchor,tip)])
            intrusion=any(clipped is not None and not contains(local,clipped)
                for clipped in (segment_clip(a,b,expanded) for a,b in zip(route['route'],route['route'][1:])))
            add('endpoint_clearance','unsupported' if intrusion else 'passed',
                ref+(': route re-enters endpoint envelope outside authorized nozzle region; narrow-phase evidence required' if intrusion else ': no endpoint-envelope intrusion outside nozzle region'),[key],critical(key))

    # Every relation still needs the existing geometric contact validator.
    graph={k:[] for k in parts};ground=set(data.get('grounded',[]))
    for field in ('bearings','mounts','custom_contacts','surface_contacts'):
        for c in data.get(field,[]):
            if c['part'] in graph:graph[c['part']].append(c['on'])
    for key,p in parts.items():
        if p['kind']=='worker' and p.get('parent'):graph[key].append(p['parent'])
    def reaches(key,seen):
        if key in ground:return True
        if key in seen:return False
        return any(reaches(other,seen|{key}) for other in graph.get(key,[]))
    for key,p in parts.items():
        if p['kind'] not in SUPPORT_ADAPTERS:
            add('support','unsupported','No support adapter for '+p['kind'],[key],critical(key))
        elif not reaches(key,set()):add('support','failed','No declared support path to ground',[key],critical(key))
        else:add('support','passed','Declared support path exists; loads and stability are unverified',[key],critical(key))

    exceptions=[]
    for e in data.get('contact_exceptions',[]):
        if e['a'] not in parts or e['b'] not in parts or e['a']==e['b'] or e['relation'] not in ('mount','joint','containment'):
            add('contact_exception','failed','Unknown pair or relation',[e['a'],e['b']]);continue
        region=(e['region']['min'],e['region']['max']);overlap=intersection(bounds(parts[e['a']]),bounds(parts[e['b']]))
        if overlap is None or not contains(region,overlap):
            add('contact_exception','failed','Local region does not contain this assembly overlap',[e['a'],e['b']]);continue
        # Prevent an arbitrary scene-sized skip region. It must itself stay inside
        # the shared AABB; narrow-phase geometry still depends on assembly evidence.
        if not contains(overlap,region):
            add('contact_exception','failed','Contact region extends beyond shared local overlap',[e['a'],e['b']]);continue
        if data.get('relation_contract_version')==1:
            relations=[r for r in relation_report(data)['checks'] if r['relation_id']==e.get('relation_id')]
            if len(relations)!=1 or relations[0]['status']!='passed' or set(relations[0]['owners'])!={e['a'],e['b']}:
                add('contact_exception','failed','Typed contact exception needs its verified physical relation ID',[e['a'],e['b']]);continue
            physical=relations[0]['region']
            if physical is None or not contains((physical['min'],physical['max']),region):
                add('contact_exception','failed','Collision exemption exceeds verified relation region',[e['a'],e['b']]);continue
        exceptions.append(e)
    ordered=sorted(parts,key=lambda k:parts[k]['origin'][0]);candidates=0
    for i,a in enumerate(ordered):
        aa=bounds(parts[a])
        for b in ordered[i+1:]:
            bb=bounds(parts[b])
            if bb[0][0]>=aa[1][0]-1e-6:break
            overlap=intersection(aa,bb)
            if overlap is None:continue
            candidates+=1
            e=next((e for e in exceptions if {e['a'],e['b']}=={a,b}),None)
            if e:add('collision','passed','Explicit bounded '+e['relation']+' contact: '+e['reason'],[a,b],critical(a,b));continue
            actor=next((key for key in (a,b) if parts[key]['kind']=='worker' and parts[key].get('parameters',{}).get('pose') in ('seated','leaning')),None)
            if actor is not None:
                from worker_pose import collision_status
                other=b if actor==a else a;status,message=collision_status(parts[actor],parts[other])
                add('collision',status,message,[a,b],critical(a,b));continue
            exact=parts[a]['kind'] in BOXES and parts[b]['kind'] in BOXES
            add('collision','failed' if exact else 'unsupported','Opaque box penetration' if exact else 'Overlapping envelopes require shape-specific narrow-phase evidence or bounded assembly contact',[a,b],critical(a,b))
    if not candidates:add('collision','passed','No intersecting component envelopes')

    node_list=data.get('access_nodes',[]);nodes={n['id']:n for n in node_list};roots=data.get('access_roots',[]);edges={n:[] for n in nodes}
    if len(nodes)!=len(node_list):add('navigation','failed','Duplicate access node IDs')
    volumes=data.get('access_volumes',[])
    if any(p['kind'] in ('stair','ramp') for p in parts.values()) and not volumes:
        add('access','failed','Stair/ramp scene requires access volume and navigation contracts')
    if not volumes:add('access','not_applicable','No circulation volume requested')
    for v in volumes:
        cb=(v['min'],v['max']);ids=[]
        from access_geometry import profile_errors,volume_obstructed
        profile=profile_errors(v,nodes)
        if profile:
            add('access','failed',v['id']+': '+'; '.join(profile));continue
        if any(key not in parts or parts[key]['kind'] not in ('stair','ramp','slab','landing') for key in v.get('traversable_parts',[])):
            add('access','failed',v['id']+': traversable exclusions must reference actual stair/ramp/slab/landing components')
        for key,p in parts.items():
            if intersection(cb,bounds(p)):
                if key in v.get('traversable_parts',[]) and p['kind'] in ('slab','landing'):
                    # A walking surface may meet the feet plane, but cannot be
                    # exempted through the person's body or overhead clearance.
                    # Positive overlap means its top exceeds the envelope base.
                    add('access','failed',v['id']+': traversable slab/landing must remain below the walking envelope',[key])
                if not volume_obstructed(p,v):continue
                ids.append(key)
        add('access','failed' if ids else 'passed',v['id']+(': occupied walking envelope' if ids else ': clear walking envelope'),ids,v.get('critical',True))
        a,b=v.get('from'),v.get('to')
        if a not in nodes or b not in nodes:add('navigation','failed',v['id']+': known from/to nodes required');continue
        if not all(contains(cb,(nodes[k]['position'],nodes[k]['position'])) for k in (a,b)):
            add('navigation','failed',v['id']+': endpoint lies outside its walking envelope');continue
        if not ids:edges[a].append(b);edges[b].append(a)
    if nodes:
        if not roots or any(x not in nodes for x in roots):add('navigation','failed','Known access roots required')
        reached=set(roots);pending=list(roots)
        while pending:
            for n in edges.get(pending.pop(),[]):
                if n not in reached:reached.add(n);pending.append(n)
        missing=set(nodes)-reached
        add('navigation','failed' if missing else 'passed','Unreachable access nodes: '+','.join(sorted(missing)) if missing else 'All declared access nodes reachable')
    failed=any(c['status']=='failed' or c['status']=='unsupported' and c['critical'] for c in checks)
    return dict(policy='strict',status='failed' if failed else 'passed',checks=checks,
                limits=['Conceptual geometry only; no loads, pressure, operating performance or raster certification','Unsupported critical checks block strict acceptance'])

def coherence_report(data):
    """Coherence-only evidence; use scene_model.validation_report for all gates."""
    try:return _coherence_report(data)
    except (KeyError,TypeError,ValueError,IndexError,OverflowError) as error:
        return {'policy':data.get('validation_policy','legacy') if isinstance(data,dict) else 'legacy',
                'status':'failed','checks':[{'check':'coherence_input','status':'failed',
                'message':'Invalid coherence input: '+str(error),'parts':[],'critical':True},
                {'check':'remaining_coherence','status':'not_run','message':'Dependent checks require valid input','parts':[],'critical':True}]}

def strict_errors(data):
    if data.get('validation_policy')!='strict':return []
    report=coherence_report(data)
    return ['coherence '+c['check']+': '+c['message']+' ('+', '.join(c['parts'])+')' for c in report['checks']
            if c['status']=='failed' or c['status']=='unsupported' and c['critical']]
