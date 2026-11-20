"""Two supported water modules with five people; no hydraulic performance claim."""
from collections import Counter
from typed_water_plant import scene as module
from scene_model import make_part

def scene():
    d=dict(units='m',schema_version=2,grounded=['floor'],parts=[make_part('floor','slab',(-2,-1,-.2),(18,8,.2))],connections=[],bearings=[],stair_access=[],clearance_pairs=[])
    for i in range(2):
        s=module();prefix=f'm{i}-';shift=8*i
        keep={'inspector','operator','supervisor'} if i==0 else {'inspector','operator'}
        def ref(x):return 'floor' if x=='floor' else prefix+x
        for p in s['parts']:
            if p['id']=='floor' or (p['kind']=='worker' and p['id'] not in keep):continue
            if p['id']=='operator':p['origin'][0]+=1
            p['id']=ref(p['id']);p['origin'][0]+=shift
            if p.get('parent'):p['parent']=ref(p['parent'])
            d['parts'].append(p)
        for link in s['connections']:
            link['from']=prefix+link['from'];link['to']=prefix+link['to']
            for point in link['route']:point[0]+=shift
            d['connections'].append(link)
        for relation in s['bearings']:d['bearings'].append({k:ref(v) for k,v in relation.items()})
        for relation in s['stair_access']:d['stair_access'].append({k:ref(v) for k,v in relation.items()})
        d['clearance_pairs'].extend([[ref(a),ref(b)] for a,b in s['clearance_pairs']])
    for i,x in enumerate([-1.7,14.5]):
        name=f'front-column-{i}';d['parts'].append(make_part(name,'column',(x,6,0),(.3,.3,4.9)))
        d['bearings'].append({'part':name,'on':'floor'})
    d['parts'].append(make_part('front-beam','beam',(-1.7,6,4.9),(16.5,.3,.3)))
    d['bearings'].extend([{'part':'front-beam','on':f'front-column-{i}'} for i in range(2)])
    for i,x in enumerate([-1.7,14.5]):
        name=f'roof-beam-{i}';d['parts'].append(make_part(name,'beam',(x,-.8,5.2),(.3,7.1,.2)))
        d['bearings'].extend([{'part':name,'on':'front-beam'},{'part':name,'on':f'm{i}-hall-beam'}])
    for i,x in enumerate([.5,3,5.5,8.5,11,13.5]):
        name=f'roof-secondary-{i}';d['parts'].append(make_part(name,'beam',(x,-.8,5.2),(.12,7.1,.15)))
        d['bearings'].extend([{'part':name,'on':'front-beam'},{'part':name,'on':f'm{0 if x<7 else 1}-hall-beam'}])
    for i,y in enumerate([.8,2.8,4.8]):
        name=f'purlin-{i}';d['parts'].append(make_part(name,'beam',(.5,y,5.35),(13.12,.1,.1)))
        d['bearings'].extend([{'part':name,'on':f'roof-secondary-{j}'} for j in range(6)])
    d['expected_counts']=dict(Counter(p['kind'] for p in d['parts']))
    return d
