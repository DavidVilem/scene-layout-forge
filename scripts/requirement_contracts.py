"""Coverage and physical witnesses for selected graph requirements."""
import math
from access_geometry import profile_errors,volume_obstructed

EPS=1e-6


def _intersects(a,b):
    return all(min(a[1][k],b[1][k])-max(a[0][k],b[0][k])>EPS for k in range(3))


def _bounds(p):return p['origin'],[a+b for a,b in zip(p['origin'],p['size'])]


def requirement_checks(scene,selected):
    material=scene['materialized_design'];proofs=material.get('requirements',{});strict=scene.get('validation_policy')=='strict'
    enabled=strict or 'requirements' in material;parts={p['id']:p for p in scene.get('parts',[])}
    volumes={v['id']:v for v in scene.get('access_volumes',[])};nodes={n['id']:n for n in scene.get('access_nodes',[])}
    openings={o['id']:o for o in scene.get('openings',[])};checks=[]
    from design_realization import edge_id
    from typed_interfaces import support_errors
    from physical_support import support_checks
    from registered_geometry import mount_errors,contact_errors
    from assembly_model import opening_errors
    from relation_contracts import relation_report
    relation_results={r['relation_id']:r for r in relation_report(scene)['checks']}
    support_faults=support_errors(scene)+mount_errors(scene)+contact_errors(scene)
    support_faults += [c['message']+' '+','.join(c['parts']) for c in support_checks(scene) if c['status'] in ('failed','unsupported')]
    graph={key:[] for key in parts}
    for field in ('bearings','mounts','custom_contacts','surface_contacts'):
        for c in scene.get(field,[]):
            if c.get('part') in graph:graph[c['part']].append(c.get('on'))
    roots=set(scene.get('grounded',[]))
    def supported(key,seen=None):
        seen=set() if seen is None else seen
        if key in roots:return True
        if key in seen:return False
        return any(supported(k,seen|{key}) for k in graph.get(key,[]))
    for edge in selected['edges']:
        key=edge_id(edge);expected=edge.get('requires',[]);mapping=proofs.get(key,{}) if isinstance(proofs,dict) else {}
        edgevols=material['edges'].get(key,[]);zones=material.get('zones',{});edge_lo=min(zones[edge['from']]['anchor'][2],zones[edge['to']]['anchor'][2]);edge_hi=max(zones[edge['from']]['anchor'][2],zones[edge['to']]['anchor'][2])
        for requirement in expected:
            status='passed';message='';evidence=mapping.get(requirement) if isinstance(mapping,dict) else None;validators=[]
            try:
                if not enabled:status='not_run';message='Legacy graph-only evidence; requirement physics not requested'
                elif requirement not in ('supported_flight','landing','headroom','clearance','opening'):status='unsupported';message='No physical adapter for requirement '+str(requirement)
                elif not isinstance(evidence,dict):raise ValueError('Missing typed requirement evidence')
                elif requirement in ('supported_flight','landing'):
                    ids=evidence.get('parts',[])
                    if not isinstance(ids,list) or not ids or len(ids)!=len(set(ids)) or any(p not in parts for p in ids):raise ValueError('Known unique part witnesses required')
                    for pid in ids:
                        p=parts[pid]
                        if not any(vid in volumes and _intersects(_bounds(p),(volumes[vid]['min'],volumes[vid]['max'])) for vid in edgevols):
                            # Landing contact is at the feet plane, so test its
                            # registered flight edge below rather than claiming
                            # positive solid/body overlap as evidence.
                            if requirement!='landing' or not any(pid==a.get('landing') and a.get('stair',a.get('ramp')) in mapping.get('supported_flight',{}).get('parts',[]) for a in scene.get('stair_access',[])+scene.get('ramp_access',[])):
                                raise ValueError('Part witness does not belong to this edge: '+pid)
                        if not supported(pid):raise ValueError('Witness has no physical support path: '+pid)
                        relevant=[fault for fault in support_faults if pid in fault]
                        if relevant:raise ValueError('; '.join(relevant))
                    if requirement=='supported_flight':
                        if any(parts[p]['kind'] not in ('stair','ramp') for p in ids):raise ValueError('Supported flight requires a real stair/ramp adapter')
                        spans=sorted((parts[p]['origin'][2],sum((parts[p]['origin'][2],parts[p]['size'][2]))) for p in ids)
                        end=edge_lo
                        for a,b in spans:
                            if abs(a-end)>EPS:raise ValueError('Flight witness belongs to another level or has a vertical gap')
                            end=b
                        if abs(end-edge_hi)>EPS or edge_hi-edge_lo<=EPS:raise ValueError('Flights do not span this selected edge levels')
                        for pid in ids:
                            matched=[a for a in scene.get('stair_access',[])+scene.get('ramp_access',[]) if a.get('stair',a.get('ramp'))==pid]
                            if not matched:raise ValueError('Flight has no declared landing relation')
                            if any(relation_results.get('stair_landing:'+pid+'->'+a['landing'],{}).get('status')!='passed' for a in matched):raise ValueError('Flight landing relation geometry failed')
                            flight=parts[pid];x,y,z=flight['origin'];w,d,h=flight['size'];samples=[]
                            for vid in edgevols:
                                v=volumes[vid]
                                for point in v.get('walking_path',[]):
                                    if x+EPS<point[0]<x+w-EPS and y+EPS<point[1]<y+d-EPS:
                                        offset=v.get('walking_offset')
                                        if type(offset) not in (int,float) or not math.isfinite(offset) or offset<=0:raise ValueError('Flight traversal needs explicit positive walking_offset')
                                        q=(point[1]-y)/d
                                        if flight.get('parameters',{}).get('reverse',False):q=1-q
                                        surface=z+h*q if flight['kind']=='ramp' else z+h*(min(flight['parameters']['steps']-1,int(q*flight['parameters']['steps']))+1)/flight['parameters']['steps']
                                        if abs(point[2]-offset-surface)>EPS:raise ValueError('Walking path is detached from actual flight surface: '+pid)
                                        samples.append(q)
                            if not samples or min(samples)>.1 or max(samples)<.9:raise ValueError('Walking path does not cover both ends of the flight: '+pid)
                        validators=['support_path','support_contact','flight_level_span','landing_relation']
                    else:
                        if any(parts[p]['kind'] not in ('slab','landing') for p in ids):raise ValueError('Landing requires a real slab/landing')
                        flights=mapping.get('supported_flight',{}).get('parts',[])
                        if not flights:raise ValueError('Landing must bind to this edge supported_flight witnesses')
                        if not all(any(a.get('stair',a.get('ramp'))==f and a.get('landing') in ids for a in scene.get('stair_access',[])+scene.get('ramp_access',[])) for f in flights):raise ValueError('Landing witness is unrelated to this edge flight')
                        if any(relation_results.get('stair_landing:'+f+'->'+p,{}).get('status')!='passed' for f in flights for p in ids if any(a.get('stair',a.get('ramp'))==f and a.get('landing')==p for a in scene.get('stair_access',[])+scene.get('ramp_access',[]))):raise ValueError('Landing relation geometry failed')
                        validators=['support_path','support_contact','landing_relation']
                    message='Physical part witnesses belong to this edge and its support/landing relations'
                elif requirement in ('headroom','clearance'):
                    ids=evidence.get('access_volumes',[])
                    if not ids or len(ids)!=len(set(ids)) or set(ids)!=set(edgevols):raise ValueError('Access evidence must cover exactly the mapped edge volumes')
                    minimum=evidence.get('min_height',1.8)
                    if type(minimum) not in (int,float) or not math.isfinite(minimum) or minimum<1.8:raise ValueError('Conceptual walking clearance minimum must be at least 1.8 m')
                    for vid in ids:
                        v=volumes[vid];errs=profile_errors(v,nodes)
                        if errs:raise ValueError(vid+': '+'; '.join(errs))
                        height=v['body_above']+v['body_below'] if 'walking_path' in v else v['max'][2]-v['min'][2]
                        if height<minimum-EPS:raise ValueError('Insufficient declared body height: '+vid)
                        for p in parts.values():
                            if _intersects(_bounds(p),(v['min'],v['max'])) and volume_obstructed(p,v):raise ValueError('Occupied access witness '+vid+': '+p['id'])
                    validators=['body_profile','solid_clearance'];message='Mapped edge walking envelopes are clear at the declared conceptual height'
                elif requirement=='opening':
                    ids=evidence.get('openings',[])
                    if not ids or len(ids)!=len(set(ids)) or any(o not in openings for o in ids):raise ValueError('Registered opening witnesses required')
                    for oid in ids:
                        o=openings[oid];errors=opening_errors(dict(scene,openings=[o]))
                        if errors:raise ValueError('; '.join(errors))
                        if not any(vid in volumes and _intersects(_bounds(o),(volumes[vid]['min'],volumes[vid]['max'])) for vid in edgevols):raise ValueError('Opening witness does not intersect this edge: '+oid)
                    validators=['registered_host_opening','edge_intersection'];message='Registered clear openings intersect this edge access route'
                else:status='unsupported';message='No physical adapter for requirement '+str(requirement)
            except (KeyError,ValueError,TypeError,IndexError) as exc:status='failed';message=str(exc)
            checks.append(dict(id=key+'/'+str(requirement),edge_id=key,requirement=requirement,status=status,critical=True,evidence=evidence,validators=validators,message=message))
        if enabled and isinstance(mapping,dict):
            for extra in set(mapping)-set(expected):
                checks.append(dict(id=key+'/'+str(extra),edge_id=key,requirement=extra,status='failed',critical=True,evidence=mapping[extra],validators=[],message='Evidence names a requirement absent from selected edge'))
    return checks


