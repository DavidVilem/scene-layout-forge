"""Rigid assembly placement, actual box openings and non-destructive cutaway views.

Geometry helpers, not a dynamics solver. Physical and display scenes remain distinct.
No hidden geometry is declared validated by compiling a display view.
"""
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import itertools
import json
import math

BOX_KINDS={'wall','slab','footing','beam','column','landing'}
EPS=1e-8

def stair_obstructs_volume(part, volume):
    """Narrow-phase conservative walk-volume check against native stair treads/rails.

    Mirrors components.circulation: thin step boxes, diagonal edge stringers,
    rail posts and two sloping handrails. Does not treat the entire stair AABB
    as filled. Unsupported/malformed stair inputs fail closed.
    """
    try:
        if part['kind']!='stair':raise ValueError('native stair required')
        x,y,z=part['origin'];w,d,h=part['size'];n=part['parameters']['steps']
        if type(n)!=int or n<1 or min(w,d,h)<=0:return True
        lo=_vec(volume['min']);hi=_vec(volume['max']);reverse=part['parameters'].get('reverse',False)
        def box_hit(a,b):return all(min(hi[k],b[k])-max(lo[k],a[k])>EPS for k in range(3))
        def segment_hit(a,b,r):
            t0,t1=0.,1.
            for k in range(3):
                delta=b[k]-a[k];low=lo[k]-r;high=hi[k]+r
                if abs(delta)<EPS:
                    if not low<=a[k]<=high:return False
                else:
                    p,q=sorted(((low-a[k])/delta,(high-a[k])/delta));t0=max(t0,p);t1=min(t1,q)
            return t1-t0>EPS
        rise=h/n;tread=d/n
        for i in range(n):
            yy=y+(n-1-i if reverse else i)*tread
            if box_hit([x,yy,z+i*rise],[x+w,yy+tread,z+(i+1)*rise]):return True
        lowy,highy=(y+d,y) if reverse else (y,y+d)
        for xx in (x,x+w):
            if segment_hit([xx,lowy,z+.05],[xx,highy,z+h-.05],.045):return True
            a=[xx,lowy,z+rise];b=[xx,highy,z+h]
            posts=max(1,math.ceil(math.dist(a,b)/.8))
            for i in range(posts+1):
                p=[a[k]+(b[k]-a[k])*i/posts for k in range(3)]
                if segment_hit(p,[p[0],p[1],p[2]+1],.022):return True
            for dz in (.5,1):
                if segment_hit([a[0],a[1],a[2]+dz],[b[0],b[1],b[2]+dz],.025):return True
        return False
    except (KeyError,ValueError,TypeError,IndexError):return True

def _vec(value):
    if not isinstance(value,(list,tuple)) or len(value)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) for v in value):
        raise ValueError('finite XYZ required')
    return list(value)

@dataclass(frozen=True)
class RigidTransform:
    translation: tuple=(0,0,0)
    yaw: float=0

    def __post_init__(self):
        _vec(self.translation)
        if type(self.yaw) not in (int,float) or not math.isfinite(self.yaw):raise ValueError('finite yaw required')

    def vector(self,value):
        x,y,z=_vec(value);angle=math.radians(self.yaw);c=math.cos(angle);s=math.sin(angle)
        return [c*x-s*y,s*x+c*y,z]

    def point(self,value):return [a+b for a,b in zip(self.vector(value),self.translation)]

    def inverse(self):
        inverse=RigidTransform(yaw=-self.yaw)
        return RigidTransform(tuple(-v for v in inverse.vector(self.translation)),-self.yaw)

    def compose(self,child):
        """Return parent(self) after child, including rotation of child translation."""
        return RigidTransform(tuple(self.point(child.translation)),self.yaw+child.yaw)

    def bounds(self,origin,size):
        o=_vec(origin);s=_vec(size)
        corners=[self.point([o[k]+s[k]*b[k] for k in range(3)]) for b in itertools.product((0,1),repeat=3)]
        lo=[min(v[k] for v in corners) for k in range(3)];hi=[max(v[k] for v in corners) for k in range(3)]
        return lo,[hi[k]-lo[k] for k in range(3)]

