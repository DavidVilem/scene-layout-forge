"""Check that selected spatial graphs were actually realized in scene geometry.

This gate checks identity, allocation, programs and realized access connectivity.
It does not certify structural loads, semantic image recognition or raster fidelity.
"""
import math
from design_variants import verify_selection

GENERIC_ROLES={'box','wall','floor','slab','column','beam','cabinet','room','zone','part','object','equipment','generic'}

def edge_id(edge):
    return edge['kind']+':'+edge['from']+'->'+edge['to']

def _vec(value):
    return isinstance(value,(tuple,list)) and len(value)==3 and all(type(x) in (int,float) and math.isfinite(x) for x in value)

def _contains(lo,hi,padlo,padhi,tol=1e-6):
    return all(lo[k]-tol<=padlo[k] and padhi[k]<=hi[k]+tol for k in range(3))

def realization_errors(scene):
    """Return detailed errors, recomputing selection rather than trusting flags.

    With no design metadata, legacy callers get no new claim/check. Once any
    field is present, the complete selected graph and materialization are required.
    """
    fields=('design_intent','design_selection','materialized_design')
    if not any(key in scene for key in fields):return []
    errors=[]
    try:
        if not all(key in scene for key in fields):raise ValueError('intent, selection and materialization are all required')
        evidence=scene['design_selection']
        selected=verify_selection(scene['design_intent'],evidence['candidates'],evidence)
        material=scene['materialized_design'];nodes=material['nodes'];edges=material['edges'];zones=material['zones']
        if not all(isinstance(v,dict) for v in (material,nodes,edges,zones)):raise ValueError('materialization maps required')
        transform=material['topology_transform'];translation=transform['translation'];scale=transform['scale_xy']
        if not _vec(translation) or type(scale) not in (int,float) or not math.isfinite(scale) or scale<=0:raise ValueError('finite translation and positive uniform XY scale required')
        parts={p['id']:p for p in scene.get('parts',[])}
        if len(parts)!=len(scene.get('parts',[])):raise ValueError('duplicate scene part IDs')
        access={n['id']:n for n in scene.get('access_nodes',[])}
        volumes={v['id']:v for v in scene.get('access_volumes',[])}
        if len(access)!=len(scene.get('access_nodes',[])) or len(volumes)!=len(scene.get('access_volumes',[])):raise ValueError('duplicate access IDs')
        by={n['id']:n for n in selected['nodes']};expected_edges={edge_id(e):e for e in selected['edges']}
        for label,mapping,expected in [('nodes',nodes,by),('zones',zones,by),('edges',edges,expected_edges)]:
            if set(mapping)!=set(expected):errors.append(f'{label}: missing {sorted(set(expected)-set(mapping))}, unknown {sorted(set(mapping)-set(expected))}')
        ownership={};valid_zones={}
        for key,node in by.items():
            try:
                members=nodes[key];zone=zones[key]
                if not isinstance(members,list) or not members or len(set(members))!=len(members):raise ValueError('nonempty unique part mapping required')
                if any(pid not in parts for pid in members):raise ValueError('mapped part ID is absent/stale')
                if zone.get('program')!=node.get('program'):raise ValueError('program differs from selected node')
                lo=zone['min'];hi=zone['max'];anchor=zone['anchor']
                if not all(_vec(v) for v in (lo,hi,anchor)) or any(hi[k]<=lo[k] for k in range(3)):raise ValueError('finite positive allocated zone required')
                expected=[node['center'][k]*(scale if k<2 else 1)+translation[k] for k in range(3)]
                if math.dist(anchor,expected)>1e-5:raise ValueError('anchor violates selected topology transform')
                if not _contains(lo,hi,anchor,anchor):raise ValueError('anchor outside allocated zone')
                if any(abs(anchor[k]-(lo[k]+hi[k])/2)>(hi[k]-lo[k])*.05+1e-5 for k in (0,1)):
                    raise ValueError('zone center does not realize selected anchor')
                for pid in members:
                    if pid in ownership:raise ValueError('part also allocated to '+ownership[pid])
                    ownership[pid]=key;p=parts[pid];end=[p['origin'][k]+p['size'][k] for k in range(3)]
                    if not _contains(lo,hi,p['origin'],end):raise ValueError('mapped part outside allocated zone: '+pid)
                    if p.get('design_node',key)!=key:raise ValueError('part design_node disagrees: '+pid)
                proof=zone.get('program_evidence',[])
                if not isinstance(proof,list) or not proof or any(pid not in members for pid in proof):raise ValueError('mapped semantic program evidence required')
                for pid in proof:
                    p=parts[pid];role=p.get('semantic_role','')
                    if p.get('design_program')!=node.get('program'):raise ValueError('program evidence has wrong program: '+pid)
                    if not isinstance(role,str) or not role.strip() or role.lower() in GENERIC_ROLES:
                        raise ValueError('program evidence requires a specific semantic component role: '+pid)
                a=access[zone['access_node']]
                if not _vec(a.get('position')) or not _contains(lo,hi,a['position'],a['position']):raise ValueError('access node outside allocated zone')
                valid_zones[key]=zone
            except (KeyError,TypeError,ValueError,IndexError) as exc:errors.append('node '+key+': '+str(exc))
        # Uniformly oversized shared allocations cannot mask an unchanged layout.
        for i,a in enumerate(selected['nodes']):
            if a['id'] not in valid_zones:continue
            aa=valid_zones[a['id']]
            for b in selected['nodes'][i+1:]:
                if b['id'] not in valid_zones or a['level']!=b['level']:continue
                bb=valid_zones[b['id']]
                if all(min(aa['max'][k],bb['max'][k])-max(aa['min'][k],bb['min'][k])>1e-5 for k in range(3)):
                    errors.append('allocated zones overlap: '+a['id']+' / '+b['id'])
        for key,edge in expected_edges.items():
            try:
                ids=edges[key]
                if not isinstance(ids,list) or not ids or len(ids)!=len(set(ids)):raise ValueError('nonempty unique access-volume mapping required')
                if any(v not in volumes for v in ids):raise ValueError('access volume ID is absent/stale')
                start=zones[edge['from']]['access_node'];finish=zones[edge['to']]['access_node'];graph={}
                for vid in ids:
                    v=volumes[vid];a,b=v['from'],v['to']
                    if a not in access or b not in access:raise ValueError('volume endpoint access node absent')
                    if not all(_vec(v.get(k)) for k in ('min','max')) or any(v['max'][k]<=v['min'][k] for k in range(3)):raise ValueError('invalid access volume bounds')
                    if any(not _contains(v['min'],v['max'],access[n]['position'],access[n]['position']) for n in (a,b)):
                        raise ValueError('volume is detached from its endpoint position')
                    graph.setdefault(a,set()).add(b);graph.setdefault(b,set()).add(a)
                reached={start};queue=[start]
                while queue:
                    for n in graph.get(queue.pop(),()):
                        if n not in reached:reached.add(n);queue.append(n)
                if finish not in reached:raise ValueError('mapped routes do not connect selected endpoint zones')
                if set(graph)-reached:raise ValueError('mapped routes contain an unrelated disconnected component')
            except (KeyError,TypeError,ValueError,IndexError) as exc:errors.append('edge '+key+': '+str(exc))
    except (KeyError,TypeError,ValueError,IndexError) as exc:errors.append('design realization: '+str(exc))
    if not errors:
        from requirement_contracts import requirement_checks,program_checks
        for check in requirement_checks(scene,selected):
            if check['status'] in ('failed','unsupported'):
                errors.append('edge '+check['edge_id']+' requirement '+str(check['requirement'])+': '+check['message'])
        for check in program_checks(scene):
            if check['status'] in ('failed','unsupported'):errors.append('program '+check['node_id']+': '+check['message'])
    return errors

def realization_report(scene):
    if not any(k in scene for k in ('design_intent','design_selection','materialized_design')):
        return {'status':'not_applicable','errors':[],'scope':'No design-selection contract supplied'}
    errors=realization_errors(scene)
    checks=[];programs=[]
    try:
        from requirement_contracts import requirement_checks,program_checks
        selected=verify_selection(scene['design_intent'],scene['design_selection']['candidates'],scene['design_selection'])
        checks=requirement_checks(scene,selected);programs=program_checks(scene)
    except (KeyError,TypeError,ValueError,IndexError):pass
    return {'status':'failed' if errors else 'passed','errors':errors,'requirements':checks,'programs':programs,
            'requirement_coverage':{'declared':sum(len(e.get('requires',[])) for e in selected['edges']) if checks else 0,'reported':len(checks)},
            'compatibility':'strict requirements-v1' if scene.get('validation_policy')=='strict' else 'legacy graph evidence; see individual requirement status',
            'scope':'selected topology allocation, actual access graph and individually reported physical requirements',
            'limits':['semantic roles are declared, not visually recognized','physical collisions/supports and final raster require independent checks']}
