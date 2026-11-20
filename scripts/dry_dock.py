"""Original registered dry-dock scene. Conceptual geometry, no docking certification."""
from collections import Counter
from scene_model import make_part
from typed_interfaces import add_interface
from route_geometry import rounded_route

def hull_parameters():
    # Local X, half breadth, keel height. Flat middle keel has finite contact width.
    stations=[(0,.1,2.8),(2,1.9,1.1),(4,2.7,0),(8,3,0),(18,3,0),(22,2.7,0),(25,1.7,1.3),(27,.1,3.5)]
    vertices=[];faces=[];edges=[]
    for x,w,k in stations:
        vertices.extend([[x,3+y,z] for y,z in [(-min(.22,w/2),k),(-w*.5,k+.5),(-w*.92,2.4),(-w,5),(w,5),(w*.92,2.4),(w*.5,k+.5),(min(.22,w/2),k)]])
    for j in range(len(stations)-1):
        for k in range(8):faces.append([j*8+k,(j+1)*8+k,(j+1)*8+(k+1)%8,j*8+(k+1)%8])
        for k in [0,2,3,4,5,7]:edges.append([j*8+k,(j+1)*8+k])
    faces.extend([list(range(7,-1,-1)),list(range((len(stations)-1)*8,len(stations)*8))])
    return dict(adapter='flat-keel-loft-v1',vertices=vertices,faces=faces,edges=edges,
                limitations='sampled keel contact only; no hull scantlings, lateral stability, displacement or load analysis')

