"""Visual route intent: meaningful ends, real junctions, and explicit occlusion.

No pressures, loads or hydraulic simulation. A valid graph proves only that the
declared design has connected destinations, never that generated pixels obey it.
Optional coordinates check endpoint contact without requiring a full CAD scene.
"""
import math
from collections import Counter

TERMINALS = {'equipment_port', 'cap', 'wall_passage', 'frame_exit', 'outlet'}
JOINERS = {'connector', 'junction'}
REVIEW_KEYS = {'continuity:ends', 'continuity:crossings', 'continuity:occlusion', 'continuity:added_routes'}

def nonempty(value): return isinstance(value, str) and bool(value.strip())
def xyz(value):
    return isinstance(value, (list, tuple)) and len(value)==3 and all(type(v) in (float,int) and math.isfinite(v) for v in value)

def inspect(contract):
    """Report invalid input as failed evidence, never an exception or approval."""
    if contract is None:
        return {'status':'not_run','errors':[], 'checked':[], 'limits':['No route-continuity contract supplied.']}
    try: return _inspect(contract)
    except (TypeError, KeyError, ValueError, IndexError, OverflowError, AttributeError) as exc:
        return {'status':'failed','errors':['Invalid route-continuity contract: '+str(exc)],'checked':[],
                'limits':['Dependent route checks not run.']}

def _inspect(c):
    errors=[];checks=[]
    if not isinstance(c,dict) or c.get('version')!=1: raise ValueError('version 1 required')
    nodes=c['nodes'];routes=c['routes'];inventory=c['inventory']
    if not isinstance(nodes,dict) or not isinstance(routes,list) or not isinstance(inventory,list):
        raise ValueError('nodes object, routes array and inventory array required')
    if not routes:errors.append('A route contract must contain routes; omit it for subjects without routes')
    ids=[r['id'] for r in routes]
    if not all(nonempty(x) for x in ids+inventory) or len(set(ids))!=len(ids) or len(set(inventory))!=len(inventory):
        errors.append('Route and inventory IDs must be nonempty and unique')
    if set(ids)!=set(inventory):errors.append('Declared route inventory differs from connected routes')
    counts=Counter();by={r['id']:r for r in routes};positions=0;unpositioned=0
    for key,node in nodes.items():
        if not nonempty(key) or node.get('kind') not in TERMINALS|JOINERS:
            errors.append(str(key)+': unknown endpoint kind; occlusion is not an endpoint');continue
        if not nonempty(node.get('description')):errors.append(key+': describe the actual destination or junction')
        if 'position' in node and not xyz(node['position']):errors.append(key+': invalid endpoint coordinates')
        if node['kind'] in {'wall_passage','frame_exit'} and not nonempty(node.get('continues_to')):
            errors.append(key+': boundary needs an explicit continuation, not a disappearing end')
        if node['kind'] in {'wall_passage','cap','outlet','equipment_port'} and not nonempty(node.get('cue')):
            errors.append(key+': visible termination/interface cue required')
    for r in routes:
        key=r['id'];a,b=r['from'],r['to']
        if a not in nodes or b not in nodes:errors.append(key+': unknown start/end destination');continue
        if a==b:errors.append(key+': use distinct junction ports or split a closed loop into routes')
        if not nonempty(r.get('trace')):errors.append(key+': describe the continuous path')
        counts[a]+=1;counts[b]+=1
        points=r.get('points')
        if points is not None:
            if not isinstance(points,list) or len(points)<2 or not all(xyz(p) for p in points):
                errors.append(key+': invalid path coordinates');continue
            if any(math.dist(p,q)<=1e-9 for p,q in zip(points,points[1:])):errors.append(key+': repeated path point')
            for node,end in ((nodes[a],points[0]),(nodes[b],points[-1])):
                if xyz(node.get('position')):
                    positions+=1
                    if math.dist(node['position'],end)>1e-5:errors.append(key+': path end does not meet destination')
                else:unpositioned+=1
        else:unpositioned+=2
    for key,node in nodes.items():
        degree=counts[key];kind=node.get('kind')
        if kind in TERMINALS and degree!=1:errors.append(key+': terminal must meet exactly one route')
        if kind=='connector' and degree!=2:errors.append(key+': connector must join two routes')
        if kind=='junction' and degree<3:errors.append(key+': junction must join at least three routes')
    for crossing in c.get('crossings',[]):
        pair=crossing.get('routes',[])
        if len(pair)!=2 or len(set(pair))!=2 or any(x not in by for x in pair):
            errors.append('Crossing needs two distinct known routes');continue
        if crossing.get('kind')=='separate':
            if not nonempty(crossing.get('cue')):errors.append('Separate crossing needs front/behind or clearance cue')
            shared={by[pair[0]]['from'],by[pair[0]]['to']} & {by[pair[1]]['from'],by[pair[1]]['to']}
            if shared:errors.append('Separate crossing cannot share a connection endpoint')
        elif crossing.get('kind')=='joined':
            node=crossing.get('node')
            if node not in nodes or nodes[node]['kind']!='junction' or any(node not in (by[k]['from'],by[k]['to']) for k in pair):
                errors.append('Joined crossing needs an actual shared junction; proximity is not a connection')
        else:errors.append('Crossing must be separate or joined')
    for hidden in c.get('occlusions',[]):
        if hidden.get('route') not in by or not nonempty(hidden.get('behind')) or not nonempty(hidden.get('continuation')):
            errors.append('Occlusion must name a route, an occluder and its continuing path')
    checks=['Every inventoried route has declared start/end destinations','Terminal and junction connectivity',
            'Explicit crossing and occlusion semantics']
    if positions:checks.append(str(positions)+' coordinate-bound endpoint contacts')
    limits=['Graph intent is not a verification of the generated image.',
            'No flow, pressure, strength or hidden physical construction is inferred.']
    if unpositioned:limits.append(str(unpositioned)+' endpoint contacts have descriptive intent only, without coordinate checks.')
    return {'status':'failed' if errors else 'passed','route_count':len(routes),'errors':errors,'checked':checks,'limits':limits}

def review_keys(plan):
    return REVIEW_KEYS if plan.get('continuity') is not None else set()

def finish_rules(plan):
    if plan.get('continuity') is None:return ''
    return ('\nVISUAL CONTINUITY: follow every planned route from its declared start to its declared end. '
            'An end must meet its equipment port, explicit junction, blind cap, intentional outlet, wall sleeve '
            'or natural frame exit. A pipe must not fade, dissolve, stop in open space or merge into a nearby silhouette. '
            'Occlusion hides a continuous route; it does not terminate it. Preserve diameter and trajectory across hidden spans. '
            'A crossing is separate unless an explicit tee/junction joins it. Keep crossing depth readable. '
            'Never cure an endpoint defect by deleting pipes, reducing detail or replacing the composition. '
            'Any new secondary route must also have two meaningful endpoints; attach it with a readable fitting. '
            'Keep all existing art direction, detail density and camera freedom. Do not add diagrams, labels or extra views.\n')
