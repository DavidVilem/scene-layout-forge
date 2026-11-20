"""Version-2 conceptual interfaces and support coverage; not engineering analysis."""
import math

TOL=1e-6
SUPPORTED={'vessel','pump','manifold','cabinet','column','beam','landing','stair','ramp','worker','footing','slab','railing','custom','wall'}
def vector(x):
    if not isinstance(x,(list,tuple)) or len(x)!=3 or any(type(v) not in (float,int) or not math.isfinite(v) for v in x):
        raise ValueError('three finite coordinates required')
    return list(x)
def unit(x):
    x=vector(x);n=math.sqrt(sum(v*v for v in x))
    if abs(n-1)>TOL:raise ValueError('unit normal required')
    return x
def surface(p,point,normal):
    """Check interface against the surface actually used by these adapters."""
    x,y,z=point;w,d,h=p['size'];kind=p['kind'];axis=None
    if kind=='vessel':
        axis=2;center=[w/2,d/2,h/12];length=h*35/36-h/12;radius=min(w,d)/2
    elif kind=='manifold':axis=0;center=[0,d/2,h/2];length=w;radius=min(d,h)/2
    elif kind=='pump':axis=1;center=[w*.25,d*.25,h*.5];length=d*.45;radius=min(h*.3,d*.3,w*.24)
    elif kind in {'cabinet','column','beam','landing','slab','footing'}:
        for a in range(3):
            for sign,bound in [(-1,0),(1,p['size'][a])]:
                expected=[0,0,0];expected[a]=sign
                if abs(point[a]-bound)<TOL and math.dist(normal,expected)<TOL and all(-TOL<=point[i]<=p['size'][i]+TOL for i in range(3)):
                    return True
        return False
    else:raise ValueError('surface adapter unsupported: '+kind)
    radial=[i for i in range(3) if i!=axis]
    delta=[point[i]-center[i] for i in range(3)];rr=math.sqrt(sum(delta[i]**2 for i in radial))
    if -TOL<=delta[axis]<=length+TOL and abs(rr-radius)<TOL:
        expected=[0,0,0]
        for i in radial:expected[i]=delta[i]/radius
        if math.dist(normal,expected)<TOL:return True
    for sign,end in [(-1,0),(1,length)]:
        expected=[0,0,0];expected[axis]=sign
        if abs(delta[axis]-end)<TOL and rr<=radius+TOL and math.dist(normal,expected)<TOL:return True
    return False

def add_interface(part,name,anchor,normal,diameter,role,medium='water',extension=.12,termination=None):
    """One definition drives port location, visible nozzle and checks."""
    normal=unit(normal);anchor=vector(anchor)
    spec=dict(anchor=anchor,normal=normal,diameter=diameter,role=role,medium=medium,extension=extension)
    if termination:spec['termination']=termination
    part.setdefault('interfaces',{})[name]=spec
    part.setdefault('ports',{})[name]=[a+extension*n for a,n in zip(anchor,normal)]
    return part

def interface_errors(data):
    if data.get('schema_version',1)!=2:return []
    errors=[];parts={p['id']:p for p in data['parts']};interfaces={};uses={}
    for p in parts.values():
        specs=p.get('interfaces',{})
        if not isinstance(specs,dict):errors.append(p['id']+': interfaces must be object');continue
        if set(p.get('ports',{}))!=set(specs):errors.append(p['id']+': every port requires a typed interface')
        for name,s in specs.items():
            key=p['id']+':'+name
            try:
                a=vector(s['anchor']);n=unit(s['normal']);diam=s['diameter'];ext=s['extension']
                if type(diam) not in (float,int) or not math.isfinite(diam) or diam<=0:raise ValueError('positive diameter required')
                if type(ext) not in (float,int) or not math.isfinite(ext) or ext<=0:raise ValueError('positive nozzle extension required')
                if s['role'] not in {'inlet','outlet','bidirectional'}:raise ValueError('unknown flow role')
                if not isinstance(s['medium'],str) or not s['medium']:raise ValueError('medium required')
                if p['kind'] not in {'vessel','pump','manifold'}:raise ValueError('fluid interfaces require a supported fluid component')
                if not surface(p,a,n):raise ValueError('anchor/normal does not match component surface')
                if math.dist(p['ports'][name],[x+ext*y for x,y in zip(a,n)])>TOL:raise ValueError('port differs from generated nozzle end')
                if s.get('termination') not in {None,'cap','external'}:raise ValueError('unknown termination')
                interfaces[key]=s;uses[key]=0
            except (ValueError,KeyError,TypeError) as e:errors.append(key+': '+str(e))
    for i,link in enumerate(data.get('connections',[])):
        tag=f'connection[{i}] {link["from"]} -> {link["to"]}'
        try:
            a=interfaces[link['from']];b=interfaces[link['to']]
            uses[link['from']]+=1;uses[link['to']]+=1
            if a['medium']!=b['medium']:errors.append(tag+': incompatible medium')
            if a['role']=='inlet' or b['role']=='outlet':errors.append(tag+': reversed flow roles')
            if abs(a['diameter']-2*link['radius'])>TOL or abs(b['diameter']-2*link['radius'])>TOL:errors.append(tag+': diameter mismatch; model a transition explicitly')
            route=link['route']
            for spec,start,end in [(a,route[0],route[1]),(b,route[-1],route[-2])]:
                direction=[y-x for x,y in zip(start,end)];length=math.sqrt(sum(x*x for x in direction))
                if length<TOL or math.dist([x/length for x in direction],spec['normal'])>1e-4:errors.append(tag+': route not tangent to interface normal')
        except (KeyError,TypeError,ValueError):errors.append(tag+': missing or invalid typed interface')
    for key,s in interfaces.items():
        count=uses[key]
        if count==0 and not s.get('termination'):errors.append(key+': unconnected interface without termination')
        if count>1:errors.append(key+': multiple routes require separate junction ports')
        if count and s.get('termination'):errors.append(key+': terminated interface is connected')
    return errors