def scene(detail='developed'):
    d=dict(schema_version=2,registered_geometry=True,units='m',grounded=['floor'],parts=[],connections=[],bearings=[],stair_access=[],custom_contacts=[],mounts=[])
    def add(id,kind,o,sz,on=None,**kw):
        p=make_part(id,kind,o,sz,**kw);d['parts'].append(p)
        if on:d['bearings'].append({'part':id,'on':on})
        return p
    add('floor','slab',(0,0,-.3),(36,32,.3))
    add('rear-wall','wall',(0,22,0),(36,.5,7),'floor',parameters={'panel_size':[3,2]})
    add('end-wall','wall',(35.5,0,0),(.5,22,7),'floor',parameters={'panel_size':[3,2]})
    ship=add('ship','custom',(5,11,1.2),(27,6,5),parameters=hull_parameters())
    for i,x in enumerate([10,13,16,19,22,25]):
        name=f'keel-block-{i}';add(name,'footing',(x-.55,13.4,0),(1.1,1.2,1.2),'floor')
        d['custom_contacts'].append({'part':'ship','on':name,'points':[[x-.4,13.85,1.2],[x+.4,13.85,1.2],[x+.4,14.15,1.2],[x-.4,14.15,1.2]]})
    add('deckhouse','cabinet',(18,12.4,6.2),(7,3.2,2.2),'ship')
    add('bridge','cabinet',(19,12.6,8.4),(4.8,2.8,1.6),'deckhouse')
    add('mast','column',(21.2,13.8,10),(.16,.16,2.8),'bridge')
    for i in range(5):add(f'bridge-window-{i}','window',(19.15+i*.85,12.55,8.8),(.65,.08,.85))
    for i,x in enumerate([9,12,15]):add(f'deck-fitting-{i}','cabinet',(x,13,6.2),(.7,.7,.55),'ship')
    for side,y in [('near',11.3),('far',16.65)]:
        add('ship-rail-'+side,'railing',(9,y,6.2),(18,.05,.9),'ship')
    add('walkway','landing',(1,4,2.2),(1.6,13,.2),parameters={'surface':'grating','grid_spacing':.14})
    for i,y in enumerate([4.2,10,16.5]):
        for side,x in enumerate([1.1,2.3]):
            name=f'walkleg-{i}-{side}';add(name,'column',(x,y,0),(.18,.18,2.2),'floor');d['bearings'].append({'part':'walkway','on':name})
    add('stairs','stair',(1,0,0),(1.6,4,2.4),'floor',parameters={'steps':12})
    d['stair_access'].append({'stair':'stairs','landing':'walkway'})
    for name,x in [('left-rail',1),('right-rail',2.59)]:add(name,'railing',(x,4,2.4),(.05,13,1),'walkway',parameters={'start':[x,4,2.4],'end':[x,17,2.4]})
    # One common discharge header; no copied water-plant skid topology.
    header=add('discharge-header','manifold',(6,6.88,2.28),(24,.24,.24))
    for i,x in enumerate([6,12,18,24,29.8]):
        name=f'header-foot-{i}';add(name,'column',(x,6.9,0),(.16,.2,2.28),'floor');d['bearings'].append({'part':'discharge-header','on':name})
    add_interface(header,'external',[24,.12,.12],[1,0,0],.24,'outlet',termination='external')
    header['interfaces']['external']['meaning']='discharge toward an off-scene outfall; never reconnect to a dock sump'
    by={p['id']:p for p in d['parts']}
    def world(ref):
        name,port=ref.split(':');p=by[name];return [a+b for a,b in zip(p['origin'],p['ports'][port])]
    def connect(a,b,via):d['connections'].append({'from':a,'to':b,'route':rounded_route([world(a)]+via+[world(b)],.22),'radius':.12})
    for i,x in enumerate([7,19]):
        p=add(f'pump-{i}','pump',(x,3,0),(3,1.6,1.6),'floor')
        add_interface(p,'in',[.75,.4,.8],[0,-1,0],.24,'inlet')
        add_interface(p,'out',[.75,.8,1.28],[0,0,1],.24,'outlet')
        inlet=add(f'intake-{i}','manifold',(x-1.3,1.8,.68),(1.6,.24,.24))
        add_interface(inlet,'external',[0,.12,.12],[-1,0,0],.24,'inlet',termination='external')
        inlet['interfaces']['external']['meaning']='intake from covered dock sump; underground intake unmodeled, not discharge'
        add_interface(inlet,'pump',[1.6,.12,.12],[1,0,0],.24,'outlet')
        for j,xx in enumerate([x-1.3,x+.08]):
            name=f'intake-foot-{i}-{j}';add(name,'column',(xx,1.82,0),(.16,.2,.68),'floor');d['bearings'].append({'part':inlet['id'],'on':name})
        add_interface(header,f'pump-{i}',[x+.75-6,.12,0],[0,0,-1],.24,'inlet')
        by.update({p['id']:p for p in d['parts']})
        connect(f'intake-{i}:pump',f'pump-{i}:in',[[x+.75,1.92,.8]])
        connect(f'pump-{i}:out',f'discharge-header:pump-{i}',[[x+.75,3.8,1.8],[x+.75,7,1.8]])
        add(f'control-{i}','cabinet',(x+3.8,3.5,0),(1,.55,1.8),'floor')
        add(f'sump-cover-{i}','drain',(x-3.2,1.3,.005),(1.5,1.3,.06))
    for i,(x,y,z,parent) in enumerate([(1.6,10,2.4,'walkway'),(13,1,0,'floor'),(25,4.8,0,'floor'),(14,11.2,0,'floor'),(26,11.2,0,'floor')]):
        add(f'worker-{i}','worker',(x,y,z),(.5,.5,1.75),parent=parent)
    # Visible secondary construction comes from registered components before finishing.
    secondary=[]
    if detail=='developed':
        add('quay','slab',(0,22.5,0),(36,9.5,7),'floor')
        workshop=[]
        for i,x in enumerate([3,7,11]):
            for j,y in enumerate([25,30]):
                name=f'workshop-post-{i}-{j}';add(name,'column',(x,y,7),(.25,.25,3.5),'quay',parameters={'profile':'steel'});workshop.append(name)
        add('workshop-roof','slab',(2.5,24.5,10.5),(9.3,6.2,.2))
        for name in workshop:d['bearings'].append({'part':'workshop-roof','on':name})
        add('workshop-back','wall',(3,30,7),(8.25,.25,3.5),'quay',parameters={'panel_size':[1.5,1]})
        for i,x in enumerate([4,7.5]):add(f'workshop-bench-{i}','cabinet',(x,28.5,7),(2,.8,1),'quay')
        secondary+=workshop+['quay','workshop-roof','workshop-back','workshop-bench-0','workshop-bench-1']
        for i,x in enumerate([6,12,18,24,30]):
            name=f'quay-bollard-{i}';add(name,'column',(x,22.08,7),(.35,.35,.65),'rear-wall');secondary.append(name)
        for i,x in enumerate([8,16,24]):
            name=f'wall-service-{i}';add(name,'cabinet',(x,21.65,4),(1,.35,1.1));secondary.append(name)
            d['mounts'].append({'part':name,'on':'rear-wall','axis':'y','side':-1})
        # Subordinate wall cable routes, not fluid lines. Geometry stays out of pump graph.
        for i,z in enumerate([4.3,5.4]):
            tray=f'wall-tray-{i}';add(tray,'cable_tray',(3,21.5,z),(29,.3,.18),parameters={'orientation':'x'});secondary.append(tray)
            for j,x in enumerate([4,10,16,22,28]):
                name=f'service-bracket-{i}-{j}';add(name,'corbel',(x,21.5,z-.35),(.2,.5,.35),parameters={'top_flat':True});secondary.append(name)
                d['mounts'].append({'part':name,'on':'rear-wall','axis':'y','side':-1})
                d['bearings'].append({'part':tray,'on':name})
        for i,x in enumerate([10,15,27]):
            name=f'deck-hatch-{i}';add(name,'cabinet',(x,13,6.2),(.9,1.2,.18),'ship');secondary.append(name)
    d['expected_counts']=dict(Counter(p['kind'] for p in d['parts']))
    d['callouts']=[{'id':str(i),'text':t,'target':target} for i,(t,target) in enumerate([
        ('KEEL BLOCKS','keel-block-2'),('SUCTION LINE','intake-0'),('DEWATERING PUMP','pump-0'),('MAINTENANCE WALKWAY','walkway'),('DISCHARGE HEADER','discharge-header')])]
    d['detail_regions']=[
        {'name':'vessel and contact','primary':['ship'],'secondary':['deckhouse','bridge','mast','keel-block-2']+[x for x in secondary if x.startswith('deck')],'microdetails':'fair plate strakes, hull seams, scuppers, wheelhouse frames, keel timber caps and visible contact shadows'},
        {'name':'pumping and services','primary':['pump-0','pump-1','discharge-header'],'secondary':['intake-0','intake-1','control-0','control-1']+[x for x in secondary if x.startswith(('wall','service'))],'microdetails':'casing joints, nozzle necks and flanges, saddle anchors, cabinet hinges, attached cable routes distinct from fluid routes'},
        {'name':'dock access','primary':['walkway','stairs'],'secondary':['walkleg-0-0','left-rail','right-rail']+[x for x in secondary if x.startswith('quay')],'microdetails':'grating, stringer ends, bolts, toe boards, wall construction joints and selective near/far line emphasis'}]
    if detail=='developed':
        d['detail_regions'].append({'name':'quay workshop context','primary':['quay','workshop-roof'],
            'secondary':[key for key in secondary if key.startswith('workshop') and key!='workshop-roof'],
            'microdetails':'steel post base plates, roof edge seams and drainage, cabinet hardware, paving joints; subordinate harbor setting, no unrelated extra machines'})
    return d