def _box(id,kind,origin,size,**extra):
    return dict(id=id,kind=kind,origin=list(origin),size=list(size),**extra)

def cut_host(host,openings,normal_axis):
    """Subtract through-openings from a native rectangular host into disjoint solids.

    Opening coordinates are world coordinates. Cell IDs are deterministic, and
    records preserve the logical host even though the solid is split. The caller
    must remap physical support relations to the resulting fragments.
    """
    if host.get('kind') not in BOX_KINDS or host.get('parameters'):raise ValueError('opening host needs a plain rectangular adapter')
    if not isinstance(host.get('id'),str) or not host['id']:raise ValueError('host ID required')
    if normal_axis not in ('x','y','z'):raise ValueError('normal_axis must be x, y or z')
    axis='xyz'.index(normal_axis);lo=_vec(host['origin']);size=_vec(host['size'])
    if min(size)<=0:raise ValueError('positive host size required')
    hi=[lo[k]+size[k] for k in range(3)];cuts=[];seen=set()
    for opening in openings:
        name=opening.get('id')
        if not isinstance(name,str) or not name or name in seen:raise ValueError('unique opening ID required')
        seen.add(name);a=_vec(opening['origin']);s=_vec(opening['size']);b=[a[k]+s[k] for k in range(3)]
        if min(s)<=0:raise ValueError('positive opening size required')
        if a[axis]>lo[axis]+EPS or b[axis]<hi[axis]-EPS:raise ValueError('opening must pass through host thickness')
        if any(a[k]<lo[k]-EPS or b[k]>hi[k]+EPS for k in range(3) if k!=axis):raise ValueError('opening outside host face')
        a[axis]=lo[axis];b[axis]=hi[axis]
        record=deepcopy(opening);record.update(host=host['id'],origin=a,size=[b[k]-a[k] for k in range(3)],normal_axis=normal_axis)
        cuts.append(record)
    coordinates=[sorted({lo[k],hi[k]}|{v for c in cuts for v in (c['origin'][k],c['origin'][k]+c['size'][k])}) for k in range(3)]
    if math.prod(len(c)-1 for c in coordinates)>4096:raise ValueError('opening partition exceeds 4096 cells')
    parts=[]
    for cells in itertools.product(*(list(zip(c[:-1],c[1:])) for c in coordinates)):
        a=[c[0] for c in cells];b=[c[1] for c in cells];mid=[(a[k]+b[k])/2 for k in range(3)]
        if any(all(c['origin'][k]-EPS<=mid[k]<=c['origin'][k]+c['size'][k]+EPS for k in range(3)) for c in cuts):continue
        p=deepcopy(host);p.update(id=f'{host["id"]}/cell-{len(parts)}',origin=a,size=[b[k]-a[k] for k in range(3)],host_id=host['id'])
        p.pop('ports',None);p.pop('interfaces',None);parts.append(p)
    if not parts:raise ValueError('openings remove the complete host')
    return {'parts':parts,'hosts':[dict(id=host['id'],kind=host['kind'],origin=lo,size=size,fragments=[p['id'] for p in parts])],'openings':cuts}