def program_checks(scene):
    """Small observable component-set adapter, distinct from semantic labels."""
    parts={p['id']:p for p in scene.get('parts',[])};assemblies={a['id']:a for a in scene.get('assemblies',[])};checks=[]
    material=scene.get('materialized_design',{})
    for key,zone in material.get('zones',{}).items():
        contract=zone.get('program_contract');status='not_run';message='Semantic program labels only; no function or recognition claim'
        if contract is not None:
            try:
                if contract.get('adapter')!='component_set':status='unsupported';message='Unknown program evidence adapter'
                else:
                    members=material['nodes'][key];required=contract.get('required_kinds',[])
                    if not required:raise ValueError('Program contract requires observable component kinds')
                    if set(required)-{parts[p]['kind'] for p in members}:raise ValueError('Missing required program component kinds')
                    for aid in contract.get('assemblies',[]):
                        if aid not in assemblies or not set(assemblies[aid]['members'])<=set(members):raise ValueError('Program assembly is absent or outside this node')
                    status='passed';message='Required component kinds and assembly membership verified; operational function and image recognition unverified'
            except (KeyError,TypeError,ValueError) as exc:status='failed';message=str(exc)
        checks.append(dict(node_id=key,status=status,critical=True,message=message,contract=contract))
    return checks
