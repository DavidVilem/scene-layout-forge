"""Executable architectural gates, not structural engineering or image recognition.

Version 4 contracts supplement (never replace) strict scene/contact validation.
Evidence is append-only, bound to exact scene/view hashes and chained in order.
Unknown building adapters block; historical v2/v3 studies remain readable.
"""
import hashlib
import json
import math
from pathlib import Path

STAGES=('site','program','massing','structure','levels','systems','representation','finish')

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def enabled(scene):
    return scene.get('workflow_version',2)>=4

def _inside(point,box,xy=False):
    return all(box['min'][i]-1e-6<=point[i]<=box['max'][i]+1e-6 for i in range(2 if xy else 3))

def _box(part):
    return {'min':part['origin'],'max':[a+b for a,b in zip(part['origin'],part['size'])]}

def _reachable(scene,start):
    graph={n['id']:set() for n in scene.get('access_nodes',[])}
    for v in scene.get('access_volumes',[]):
        if v['from'] in graph and v['to'] in graph:
            graph[v['from']].add(v['to']);graph[v['to']].add(v['from'])
    seen=set();pending=[start]
    while pending:
        k=pending.pop()
        if k not in seen:seen.add(k);pending.extend(graph.get(k,set())-seen)
    return seen

def _contact_pairs(scene):
    pairs=set()
    for field in ('bearings','mounts','custom_contacts','surface_contacts'):
        for c in scene.get(field,[]):
            if 'part' in c and 'on' in c:pairs.add(frozenset((c['part'],c['on'])))
    for c in scene.get('connections',[]):
        pairs.add(frozenset((c['from'].split(':')[0],c['to'].split(':')[0])))
    return pairs