def opening_errors(data):
    """Check host records, fill fit and absence of solid fragments inside openings."""
    parts={p['id']:p for p in data.get('parts',[])};hosts={h['id']:h for h in data.get('hosts',[])};errors=[]
    for c in data.get('openings',[]):
        try:
            h=hosts[c['host']];a=_vec(c['origin']);size=_vec(c['size']);b=[a[k]+size[k] for k in range(3)]
            if min(size)<=0:raise ValueError('positive opening size required')
            ho=_vec(h['origin']);hs=_vec(h['size']);axis='xyz'.index(c['normal_axis'])
            if any(a[k]<ho[k]-EPS or b[k]>ho[k]+hs[k]+EPS for k in range(3)):raise ValueError('opening outside logical host')
            if abs(a[axis]-ho[axis])>EPS or abs(b[axis]-ho[axis]-hs[axis])>EPS:raise ValueError('opening is not through host')
            if not h['fragments']:raise ValueError('host has no solid fragments')
            for pid in h['fragments']:
                p=parts[pid];o=p['origin'];end=[o[k]+p['size'][k] for k in range(3)]
                if all(min(b[k],end[k])-max(a[k],o[k])>EPS for k in range(3)):raise ValueError('solid fragment obstructs opening')
            if c.get('filled_by'):
                fill=parts[c['filled_by']];o=fill['origin'];end=[o[k]+fill['size'][k] for k in range(3)]
                if any(o[k]<a[k]-EPS or end[k]>b[k]+EPS for k in range(3)):raise ValueError('fill does not fit opening')
        except (ValueError,KeyError,TypeError) as exc:errors.append(f'opening {c.get("id")}: {exc}')
    return errors

def _bake(part,transform):
    """Bake an existing adapter, preserving its real defining shape, not its AABB."""
    import numpy as np
    from render_scene import build
    source=deepcopy(part);source.pop('parent',None)
    # Local isolated render has no functional/support validation claim.
    data={'units':'m','schema_version':1,'registered_geometry':source['kind']=='custom','parts':[source]}
    mesh=build(data);points=[];faces=[];edges=[]
    def append(v):points.append(transform.point(np.asarray(v).tolist()));return len(points)-1
    for face,_ in mesh.faces:faces.append([append(v) for v in face])
    for a,b in mesh.edges:edges.append([append(a),append(b)])
    # View-dependent smooth silhouette edges cannot be copied into indexed hard
    # edges without making tube tessellation visible. Faces preserve the shape.
    lo=[min(v[k] for v in points) for k in range(3)];hi=[max(v[k] for v in points) for k in range(3)]
    result=deepcopy(part);result.update(kind='custom',origin=lo,size=[hi[k]-lo[k] for k in range(3)])
    result['parameters']={'adapter':'rigid-baked-'+part['kind'],'vertices':[[v[k]-lo[k] for k in range(3)] for v in points],
        'faces':faces,'edges':edges,'limitations':'rigidly transformed adapter geometry; source functional contracts must be validated separately'}
    result['source_kind']=part['kind'];result['source_part']=deepcopy(part)
    return result

