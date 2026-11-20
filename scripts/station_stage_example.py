"""Portable regression example: an integrated contour-side ropeway terminal.
The supplied seed makes this example reproducible, not a universal composition.
No artwork or project history is loaded. Geometry originates in procedural parts.
"""
import sys,json,math,copy,secrets
from pathlib import Path
import numpy as np
import argparse
SKILL=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(SKILL),str(SKILL/'scripts')]
from kit import make_part as p
from render_scene import Mesh,build,Renderer
from scene_model import validation_report
from design_intent import DesignIntent
from design_variants import generate_candidates,choose_candidate
from design_realization import edge_id
from assembly_model import cut_host,RigidTransform,compile_cutaway
from room_programs import place_program
from projection_review import review,choose
from view_contract import create
from finish_contract import freeze,request

def build_station(RUN,seed=895756014):
    def save(stage,name,obj):
     path=RUN/stage/name
     with path.open('x',encoding='utf-8') as out:out.write(obj if isinstance(obj,str) else json.dumps(obj,indent=2))
     return path
    seed=int(seed)
    from pattern_rules import select_patterns
    early={'design_intent':{'domain':'building'},'visual_plan':{'view_intent':'exterior'},'context_plan':{'mode':'situated'},'light_material_plan':{'value_policy':'open_air'}}
    save('01-site','early-drawing-rules.json',select_patterns(early))
    brief='Mountain cable-car station with a well-equipped machine hall, workshop and boarding area; four workers and five English annotations.'
    save('01-site','brief.txt',brief);save('01-site','site-and-operation.json',{'seed':seed,'site':'bedrock bench on alpine slope, lower south face exposed','entry':'east apron to boarding and common front service walk','operating_axis':'two rope legs depart south toward valley','levels':'one occupied station floor, overhead rope and suspended cabin','limits':'Conceptual stationary ropeway, no dynamics or strength calculation'})
    intent=DesignIntent.from_data({'domain':'building','subject':brief,'constraints':{'connected':True,'required_roles':['machinery','workshop','boarding']},'choices':{'levels':1,'zones_per_level':3},'program_roles':['machinery','workshop','boarding']})
    cands=generate_candidates(intent,seed,3)
    # Three site-fitted programs; every alternative keeps drive/boarding adjacent.
    for c,(wx,wy) in zip(cands,[(-12,6),(-12,-5),(13,6)]):
     for n,role,center in zip(c['nodes'],['boarding','machinery','workshop'],[[7.15,-5,0],[0,6,0],[wx,wy,0]]):n.update(role=role,program=role,center=center)
     c['edges']=[{'from':'L0Z0','to':'L0Z1','kind':'circulation','requires':['opening','clearance']},{'from':'L0Z1','to':'L0Z2','kind':'circulation','requires':['opening','clearance']}]
    selected,evidence=choose_candidate(intent,cands);wx,wy=selected['nodes'][2]['center'][:2]
    save('03-massing','alternatives-and-selection.json',evidence);save('03-massing','decision.json',{'selected':selected['id'],'workshop_center':[wx,wy],'reason':'Seeded choice among distinct left-rear, left-front and right-rear service wings; all preserve south rope departure and independent east boarding access.'})
    s={'schema_version':2,'workflow_version':3,'registered_geometry':True,'validation_policy':'strict','support_contract_version':1,'units':'m','parts':[],'connections':[],'grounded':['bedrock'],'ground_surfaces':[{'id':'subsurface','type':'plane','point':[0,0,-3],'normal':[0,0,1],'bounds':{'min':[-30,-20,-3],'max':[30,20,-3]}}],'ground_contacts':[{'part':'bedrock','surface':'subsurface','points':[[-10,-10,-3],[10,-10,-3],[0,10,-3]]}],'bearings':[],'mounts':[],'custom_contacts':[],'surface_contacts':[],'hosts':[],'openings':[],'assemblies':[],'functional_contracts':[],'access_nodes':[],'access_volumes':[],'access_roots':['entry'],'expected_counts':{'worker':4},'delivery_counts':{'worker':4,'annotations':5,'gondola_cabin':1},'design_intent':intent.to_data(),'design_selection':evidence}
    def add(i,k,o,d,on='floor',**kw):
     s['parts'].append(p(i,k,o,d,**kw))
     if on:s['bearings'].append({'part':i,'on':on})
    def custom(i,m,on=None,patch=None,role=''):
     vv=[];ff=[];ee=[]
     for f,t in m.faces:ff.append(list(range(len(vv),len(vv)+len(f))));vv.extend(f)
     for a,b in m.edges:ee.append([len(vv),len(vv)+1]);vv.extend([a,b])
     v=np.array(vv);lo=v.min(0);dim=v.max(0)-lo
     add(i,'custom',lo.tolist(),dim.tolist(),None,parameters={'adapter':'ropeway-static-v1' if i=='ropeway' else 'site-rock-bench-v1','vertices':(v-lo).tolist(),'faces':ff,'edges':ee,'limitations':'Finite bounds/nondegenerate indexed geometry and sampled contact; supplemental local station tests cover explicit shaft/grip/rope topology. No stress, slip, dynamics or geotechnical certification.'},semantic_role=role)
     if on:s['custom_contacts'].append({'part':i,'on':on,'points':patch})
    # Actual geological support volume: terrace bench, sloping exposed sides.
    x0=min(-7.5,wx-5.5);x1=max(11,wx+5.5);y0=min(-11.5,wy-5.5);y1=max(11.5,wy+5.5)
    m=Mesh();top=[[x0,y0,0],[x1,y0,0],[x1,y1,0],[x0,y1,0]];bottom=[[x0-2,y0-2,-3],[x1+2,y0-2,-3],[x1+2,y1+2,-3],[x0-2,y1+2,-3]]
    m.faces.extend([(top,0),(bottom[::-1],0)])
    for j in range(4):k=(j+1)%4;m.faces.append(([top[j],bottom[j],bottom[k],top[k]],0));m.edges.extend([(np.array(top[j]),np.array(top[k])),(np.array(top[j]),np.array(bottom[j]))])
    custom('bedrock',m,role='cut alpine rock bench');add('foundation','footing',[x0+.2,y0+.2,0],[x1-x0-.4,y1-y0-.4,.25],'bedrock');add('floor','slab',[x0+.2,y0+.2,.25],[x1-x0-.4,y1-y0-.4,.25],'foundation')
    mat={'nodes':{},'edges':{},'zones':{},'requirements':{},'topology_transform':{'translation':[0,0,0],'scale_xy':1}};s['materialized_design']=mat
    def aperture_wall(id,o,d,holes):
     cut=cut_host(p(id,'wall',o,d),holes,normal_axis='y');s['parts']+=cut['parts'];s['hosts']+=cut['hosts'];s['openings']+=cut['openings']
     # Disjoint subtraction cells: bottom cells bear on floor, upper cells on cells below;
     # lintel-only cells side mount to supported neighbor at same height.
     pending=list(cut['parts']);done=[]
     while pending:
      progress=False
      for q in pending[:]:
       qo=q['origin'];qs=q['size'];match=None;typ='bearings'
       if abs(qo[2]-.5)<1e-6:match='floor'
       else:
        for b in done:
         bo=b['origin'];bs=b['size']
         if abs(bo[2]+bs[2]-qo[2])<1e-6 and min(bo[0]+bs[0],qo[0]+qs[0])-max(bo[0],qo[0])>1e-6:match=b['id'];break
        if not match:
         for b in done:
          bo=b['origin'];bs=b['size']
          if abs(bo[0]+bs[0]-qo[0])<1e-6 and min(bo[2]+bs[2],qo[2]+qs[2])-max(bo[2],qo[2])>1e-6:match=b['id'];typ='mounts';break
       if match:
        s[typ].append({'part':q['id'],'on':match,**({'axis':'x','side':1} if typ=='mounts' else {})});done.append(q);pending.remove(q);progress=True
      if not progress:raise ValueError('Unsupported lintel cells '+str([q['id'] for q in pending]))
     return [q['id'] for q in cut['parts']]
    # Machinery enclosure with real passenger-independent service door and two rope apertures.
    start=len(s['parts']);add('machine-rear','wall',[-6.5,10.7,.5],[13,.3,6]);add('machine-west','wall',[-6.5,1,.5],[.3,9.7,6]);add('machine-east','wall',[6.2,1,.5],[.3,9.7,6])
    aperture_wall('machine-front',[-6.5,.7,.5],[13,.3,6],[{'id':'machine-door','origin':[4.4,.7,.5],'size':[1.6,.3,2.5]},{'id':'rope-left-opening','origin':[-3.3,.7,4.8],'size':[.6,.3,.7]},{'id':'rope-right-opening','origin':[2.7,.7,4.8],'size':[.6,.3,.7]}]);add('machine-roof','slab',[-6.5,.7,6.5],[13,10.3,.25],'machine-rear')
    add('control-panel','cabinet',[4.65,8,.5],[1.1,.8,2.1]);add('spares-cabinet','cabinet',[-5.8,8,.5],[1,.8,1.4]);machine_ids=[q['id'] for q in s['parts'][start:]]
    # Equipped workshop sized for workbench movement and two technicians.
    start=len(s['parts']);add('workshop-rear','wall',[wx-5,wy+4.7,.5],[10,.3,3.8]);add('workshop-west','wall',[wx-5,wy-4.7,.5],[.25,9.4,3.8]);add('workshop-east','wall',[wx+4.75,wy-4.7,.5],[.25,9.4,3.8]);aperture_wall('workshop-front',[wx-5,wy-5,.5],[10,.3,3.8],[{'id':'workshop-door','origin':[wx-1.2,wy-5,.5],'size':[2.4,.3,2.5]}]);add('workshop-roof','slab',[wx-5,wy-5,4.3],[10,10,.22],'workshop-rear')
    kit=place_program('workshop','shop',floor_id='floor',wall_parts={'north':['workshop-rear']},scene_parts=s['parts'],transform=RigidTransform((wx,wy,.5)),width=10,depth=9.4,seed=seed,variant_index=2)
    for field in ['parts','bearings','mounts','assemblies']:s[field]+=kit.get(field,[])
    s['assemblies'].append(kit['assembly']);workshop_ids=[q['id'] for q in s['parts'][start:]]
    # Boarding deck touches cabin's doorway threshold; public side is open to apron.
    start=len(s['parts']);add('boarding-platform','slab',[4.2,-9,.5],[5.6,8.5,.15]);add('boarding-controls','console',[8,-1.9,.65],[1.25,.8,1.2],'boarding-platform');add('gate-pedestal','cabinet',[8,-7,.65],[.45,.5,1],'boarding-platform');add('waiting-seat','seat',[8.3,-5,.65],[1.1,2,1],'boarding-platform')
    for j,(x,y) in enumerate([(4.25,-9),(9.45,-9),(4.25,-.8),(9.45,-.8)]):add('canopy-post'+str(j),'column',[x,y,.65],[.3,.3,5.85],'boarding-platform',parameters={'profile':'steel'})
    add('boarding-roof','slab',[4.2,-9,6.5],[5.6,8.5,.2],'canopy-post0');boarding_ids=[q['id'] for q in s['parts'][start:]]
    # Original defining-system adapter. Stationary integrated assembly: drive -> wheel ->
    # two tangent rope legs -> fixed grip -> hanger -> cabin. A common physical mesh
    # retains all actual supports and contacts; source subassemblies remain documented.
    m=Mesh();m.box([-3.8,3,.5],[7.6,6,.25])
    for xx in [-1.1,.8]:
     for yy in [4,5.8]:m.box([xx,yy,.75],[.3,.3,3.3])
    for xx in [-1.1,.8]:m.box([xx,4,4.05],[.3,2.1,.25])
    m.box([-1.1,4,4.05],[2.2,.3,.25]);m.box([-1.1,5.8,4.05],[2.2,.3,.25])
    m.box([-.55,4.45,.75],[1.1,1.1,.9]);m.sweep([[0,5,1.65],[0,5,5.25]],.16,n=16)
    # annular bearing housing with an actual shaft aperture, connected to bridge.
    def ring(cx,cy,z,ri,ro,h):
     for t,u in zip(np.linspace(0,2*math.pi,49)[:-1],np.linspace(0,2*math.pi,49)[1:]):
      a=[cx+ro*math.cos(t),cy+ro*math.sin(t),z];b=[cx+ro*math.cos(u),cy+ro*math.sin(u),z];c=[cx+ri*math.cos(u),cy+ri*math.sin(u),z];d=[cx+ri*math.cos(t),cy+ri*math.sin(t),z]
      A=[a[0],a[1],z+h];B=[b[0],b[1],z+h];C=[c[0],c[1],z+h];D=[d[0],d[1],z+h]
      m.faces += [([a,b,B,A],0),([d,D,C,c],0),([A,B,C,D],0),([d,c,b,a],0)];m.edges += [(np.array(A),np.array(B)),(np.array(a),np.array(b))]
    ring(0,5,4.3,.16,.5,.3)
    m.box([-1.1,4.5,4.1],[.7,1,.2]);m.box([.4,4.5,4.1],[.7,1,.2])
    for z in [5.04,5.22]:ring(0,5,z,2.82,3.05,.08)
    for t in np.linspace(0,2*math.pi,8,endpoint=False):m.sweep([[0,5,5.17],[2.88*math.cos(t),5+2.88*math.sin(t),5.17]],.09,n=8)
    m.sweep([[0,5,5.04],[0,5,5.3]],.35,n=24)
    m.box([-2.5,4.5,.75],[1.5,1,.35]);m.sweep([[-2.5,5,1.4],[-1,5,1.4]],.42,n=24);m.sweep([[-1,5,1.4],[-.55,5,1.4]],.10,n=12)
    # Rope tangent return and external departures, registered continuous centerline.
    rope=[[-3,-13,5.17],[-3,5,5.17]]+[[3*math.cos(t),5+3*math.sin(t),5.17] for t in np.linspace(math.pi,0,61)[1:]]+[[3,-13,5.17]]
    m.sweep(rope,.045,n=8);m.edges.extend((np.array(a),np.array(b)) for a,b in zip(rope,rope[1:]))
    # Fixed grip surrounds right rope at y=-5.5; hanger descends to cabin roof.
    m.box([2.86,-5.7,5.08],[.28,.4,.2]);m.box([2.94,-5.65,3.1],[.12,.3,1.98])
    # Distinct gondola shell: chamfered footprint, open east doorway, roof and glazing frames.
    poly=[(1.8,-6.9),(2.05,-7.2),(3.7,-7.2),(4,-6.9),(4,-4.2),(3.7,-3.9),(2.05,-3.9),(1.8,-4.2)]
    bottom=[[x,y,.65] for x,y in poly];top=[[x,y,.85] for x,y in poly];roof=[[x,y,3.1] for x,y in poly];m.faces += [(bottom[::-1],0),(top,0),(roof,0)]
    for j in range(8):k=(j+1)%8;m.faces.append(([bottom[j],bottom[k],top[k],top[j]],0));m.edges.append((np.array(roof[j]),np.array(roof[k])))
    for j,(x,y) in enumerate(poly):m.box([x-.035,y-.035,.85],[.07,.07,2.25])
    for j in [0,1,2,4,5,6,7]:
     k=(j+1)%8;a=top[j];b=top[k];m.faces.append(([a,b,[b[0],b[1],1.35],[a[0],a[1],1.35]],0));m.edges.append((np.array([a[0],a[1],1.35]),np.array([b[0],b[1],1.35])))
    m.box([2,-6.8,.85],[.5,2.6,.45]);m.box([3.95,-5.9,.65],[.25,.9,.08])
    custom('ropeway',m,'floor',[[-3.7,3.1,.5],[3.7,3.1,.5],[3.7,8.9,.5]],'integrated motor gearbox shaft bearing bullwheel haul rope grip hanger and suspended gondola')
    system={'rope_centerline':rope,'radius':3,'wheel_center':[0,5,5.17],'motor_axis':[[-2.5,5,1.4],[-.55,5,1.4]],'reducer_input':[-.55,5,1.4],'reducer_output':[0,5,1.65],'shaft_axis':[[0,5,1.65],[0,5,5.25]],'grip':[3,-5.5,5.17],'hanger_top':[3,-5.5,5.17],'hanger_bottom':[3,-5.5,3.1],'cabin_roof_z':3.1,'external_boundary':'both taut rope legs continue downhill beyond y=-13; lower terminal outside scope'}
    def check_system(d):
     if math.dist(d['motor_axis'][-1],d['reducer_input'])>1e-6:raise ValueError('detached reducer input')
     if math.dist(d['reducer_output'],d['shaft_axis'][0])>1e-6:raise ValueError('detached output shaft')
     if any(abs(q[0])+abs(q[1]-5)>1e-6 for q in d['shaft_axis']):raise ValueError('noncoaxial wheel shaft')
     if abs(d['grip'][0]-3)>1e-6 or abs(d['grip'][2]-5.17)>1e-6:raise ValueError('grip misses rope')
     if math.dist(d['grip'],d['hanger_top'])>1e-6 or abs(d['hanger_bottom'][2]-d['cabin_roof_z'])>1e-6:raise ValueError('disconnected suspension')
     if len(d['rope_centerline'])<60 or any(math.dist(a,b)<1e-8 for a,b in zip(d['rope_centerline'],d['rope_centerline'][1:])):raise ValueError('invalid continuous rope route')
     return 'passed: explicit endpoint, axis and stationary contact geometry; no dynamics/strength calculation'
    check_system(system);bad=copy.deepcopy(system);bad['grip'][0]+=.4
    try:check_system(bad);raise AssertionError('negative failed')
    except ValueError:pass
    save('06-systems','ropeway-contract-v1.json',system);save('06-systems','adapter-tests-v1.json',{'positive':check_system(system),'detached_grip':'rejected','scope':'static original adapter; raw triangle bounds checked by registered geometry; no arbitrary collision or force solver'})
    # Four workers, two in workshop rather than arbitrary one-per-room allocation.
    actor_specs=[('mechanic',[5.1,4,.5],'floor','inspect drive from service aisle'),('bench-tech',[wx-2,wy-1,.5],'floor','inspect bench and tools'),('workshop-tech',[wx+2,wy-2,.5],'floor','check inspection equipment'),('boarding-attendant',[6.4,-7,.65],'boarding-platform','supervise open cabin doorway')]
    for name,o,parent,task in actor_specs:add(name,'worker',o,[.55,.5,1.75],parent,parent=parent)
    s['actor_plan']={'version':1,'exact_count':4,'actors':[{'id':name,'task':task,'physical_height':1.75,'support':parent,'pose':'standing'} for name,o,parent,task in actor_specs]}
    # Bind selected graph nodes to actual spaces, primary fixtures and allocated members.
    node_data={'L0Z0':(boarding_ids,'boarding',[4.2,-10,0],[10.1,0,6.8],[7.15,-5,0],'boarding-controls',[6,-2,1.5]),'L0Z1':(machine_ids,'machinery',[-6.5,.7,0],[6.5,11,6.8],[0,6,0],'control-panel',[5.2,2,1.5]),'L0Z2':(workshop_ids,'workshop',[wx-5,wy-5,0],[wx+5,wy+5,4.6],[wx,wy,0],'shop/bench-0/top',[wx,wy,1.5])}
    for id,(members,program,lo,hi,anchor,proof,access) in node_data.items():
     for part in s['parts']:
      if part['id'] in members:part['design_node']=id;part['design_program']=program
     next(q for q in s['parts'] if q['id']==proof)['semantic_role']=program+' defining fixture'
     mat['nodes'][id]=members;mat['zones'][id]={'program':program,'min':lo,'max':hi,'anchor':anchor,'access_node':id,'program_evidence':[proof]};s['access_nodes'].append({'id':id,'position':access})
    # Exterior entry and L-shaped service corridors: generated after room placement.
    positions={n['id']:n['position'] for n in s['access_nodes']};s['access_nodes'].append({'id':'entry','position':[9.5,-10.5,1.5]})
    def route(key,names,pts,openings=None):
     vids=[]
     for id,pt in zip(names[1:-1],pts[1:-1]):s['access_nodes'].append({'id':id,'position':pt})
     for j,(a,b) in enumerate(zip(pts,pts[1:])):
      v=key+f'-{j}';vids.append(v);s['access_volumes'].append({'id':v,'from':names[j],'to':names[j+1],'min':[min(a[0],b[0])-.42,min(a[1],b[1])-.42,.8],'max':[max(a[0],b[0])+.42,max(a[1],b[1])+.42,2.8],'critical':True})
     if openings is not None:mat['edges'][key]=vids;mat['requirements'][key]={'opening':{'openings':openings},'clearance':{'access_volumes':vids,'min_height':1.8}}
    route('entry-access',['entry','entry-turn','L0Z0'],[[9.5,-10.5,1.5],[6,-10.5,1.5],positions['L0Z0']])
    key=edge_id(selected['edges'][0]);route(key,['L0Z0','public-turn','service-turn','L0Z1'],[positions['L0Z0'],[6,-.05,1.5],[5.2,-.05,1.5],positions['L0Z1']],['machine-door'])
    key=edge_id(selected['edges'][1]);route(key,['L0Z1','m-exit','shop-approach','L0Z2'],[positions['L0Z1'],[5.2,-.05,1.5],[wx,wy-6,1.5],positions['L0Z2']],['machine-door','workshop-door'])
    # Five useful annotations, all separately named visible owners.
    s['callouts']=[{'id':'drive','text':'DRIVE SYSTEM','target':'ropeway'},{'id':'control','text':'MACHINE CONTROLS','target':'control-panel'},{'id':'bench','text':'MAINTENANCE BENCH','target':'shop/bench-0/top'},{'id':'tools','text':'TOOL STORAGE','target':'shop/toolboard'},{'id':'platform','text':'BOARDING PLATFORM','target':'boarding-platform'}]
    details=[{'name':'integrated ropeway','primary':['ropeway'],'secondary':['control-panel','spares-cabinet'],'microdetails':['wheel groove, hub fasteners, bearings and motor fins','two continuous cable legs, fixed grip and hanger attached to cabin roof','gondola glazing frames and open east doorway']},{'name':'workshop','primary':['shop/bench-0/top'],'secondary':['shop/bench-1/top','shop/toolboard','shop/tool-cabinet','shop/inspection-table/top'],'microdetails':['vise, drawers, toolboard clips and supported inspection case']},{'name':'boarding','primary':['boarding-platform'],'secondary':['boarding-controls','gate-pedestal','waiting-seat'],'microdetails':['gate hardware, edge strip and column baseplates, open doorway alignment']}]
    s['detail_regions']=[dict(d,microdetails='; '.join(d['microdetails'])) for d in details];s['detail_budget']={'regions':details,'usage_size':[1600,1200]};prim=[k for d in details for k in d['primary']];sec=[k for d in details for k in d['secondary']]
    s['visual_plan']={'objective':'Explain an integrated mountain ropeway, equipped workshop and public boarding with four workers','primary':prim,'secondary':sec,'readable':prim+[a[0] for a in actor_specs],'usage_size':[1600,1200],'view_intent':'cutaway','subject_framing':{'ids':prim+sec,'purpose':'Mechanism and programs dominate the cutaway','min_width_fraction':.45,'min_height_fraction':.35,'min_owned_area_fraction':.02}}
    s['context_plan']={'mode':'situated','entities':[{'id':'bedrock','role':'support','reason':'Real bench supporting terrace, cut downslope face sets cable departure'}],'max_area_fraction':.8,'exact_counts':{'worker':4},'exclusions':['extra_workers','unconnected_cabin']}
    s['light_material_plan']={'value_policy':'open_air','key_direction':[-.6,-.8,1.5],'materials':{'bedrock':{'family':'stone','density':.08},'floor':{'family':'concrete'},'ropeway':{'family':'matte_metal'},'shop/bench-0/top':{'family':'wood'}}}
    s['functional_contracts']=[{'part':'ropeway','role':'component_set','members':['ropeway','control-panel'],'required_kinds':['custom','cabinet']},{'part':'shop/bench-0/top','role':'component_set','members':['shop/bench-0/top','shop/toolboard','shop/tool-cabinet'],'required_kinds':['slab','cabinet'] }]
    
    from kit import make_part
    s=json.loads(json.dumps(s))
    old=next(p for p in s['parts'] if p['id']=='ropeway');v=np.array(old['parameters']['vertices'])+old['origin'];faces=[v[f] for f in old['parameters']['faces']];edges=[v[e] for e in old['parameters']['edges']]
    def clip(poly,y,above):
     out=[]
     for a,b in zip(poly,np.roll(poly,-1,axis=0)):
      ia=(a[1]>=y-1e-9) if above else (a[1]<=y+1e-9);ib=(b[1]>=y-1e-9) if above else (b[1]<=y+1e-9)
      if ia:out.append(a)
      if ia!=ib:out.append(a+(b-a)*((y-a[1])/(b[1]-a[1])))
     if len(out)<3:return None
     clean=[]
     for a in out:
      if not clean or np.linalg.norm(a-clean[-1])>1e-8:clean.append(a)
     if len(clean)>1 and np.linalg.norm(clean[0]-clean[-1])<1e-8:clean.pop()
     if len(clean)<3:return None
     return np.array(clean)
    def portion(name,low,high,side=None):
     ff=[]
     for f in faces:
      q=f
      for y,above in [(low,True),(high,False)]:
       if y is not None and q is not None:q=clip(q,y,above)
      if q is not None and (side is None or (q[:,0].mean()<0)==(side=='left')):ff.append(q)
     # The only cut solids are the two octagonal cable sections. Close each with
     # source-derived polygon points, creating opposite planar virtual interfaces.
     for y,normal in [(low,-1),(high,1)]:
      if y is None:continue
      for cx in [-3,3]:
       if side and (cx<0)!=(side=='left'):continue
       pts=[]
       for f in ff:
        for a in f:
         if abs(a[1]-y)<1e-7 and abs(a[0]-cx)<.06 and abs(a[2]-5.17)<.06 and not any(np.linalg.norm(a-b)<1e-7 for b in pts):pts.append(a)
       if len(pts)<3:raise ValueError('missing rope cut')
       pts.sort(key=lambda a:math.atan2(a[2]-5.17,a[0]-cx))
       q=np.array(pts);n=np.cross(q[1]-q[0],q[2]-q[0]);q=q if n[1]*normal>0 else q[::-1];ff.append(q)
     vv=[];ii=[];ee=[]
     for f in ff:
      # Triangulate and discard only numerically collinear clipping fragments.
      for j in range(1,len(f)-1):
       t=f[[0,j,j+1]]
       if np.linalg.norm(np.cross(t[1]-t[0],t[2]-t[0]))>1e-9:ii.append(list(range(len(vv),len(vv)+3)));vv.extend(t)
     for a,b in edges:
      pa,pb=a.copy(),b.copy();good=True
      for y,above in [(low,True),(high,False)]:
       if y is None:continue
       ia=pa[1]>=y if above else pa[1]<=y;ib=pb[1]>=y if above else pb[1]<=y
       if not ia and not ib:good=False;break
       if ia!=ib:
        at=pa+(pb-pa)*((y-pa[1])/(pb[1]-pa[1]))
        if not ia:pa=at
        else:pb=at
      if good and (side is None or ((pa[0]+pb[0])/2<0)==(side=='left')) and np.linalg.norm(pa-pb)>1e-8:ee.append([len(vv),len(vv)+1]);vv.extend([pa,pb])
     vv=np.array(vv);lo=vv.min(0);sz=vv.max(0)-lo
     return make_part(name,'custom',lo.tolist(),sz.tolist(),semantic_role='continuous ropeway subassembly; artificial source partition, not a physical cable splice',parameters={'adapter':'ropeway-section-v2','vertices':(vv-lo).tolist(),'faces':ii,'edges':ee,'limitations':old['parameters']['limitations']})
    parts=[portion('drive-unit',1,None),portion('suspended-cabin-and-ropes',None,.7),portion('left-rope-interface',.7,1,'left'),portion('right-rope-interface',.7,1,'right')]
    s['parts']=[p for p in s['parts'] if p['id']!='ropeway']+parts
    for c in s['custom_contacts']:
     if c['part']=='ropeway':c['part']='drive-unit'
    def patch(cx,y):return [[cx-.012,y,5.158],[cx+.012,y,5.158],[cx,y,5.182]]
    for side,cx in [('left',-3),('right',3)]:
     s['surface_contacts'] += [{'part':side+'-rope-interface','on':'drive-unit','points':patch(cx,1)},{'part':'suspended-cabin-and-ropes','on':side+'-rope-interface','points':patch(cx,.7)}]
    s['ground_contacts'][0]['points']=[[-5,-5,-3],[5,-5,-3],[0,5,-3]]
    next(p for p in s['parts'] if p['id']=='boarding-attendant')['origin'][0]=7.1
    for c in s['callouts']:
     if c['target']=='ropeway':c['target']='drive-unit'
    for field in ['detail_regions','detail_budget']:
     ds=s[field] if field=='detail_regions' else s[field]['regions']
     for d in ds:
      d['primary']=['drive-unit' if i=='ropeway' else i for i in d['primary']]
      if d['name']=='integrated ropeway':d['secondary'].append('suspended-cabin-and-ropes')
    for key in ['primary','readable']:
     s['visual_plan'][key]=['drive-unit' if i=='ropeway' else i for i in s['visual_plan'][key]]
    s['visual_plan']['readable'].append('suspended-cabin-and-ropes');s['visual_plan']['secondary'].append('suspended-cabin-and-ropes')
    s['visual_plan']['subject_framing']['ids']=['drive-unit' if i=='ropeway' else i for i in s['visual_plan']['subject_framing']['ids']]+['suspended-cabin-and-ropes']
    s['light_material_plan']['materials']['drive-unit']=s['light_material_plan']['materials'].pop('ropeway');s['light_material_plan']['materials']['suspended-cabin-and-ropes']={'family':'matte_metal'}
    for c in s['functional_contracts']:
     if c['part']=='ropeway':c['part']='drive-unit';c['members']=['drive-unit','suspended-cabin-and-ropes','left-rope-interface','right-rope-interface','control-panel']
    
    from station_architecture import upgrade
    s=upgrade(s,save)
    from annotation_policy import configure
    return configure(s,requested=True,request_excerpt='four workers and five English annotations')

def main():
    from history_run import new_run
    from architecture_stages import report,record_stage,save_record
    from station_views import candidates
    import shutil
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,required=True)
    args=parser.parse_args();run=new_run(args.project,'mountain-station')
    source=run/'01-site'/'source';source.mkdir()
    for name in ('station_stage_example.py','station_architecture.py','station_views.py','architecture_stages.py'):
        shutil.copyfile(SKILL/'scripts'/name,source/name)
    scene=build_station(run)
    (run/'04-structure'/'physical-final.json').write_text(json.dumps(scene),encoding='utf-8')
    validation=validation_report(scene)
    (run/'04-structure'/'physical-validation.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
    (run/'04-structure'/'architectural-validation.json').write_text(json.dumps(report(scene),indent=2),encoding='utf-8')
    if validation['status']!='passed':raise ValueError('physical checks failed; inspect retained report')
    print('HISTORY',run,flush=True)
    candidates(scene,run)
    print('Inspect candidate guides, select a camera, then approve stages 1-7 on that exact scene and view before freeze. No artistic PNG was generated.',flush=True)

if __name__=='__main__':main()
