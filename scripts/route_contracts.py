"""Logical destination, bend, separation, support and maintenance route evidence."""
import math
from physical_support import surface_normals
from sweep_geometry import segment_distance

EPS=1e-6


def _distance(point,a,b):
    delta=[b[k]-a[k] for k in range(3)];den=sum(v*v for v in delta)
    if den<=EPS*EPS:return math.dist(point,a)
    t=max(0,min(1,sum((point[k]-a[k])*delta[k] for k in range(3))/den))
    return math.dist(point,[a[k]+t*delta[k] for k in range(3)])


def route_checks(scene):
    checks=[];parts={p['id']:p for p in scene.get('parts',[])};connections=scene.get('connections',[]);seen=set()
    for index,c in enumerate(scene.get('route_contracts',[])):
        status='passed';message='Declared route constraints verified geometrically; operating performance unverified';cid=c.get('id',f'route-contract[{index}]');owners=[]
        try:
            if cid in seen:raise ValueError('Duplicate route contract ID')
            seen.add(cid)
            matches=[r for r in connections if r.get('contract_id')==cid]
            if len(matches)!=1:raise ValueError('Exactly one spatial connection must bind this logical route contract')
            route=matches[0];owners=[route['from'].split(':')[0],route['to'].split(':')[0]]
            if route['from']!=c['from'] or route['to']!=c['to']:raise ValueError('Spatial route changed its logical source/destination')
            for ref in (c['from'],c['to']):
                pid,name=ref.split(':');spec=parts[pid]['interfaces'][name]
                if spec['medium']!=c['medium']:raise ValueError('Route medium differs from logical network')
            path=route['route'];radius=route['radius'];minimum=c.get('min_bend_radius',radius)
            if type(minimum) not in (int,float) or not math.isfinite(minimum) or minimum<radius:raise ValueError('Minimum bend radius must be finite and at least tube radius')
            for a,b,d in zip(path,path[1:],path[2:]):
                u=[b[k]-a[k] for k in range(3)];v=[d[k]-b[k] for k in range(3)];cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];area=math.sqrt(sum(x*x for x in cross))
                if area>EPS and math.dist(a,b)*math.dist(b,d)*math.dist(a,d)/(2*area)<minimum-EPS:raise ValueError('Sampled elbow radius is below declared route minimum')
            separation=c.get('min_separation',0)
            if type(separation) not in (int,float) or not math.isfinite(separation) or separation<0:raise ValueError('Nonnegative separation required')
            if separation:
                for other in connections:
                    if other is route:continue
                    # Shared junctions require a separate explicit local adapter.
                    if any(segment_distance(a,b,d,e)[0]<radius+other['radius']+separation-EPS for a,b in zip(path,path[1:]) for d,e in zip(other['route'],other['route'][1:])):raise ValueError('Route maintenance separation is insufficient')
            for support in c.get('supports',[]):
                p=parts[support['part']];point=support['point'];normal=support['normal'];normals=surface_normals(p,point)
                if normals is None:status='unsupported';message='Route support surface lacks an exact adapter';break
                if not any(math.dist(normal,n)<EPS for n in normals):raise ValueError('Route support point/normal misses actual support surface')
                center=[point[k]+normal[k]*radius for k in range(3)]
                if min(_distance(center,a,b) for a,b in zip(path,path[1:]))>EPS:raise ValueError('Route tube is detached from declared support')
            maximum=c.get('max_unsupported_length')
            if maximum is not None:
                if type(maximum) not in (int,float) or not math.isfinite(maximum) or maximum<=0:raise ValueError('Positive unsupported length required')
                # Arc coordinates bind supports to their positions, not their count.
                arcs=[0.,sum(math.dist(a,b) for a,b in zip(path,path[1:]))]
                for support in c.get('supports',[]):
                    point=[support['point'][k]+support['normal'][k]*radius for k in range(3)];start=0.;found=False
                    for a,b in zip(path,path[1:]):
                        length=math.dist(a,b)
                        if _distance(point,a,b)<EPS:arcs.append(start+math.dist(a,point));found=True;break
                        start+=length
                    if not found:raise ValueError('Route support is stale')
                arcs.sort()
                if any(b-a>maximum+EPS for a,b in zip(arcs,arcs[1:])):raise ValueError('Route exceeds declared unsupported length')
            if c.get('maintenance_volumes'):
                from access_geometry import profile_errors,volume_obstructed
                volumes={v['id']:v for v in scene.get('access_volumes',[])};nodes={n['id']:n for n in scene.get('access_nodes',[])}
                for key in c['maintenance_volumes']:
                    volume=volumes[key]
                    if profile_errors(volume,nodes):raise ValueError('Invalid maintenance access profile')
                    if any(volume_obstructed(p,volume) for p in parts.values()):raise ValueError('Occupied route maintenance envelope')
        except (KeyError,ValueError,TypeError,IndexError) as exc:status='failed';message=str(exc)
        checks.append(dict(check='route_contract',contract_id=cid,status=status,message=message,parts=owners,critical=c.get('critical',True)))
    # Explicit external meanings are versioned so legacy examples remain labelled
    # as partial boundary semantics instead of silently inventing a service.
    if scene.get('route_contract_version')==1:
        ids={c.get('id') for c in scene.get('route_contracts',[])}
        for route in connections:
            if route.get('contract_id') not in ids:checks.append(dict(check='route_contract',contract_id=None,status='failed',message='Spatial route has no logical contract',parts=[],critical=True))
        for p in parts.values():
            for name,s in p.get('interfaces',{}).items():
                if s.get('termination')=='external':
                    boundary=s.get('boundary',{});ok=isinstance(boundary,dict) and all(isinstance(boundary.get(k),str) and boundary[k].strip() for k in ('service','destination'))
                    checks.append(dict(check='external_boundary',status='passed' if ok else 'failed',message='External boundary requires service and destination meaning',parts=[p['id']],critical=True,interface=name))
    return checks