def compose_assembly(scene,transform=RigidTransform(),prefix=''):
    """Place an assembly, preserving relation IDs and route/port coincidence.

    Translation-only scenes retain adapter types. For rotation, featureless
    rectangular solids at quarter turns stay native. All other defining shapes
    are baked from their original adapter. The output is explicitly geometry
    compilation, not a replacement for typed physical validation.
    """
    output=deepcopy(scene);names={p['id']:prefix+p['id'] for p in scene['parts']}
    def ref(value):
        if ':' in value:
            pid,port=value.split(':',1);return names.get(pid,pid)+':'+port
        return names.get(value,value)
    quarter=abs(transform.yaw/90-round(transform.yaw/90))<EPS
    zero=abs(transform.yaw%360)<EPS
    output['parts']=[];baked=[]
    for source in scene['parts']:
        if zero:
            part=deepcopy(source);part['origin']=transform.point(source['origin'])
        elif quarter and source['kind'] in BOX_KINDS and not source.get('parameters'):
            part=deepcopy(source);part['origin'],part['size']=transform.bounds(source['origin'],source['size'])
        else:part=_bake(source,transform);baked.append(names[source['id']])
        part['id']=names[source['id']]
        if part.get('parent'):part['parent']=ref(part['parent'])
        part['ports']={key:[v-part['origin'][k] for k,v in enumerate(transform.point([source['origin'][j]+local[j] for j in range(3)]))] for key,local in source.get('ports',{}).items()}
        if not zero:
            # Analytic source surfaces no longer describe the oriented AABB.
            if part.get('interfaces'):part['source_interfaces']=part.pop('interfaces')
        params=part.get('parameters',{})
        if zero:
            for key in ('points','start','end'):
                if key in params:params[key]=[transform.point(p) for p in params[key]] if key=='points' else transform.point(params[key])
        output['parts'].append(part)
    for key in ('connections','attachments'):
        for item in output.get(key,[]):
            for end in ('from','to'):item[end]=ref(item[end])
            if 'route' in item:item['route']=[transform.point(p) for p in item['route']]
    for key in ('bearings','mounts','custom_contacts','stair_access','ramp_access'):
        for item in output.get(key,[]):
            for name in ('part','on','stair','ramp','landing'):
                if name in item:item[name]=ref(item[name])
            if 'points' in item:item['points']=[transform.point(p) for p in item['points']]
    for key in ('grounded','route_obstacles'):output[key]=[ref(x) for x in output.get(key,[])]
    output['clearance_pairs']=[[ref(a),ref(b)] for a,b in output.get('clearance_pairs',[])]
    for item in output.get('mounts',[]):
        if not zero and item.get('axis') in ('x','y','z'):
            k='xyz'.index(item['axis']);v=[0,0,0];v[k]=1
            normal=transform.vector(v)
            if quarter:
                target=max(range(3),key=lambda i:abs(normal[i]));item['axis']='xyz'[target]
                if normal[target]<0 and item.get('side') in (-1,1):item['side']=-item['side']
            else:item['oriented_normal']=normal;item['validation_limitation']='AABB mounting axis is invalid after non-orthogonal rotation'
    groups=output.get('assemblies',[])+([output['assembly']] if 'assembly' in output else [])
    for group in groups:
        if group.get('id'):group['id']=prefix+group['id']
        for key in ('members','ground_contacts'):group[key]=[ref(v) for v in group.get(key,[])]
        if 'required_clear_volume' in group:
            volume=group['required_clear_volume'];o,s=transform.bounds(volume['origin'],volume['size'])
            volume.update(origin=o,size=s)
            if not quarter:volume['conservative_aabb']=True
    # Host apertures remain native axis-aligned geometry only at quarter turns.
    if (output.get('hosts') or output.get('openings')) and not quarter:
        raise ValueError('non-orthogonal aperture placement needs an oriented opening adapter')
    for host in output.get('hosts',[]):
        host['id']=prefix+host['id'];host['fragments']=[ref(v) for v in host['fragments']]
        host['origin'],host['size']=transform.bounds(host['origin'],host['size'])
    for opening in output.get('openings',[]):
        opening['id']=prefix+opening['id'];opening['host']=prefix+opening['host']
        if opening.get('filled_by'):opening['filled_by']=ref(opening['filled_by'])
        opening['origin'],opening['size']=transform.bounds(opening['origin'],opening['size'])
        v=[0,0,0];v['xyz'.index(opening['normal_axis'])]=1;n=transform.vector(v)
        opening['normal_axis']='xyz'[max(range(3),key=lambda i:abs(n[i]))]
    for part in output['parts']:
        if part.get('host_id'):part['host_id']=prefix+part['host_id']
    source_parts={p['id']:p for p in scene['parts']};placed_parts={p['id']:p for p in output['parts']}
    relation_names={r['id']:prefix+r['id'] for r in scene.get('relations',[]) if r.get('id')}
    def relation_ref(value):
        if value in relation_names:return relation_names[value]
        if ':' in value and '->' in value:
            kind,ends=value.split(':',1);a,b=ends.split('->',1)
            return kind+':'+ref(a)+'->'+ref(b)
        return prefix+value
    for relation in output.get('relations',[]):
        if 'id' in relation:relation['id']=relation_names[relation['id']]
        for name in ('a','b'):
            endpoint=relation.get(name)
            if not isinstance(endpoint,dict):continue
            old_id=endpoint.get('part');endpoint['part']=ref(old_id)
            if old_id in source_parts:
                if 'anchor' in endpoint:
                    world=transform.point([source_parts[old_id]['origin'][k]+endpoint['anchor'][k] for k in range(3)])
                    endpoint['anchor']=[world[k]-placed_parts[ref(old_id)]['origin'][k] for k in range(3)]
                for key in ('normal','axis'):
                    if key in endpoint:endpoint[key]=transform.vector(endpoint[key])
        for key in ('points','normals'):
            if key in relation:relation[key]=[(transform.point if key=='points' else transform.vector)(v) for v in relation[key]]
        for key in ('flight','landing','from','to'):
            if key in relation:relation[key]=ref(relation[key])
        if 'opening' in relation:relation['opening']=prefix+relation['opening']
    for contact in output.get('surface_contacts',[]):
        for key in ('part','on'):
            if key in contact:contact[key]=ref(contact[key])
        if 'id' in contact:contact['id']=prefix+contact['id']
        for key in ('points','normals'):
            if key in contact:contact[key]=[(transform.point if key=='points' else transform.vector)(v) for v in contact[key]]
    surface_names={s['id']:prefix+s['id'] for s in scene.get('ground_surfaces',[])}
    for surface in output.get('ground_surfaces',[]):
        surface['id']=surface_names[surface['id']]
        if 'point' in surface:surface['point']=transform.point(surface['point'])
        if 'normal' in surface:surface['normal']=transform.vector(surface['normal'])
        if 'bounds' in surface:
            bounds=surface['bounds'];lo=bounds['min'];hi=bounds['max'];newlo,size=transform.bounds(lo,[hi[k]-lo[k] for k in range(3)])
            surface['bounds']={'min':newlo,'max':[newlo[k]+size[k] for k in range(3)]}
    for contact in output.get('ground_contacts',[]):
        if not isinstance(contact,dict):raise ValueError('scene ground_contacts must be records; assembly ground contacts belong inside assembly')
        contact['part']=ref(contact['part']);contact['surface']=surface_names.get(contact['surface'],contact['surface'])
        contact['points']=[transform.point(p) for p in contact['points']]
    for witness in output.get('camera_junctions',[]):
        if 'id' in witness:witness['id']=prefix+witness['id']
        witness['owners']=[ref(v) for v in witness.get('owners',[])]
        if 'point' in witness:witness['point']=transform.point(witness['point'])
        if 'relation_id' in witness:witness['relation_id']=relation_ref(witness['relation_id'])
    for node in output.get('access_nodes',[]):
        node['id']=prefix+node['id'];node['position']=transform.point(node['position'])
    for volume in output.get('access_volumes',[]):
        volume['id']=prefix+volume['id']
        for key in ('from','to'):volume[key]=prefix+volume[key]
        oldlo=volume['min'];oldhi=volume['max'];lo,size=transform.bounds(oldlo,[oldhi[k]-oldlo[k] for k in range(3)])
        volume['min']=lo;volume['max']=[lo[k]+size[k] for k in range(3)]
        if 'walking_path' in volume:volume['walking_path']=[transform.point(p) for p in volume['walking_path']]
        if 'traversable_parts' in volume:volume['traversable_parts']=[ref(v) for v in volume['traversable_parts']]
    if 'access_roots' in output:output['access_roots']=[prefix+v for v in output['access_roots']]
    output['placement']={'translation':list(transform.translation),'yaw':transform.yaw,'source_sha256':_digest(scene),'baked_parts':baked,
        'scope':'placed source geometry; rotated analytic checks require an applicable oriented adapter'}
    if baked:
        output['registered_geometry']=True
        if 'expected_counts' in output:
            output['source_expected_counts']=output.pop('expected_counts')
        output['placement']['unverified']=['rotated analytic supports, interfaces and clearances','source kind counts must be checked on the physical source']
    return output

