"""Original, reusable occupied-room programs with real compound assemblies.

Local geometry is independent of a bunker or a fixed level count. A caller supplies
the floor, wall fragments and placement frame. The central cross remains clear;
small/unknown footprints are rejected instead of shrinking equipment arbitrarily.
Fixtures are conceptual furniture, not electrical, medical or machinery simulation.
"""
import copy
import hashlib
import random
from assembly_model import bed,workbench,storage_rack,compose_assembly,RigidTransform

VERSION='room-programs-1'
PROGRAMS={
 'control':{'description':'Operator consoles and seats, a communications rack, document storage and a planning surface.',
    'fine_detail':'Console face divisions, communications module seams, document drawer fronts and planning-table edge joints; preserve the open route between workstations.'},
 'dormitory':{'description':'Separate sleeping berths, bedside surfaces, personal lockers, a shared writing desk and low luggage storage.',
    'fine_detail':'Mattress/frame separation, folded bedding, locker doors, bedside drawer pulls and desk joinery; preserve the circulation beside each berth.'},
 'storage':{'description':'Open shelving with varied bins, supported palletized supplies and a packing table with sorting containers.',
    'fine_detail':'Shelf-to-upright joints, different bin proportions, pallet sleepers and packing-table edges; keep the inventory accessible from the clear aisle.'},
 'workshop':{'description':'Framed workbenches with under-bench drawers, a mounted toolboard, a supported vise and an inspection table.',
    'fine_detail':'Bench leg/top joints, vise jaws, toolboard fixtures, drawer fronts and inspection-case seams; retain work surfaces and service access.'},
 'utilities':{'description':'Wall-mounted distribution cupboards, local service consoles, maintenance storage and connected rectangular ventilation fittings.',
    'fine_detail':'Distribution enclosure divisions, service-console faces, filter cassette frame and rectangular duct seams; do not invent process pipes or unsupported cables.'},
 'medical':{'description':'Patient berths with bedside units, low supplies storage and a framed treatment cart with separate trays.',
    'fine_detail':'Mattress and pillow layers, bedside drawer fronts, cart tray rims and supplies-case seams; no medical performance or unsupported human pose is implied.'}}

def _stable_seed(seed,program):
    if type(seed)!=int or seed<0:raise ValueError('nonnegative integer room seed required')
    return int.from_bytes(hashlib.sha256(f'{seed}:{program}'.encode()).digest()[:8],'big')

