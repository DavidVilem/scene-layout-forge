"""Portable architectural scene contracts. No rendering or external dependencies."""
import math
from dataclasses import dataclass, field
from scene_schema import shape_errors
from mechanical_checks import shaft_bearing_errors
from technical_parts import parameter_errors
from access_geometry import railing_blocks_access
from sweep_geometry import check_tube_curvature,check_route_self_clearance,route_pair_conflicts

LIBRARIES = {
    'structure': ('column', 'beam', 'slab', 'footing', 'brace', 'corbel'),
    'envelope': ('wall', 'window', 'door', 'curtain_panel', 'mullion', 'parapet'),
    'circulation': ('stair', 'landing', 'railing', 'ramp'),
    'industrial': ('vessel', 'pump', 'pipe', 'valve', 'manifold', 'flange'),
    'services': ('cabinet', 'conduit', 'cable_tray', 'drain', 'duct'),
    'site': ('paving', 'planter', 'bollard'),
    'people': ('worker',),
    'technical': ('shell','ring_frame','bulkhead','truss','panel_array','console','seat','gear','rotor','heat_exchanger','luminaire','instrument_panel'),
}
KINDS = {x for group in LIBRARIES.values() for x in group} | {'custom'}

def vec(value, name):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError(f'{name}: expected three coordinates')
    if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in value):
        raise ValueError(f'{name}: coordinates must be finite numbers')
    return tuple(float(x) for x in value)

@dataclass
class Part:
    id: str
    kind: str
    origin: tuple
    size: tuple
    parent: str | None = None
    ports: dict = field(default_factory=dict)
    parameters: dict = field(default_factory=dict)

    @classmethod
    def from_data(cls, data):
        if not isinstance(data.get('id'),str) or not data['id'].strip():
            raise ValueError('Part ID must be nonempty')
        if data.get('kind') not in KINDS: raise ValueError(f"Unknown component: {data.get('kind')}")
        size = vec(data['size'], data['id']+'.size')
        if min(size)<=0: raise ValueError(data['id']+': dimensions must be positive')
        origin = vec(data['origin'], data['id']+'.origin')
        ports = {k:vec(v,data['id']+'.'+k) for k,v in data.get('ports',{}).items()}
        return cls(data['id'], data['kind'], origin, size, data.get('parent'), ports, data.get('parameters',{}))

    def port(self,name):
        return tuple(a+b for a,b in zip(self.origin,self.ports[name]))

    def bounds(self):
        return self.origin, tuple(a+b for a,b in zip(self.origin,self.size))