def _digest(data):return hashlib.sha256(json.dumps(data,sort_keys=True,allow_nan=False,separators=(',',':')).encode()).hexdigest()

def compile_cutaway(physical_scene,hide_ids=(),cuts=()):
    """Derive display solids without modifying/removing physical validation data.

    Cuts are axis-aligned clipping planes on rectangular hosts. Arbitrary mesh
    clipping is rejected instead of silently deleting a defining shape.
    """
    ids={p['id'] for p in physical_scene['parts']};hidden=set(hide_ids)
    if hidden-ids:raise ValueError('unknown hidden component')
    clip={}
    for cut in cuts:
        if cut['host'] not in ids or cut['host'] in clip:raise ValueError('unknown or duplicate cut host')
        if cut['axis'] not in ('x','y','z') or cut['keep'] not in ('lower','upper'):raise ValueError('invalid cut plane')
        if type(cut['value']) not in (int,float) or not math.isfinite(cut['value']):raise ValueError('finite cut plane required')
        clip[cut['host']]=cut
    parts=[]
    for source in physical_scene['parts']:
        if source['id'] in hidden:continue
        part=deepcopy(source)
        if part['id'] in clip:
            if part['kind'] not in BOX_KINDS or part.get('parameters'):raise ValueError('cutaway requires plain rectangular host; custom clipping unsupported')
            c=clip[part['id']];k='xyz'.index(c['axis']);lo=part['origin'][k];hi=lo+part['size'][k]
            if not lo+EPS<c['value']<hi-EPS:raise ValueError('cut plane must intersect host interior')
            if c['keep']=='lower':part['size'][k]=c['value']-lo
            else:part['origin'][k]=c['value'];part['size'][k]=hi-c['value']
        if part.get('parent') in hidden:part.pop('parent')
        # Ports on uncut parts remain available to render surviving routes.
        if part['id'] in clip:part.pop('ports',None);part.pop('interfaces',None)
        parts.append(part)
    visible={p['id'] for p in parts};connections=[];omitted=[]
    for connection in physical_scene.get('connections',[]):
        endpoints={connection[end].split(':',1)[0] for end in ('from','to')}
        if endpoints<=visible and not endpoints.intersection(clip):connections.append(deepcopy(connection))
        else:omitted.append([connection['from'],connection['to']])
    result={'units':physical_scene.get('units','m'),'schema_version':1,'registered_geometry':physical_scene.get('registered_geometry',False),
        'parts':parts,'connections':connections,
        'representation':{'type':'cutaway','physical_sha256':_digest(physical_scene),'hidden':sorted(hidden),'cuts':deepcopy(list(cuts)),
            'omitted_connections':omitted,
            'validation_scope':'display geometry only; validate the complete physical scene independently'}}
    if 'light_material_plan' in physical_scene:
        result['light_material_plan']=deepcopy(physical_scene['light_material_plan'])
        result['light_material_plan']['materials']={k:v for k,v in result['light_material_plan'].get('materials',{}).items() if k in visible}
    return result

