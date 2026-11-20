"""Original, bounded natural mass adapters with actual registered ground contact.

These establish silhouette and location, not botany, flexible branches or terrain
mechanics. Landscape detail stays subordinate to required IDs in ContextPlan.
"""
import math
import random


def tree_mass(identifier, origin, size, *, family='broadleaf', seed=1):
    """Return a registered custom tree with a flat trunk base and varied crown."""
    if family not in {'broadleaf', 'columnar', 'pyramidal'}: raise ValueError('unsupported tree silhouette family')
    if len(origin) != 3 or len(size) != 3 or any(not math.isfinite(v) for v in list(origin)+list(size)) or min(size) <= 0:
        raise ValueError('tree requires finite origin and positive size')
    rng = random.Random(seed); w,d,h = size
    vertices=[]; faces=[]; edges=[]
    def rings(profile, count, variation):
        start=len(vertices)
        phases=[rng.uniform(.88,1) for _ in range(count)] if variation else [1]*count
        for z,rx,ry in profile:
            for i in range(count):
                angle=2*math.pi*i/count
                vertices.append([w/2+rx*phases[i]*math.cos(angle), d/2+ry*phases[i]*math.sin(angle), z])
        faces.append(list(range(start+count-1,start-1,-1)))
        for row in range(len(profile)-1):
            for i in range(count):
                a=start+row*count+i; b=start+row*count+(i+1)%count
                faces.append([a,b,b+count,a+count])
        last=start+(len(profile)-1)*count;faces.append(list(range(last,last+count)))
        for row in (0,len(profile)-1):
            base=start+row*count
            edges.extend([[base+i,base+(i+1)%count] for i in range(count)])
    # Square trunk allows an auditable nonzero-area base patch.
    rx,ry = w*.055,d*.055
    for z in (0,h*.65):
        vertices.extend([[w/2-rx,d/2-ry,z],[w/2+rx,d/2-ry,z],[w/2+rx,d/2+ry,z],[w/2-rx,d/2+ry,z]])
    faces.extend([[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]])
    edges.extend([[0,4],[1,5],[2,6],[3,7]])
    profile={'broadleaf':[(.35,.16),(.48,.48),(.7,.5),(.88,.35),(1,.07)],
             'columnar':[(.2,.10),(.4,.24),(.7,.25),(.9,.15),(1,.03)],
             'pyramidal':[(.25,.5),(.42,.39),(.64,.28),(.82,.16),(1,.025)]}[family]
    rings([(h*z,w*r,d*r) for z,r in profile],12,True)
    return {'id':identifier,'kind':'custom','origin':list(origin),'size':list(size),
            'parameters':{'adapter':'natural_tree_mass_v1','family':family,'seed':seed,
                          'vertices':vertices,'faces':faces,'edges':edges,
                          'limitations':'Conceptual trunk and crown masses only; no botanical species, branch mechanics or leaf simulation'},
            'semantic_role':'context_tree'}


def add_tree(scene, identifier, ground_id, xy, size, *, family='broadleaf', seed=1):
    """Add a tree only on a supported flat ground slab, with actual contact patch."""
    if not scene.get('registered_geometry'):
        raise ValueError('natural context requires registered_geometry mode')
    ground=next((p for p in scene['parts'] if p['id']==ground_id),None)
    if ground is None or ground['kind'] not in {'slab','footing','landing'}:
        raise ValueError('tree needs an explicit supported planar ground adapter')
    if any(p['id']==identifier for p in scene['parts']): raise ValueError('duplicate tree ID')
    z=ground['origin'][2]+ground['size'][2]
    tree=tree_mass(identifier,[xy[0],xy[1],z],size,family=family,seed=seed)
    points=[[v[k]+tree['origin'][k] for k in range(3)] for v in tree['parameters']['vertices'][:4]]
    for p in points:
        if any(not ground['origin'][k] <= p[k] <= ground['origin'][k]+ground['size'][k] for k in (0,1)):
            raise ValueError('tree root patch lies outside ground surface')
    scene['parts'].append(tree)
    scene.setdefault('custom_contacts',[]).append({'part':identifier,'on':ground_id,'points':points})
    return identifier