def support_errors(data):
    if data.get('schema_version',1)!=2:return []
    errors=[];parts={p['id']:p for p in data['parts']};roots=data.get('grounded',[]);graph={k:[] for k in parts}
    if not isinstance(roots,list):return ['grounded: list required']
    for key in roots:
        if data.get('support_contract_version')==1:
            if key not in parts:errors.append(str(key)+': unknown explicit grounded root')
        elif key not in parts or parts[key]['kind'] not in {'slab','footing'} or abs(parts[key]['origin'][2]+parts[key]['size'][2])>TOL:
            errors.append(str(key)+': grounded root must be slab/footing with top at ground plane')
    for c in data.get('bearings',[]):
        if c['part'] in graph:graph[c['part']].append(c['on'])
    for c in data.get('mounts',[]):
        if isinstance(c,dict) and c.get('part') in graph:graph[c['part']].append(c.get('on'))
    for c in data.get('custom_contacts',[]):
        if isinstance(c,dict) and c.get('part') in graph:graph[c['part']].append(c.get('on'))
    for c in data.get('surface_contacts',[]):
        if isinstance(c,dict) and c.get('part') in graph:graph[c['part']].append(c.get('on'))
    for p in parts.values():
        if p['kind']=='worker' and p.get('parent'):graph[p['id']].append(p['parent'])
    def reaches(key,seen):
        if key in roots:return True
        if key in seen:return False
        return any(reaches(x,seen|{key}) for x in graph.get(key,[]))
    for p in parts.values():
        key=p['id']
        if p['kind']=='custom' and key not in roots and not any(c.get('part')==key for c in data.get('custom_contacts',[])+data.get('surface_contacts',[])):errors.append(key+': custom surface contact required')
        if p['kind'] in SUPPORTED and (p['kind']!='wall' or data.get('registered_geometry')) and not reaches(key,set()):errors.append(key+': no declared bearing path to ground')
        if p['kind'] in {'beam','landing'} and len(set(graph[key]))<2:errors.append(key+': two distinct supports required by current adapter')
        if p['kind']=='stair' and not any(a['stair']==key for a in data.get('stair_access',[])):errors.append(key+': stair landing access missing')
        if p['kind']=='ramp' and not any(a['ramp']==key for a in data.get('ramp_access',[])):errors.append(key+': ramp landing access missing')
    return errors

def coverage(data):
    strict=data.get('schema_version',1)==2
    supported=SUPPORTED
    if data.get('validation_policy')=='strict':
        from coherence_validation import SUPPORT_ADAPTERS
        supported=SUPPORTED|SUPPORT_ADAPTERS
    return {'mode':'typed-v2' if strict else 'legacy-partial',
            'validation_policy':data.get('validation_policy','legacy'),
            'unverified':['loads, dynamics, process performance and hidden raster connections']+([] if strict else ['typed interface and support completeness']),
            'unsupported_support_kinds':sorted({p['kind'] for p in data.get('parts',[]) if p['kind'] not in supported or (p['kind']=='wall' and not data.get('registered_geometry'))}),
            'custom_adapters':[{'id':p['id'],'adapter':p.get('parameters',{}).get('adapter'),'limitations':p.get('parameters',{}).get('limitations')} for p in data.get('parts',[]) if p['kind']=='custom'],
            'registered_geometry_requested':bool(data.get('registered_geometry',False)),
            'custom_contact_patches':len(data.get('custom_contacts',[]))}

def render_interfaces(mesh,p):
    for s in p.get('interfaces',{}).values():
        a=[x+y for x,y in zip(p['origin'],s['anchor'])];b=[x+s['extension']*n for x,n in zip(a,s['normal'])]
        sealed=s.get('termination')=='cap'
        mesh.sweep([a,b],s['diameter']/2,24,caps=(False,sealed))
        mesh.flange(b,s['normal'],s['diameter']/2,bore=0 if sealed else s['diameter']*.43)
        # An external continuation is open geometry, never a blind end plate.
