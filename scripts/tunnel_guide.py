"""Optional tunnel composition study, not a hydraulic or structural model.

Checks straight pipe spacing, bracket contact and central aisle separation.
Arch loads, joints and generated pixels remain unverified. Outputs stay outside
the package. This example is not a required adapter for other interior subjects.
"""
import argparse
import json
import math
from pathlib import Path

def layout(length=42):
    pipes=[]
    for side in (-1,1):
        for i in range(8):
            pipes.append({'id':f'bank-{side}-{i}', 'x':side*2.05, 'z':.52+i*.42,
                          'radius':(.16,.11,.14,.19,.12,.16,.1,.14)[i], 'start':0., 'end':length})
        for i in range(7):
            pipes.append({'id':f'back-{side}-{i}', 'x':side*2.65, 'z':.36+i*.45,
                          'radius':.065, 'start':0., 'end':length})
    for i,x in enumerate([-1.4,-.7,0,.7,1.4]):
        pipes.append({'id':f'ceiling-{i}', 'x':x, 'z':4.05-.09*abs(x),
                      'radius':.14 if i==2 else .09, 'start':0., 'end':length})
    brackets=[{'pipe':p['id'],'x':p['x'],'z':p['z']-p['radius'], 'y':y}
              for p in pipes if p['id'].startswith('bank') for y in range(2,int(length),4)]
    return {'length':length,'pipes':pipes,'brackets':brackets,'aisle_half_width':.8,'headroom':2.3}

def check(data):
    pipes=data['pipes'];errors=[]
    ids={p['id']:p for p in pipes}
    if len(ids)!=len(pipes):errors.append('duplicate pipe IDs')
    for p in pipes:
        if not all(math.isfinite(p[k]) for k in ('x','z','radius','start','end')) or p['radius']<=0 or p['start']>=p['end']:
            errors.append(p['id']+': invalid route');continue
        if abs(p['x'])-p['radius'] < data['aisle_half_width'] and p['z']-p['radius'] < data['headroom']:
            errors.append(p['id']+': intrudes into walking envelope')
    for i,p in enumerate(pipes):
        for q in pipes[i+1:]:
            if min(p['end'],q['end'])>max(p['start'],q['start']) and math.hypot(p['x']-q['x'],p['z']-q['z'])<p['radius']+q['radius']:
                errors.append(p['id']+' intersects '+q['id'])
    for b in data['brackets']:
        p=ids.get(b['pipe'])
        if not p or abs(b['x']-p['x'])>1e-6 or abs(b['z']-(p['z']-p['radius']))>1e-6 or not p['start']<=b['y']<=p['end']:
            errors.append('bracket does not contact its pipe')
    supported={b['pipe'] for b in data['brackets']}
    for p in pipes:
        if p['id'].startswith('bank') and p['id'] not in supported:errors.append(p['id']+': missing bracket')
    continuity = route_contract(data)
    from route_continuity import inspect
    route_report=inspect(continuity)
    errors.extend(route_report['errors'])
    return {'status':'failed' if errors else 'passed','errors':errors,
            'checked':['straight pipe pairs','central walking envelope','declared bank bracket tangency'],
            'route_continuity':route_report,
            'unverified':['ceiling/rear pipe hangers','vault loads and foundations','hydraulic destinations outside view',
                          'branch topology and fasteners added by artistic finish','all generated pixels']}