def bed(id='bed',width=1,depth=2,height=.55):
    """Recognizable bed assembly: four legs, frame, mattress and headboard."""
    if min(width,depth,height)<=.2:raise ValueError('bed dimensions too small')
    t=.08;legs=[];parts=[];bearings=[]
    for i,(x,y) in enumerate(itertools.product((0,width-t),(0,depth-t))):
        name=f'{id}/leg-{i}';parts.append(_box(name,'column',[x,y,0],[t,t,height-.12]));legs.append(name)
    frame=id+'/frame';parts.append(_box(frame,'slab',[0,0,height-.12],[width,depth,.12]))
    bearings.extend({'part':frame,'on':name} for name in legs)
    parts.append(_box(id+'/mattress','slab',[.04,.04,height],[width-.08,depth-.12,.16]));bearings.append({'part':id+'/mattress','on':frame})
    parts.append(_box(id+'/headboard','wall',[0,depth-.06,height],[width,.06,.55]));bearings.append({'part':id+'/headboard','on':frame})
    return {'units':'m','parts':parts,'bearings':bearings,'assembly':{'id':id,'role':'bed','members':[p['id'] for p in parts],'ground_contacts':legs}}

def workbench(id='workbench',width=2,depth=.8,height=.9):
    if min(width,depth,height)<=.2:raise ValueError('workbench dimensions too small')
    t=.08;parts=[];legs=[]
    for i,(x,y) in enumerate(itertools.product((0,width-t),(0,depth-t))):
        name=f'{id}/leg-{i}';parts.append(_box(name,'column',[x,y,0],[t,t,height-.1]));legs.append(name)
    top=id+'/top';parts.append(_box(top,'slab',[0,0,height-.1],[width,depth,.1]))
    return {'units':'m','parts':parts,'bearings':[{'part':top,'on':p} for p in legs],
        'assembly':{'id':id,'role':'workbench','members':[p['id'] for p in parts],'ground_contacts':legs}}