def validate(data):
    """Return errors; no silent fixes. AABB overlap is conservative, not a mesh test."""
    errors=shape_errors(data,KINDS)
    if errors:return errors
    from exterior_environment import errors as exterior_errors
    errors.extend(exterior_errors(data))
    if errors:return errors
    parts={}
    if data.get('units')!='m': errors.append('Scene units must be m')
    for raw in data.get('parts',[]):
        try:
            p=Part.from_data(raw)
            errors.extend(p.id+': '+e for e in parameter_errors(p.kind,p.parameters))
            if p.id in parts: errors.append('Duplicate ID: '+p.id)
            parts[p.id]=p
            if p.kind=='custom':
                if not data.get('registered_geometry',False):errors.append(p.id+': custom geometry requires registered_geometry mode')
                from registered_geometry import errors as registered_errors
                errors.extend(registered_errors(raw))
        except (ValueError,KeyError,TypeError) as e: errors.append(str(e))
    if not parts:errors.append('Empty scene')
    for p in parts.values():
        if p.parent and p.parent not in parts:errors.append(p.id+': unknown parent')
        seen={p.id};node=p
        while node.parent in parts:
            if node.parent in seen:errors.append(p.id+': parent cycle');break
            seen.add(node.parent);node=parts[node.parent]
        if p.kind=='stair':
            n=p.parameters.get('steps')
            if type(n)!=int or n<1:errors.append(p.id+': positive integer steps required')
        if p.kind=='worker' and p.parent in parts:
            floor=parts[p.parent];lo,hi=floor.bounds()
            if abs(p.origin[2]-hi[2])>1e-6:errors.append(p.id+': feet not on support plane')
            if not (lo[0]<=p.origin[0] and p.origin[0]+p.size[0]<=hi[0] and lo[1]<=p.origin[1] and p.origin[1]+p.size[1]<=hi[1]):
                errors.append(p.id+': outside support footprint')
    for link in data.get('attachments',[]):
        try:
            a,pa=link['from'].split(':',1);b,pb=link['to'].split(':',1)
            if math.dist(parts[a].port(pa),parts[b].port(pb))>1e-6:errors.append('Attachment endpoint mismatch: '+link['from'])
        except (KeyError,ValueError,TypeError) as e:errors.append('Invalid attachment: '+str(e))
    valid_links=[]
    for link in data.get('connections',[]):
        try:
            route=[vec(v,'route') for v in link['route']]
            if len(route)<2:raise ValueError('Route requires two or more points')
            for endpoint,point in [(link['from'],route[0]),(link['to'],route[-1])]:
                pid,port=endpoint.split(':',1)
                if math.dist(parts[pid].port(port),point)>1e-6:errors.append(endpoint+': endpoint mismatch')
            if any(math.dist(a,b)<1e-8 for a,b in zip(route,route[1:])):errors.append('Route has zero-length segment')
            if not isinstance(link.get('radius'),(float,int)) or link['radius']<=0:errors.append('Pipe radius must be positive')
            else:
                check_tube_curvature(route,link['radius'])
                check_route_self_clearance(route,link['radius'])
                valid_links.append(link)
        except (KeyError,ValueError,TypeError) as e:errors.append('Invalid connection: '+str(e))
    junction_boxes={p.id:p.bounds() for p in parts.values() if p.kind=='manifold'}
    for i,j in route_pair_conflicts(valid_links,junction_boxes):
        errors.append('Route pair clearance: '+valid_links[i]['from']+' / '+valid_links[j]['from'])
    # Segment/AABB slab test, expanded by tube radius; conservative near corners.
    obstacles=list(parts) if data.get('schema_version',1)==2 else data.get('route_obstacles',[])
    for obstacle in obstacles:
        if obstacle not in parts:errors.append('Unknown route obstacle: '+str(obstacle));continue
        lo,hi=parts[obstacle].bounds()
        for link in data.get('connections',[]):
            if data.get('schema_version',1)==2 and obstacle in {link['from'].split(':')[0],link['to'].split(':')[0]}:continue
            try:
                radius=float(link['radius']);route=[vec(v,'route') for v in link['route']]
                for a,b in zip(route,route[1:]):
                    entry,leave=0.,1.
                    for axis in range(3):
                        lower,upper=lo[axis]-radius,hi[axis]+radius;delta=b[axis]-a[axis]
                        if abs(delta)<1e-12:
                            if a[axis]<lower or a[axis]>upper:entry,leave=1.,0.;break
                        else:
                            t0,t1=sorted(((lower-a[axis])/delta,(upper-a[axis])/delta))
                            entry=max(entry,t0);leave=min(leave,t1)
                    if entry<=leave:
                        errors.append(f"Route clearance: {link.get('from')} / {obstacle}");break
            except (ValueError,KeyError,TypeError):pass # Connection validation reports malformed routes.
    # Only explicitly declared clearance pairs: touching is allowed, penetration is not.
    for a,b in data.get('clearance_pairs',[]):
        if a not in parts or b not in parts:errors.append('Unknown clearance part');continue
        alo,ahi=parts[a].bounds();blo,bhi=parts[b].bounds()
        if all(min(ahi[i],bhi[i])-max(alo[i],blo[i])>1e-6 for i in range(3)):
            errors.append(f'Bounding-box penetration: {a} / {b}')
    for kind,count in data.get('expected_counts',{}).items():
        actual=sum(p.kind==kind for p in parts.values())
        if actual!=count:errors.append(f'{kind}: expected {count}, got {actual}')
    for contact in data.get('bearings',[]):
        try:
            upper,lower=parts[contact['part']],parts[contact['on']]
            alo,ahi=upper.bounds();blo,bhi=lower.bounds()
            if abs(alo[2]-bhi[2])>1e-6:errors.append(upper.id+': bearing height mismatch')
            if any(min(ahi[i],bhi[i])-max(alo[i],blo[i])<=1e-6 for i in [0,1]):
                errors.append(upper.id+': bearing footprints do not overlap')
        except (KeyError,TypeError) as e:errors.append('Invalid bearing: '+str(e))
    for access in data.get('stair_access',[])+data.get('ramp_access',[]):
        try:
            stair,landing=parts[access.get('stair',access.get('ramp'))],parts[access['landing']]
            if stair.kind not in {'stair','ramp'} or landing.kind not in {'landing','slab'}:raise ValueError('Expected stair/ramp and landing/slab')
            lo,hi=stair.bounds();llo,lhi=landing.bounds()
            reverse=stair.parameters.get('reverse',False)
            edge=lo[1] if reverse else hi[1];target=lhi[1] if reverse else llo[1]
            if abs(hi[2]-lhi[2])>1e-6:errors.append(stair.id+': landing height mismatch')
            if abs(edge-target)>1e-6 or lo[0]<llo[0]-1e-6 or hi[0]>lhi[0]+1e-6:
                errors.append(stair.id+': landing edge mismatch')
            for rail in parts.values():
                if rail.kind=='railing' and railing_blocks_access(rail,stair):
                    errors.append(stair.id+': landing entrance blocked by railing '+rail.id)
        except (KeyError,TypeError,ValueError) as e:errors.append('Invalid stair access: '+str(e))
    if not errors:errors.extend(shaft_bearing_errors(data))
    if not errors:
        from typed_interfaces import interface_errors,support_errors
        errors.extend(interface_errors(data));errors.extend(support_errors(data))
        from registered_geometry import contact_errors,mount_errors
        errors.extend(contact_errors(data));errors.extend(mount_errors(data))
    if not errors:
        from actor_plan import scene_errors
        errors.extend(scene_errors(data))
    if not errors:
        from coherence_validation import strict_errors
        errors.extend(strict_errors(data))
    if not errors and any(k in data for k in ('design_intent','design_selection','materialized_design')):
        from design_realization import realization_errors
        errors.extend('design realization: '+e for e in realization_errors(data))
    if not errors:
        from architecture_stages import preflight_errors
        errors.extend('architecture: '+e for e in preflight_errors(data))
    return errors