def program_assembly(program,*,width=7.4,depth=7.4,seed=1,variant_index=0):
    """Return one local program; external supports are @floor and @north.

    Width/depth are clear inside dimensions. The current kit needs >=7.4 x 7.4 m;
    those are explicit kit limits, not general rules for rooms or room counts.
    Three functional secondary arrangements vary across instance/seed while primary
    IDs remain stable for semantic callouts.
    """
    if program not in PROGRAMS:raise ValueError('unsupported room program: '+str(program))
    if min(width,depth)<=0 or width<7.4-1e-8 or depth<7.4-1e-8:raise ValueError('room program needs clear footprint >=7.4 x 7.4 m')
    if type(variant_index)!=int or variant_index<0:raise ValueError('nonnegative variant index required')
    rng=random.Random(_stable_seed(seed,program));variant=(variant_index+rng.randrange(3))%3
    left=-width/2+.7;right=width/2-2.7;back=depth/2-1.7;front=-depth/2+.4
    s={'units':'m','parts':[],'bearings':[],'mounts':[],'assemblies':[]}
    by={};objects=[];detail=[]
    def add(name,kind,o,size,on=None,role=None,material='matte_metal',**extra):
        p={'id':name,'kind':kind,'origin':list(o),'size':list(size),'semantic_role':role or program+'_fixture_member',
           'design_program':program,'material_family':material,**extra};s['parts'].append(p);by[name]=p
        if on:s['bearings'].append({'part':name,'on':on})
        return name
    def mount(name,on,axis='y',side=-1):s['mounts'].append({'part':name,'on':on,'axis':axis,'side':side})
    def group(name,role,description,members):
        s['assemblies'].append({'id':name,'role':role,'description':description,'members':list(members),'ground_contacts':[]})
        objects.append(name)
    def merge(fragment,origin,role,description):
        placed=compose_assembly(fragment,RigidTransform(tuple(origin)))
        for p in placed['parts']:
            p.update(design_program=program,semantic_role=role+'_member',material_family='wood' if role=='workbench' and p['id'].endswith('/top') else 'cloth' if '/mattress' in p['id'] else 'matte_metal')
            by[p['id']]=p
        s['parts'].extend(placed['parts']);s['bearings'].extend(placed.get('bearings',[]));s['mounts'].extend(placed.get('mounts',[]))
        for member in placed['assembly'].get('ground_contacts',[]):s['bearings'].append({'part':member,'on':'@floor'})
        placed['assembly']['description']=description;s['assemblies'].append(placed['assembly']);objects.append(placed['assembly']['id'])
        return placed['assembly']['members']
    def cabinet(name,x,y,w=1.25,d=.65,h=.9,z=0,on='@floor',role='storage_cupboard',drawers=2,wall=False):
        members=[add(name,'cabinet',[x,y,z],[w,d,h],None if wall else on,role)]
        if wall:mount(name,'@north')
        # Deliberate low-relief front geometry: real supported faces, not noise.
        for j in range(drawers):
            face=name+f'/front-{j}';hh=(h-.12)/drawers-.035
            add(face,'wall',[x+.07,y-.045,z+.06+j*(h-.12)/drawers],[w-.14,.045,hh],role=role+'_front')
            mount(face,name);members.append(face)
        top=name+'/top';add(top,'slab',[x-.025,y-.025,z+h],[w+.05,d+(.025 if wall else .05),.045],name,role+'_worktop');members.append(top)
        group(name+'/assembly',role,'Supported '+role.replace('_',' ')+' with separate front divisions and top surface.',members)
        return name,top
    def shelf(name,x,z,width_=1.6,contents=2):
        yy=depth/2-.35;members=[]
        for j,xx in enumerate((x,x+width_-.09)):
            bracket=add(name+f'/bracket-{j}','column',[xx,yy,z-.28],[.09,.35,.28],role='shelf_bracket')
            mount(bracket,'@north');members.append(bracket)
        top=add(name+'/board','slab',[x,yy,z],[width_,.35,.08],role='wall_shelf_board',material='wood')
        for bracket in members:s['bearings'].append({'part':top,'on':bracket})
        members.append(top)
        for j in range(contents):
            width_bin=(width_-.15)/contents-.04
            item=add(name+f'/supply-{j}','cabinet',[x+.075+j*(width_bin+.04),yy+.04,z+.08],[width_bin,.26,.24],top,'shelf_supply_bin')
            members.append(item)
        group(name,'wall_shelf','A boarded shelf on two actual wall brackets with supported contents.',members)
        return top
    def tabletop_item(name,table,x,y,size=(.5,.35,.22),role='equipment_case'):
        top=by[table];return add(name,'cabinet',[x,y,top['origin'][2]+top['size'][2]],size,table,role)
    def low_table(name,x,y,w=1.6,d=.8,h=.85,description='A supported work surface.'):
        merge(workbench(name,width=w,depth=d,height=h),[x,y,0],'workbench',description)
        return name+'/top'

    if program in ('dormitory','medical'):
        for j,x in enumerate((left,right)):
            name=f'bed-{j}';yy=depth/2-2.6
            merge(bed(name,width=1.05,depth=2.05),[x,yy,0],'patient_berth' if program=='medical' else 'sleeping_berth','Framed berth with legs, fitted mattress and headboard.')
            mattress=by[name+'/mattress'];top=matress_z=mattress['origin'][2]+mattress['size'][2]
            add(name+'/pillow','slab',[x+.15,yy+1.5,top],[.7,.35,.1],name+'/mattress','pillow',material='cloth')
            add(name+'/folded-cover','slab',[x+.1,yy+.25,top],[.82,.48,.045],name+'/mattress','folded_bed_cover',material='cloth')
            side_x=x+1.25
            cabinet(f'bedside-{j}',side_x,yy+.1,.55,.55,.62,role='bedside_unit',drawers=2)
        if program=='dormitory':
            cabinet('personal-lockers',right+1.25,depth/2-1.2,1.1,.65,1.55+.1*variant,role='personal_locker_bank',drawers=2+variant)
            table=low_table('writing-desk',right,front,w=1.5+.1*variant,d=.7,h=.78,description='Shared writing surface separate from the sleeping berths.')
            add('desk-seat','seat',[right+.45,front+1.05,0],[.5,.55,.9],'@floor','writing_seat')
            cabinet('footlocker',left,front,1.25+.12*variant,.7,.48,role='personal_luggage_storage',drawers=1)
            detail=['personal-lockers','bedside-0','footlocker','writing-desk/top','bed-0/headboard']
        else:
            cabinet('medical-supplies',left,front,1.5,.7,1.05,role='clinical_supply_cupboard',drawers=2+variant)
            cart=low_table('treatment-cart',right+.2,front,w=1.1+.1*variant,d=.7,h=.82,description='A framed treatment cart with upper and lower trays; no clinical performance claim.')
            tray=add('treatment-cart/lower-tray','slab',[right+.28,front,.24],[.94+.1*variant,.7,.06],role='cart_lower_tray')
            for j in range(4):mount(tray,f'treatment-cart/leg-{j}','x',1 if j<2 else -1)
            tabletop_item('treatment-case',cart,right+.35,front+.12,(.55,.4,.24),'sealed_treatment_case')
            shelf('supply-shelf',left,2.15,width_=1.65,contents=2+variant)
            detail=['bed-0/headboard','bedside-0','medical-supplies','treatment-case','treatment-cart/top']
    elif program=='control':
        for j,x in enumerate((left,right)):
            add(f'console-{j}','console',[x,back,0],[1.5,.8,1.1],'@floor','operator_console')
            add(f'operator-seat-{j}','seat',[x+.4,back-1.1,0],[.5,.55,.95],'@floor','operator_seat')
            group(f'operator-station-{j}','operator_station','A dedicated console and supported operator seat.',[f'console-{j}',f'operator-seat-{j}'])
        rack_x=left if variant!=1 else right
        rack,_=cabinet('communications-rack',rack_x,front,1.35,.7,1.25+.1*variant,role='communications_equipment_rack',drawers=3+variant)
        other=right if variant!=1 else left
        table=low_table('planning-table',other,front,w=1.65,d=.85,h=.84,description='Planning and document review surface distinct from the operator consoles.')
        tabletop_item('document-tray',table,other+.15,front+.15,(.75,.5,.12),'document_sorting_tray')
        cabinet('document-cupboard',other,front+1.4,1.3,.55,.68,role='document_storage',drawers=2)
        shelf('communications-shelf',left,2.15,width_=1.7,contents=1+variant)
        detail=['operator-seat-0','communications-rack','planning-table/top','document-cupboard','document-tray']
    elif program=='workshop':
        for j,x in enumerate((left,right)):
            low_table(f'bench-{j}',x,back,w=2,d=.8,h=.9,description='Framed maintenance bench with a separate supported drawer cabinet below.')
            cabinet(f'bench-{j}/drawers',x+.2,back+.12,.9,.52,.62,role='underbench_drawer_unit',drawers=2+variant)
        vise=add('vise/base','slab',[left+.3,back+.15,.9],[.5,.4,.12],'bench-0/top','bench_vise_base')
        for j,xx in enumerate((left+.3,left+.65)):add(f'vise/jaw-{j}','wall',[xx,back+.15,1.02],[.15,.4,.2],vise,'bench_vise_jaw')
        group('bench-vise','bench_vise','Two opposed jaws supported on a real vise base fixed to the bench.',[vise,'vise/jaw-0','vise/jaw-1'])
        board=add('toolboard','wall',[left,depth/2-.14,1.25],[1.8,.14,1.1],role='mounted_tool_board');mount(board,'@north')
        tools=[]
        for j in range(3+variant):
            tool=add(f'toolboard/tool-{j}','wall',[left+.15+j*.29,depth/2-.23,1.4],[.14,.09,.55],role='toolboard_tool_holder');mount(tool,board);tools.append(tool)
        group('tool-wall','mounted_tool_storage','A wall-mounted backboard with attached tool holders.',[board]+tools)
        cabinet('tool-cabinet',left,front,1.45,.7,.85,role='tool_storage_cabinet',drawers=2+variant)
        table=low_table('inspection-table',right,front,w=1.5+.1*variant,d=.8,h=.84,description='Separate inspection surface with a supported instrument case.')
        tabletop_item('inspection-case',table,right+.2,front+.15,(.7,.5,.26),'inspection_instrument_case')
        detail=['inspection-case','tool-cabinet','inspection-table/top','toolboard','bench-1/top']
    elif program=='storage':
        for j,x in enumerate((left,right)):
            levels=3+((variant+j)%2);height=1.9+.1*((variant+j)%2)
            rack=storage_rack(f'rack-{j}',width=1.7+.15*((variant+j)%2),height=height,shelves=levels)
            for k,p in enumerate(rack['parts']):
                if '/crate-' in p['id']:
                    p['size'][0]*=.78+.08*((k+variant)%3);p['size'][2]=.18+.04*((k+variant)%3)
            merge(rack,[x,back,0],'supply_rack','Open uprights and shelves with independently supported bins of varied proportions.')
        table=low_table('packing-table',right,front,w=1.75,d=.85,h=.88,description='A packing/sorting station distinct from the storage shelves.')
        tabletop_item('sorting-bin-0',table,right+.12,front+.12,(.65,.55,.3),'packing_sorting_bin')
        tabletop_item('sorting-bin-1',table,right+.92,front+.12,(.6,.55,.22),'packing_sorting_bin')
        pallet=add('supply-pallet','slab',[left,front,.12],[1.7,1.05,.12],role='supply_pallet_deck',material='wood')
        for j,x in enumerate((left+.12,left+1.38)):
            sleeper=add(f'supply-pallet/sleeper-{j}','footing',[x,front,0],[.2,1.05,.12],'@floor','pallet_sleeper',material='wood')
            s['bearings'].append({'part':pallet,'on':sleeper})
        for j in range(2):add(f'pallet-supply-{j}','cabinet',[left+.1+j*.8,front+.1,.24],[.65,.85,.5+.12*((j+variant)%2)],pallet,'palletized_supply_container')
        group('pallet-stock','palletized_storage','Visible pallet sleepers support its deck and separate supply containers.',[pallet,'supply-pallet/sleeper-0','supply-pallet/sleeper-1','pallet-supply-0','pallet-supply-1'])
        shelf('stock-shelf',left,2.15,width_=1.6,contents=2+variant)
        detail=['rack-0/shelf-1','packing-table/top','supply-pallet','pallet-supply-0','sorting-bin-0']
    elif program=='utilities':
        for j,x in enumerate((left,right)):
            cabinet(f'distribution-{j}',x,depth/2-.5,1.4,.5,1.6,z=.65,role='mounted_distribution_cupboard',drawers=2+variant,wall=True)
            add(f'service-console-{j}','console',[x,1,0],[1.1,.65,.9],'@floor','local_service_console')
        cabinet('maintenance-spares',left,front,1.5,.7,.85,role='electrical_maintenance_storage',drawers=2+variant)
        table=low_table('service-table',right,front,w=1.6,d=.8,h=.84,description='Service table for supported inspection instruments and replacement fittings.')
        tabletop_item('test-instrument-case',table,right+.15,front+.12,(.75,.5,.26),'electrical_test_instrument_case')
        # Rectangular fittings touch the builder's standard north-wall trunk at
        # local x=2.8; the assembly remains explicitly non-process service geometry.
        extension=add('duct-extension','duct',[2.8,depth/2-.3,2.65],[.5,.3,.3],role='rectangular_duct_extension',parameters={'orientation':'x'});mount(extension,'@north')
        turn=add('duct-return','duct',[3.3,depth/2-.9,2.65],[.3,.9,.3],role='rectangular_duct_return',parameters={'orientation':'y'});mount(turn,'@north')
        brackets=[]
        for j,xx in enumerate((3.3,3.52)):
            support=add(f'filter-support-{j}','slab',[xx,depth/2-1.5,2.15],[.08,1.5,.15],role='filter_support_bracket');mount(support,'@north');brackets.append(support)
        cassette=add('filter-cassette','cabinet',[3.3,depth/2-1.5,2.3],[.3,.6,.65],role='ventilation_filter_cassette')
        for support in brackets:s['bearings'].append({'part':cassette,'on':support})
        group('ventilation-fittings','ventilation_fittings','Wall-supported rectangular trunk extension and return; separate wall brackets support the filter cassette. Airflow performance is unverified.',[extension,turn,cassette]+brackets)
        detail=['distribution-0','service-console-0','maintenance-spares','service-table/top','test-instrument-case']
    # Stable room-level metadata provides useful semantic identity at handoff.
    s['assembly']={'id':'occupied-program','role':'program_'+program,'description':PROGRAMS[program]['description'],
        'members':[p['id'] for p in s['parts']],'ground_contacts':[]}
    s['program_recipe']={'version':VERSION,'program':program,'variant':variant,'seed':seed,'variant_index':variant_index,
        'description':PROGRAMS[program]['description'],'fine_detail':PROGRAMS[program]['fine_detail'],
        'functional_objects':objects,'detail_candidates':detail,'clear_cross_half_width':.9,
        'limits':['Conceptual furnished-room kit; no electrical, medical or mechanical performance claim.',
                  'Clear footprint and supplied floor/wall contacts must still pass scene validation.',
                  'The current native room contact adapter supports translation-only placement; arbitrary orientation is explicitly unsupported.']}
    return s