def _report(scene,view=None,observations=None):
    stages={name:[] for name in STAGES}
    def fail(stage,condition,message):
        if not condition:stages[stage].append(message)
    a=scene.get('architecture_contract')
    if not isinstance(a,dict):
        stages['site'].append('workflow v4 requires architecture_contract (or an explicit supported subject adapter)')
        return stages
    fail('site',a.get('version')==1,'unsupported architectural contract version')
    fail('site',a.get('mode')=='building','only building adapter implemented; do not invent building requirements for isolated machines')
    parts={p['id']:p for p in scene['parts']};nodes={n['id']:n for n in scene.get('access_nodes',[])}
    spaces=a.get('spaces',[]);site=a.get('site',{});approach=site.get('approach',{})
    terrain=site.get('terrain',[])
    fail('site',bool(terrain) and all(k in parts for k in terrain),'registered terrain/support geometry required')
    fail('site',bool(site.get('placement_reason')) and bool(site.get('operating_direction')),'site placement and operating direction required')
    root=approach.get('root');node=nodes.get(root)
    fail('site',node is not None and root in scene.get('access_roots',[]),'exterior approach must be an actual access root')
    if node:
        fail('site',not any(_inside(node['position'],s['bounds'],True) for s in spaces),'exterior root lies inside an occupied space')
        floors=[parts[k] for k in a.get('occupied_floors',[]) if k in parts]
        fail('site',not any(_inside(node['position'],_box(p),True) for p in floors),'exterior root lies on the occupied building floor; model a distinct arrival')
        surfaces=[parts[k] for k in approach.get('surfaces',[]) if k in parts]
        fail('site',bool(surfaces) and any(_inside(node['position'],_box(p),True) and abs(node['position'][2]-p['origin'][2]-p['size'][2]-approach.get('eye_height',1.))<.05 for p in surfaces),'arrival root must stand above a registered approach surface')
        fail('site',approach.get('entry') in _reachable(scene,root),'exterior approach does not reach the entrance')
    fail('site',all(k in parts for k in approach.get('surfaces',[])) and bool(approach.get('surfaces')),'approach surface IDs required')
    fail('program',bool(spaces) and len({s['id'] for s in spaces})==len(spaces),'distinct occupied spaces required')
    for space in spaces:
        sid=space['id'];roomnode=space.get('access_node')
        fail('program',bool(space.get('activity')) and bool(space.get('area_reason')),sid+': activity and area justification required')
        fail('program',roomnode in nodes and roomnode in _reachable(scene,root),sid+': unreachable occupied space')
        fail('program',bool(space.get('fixtures')) and all(k in parts and _inside(parts[k]['origin'],space['bounds']) for k in space.get('fixtures',[])),sid+': registered fixtures must belong to the actual allocated space')
        fail('program',roomnode in nodes and _inside(nodes[roomnode]['position'],space['bounds']),sid+': access node outside space')
    fail('program',bool(a.get('occupied_floors')) and all(k in parts for k in a['occupied_floors']),'occupied floor inventory required')
    # Numeric alternatives describe building shape, entrances and roof form, not camera/labels.
    alternatives=a.get('alternatives',[]);signatures=set()
    for c in alternatives:
        blocks=c.get('volumes',[])
        fail('massing',bool(blocks) and bool(c.get('arrival')) and bool(c.get('tradeoff')),'each massing alternative needs volumes, arrival and tradeoff')
        if blocks:
            # Translation-invariant plan/height/roof descriptor; moving a room alone is insufficient.
            signatures.add(digest(sorted([(round(b['size'][0]/b['size'][1],2),round(b['size'][2],2),b['roof']) for b in blocks])))
    fail('massing',len(alternatives)>=3 and len(signatures)>=3,'three distinct envelope/height/roof alternatives required, not relocated rooms')
    chosen=next((c for c in alternatives if c.get('id')==a.get('selected')),None)
    fail('massing',chosen is not None,'selected massing alternative absent')
    if chosen:
        fail('massing',bool(chosen.get('realized_by')) and all(k in parts for k in chosen['realized_by']),'selected envelope must bind to actual parts')
        fail('massing',chosen.get('geometry_sha256')==digest([parts[k] for k in chosen.get('realized_by',[]) if k in parts]),'selected envelope geometry changed; revisit the massing decision')
        for volume in chosen.get('volumes',[]):
            owned=[parts[k] for k in volume.get('parts',[]) if k in parts]
            fail('massing',owned and len(owned)==len(volume.get('parts',[])),'selected volume needs actual envelope component IDs')
            if owned:
                extent=[max(p['origin'][i]+p['size'][i] for p in owned)-min(p['origin'][i] for p in owned) for i in range(3)]
                fail('massing',all(abs(a-b)<1e-5 for a,b in zip(extent,volume['size'])),'selected volume dimensions disagree with realized envelope')
    pairs=_contact_pairs(scene);schemes=a.get('roof_supports',[])
    fail('structure',bool(schemes),'occupied building needs declared roof/support schemes')
    roofs=set(a.get('envelope',{}).get('roofs',[]))
    fail('structure',roofs and roofs=={s['roof'] for s in schemes},'every roof needs a support scheme')
    for scheme in schemes:
        roof=parts.get(scheme['roof']);supports=scheme.get('supports',[])
        fail('structure',roof is not None and len(set(supports))>=2 and all(k in parts for k in supports),'distributed roof support requires at least two actual supports; cantilever adapter not implemented')
        if roof and all(k in parts for k in supports) and supports:
            fail('structure',all(frozenset((roof['id'],k)) in pairs for k in supports),roof['id']+': undeclared roof/support contact')
            centers=[[parts[k]['origin'][i]+parts[k]['size'][i]/2 for i in range(2)] for k in supports]
            span=max(max(p[i] for p in centers)-min(p[i] for p in centers) for i in range(2))
            fail('structure',span>=min(roof['size'][:2])*.35,roof['id']+': support centers clustered; distribution unresolved')
    openings={o['id']:o for o in scene.get('openings',[])}
    walking_ids=set(a.get('occupied_floors',[])+approach.get('surfaces',[])+a.get('circulation_surfaces',[]))
    walking=[parts[k] for k in walking_ids if k in parts]
    for route in scene.get('access_volumes',[]):
        if route.get('from') not in nodes or route.get('to') not in nodes:continue
        pa=nodes[route['from']]['position'];pb=nodes[route['to']]['position'];steps=max(1,math.ceil(math.dist(pa,pb)/.2))
        unsupported=False
        for j in range(steps+1):
            point=[x+(y-x)*j/steps for x,y in zip(pa,pb)];supported=False
            for p in walking:
                if not _inside(point,_box(p),True):continue
                o=p['origin'];sz=p['size'];top=o[2]+sz[2]
                if p['kind']=='stair':
                    count=p.get('parameters',{}).get('steps',0)
                    if type(count)!=int or count<1:continue
                    along=(point[1]-o[1])/sz[1]
                    if p.get('parameters',{}).get('reverse'):along=1-along
                    top=o[2]+min(count,max(1,math.floor(along*count)+1))*sz[2]/count
                elif p['kind']=='ramp':
                    along=(point[1]-o[1])/sz[1]
                    if p.get('parameters',{}).get('reverse'):along=1-along
                    top=o[2]+along*sz[2]
                elif p['kind'] not in ('slab','landing'):continue
                if abs(point[2]-approach.get('eye_height',1.)-top)<=.2:supported=True;break
            if not supported:unsupported=True;break
        fail('levels',not unsupported,route['id']+': walking route crosses an unsupported gap or undeclared circulation surface')
    for space in spaces:
        if space.get('enclosed',True):
            doors=space.get('doors',[])
            fail('levels',bool(doors) and all(k in openings for k in doors),space['id']+': real door aperture required')
            for key in doors:
                if key not in openings:continue
                o=openings[key];box={'min':o['origin'],'max':[x+y for x,y in zip(o['origin'],o['size'])]}
                from access_geometry import segment_box
                cross=any(v['from'] in nodes and v['to'] in nodes and segment_box(nodes[v['from']]['position'],nodes[v['to']]['position'],box['min'],box['max']) for v in scene.get('access_volumes',[]))
                fail('levels',cross,space['id']+': circulation does not cross its door')
    required=a.get('required_systems',[]);systems=a.get('systems',[])
    fail('systems',bool(required) and set(required)=={s['id'] for s in systems},'all subject-defining systems require explicit contracts; absence is not not-applicable')
    for system in systems:
        members=system.get('members',[]);links=system.get('links',[])
        fail('systems',len(set(members))>=2 and all(k in parts for k in members),'system must name registered subassemblies')
        fail('systems',bool(links) and all(len(pair)==2 and set(pair)<=set(members) and frozenset(pair) in pairs for pair in links),'system links must bind actual typed routes or contact pairs')
        seen=set(members[:1])
        for _ in members:
            for pair in links:
                if set(pair)&seen:seen.update(pair)
        fail('systems',set(members)<=seen,'defining system has disconnected declared members')
        fail('systems',bool(system.get('limits')),'system coverage limits required')
    witnesses=a.get('witnesses',[])
    fail('representation',{'arrival','entrance','envelope','operation','context'}<={w['role'] for w in witnesses},'architectural visibility must cover arrival, entrance, envelope, operation and context')
    if view:
        components=view.get('projection_review',{}).get('components',{})
        for w in witnesses:
            fail('representation',bool(w.get('parts')) and all(k in parts for k in w['parts']),'unknown architectural witness')
            visible=sum(components.get(k,{}).get('area_fraction',0) for k in w['parts'])
            threshold=w.get('min_area_fraction',.0003)
            valid=type(threshold) in (int,float) and math.isfinite(threshold) and .0001<=threshold<=1
            fail('representation',valid,'visibility threshold must be finite and at least 0.0001')
            fail('representation',valid and visible>=threshold,w['id']+': architectural witness hidden by cut/camera')
    else:stages['representation'].append('bound view evidence required')
    if observations is not None:
        found={o['target']:o for o in observations}
        for w in witnesses:
            o=found.get('architecture:'+w['id'],{})
            fail('finish',o.get('state')=='visible_correct' and bool(o.get('region')) and bool(o.get('note')),w['id']+': actual-image identity/access evidence missing, uncertain or wrong')
    else:stages['finish'].append('independent final PNG review required')
    return stages