def make_part(id,kind,origin,size,**kw):
    return dict(id=id,kind=kind,origin=list(origin),size=list(size),**kw)

def validation_report(data):
    """Combined public report: never substitute coherence-only success for geometry."""
    from coherence_validation import coherence_report
    errors=validate(data)
    policy=data.get('validation_policy','legacy') if isinstance(data,dict) else 'legacy'
    if errors and any(not e.startswith('coherence ') for e in errors):
        return {'policy':policy,'status':'failed','checks':
            [{'check':'geometry','status':'failed','message':error,'parts':[],'critical':True} for error in errors]+
            [{'check':'coherence','status':'not_run','message':'Resolve base geometry/input errors before dependent coherence checks','parts':[],'critical':True}]}
    report=coherence_report(data)
    report['checks'].insert(0,{'check':'geometry','status':'passed','message':'Applicable base geometry checks passed; see coverage limits','parts':[],'critical':True})
    if data.get('exterior_environment'):
        from exterior_environment import handoff as exterior_handoff
        report['representation_scope']=exterior_handoff(data)
    return report

def tower(floors=20,bays=3):
    if type(floors)!=int or not 1<=floors<=100:raise ValueError('floors must be integer 1..100')
    if type(bays)!=int or not 1<=bays<=12:raise ValueError('bays must be integer 1..12')
    width=bays*4;parts=[make_part('foundation','footing',(-.5,-.5,-.6),(width+1,width+1,.6))]
    for level in range(floors):
        z=level*3.4
        parts.append(make_part(f'slab-{level}','slab',(0,0,z),(width,width,.25)))
        for x in range(bays+1):
            for y in range(bays+1):
                parts.append(make_part(f'column-{level}-{x}-{y}','column',(x*4-.15,y*4-.15,z+.25),(.3,.3,3.15),parent=f'slab-{level}'))
        for side in range(4):
            for bay in range(bays):
                o,s=((bay*4,0,z+.4),(3.95,.1,2.85)) if side==0 else ((bay*4,width-.1,z+.4),(3.95,.1,2.85)) if side==1 else ((0,bay*4,z+.4),(.1,3.95,2.85)) if side==2 else ((width-.1,bay*4,z+.4),(.1,3.95,2.85))
                parts.append(make_part(f'panel-{level}-{side}-{bay}','curtain_panel',o,s,parent=f'slab-{level}'))
    parts.append(make_part('roof','slab',(0,0,floors*3.4),(width,width,.25)))
    return dict(units='m',parts=parts,connections=[],expected_counts={'slab':floors+1,'column':floors*(bays+1)**2,'curtain_panel':floors*bays*4})
