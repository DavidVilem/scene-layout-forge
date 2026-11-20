"""Conceptual two-vessel water module, explicit interfaces and supported architecture."""
from connected_plant import fixture
from scene_model import make_part
from route_geometry import rounded_route
from typed_interfaces import add_interface

def scene():
    d=fixture();d['schema_version']=2;d['grounded']=['floor'];d['connections']=[]
    d['parts']=[p for p in d['parts'] if p['id']!='return']
    by={p['id']:p for p in d['parts']}
    for p in by.values():p['ports']={}
    for i in range(2):add_interface(by[f'tank-{i}'],'out',[.85,1.7,1.1],[0,1,0],.18,'outlet')
    h=by['header']
    for i in range(2):add_interface(h,f'branch-{i}',[i*3,.1,.2],[0,0,1],.18,'inlet')
    add_interface(h,'pump',[1.2,.2,.1],[0,1,0],.15,'outlet')
    add_interface(by['pump'],'in',[.375,.4,.64],[0,0,1],.15,'inlet')
    add_interface(by['pump'],'out',[.375,.56,.4],[0,1,0],.12,'outlet')
    boundary=make_part('boundary','manifold',(3.8,5.25,.3),(.8,.2,.2))
    add_interface(boundary,'in',[0,.1,.1],[-1,0,0],.12,'inlet')
    add_interface(boundary,'external',[.8,.1,.1],[1,0,0],.12,'outlet',termination='external')
    d['parts'].append(boundary);by['boundary']=boundary
    def port(ref):
        pid,name=ref.split(':');p=by[pid];return [a+b for a,b in zip(p['origin'],p['ports'][name])]
    def link(a,b,middle,radius,bend):
        d['connections'].append({'from':a,'to':b,'route':rounded_route([port(a)]+middle+[port(b)],bend),'radius':radius})
    for i in range(2):
        x=.85+3*i;link(f'tank-{i}:out',f'header:branch-{i}',[[x,2.35,1.1]],.09,.2)
    link('header:pump','pump:in',[[2.05,3.35,.4],[2.05,3.35,1.05],[2.05,3.9,1.05]],.075,.12)
    link('pump:out','boundary:in',[[2.05,5.35,.4]],.06,.25)
    # Every heavy part has explicit contacts; small geometry remains illustrative.
    for name,x,y in [('header-foot-0',.85,2.3),('header-foot-1',3.73,2.3),('boundary-foot-0',3.8,5.3),('boundary-foot-1',4.48,5.3)]:
        d['parts'].append(make_part(name,'column',(x,y,0),(.12,.1,.3)))
        d['bearings'].extend([{'part':name,'on':'floor'},{'part':'header' if name.startswith('header') else 'boundary','on':name}])
    for i in range(3):d['bearings'].append({'part':f'deck-leg-{i}','on':'floor'})
    for name in ['back-rail','front-rail']:d['bearings'].append({'part':name,'on':'deck'})
    d['parts'].append(make_part('control','cabinet',(-1.6,4,0),(.65,.45,1.5)))
    d['bearings'].append({'part':'control','on':'floor'})
    for name,o,parent in [('deck-inspector',(2.6,-.6,2.4),'deck'),('technician',(5,3.8,0),'floor'),('supervisor',(.1,5.8,0),'floor')]:
        d['parts'].append(make_part(name,'worker',o,(.45,.45,1.7),parent=parent))
    d['expected_counts']['worker']=5
    d['route_obstacles']=['deck','stairs','control','hall-column-0','hall-column-1','operator','technician','supervisor']
    return d