def report(scene,view=None,observations=None):
    try:
        issues=_report(scene,view,observations)
    except (KeyError,TypeError,ValueError,IndexError,ZeroDivisionError) as exc:
        issues={name:['malformed architectural contract: '+str(exc)] for name in STAGES}
    return {k:{'status':'failed' if v else 'passed','errors':v} for k,v in issues.items()}

def preflight_errors(scene):
    if 'architecture_contract' in scene and not enabled(scene):return ['architectural contract cannot be downgraded to legacy workflow']
    if not enabled(scene):return []
    result=report(scene)
    return [name+': '+e for name in STAGES[:6] for e in result[name]['errors']]

def record_stage(scene,stage,previous=(),view=None,observations=None,note=''):
    """Call after inspecting evidence; stage 8 additionally requires pixel_review.errors.

    A changed scene starts a new chain, preserving the old one. Scene-wide binding
    intentionally invalidates all approvals, rather than guessing dependencies.
    """
    if type(stage) is not int or not 1<=stage<=8:raise ValueError('stage must be 1..8')
    if len(previous)!=stage-1:raise ValueError('stages cannot be skipped')
    errors=records_errors(scene,previous,stage-1,view)
    errors+=report(scene,view,observations)[STAGES[stage-1]]['errors']
    if stage in (4,5,6):
        from scene_model import validate
        if scene.get('validation_policy')!='strict':errors.append('architectural approvals require strict physical validation')
        errors.extend(validate(scene))
    if stage==7 and 'visual_plan' in scene:
        from visual_contract import compile_visual_contract
        projection=view.get('projection_review') if isinstance(view,dict) else None
        visual=compile_visual_contract(scene,evidence=projection)
        errors.extend(visual['errors'])
        if visual['guide_status']!='passed':errors.append('representation requires usable guide detail and subject visibility')
    if not note.strip():errors.append('observed decision/evidence note required')
    if errors:raise ValueError('; '.join(errors))
    result={'stage':stage,'name':STAGES[stage-1],'scene_sha256':digest(scene),'previous':digest(previous[-1]) if previous else None,'note':note,'status':'passed'}
    if stage>=7:result['view_sha256']=digest(view)
    if stage==8:result['observations_sha256']=digest(observations)
    return result

def records_errors(scene,records,count=7,view=None):
    if not isinstance(records,list) and not isinstance(records,tuple):return ['stage records required']
    if len(records)!=count:return ['required sequential stage evidence missing']
    errors=[]
    for i,r in enumerate(records):
        if r.get('stage')!=i+1 or r.get('status')!='passed' or r.get('scene_sha256')!=digest(scene):errors.append('stale, failed or out-of-order stage evidence')
        if r.get('previous')!=(digest(records[i-1]) if i else None):errors.append('stage evidence chain changed')
        if i>=6 and r.get('view_sha256')!=digest(view):errors.append('stale stage view evidence')
    return errors

def save_record(run,record):
    """Exclusive files, including repeated/rejected design attempts kept by caller."""
    import uuid
    stage=record['stage'];folder=Path(run)/f'{stage:02d}-{STAGES[stage-1]}'
    folder.mkdir(exist_ok=True)
    path=folder/('approval-'+uuid.uuid4().hex+'.json')
    with path.open('x',encoding='utf-8') as f:json.dump(record,f,indent=2)
    return path