def storage_rack(id='rack',width=2,depth=.7,height=1.9,shelves=3,loaded=True):
    """Open rack with independent uprights, supported shelves and optional crates.

    Every contact is explicit. Capacity, anchorage and seismic behavior are not
    inferred from the conceptual geometry.
    """
    if min(width,depth)<.4 or height<.8 or type(shelves)!=int or not 2<=shelves<=5:
        raise ValueError('rack requires positive usable dimensions and 2..5 shelves')
    t=.08;parts=[];uprights=[];mounts=[];bearings=[]
    for i,(x,y) in enumerate(itertools.product((0,width-t),(0,depth-t))):
        name=f'{id}/upright-{i}';parts.append(_box(name,'column',[x,y,0],[t,t,height]));uprights.append(name)
    for j in range(shelves):
        z=.25+j*(height-.5)/(shelves-1);name=f'{id}/shelf-{j}'
        parts.append(_box(name,'slab',[t,0,z],[width-2*t,depth,t]))
        for i,upright in enumerate(uprights):mounts.append({'part':name,'on':upright,'axis':'x','side':1 if i<2 else -1})
        if loaded:
            for k in range(2):
                box=f'{id}/crate-{j}-{k}'
                parts.append(_box(box,'cabinet',[t+.08+k*(width-2*t)/2,.08,z+t],[(width-2*t)/2-.16,depth-.16,.22],semantic_role='stored_supply_container'))
                bearings.append({'part':box,'on':name})
    return {'units':'m','parts':parts,'bearings':bearings,'mounts':mounts,
        'assembly':{'id':id,'role':'storage_rack','members':[p['id'] for p in parts],'ground_contacts':uprights,
                    'limitations':'geometric shelf contacts only; capacity and anchorage unverified'}}

def elevator_shaft(id='lift',width=2.4,depth=2.4,height=18,cabin_z=.2):
    """Continuous guide rails and ONE cabin; floor penetrations are caller-owned."""
    if min(width,depth)<1 or height<3 or not 0<=cabin_z<=height-2.5:raise ValueError('invalid shaft/cabin dimensions')
    t=.1;parts=[]
    for i,x in enumerate((0,width-t)):parts.append(_box(f'{id}/guide-{i}','column',[x,depth/2,0],[t,t,height]))
    parts.append(_box(id+'/cabin-floor','slab',[.15,.15,cabin_z],[width-.3,depth-.3,.1]))
    for side,x in enumerate((.15,width-.25)):parts.append(_box(f'{id}/cabin-side-{side}','wall',[x,.15,cabin_z+.1],[.1,depth-.3,2.2]))
    parts.append(_box(id+'/cabin-back','wall',[.25,depth-.25,cabin_z+.1],[width-.5,.1,2.2]))
    parts.append(_box(id+'/cabin-roof','slab',[.15,.15,cabin_z+2.3],[width-.3,depth-.3,.1]))
    return {'units':'m','parts':parts,'assembly':{'id':id,'role':'elevator_shaft','members':[p['id'] for p in parts],
        'required_clear_volume':{'origin':[.1,.1,0],'size':[width-.2,depth-.2,height]},
        'limitations':'conceptual guide rails and cabin; suspension, drives, landing doors and floor openings require separate declared assemblies'}}