def place_program(program,namespace,*,floor_id,wall_parts,scene_parts,transform=None,width=7.4,depth=7.4,seed=1,variant_index=0):
    """Place local program and bind external supports to actual scene fragments.

    `wall_parts['north']` names fragments for the local north host after placement.
    Contacts must coincide geometrically; missing/remote walls cannot be borrowed.
    """
    transform=transform or RigidTransform()
    if abs(transform.yaw%360)>1e-8:raise ValueError('room fixture contact adapters currently support translation-only placement frames')
    local=program_assembly(program,width=width,depth=depth,seed=seed,variant_index=variant_index)
    result=compose_assembly(local,transform,prefix=namespace+'/')
    by={p['id']:p for p in list(scene_parts)+result['parts']}
    if floor_id not in by:raise ValueError('room floor is absent')
    for bearing in result['bearings']:
        if bearing['on']=='@floor':bearing['on']=floor_id
    resolved=[]
    for contact in result['mounts']:
        if contact['on']!='@north':resolved.append(contact);continue
        part=by[contact['part']];axis='xyz'.index(contact['axis']);side=contact['side'];matched=[]
        for candidate in wall_parts.get('north',[]):
            if candidate not in by:continue
            wall=by[candidate];face=part['origin'][axis] if side==1 else part['origin'][axis]+part['size'][axis]
            plane=wall['origin'][axis]+wall['size'][axis] if side==1 else wall['origin'][axis]
            if abs(face-plane)>1e-6:continue
            if all(min(part['origin'][k]+part['size'][k],wall['origin'][k]+wall['size'][k])-max(part['origin'][k],wall['origin'][k])>1e-6 for k in range(3) if k!=axis):
                matched.append(dict(contact,on=candidate))
        if not matched:raise ValueError('no actual wall surface for '+contact['part'])
        resolved.extend(matched)
    result['mounts']=resolved
    recipe=copy.deepcopy(local['program_recipe'])
    for field in ('functional_objects','detail_candidates'):recipe[field]=[namespace+'/'+v for v in recipe[field]]
    result['program_recipe']=recipe
    return result
