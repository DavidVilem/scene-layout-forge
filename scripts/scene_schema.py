"""Preflight shape checks before geometric validation. Standard library only."""
import math

def finite(value):
    try:return type(value) in (int,float) and math.isfinite(value)
    except OverflowError:return False

def shape_errors(data,kinds):
    if not isinstance(data,dict):return ['Scene must be an object']
    errors=[]
    from annotation_policy import errors as annotation_errors
    errors.extend(annotation_errors(data))
    if type(data.get("schema_version",1))!=int or data.get("schema_version",1) not in (1,2):errors.append("Unsupported schema version")
    if type(data.get('workflow_version',2))!=int or data.get('workflow_version',2) not in (2,3,4):errors.append('Unsupported workflow version')
    if data.get('workflow_version')==4 and (data.get('schema_version')!=2 or data.get('validation_policy')!='strict' or not isinstance(data.get('architecture_contract'),dict)):
        errors.append('workflow v4 requires strict schema-v2 and an architectural contract')
    delivery=data.get('delivery_counts',{})
    if not isinstance(delivery,dict) or any(not isinstance(k,str) or not k.strip() or type(v)!=int or v<0 for k,v in delivery.items()):errors.append('delivery_counts: named nonnegative integers required')
    def named(value,path):
        if not isinstance(value,str) or not value.strip():errors.append(path+': nonempty string required')
    def vector(value,path):
        if not isinstance(value,(list,tuple)) or len(value)!=3 or not all(finite(v) for v in value):errors.append(path+': three finite numbers required')
    def json_numbers(value,path,depth=0):
        if depth>32:errors.append(path+': nesting exceeds 32 levels');return
        if isinstance(value,float) and not math.isfinite(value):errors.append(path+': finite number required')
        elif isinstance(value,dict):
            for k,v in value.items():json_numbers(v,path+'.'+str(k),depth+1)
        elif isinstance(value,(list,tuple)):
            for i,v in enumerate(value):json_numbers(v,path+f'[{i}]',depth+1)
    for field in ['parts','connections','attachments','bearings','stair_access','ramp_access','labels','route_obstacles','clearance_pairs']:
        value=data.get(field,[])
        if not isinstance(value,list):errors.append(field+': array required');continue
        for i,item in enumerate(value):
            path=f'{field}[{i}]'
            if field=='route_obstacles':named(item,path);continue
            if field=='clearance_pairs':
                if not isinstance(item,(list,tuple)) or len(item)!=2:errors.append(path+': two part IDs required')
                else:
                    for entry in item:named(entry,path)
                continue
            if not isinstance(item,dict):errors.append(path+': object required');continue
            if field=='parts':
                named(item.get('id'),path+'.id');kind=item.get('kind')
                if not isinstance(kind,str) or kind not in kinds:errors.append(path+': unknown component kind')
                for key in ['origin','size']:vector(item.get(key),path+'.'+key)
                if item.get('parent') is not None:named(item['parent'],path+'.parent')
                ports=item.get('ports',{})
                if not isinstance(ports,dict):errors.append(path+'.ports: object required')
                else:
                    for key,point in ports.items():named(key,path+'.ports');vector(point,path+'.ports.'+str(key))
                params=item.get('parameters',{})
                if not isinstance(params,dict):errors.append(path+'.parameters: object required');continue
                json_numbers(params,path+'.parameters')
                if 'reverse' in params and type(params['reverse'])!=bool:errors.append(path+'.reverse: boolean required')
                if 'helmet' in params and type(params['helmet'])!=bool:errors.append(path+'.helmet: boolean required')
                if 'inspection_hatch' in params and type(params['inspection_hatch'])!=bool:errors.append(path+'.inspection_hatch: boolean required')
                if 'seam_bolts' in params and (type(params['seam_bolts'])!=int or not 0<=params['seam_bolts']<=64):errors.append(path+'.seam_bolts: integer 0..64 required')
                for endpoint in ['start','end']:
                    if endpoint in params:vector(params[endpoint],path+'.'+endpoint)
                if 'panel_size' in params:
                    pair=params['panel_size']
                    if not isinstance(pair,(list,tuple)) or len(pair)!=2 or not all(finite(v) and v>0 for v in pair):errors.append(path+'.panel_size: two positive finite numbers required')
                if 'panel_faces' in params and (params['panel_faces'] not in ('front','all') or kind!='wall' or 'panel_size' not in params):
                    errors.append(path+'.panel_faces: supported wall panel grid required')
                if 'grid_spacing' in params and (not finite(params['grid_spacing']) or params['grid_spacing']<=0):errors.append(path+'.grid_spacing: positive finite number required')
                if 'axis' in params:
                    vector(params['axis'],path+'.axis')
                    if isinstance(params['axis'],(list,tuple)) and len(params['axis'])==3 and all(finite(v) for v in params['axis']) and sum(v*v for v in params['axis'])==0:errors.append(path+'.axis: nonzero axis required')
                if isinstance(kind,str) and kind in {'pipe','conduit'}:
                    points=params.get('points')
                    if not isinstance(points,list) or len(points)<2:errors.append(path+'.points: at least two world-space points required')
                    else:
                        for point in points:vector(point,path+'.points')
                if 'radius' in params and (not finite(params['radius']) or params['radius']<=0):errors.append(path+'.radius: positive finite number required')
            elif field=='attachments':
                for key in ['from','to']:
                    endpoint=item.get(key)
                    if not isinstance(endpoint,str) or endpoint.count(':')!=1 or not all(endpoint.split(':')):errors.append(path+'.'+key+': part:port required')
            elif field=='connections':
                for key in ['from','to']:
                    endpoint=item.get(key)
                    if not isinstance(endpoint,str) or endpoint.count(':')!=1 or not all(endpoint.split(':')):errors.append(path+'.'+key+': part:port required')
                route=item.get('route')
                if not isinstance(route,list) or len(route)<2:errors.append(path+'.route: at least two points required')
                else:
                    for point in route:vector(point,path+'.route')
                if not finite(item.get('radius')) or item['radius']<=0:errors.append(path+'.radius: positive finite number required')
                if 'fittings' in item and type(item['fittings'])!=bool:errors.append(path+'.fittings: boolean required')
            elif field=='labels':
                named(item.get('target'),path+'.target');named(item.get('text'),path+'.text')
                pos=item.get('position')
                if not isinstance(pos,(list,tuple)) or len(pos)!=2 or not all(finite(v) and 0<=v<=1 for v in pos):errors.append(path+'.position: normalized XY required')
            else:
                keys={'bearings':['part','on'],'stair_access':['stair','landing'],'ramp_access':['ramp','landing']}[field]
                for key in keys:named(item.get(key),path+'.'+key)
    if data.get('schema_version',1)==2:
        roots=data.get('grounded',[])
        if not isinstance(roots,list):errors.append('grounded: array required')
        else:
            for root in roots:named(root,'grounded')
        for p in data.get('parts',[]) if isinstance(data.get('parts',[]),list) else []:
            if not isinstance(p,dict):continue
            specs=p.get('interfaces',{})
            if not isinstance(specs,dict):errors.append('interfaces: object required');continue
            for key,spec in specs.items():
                named(key,'interface name')
                if not isinstance(spec,dict):errors.append('interface: object required');continue
                vector(spec.get('anchor'),'interface anchor');vector(spec.get('normal'),'interface normal')
                json_numbers(spec,'interface')
    if 'registered_geometry' in data and type(data['registered_geometry'])!=bool:errors.append('registered_geometry: boolean required')
    mounts=data.get('mounts',[])
    if not isinstance(mounts,list):errors.append('mounts: array required')
    else:
        for c in mounts:
            if not isinstance(c,dict):errors.append('mount: object required');continue
            named(c.get('part'),'mount part');named(c.get('on'),'mount support')
            if c.get('axis') not in ('x','y','z') or type(c.get('side'))!=int or c['side'] not in (-1,1):errors.append('invalid mount orientation')
    contacts=data.get('custom_contacts',[])
    if not isinstance(contacts,list):errors.append('custom_contacts: array required')
    else:
        for c in contacts:
            if not isinstance(c,dict):errors.append('custom contact: object required');continue
            named(c.get('part'),'custom contact part');named(c.get('on'),'custom contact support')
            if not isinstance(c.get('points'),list):errors.append('custom contact points required')
            else:
                for point in c['points']:vector(point,'contact point')
    counts=data.get('expected_counts',{})
    if not isinstance(counts,dict):errors.append('expected_counts: object required')
    else:
        for kind,count in counts.items():
            if kind not in kinds or type(count)!=int or count<0:errors.append('expected_counts: known kind and nonnegative integer required')
    from coherence_validation import contract_shape_errors
    errors.extend(contract_shape_errors(data))
    return errors