def route_contract(data):
    """Every guide run continues past the frame; four short ports end in caps.

    No endpoint ends merely because it is hidden. Junctions split mains so that
    branches attach to real graph nodes instead of overlapping disconnected pipes.
    """
    nodes={};routes=[];selected={'bank--1-2':6.,'bank-1-4':8.,'bank--1-6':12.,'bank-1-1':15.}
    for p in data['pipes']:
        key=p['id'];a=key+'/near';b=key+'/far'
        for n,y,destination in ((a,p['start'],'utility route continuing behind the observer'),
                                 (b,p['end'],'same continuous utility route beyond the distant field of view')):
            nodes[n]={'kind':'frame_exit','description':key+' continues naturally beyond the frame',
                      'continues_to':destination,'position':[p['x'],y,p['z']]}
        if key not in selected:
            routes.append({'id':key,'from':a,'to':b,'trace':'Continuous longitudinal run with aligned sleeve/flange joints; no free ends.',
                           'points':[nodes[a]['position'],nodes[b]['position']]})
        else:
            j=key+'/tee';cap=key+'/cap';y=selected[key]
            nodes[j]={'kind':'junction','description':'Explicit three-way tee in '+key,'position':[p['x'],y,p['z']]}
            nodes[cap]={'kind':'cap','description':'Short service inspection branch on '+key,
                        'cue':'Readable blind flange with closed bolted face',
                        'position':[p['x']+(.45 if p['x']<0 else -.45),y,p['z']]}
            for suffix,start,end in (('near',a,j),('far',j,b),('branch',j,cap)):
                routes.append({'id':key+'/'+suffix,'from':start,'to':end,
                               'trace':'Main continues through actual tee' if suffix!='branch' else 'Short horizontal inward branch attached to tee and ending at blind flange',
                               'points':[nodes[start]['position'],nodes[end]['position']]})
    return {'version':1,'inventory':[r['id'] for r in routes],'nodes':nodes,'routes':routes,
            'crossings':[], 'occlusions':[
                {'route':r['id'],'behind':'front pipe bank where sightlines overlap',
                 'continuation':'Same longitudinal route continues at unchanged diameter to its far boundary'}
                for r in routes if r['id'].startswith('back-')]}

def render(data,path):
    report=check(data)
    if report['errors']:raise ValueError('; '.join(report['errors']))
    from render_scene import Mesh,Renderer
    m=Mesh();length=data['length']
    # Base, panel rhythm and supporting walls are only a composition study.
    m.box((-3.12,0,-.2),(6.24,length,.2))
    for side in (-1,1):m.box((side*3.12-.08,0,0),(.16,length,1.8))
    for y in range(0,int(length),3):
        points=[(3.12*math.cos(a),y,1.8+3.12*math.sin(a)) for a in [i*math.pi/32 for i in range(33)]]
        m.sweep(points,.075,n=8)
    for p in data['pipes']:
        m.sweep([(p['x'],p['start'],p['z']),(p['x'],p['end'],p['z'])],p['radius'],n=16)
        for y in range(3,int(length),7):
            m.sweep([(p['x'],y-.035,p['z']),(p['x'],y+.035,p['z'])],p['radius']*1.18,n=16)
    contract=route_contract(data)
    for route in contract['routes']:
        if route['id'].endswith('/branch'):
            a,b=route['points'];m.sweep([a,b],.065,n=16)
            axis=[b[i]-a[i] for i in range(3)]
            m.flange(b,axis,.065,bolts=6,bore=0)
    for b in data['brackets']:
        wall=3.12 if b['x']>0 else -3.12
        m.box((min(wall,b['x'])-.05,b['y']-.04,b['z']-.08),(abs(wall-b['x'])+.1,.08,.08))
    for y in [i*.33 for i in range(int(length/.33))]:m.box((-.8,y,0),(1.6,.025,.035))
    for x in (-.8,-.4,0,.4,.8):m.box((x-.012,0,0),(.025,length,.04))
    renderer=Renderer(m,width=1400,height=900,hatching=False,projection='perspective',finish='graphite',
                      camera_eye=[.12,-1.5,1.65],camera_target=[0,40,1.85],fov=78)
    renderer.draw(m).save(path)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();out=a.out.resolve();root=Path(__file__).resolve().parents[1]
    if out==root or root in out.parents:raise ValueError('Do not output inside the skill')
    out.mkdir(parents=True,exist_ok=False);data=layout()
    (out/'layout.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    report=render(data,out/'guide.png')
    (out/'coverage.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))
