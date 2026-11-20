"""Scalable connected processing hall assembled from original procedural modules."""
import argparse,copy,json
from pathlib import Path
from connected_plant import fixture
from route_geometry import rounded_route
from scene_model import make_part,validate

def factory(bays=3,enclosed=False):
    if type(bays)!=int or not 1<=bays<=12:raise ValueError('bays must be integer 1..12')
    if type(enclosed)!=bool:raise ValueError('enclosed must be boolean')
    scene={'units':'m','parts':[],'connections':[],'bearings':[],'stair_access':[],'clearance_pairs':[],'route_obstacles':[],
           'expected_counts':{'vessel':2*bays,'pump':bays,'worker':2*bays,'stair':bays,'landing':bays}}
    for i in range(bays):
        module=copy.deepcopy(fixture());prefix=f'bay-{i}-';dx=i*10
        for p in module['parts']:
            p['id']=prefix+p['id'];p['origin'][0]+=dx
            if p.get('parent'):p['parent']=prefix+p['parent']
            if p['kind']=='manifold':p['ports'].update({'left':[0,.1,.1],'right':[3,.1,.1]})
            scene['parts'].append(p)
        for c in module['connections']:
            c['from']=prefix+c['from'];c['to']=prefix+c['to']
            for v in c['route']:v[0]+=dx
            scene['connections'].append(c)
        for key in ['bearings','stair_access']:
            scene[key].extend({k:prefix+v for k,v in item.items()} for item in module[key])
        scene['clearance_pairs'].extend([[prefix+a,prefix+b] for a,b in module['clearance_pairs']])
        # Wall-mounted service cabinet and overhead tray with visible hangers.
        scene['parts'].append(make_part(prefix+'cabinet','cabinet',(dx+5.7,-.8,.8),(.6,.4,1)))
        scene['parts'].append(make_part(prefix+'tray','cable_tray',(dx+5.8,.1,4.3),(.4,5.4,.15)))
        scene['route_obstacles'].extend([prefix+'tray',prefix+'stairs'])
        for j,yy in enumerate([.3,5.3]):
            scene['parts'].append(make_part(prefix+f'tray-support-{j}','column',(dx+5.9,yy,0),(.12,.12,4.3)))
            scene['bearings'].append({'part':prefix+'tray','on':prefix+f'tray-support-{j}'})
            scene['route_obstacles'].append(prefix+f'tray-support-{j}')
    for i in range(bays-1):
        # Offset the risers from tray-support silhouettes; retain both header
        # ports and pass above the stairs without changing network topology.
        a=i*10+3.85;b=(i+1)*10+.85;y=2.35;front=3.5;top=4.0
        route=rounded_route([[a,y,.4],[a+.9,y,.4],[a+.9,front,.4],
                             [a+.9,front,top],[b-.9,front,top],
                             [b-.9,front,.4],[b-.9,y,.4],[b,y,.4]],.25)
        scene['connections'].append({'from':f'bay-{i}-header:right','to':f'bay-{i+1}-header:left','route':route,'radius':.075,'fittings':True})
    if enclosed:
        for i in range(bays):
            prefix=f'bay-{i}-';dx=i*10
            for part in scene['parts']:
                if part['id'] in [prefix+'hall-column-0',prefix+'hall-column-1']:part['size'][2]=5.2
                if part['id']==prefix+'hall-beam':part['origin'][2]=5.2
            for j,x in enumerate([-1.7,6.5]):
                name=prefix+f'front-column-{j}'
                scene['parts'].append(make_part(name,'column',(dx+x,6.7,0),(.3,.3,5.2),parameters={'profile':'steel'}))
                scene['bearings'].append({'part':name,'on':prefix+'floor'})
                cross=prefix+f'cross-beam-{j}'
                scene['parts'].append(make_part(cross,'beam',(dx+x,-.8,5.2),(.3,7.8,.3)))
                scene['bearings'] += [{'part':cross,'on':name},{'part':cross,'on':prefix+f'hall-column-{j}'}]
            front=prefix+'front-beam'
            scene['parts'].append(make_part(front,'beam',(dx-1.7,6.7,5.2),(8.5,.3,.3)))
            scene['bearings'] += [{'part':front,'on':prefix+f'front-column-{j}'} for j in range(2)]
            roof=prefix+'roof'
            scene['parts'].append(make_part(roof,'slab',(dx-2,-1,5.5),(10,8,.2)))
            scene['bearings'] += [{'part':roof,'on':name} for name in [front,prefix+'hall-beam',prefix+'cross-beam-0',prefix+'cross-beam-1']]
            wall=prefix+'aisle-wall'
            scene['parts'].append(make_part(wall,'wall',(dx-2,6.85,0),(10,.15,5.5)))
            scene['bearings'].append({'part':wall,'on':prefix+'floor'})
            scene['route_obstacles'] += [roof,wall]
        end='end-wall'
        scene['parts'].append(make_part(end,'wall',(bays*10-2.15,-1,0),(.15,8,5.5)))
        scene['bearings'].append({'part':end,'on':f'bay-{bays-1}-floor'})
        scene['route_obstacles'].append(end)
        scene['expected_counts'].update({'wall':2*bays+1,'slab':2*bays,'beam':4*bays,'column':9*bays})
    errors=validate(scene)
    if errors:raise ValueError('\n'.join(errors))
    return scene

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--bays',type=int,default=3);ap.add_argument('--out',required=True);ap.add_argument('--enclosed',action='store_true')
    a=ap.parse_args();Path(a.out).write_text(json.dumps(factory(a.bays,a.enclosed),indent=2))
