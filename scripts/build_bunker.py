"""Materialize a selected hub, spine or branched mountain bunker.

Levels, seed and family are explicit reproducible inputs. Unsupported candidate
families remain visible in planning evidence and cannot silently reuse a layout.
"""
import argparse,copy,json,math,secrets,sys
from pathlib import Path
from collections import Counter
sys.dont_write_bytecode=True
from scene_model import make_part,validate,validation_report
from design_intent import DesignIntent
from design_variants import generate_candidates,choose_candidate
from design_realization import edge_id,realization_report
from room_programs import place_program
from assembly_model import cut_host,RigidTransform,compile_cutaway

ROOT=Path(__file__).resolve().parents[1]

def build_scene(seed=1,count=5,levels=6,family=None):
    from bunker_access import build_access_core
    intent=DesignIntent.from_data({'subject':'Connected mountain bunker with varied occupied rooms',
        'domain':'building','constraints':dict(levels=levels,connected=True,**({'layout_family':family} if family else {})),
        'choices':{'zones_per_level':5,'layout_families':['hub','branched','stepped','spine','ring'],
                   'materializer':'bunker','require_materializable':True,
                   'example_scope':'Three registered physical adapters; unsupported conceptual alternatives stay in evaluation evidence'},
        'program_roles':['control','dormitory','storage','workshop','utilities','medical'],
        'features':['continuous_stair','real_door_openings','section_view']})
    candidates=generate_candidates(intent,seed,count);selected,selection=choose_candidate(intent,candidates)
    if selected['capability']['status']!='supported':raise ValueError('unsupported selected bunker family: '+selected['family'])
    d=build_access_core(levels=levels,height=3.5)
    d.update(schema_version=2,workflow_version=3,validation_policy='strict',registered_geometry=True,design_intent=intent.to_data(),design_selection=selection)
    for key in ('parts','bearings','mounts','custom_contacts','hosts','openings','access_nodes','access_volumes','assemblies','contact_exceptions'):
        d.setdefault(key,[])
    by={p['id']:p for p in d['parts']};material={'nodes':{},'edges':{},'zones':{},'requirements':{},'topology_transform':{'scale_xy':4,'translation':[0,0,0]}};hidden=[];rooms={};targets={};d['room_programs']={}
    def add(id,kind,o,size,on=None,**kw):
        p=make_part(id,kind,o,size,**kw);d['parts'].append(p);by[id]=p
        if on:d['bearings'].append({'part':id,'on':on})
        return p
    def attach_floor(p,floor):d['bearings'].append({'part':p,'on':floor})
    def wall(id,o,size,axis,door,floor):
        host=make_part(id,'wall',o,size)
        if door:
            result=cut_host(host,[door],axis);d['hosts']+=result['hosts'];d['openings']+=result['openings'];pieces=result['parts']
        else:pieces=[host]
        d['parts']+=pieces;by.update({p['id']:p for p in pieces})
        for p in pieces:
            if abs(p['origin'][2]-by[floor]['origin'][2]-by[floor]['size'][2])<1e-6:attach_floor(p['id'],floor);continue
            below=[q for q in pieces if abs(q['origin'][2]+q['size'][2]-p['origin'][2])<1e-6 and all(min(q['origin'][k]+q['size'][k],p['origin'][k]+p['size'][k])-max(q['origin'][k],p['origin'][k])>1e-6 for k in (0,1))]
            if below:
                d['bearings'] += [{'part':p['id'],'on':q['id']} for q in below];continue
            # Door lintel joins its two adjacent upper jamb cells locally.
            lateral=0 if axis=='y' else 1
            for q in pieces:
                if q['id']==p['id']:continue
                for side in (-1,1):
                    end=p['origin'][lateral] if side==1 else p['origin'][lateral]+p['size'][lateral]
                    plane=q['origin'][lateral]+q['size'][lateral] if side==1 else q['origin'][lateral]
                    if abs(end-plane)<1e-6 and min(q['origin'][2]+q['size'][2],p['origin'][2]+p['size'][2])-max(q['origin'][2],p['origin'][2])>1e-6:
                        d['mounts'].append({'part':p['id'],'on':q['id'],'axis':'xyz'[lateral],'side':side})
        return [p['id'] for p in pieces]
    nodes={n['id']:n for n in selected['nodes']}
    def direction(a,b):
        dx=b[0]-a[0];dy=b[1]-a[1]
        if abs(dx)>1e-5 and abs(dy)>1e-5:raise ValueError('bunker adapter requires orthogonal adjacency')
        return 'east' if dx>1e-5 else 'west' if dx< -1e-5 else 'north' if dy>0 else 'south'
    door_sides={n['id']:set() for n in selected['nodes']}
    for edge in selected['edges']:
        if edge['kind']=='vertical_access':continue
        a,b=edge['from'],edge['to']
        door_sides[a].add(direction(nodes[a]['center'],nodes[b]['center']))
        door_sides[b].add(direction(nodes[b]['center'],nodes[a]['center']))
    # Rooms are placed from candidate centers; no separate hardcoded floor plan.
    for node in selected['nodes']:
        level=node['level'];z=node['center'][2];key=node['id']
        if node['role']=='circulation':
            core=d['core_levels'][str(level)];ids=core['floor_parts'];material['nodes'][key]=ids
            for pid in ids:by[pid].update(design_program=node['program'],semantic_role='circulation_landing',design_node=key)
            material['zones'][key]={'program':node['program'],'anchor':[0,0,z],'min':[-3.3,-5.3,z-(.4 if level==0 else .2)],'max':[3.3,5.3,z+3.3],'access_node':core['node'],'program_evidence':ids,'program_contract':{'adapter':'component_set','required_kinds':['slab'],'assemblies':[]}}
            continue
        cx,cy=[round(v*4,6) for v in node['center'][:2]];half=node['extent'][0]*2+.7
        floor=key+'/floor';add(floor,'slab',[cx-half,cy-half,z-.2],[2*half,2*half,.2])
        members=[floor]
        if level==0:d.setdefault('grounded',[]).append(floor)
        else:
            prev=f'L{level-1}'+key[key.index('Z'):]
            for i in range(4):attach_floor(floor,prev+f'/post-{i}')
        for i,(sx,sy) in enumerate([(-1,-1),(-1,1),(1,-1),(1,1)]):
            p=key+f'/post-{i}';add(p,'column',[cx+sx*(half-.15)-.1,cy+sy*(half-.15)-.1,z],[.2,.2,3.3],floor);members.append(p)
        if level==levels-1:
            roof=key+'/roof';add(roof,'slab',[cx-half,cy-half,z+3.3],[2*half,2*half,.2]);members.append(roof);hidden.append(roof)
            for i in range(4):attach_floor(roof,key+f'/post-{i}')
        inner=half-.4;entrances=door_sides[key];entrance=sorted(entrances)[0]
        walls={}
        for side in ('south','north','west','east'):
            axis='y' if side in ('south','north') else 'x';coord=cy if axis=='y' else cx
            if axis=='y':o=[cx-inner,cy-inner if side=='south' else cy+inner-.2,z];size=[2*inner,.2,3.3]
            else:o=[cx-inner if side=='west' else cx+inner-.2,cy-inner+.2,z];size=[.2,2*inner-.4,3.3]
            door=None
            if side in entrances:
                do=o.copy();ds=size.copy();ds[2]=2.5
                lateral=0 if axis=='y' else 1;do[lateral]=(cx if axis=='y' else cy)-.9;ds[lateral]=1.8
                door={'id':key+('/doorway' if side==entrance else '/doorway-'+side),'origin':do,'size':ds}
            ids=wall(key+'/'+side,o,size,axis,door,floor);walls[side]=ids;members+=ids
            if side in ('south','east'):hidden+=ids
        program=node['program']
        kit=place_program(program,key,floor_id=floor,wall_parts=walls,scene_parts=d['parts'],
            transform=RigidTransform((cx,cy,z)),width=2*(inner-.2),depth=2*(inner-.2),
            seed=selected['detail_seed'],variant_index=int(key.split('Z')[1])-1)
        pieces=[p['id'] for p in kit['parts']]
        d['parts']+=kit['parts'];by.update({p['id']:p for p in kit['parts']})
        for field in ('bearings','mounts','assemblies'):d[field]+=kit.get(field,[])
        d['assemblies'].append(kit['assembly']);d['room_programs'][key]=kit['program_recipe']
        for p in kit['parts']:p['detail_recipe']=kit['program_recipe']['fine_detail']
        labels={'control':('CONTROL ROOM','console-0'),'dormitory':('DORMITORY','bed-0/mattress'),
            'workshop':('WORKSHOP','bench-0/top'),'medical':('MEDICAL BERTH','bed-0/mattress')}
        if program in labels:
            label,suffix=labels[program];targets.setdefault(label,key+'/'+suffix)
        # A purposeful wall service on the back wall; no decorative process piping.
        duct=key+'/ventilation';add(duct,'duct',[cx-2.8,cy+inner-.5,z+2.65],[5.6,.3,.3],parameters={'orientation':'x'})
        backs=[pid for pid in walls['north'] if min(by[pid]['origin'][0]+by[pid]['size'][0],cx+2.8)>max(by[pid]['origin'][0],cx-2.8) and
            min(by[pid]['origin'][2]+by[pid]['size'][2],z+2.95)>max(by[pid]['origin'][2],z+2.65)]
        d['mounts'] += [{'part':duct,'on':back,'axis':'y','side':-1} for back in backs];pieces.append(duct)
        if level==levels-2:targets.setdefault('VENTILATION DUCT',duct)
        members+=pieces;material['nodes'][key]=members
        nav=key+'/access';d['access_nodes'].append({'id':nav,'position':[cx,cy,z+1.2]})
        rooms[key]={'center':[cx,cy,z],'half':half,'floor':floor,'nav':nav,'entrance':entrance,'entrances':entrances,'members':members}
        roles={'control':'operator_console','dormitory':'sleeping_berth','medical':'patient_berth','workshop':'maintenance_workbench','storage':'supply_cupboard','utilities':'electrical_service_cabinet'}
        evidence=[pid for pid in pieces if pid!=duct]
        for pid in members:by[pid]['design_node']=key
        for pid in evidence:
            by[pid]['design_program']=program;by[pid].setdefault('semantic_role',roles[program])
        material['zones'][key]={'program':program,'anchor':[cx,cy,z],'min':[cx-half,cy-half,z-.2],'max':[cx+half,cy+half,z+3.5],'access_node':nav,'program_evidence':evidence,'program_contract':{'adapter':'component_set','required_kinds':sorted({by[pid]['kind'] for pid in evidence}),'assemblies':[a['id'] for a in d['assemblies'] if any(pid in evidence for pid in a['members'])]}}
    # Every selected orthogonal edge gets its own slab, stacked supports,
    # wall apertures and continuous access route. Rooms can be endpoints on
    # both sides; their program and topology are not replaced by a radial hub.
    def node_path(start,finish):
        graph={}
        for v in d['access_volumes']:
            graph.setdefault(v['from'],[]).append((v['to'],v['id']));graph.setdefault(v['to'],[]).append((v['from'],v['id']))
        queue=[(start,[])];seen={start}
        while queue:
            node,path=queue.pop(0)
            if node==finish:return path
            for nxt,vid in graph.get(node,[]):
                if nxt not in seen:seen.add(nxt);queue.append((nxt,path+[vid]))
        raise ValueError('unconnected access node: '+finish)
    for edge in selected['edges']:
        edgeid=edge_id(edge);level=nodes[edge['from']]['level'];z=level*3.5
        if edge['kind']=='vertical_access':
            ids=d['core_vertical_edges'][str(level)];material['edges'][edgeid]=ids
            stair='core-stair-'+str(level)
            landing=next(v['landing'] for v in d['stair_access'] if v['stair']==stair)
            material['requirements'][edgeid]={'supported_flight':{'parts':[stair]},'landing':{'parts':[landing]},
                'headroom':{'access_volumes':ids},'opening':{'openings':['core-opening-'+str(level+1)]}}
            continue
        a,b=edge['from'],edge['to'];ca=[v*4 for v in nodes[a]['center'][:2]];cb=[v*4 for v in nodes[b]['center'][:2]]
        side=direction(ca,cb);axis=0 if side in ('east','west') else 1;sign=1 if cb[axis]>ca[axis] else -1
        core=d['core_levels'][str(level)];a_core=nodes[a]['role']=='circulation';b_core=nodes[b]['role']=='circulation'
        ah=(3.3 if axis==0 else 5.3) if a_core else rooms[a]['half']
        bh=(3.3 if axis==0 else 5.3) if b_core else rooms[b]['half']
        ends=sorted((ca[axis]+sign*ah,cb[axis]-sign*bh));width=3.6 if axis==0 else 4.4
        origin=[ca[0],ca[1],z-.2];origin[axis]=ends[0];origin[1-axis]-=width/2
        size=[width,width,.2];size[axis]=ends[1]-ends[0]
        if size[axis]<=0:raise ValueError('corridor span is not positive')
        cid=b+'/corridor';add(cid,'slab',origin,size)
        if level==0:d['grounded'].append(cid)
        else:
            prev=f'L{level-1}'+b[b.index('Z'):]
            for i in range(4):attach_floor(cid,prev+f'/corridor-post-{i}')
        for i,(fx,fy) in enumerate([(0,0),(0,1),(1,0),(1,1)]):
            pid=b+f'/corridor-post-{i}';add(pid,'column',[origin[0]+.05+fx*(size[0]-.25),origin[1]+.05+fy*(size[1]-.25),z],[.2,.2,3.3],cid)
        positions={n['id']:n['position'] for n in d['access_nodes']}
        start_id=core['ports'][side] if a_core else rooms[a]['nav']
        end_id=rooms[b]['nav'];route=[(start_id,positions[start_id])]
        if a_core and side in ('north','south'):
            # The side return avoids the physical stairwell, then aligns to the
            # corridor after leaving the core footprint.
            for j,x in enumerate((positions[start_id][0],cb[0])):
                elbow=b+f'/elbow-{j}';pos=[x,positions[start_id][1]+(.6 if side=='north' else -.6),z+1.2]
                d['access_nodes'].append({'id':elbow,'position':pos});route.append((elbow,pos))
        route.append((end_id,positions[end_id]));volumes=[]
        for j,((na,pa),(nb,pb)) in enumerate(zip(route,route[1:])):
            vid=b+f'/corridor-walk-{j}';lo=[min(pa[k],pb[k])-.28 for k in range(3)];hi=[max(pa[k],pb[k])+.28 for k in range(3)];lo[2]=z+.01;hi[2]=z+2.15
            d['access_volumes'].append({'id':vid,'min':lo,'max':hi,'from':na,'to':nb,'critical':True,
                'walking_path':[pa,pb],'body_below':1.19,'body_above':.95,'half_width':.28});volumes.append(vid)
        prefix=node_path(core['node'],start_id) if a_core else []
        ids=prefix+volumes;material['edges'][edgeid]=ids
        opening_ids=[]
        for name,other in ((a,b),(b,a)):
            if nodes[name]['role']=='circulation':continue
            facing=direction(nodes[name]['center'],nodes[other]['center'])
            entrance=rooms[name]['entrance'];opening_ids.append(name+('/doorway' if facing==entrance else '/doorway-'+facing))
        material['requirements'][edgeid]={'opening':{'openings':opening_ids},'clearance':{'access_volumes':ids}}
    # A physical hollow mountain envelope, then a separate representation cut.
    # Outer slopes and crown are geometry, not instructions to invent a hill.
    from mountain_section import build_mountain_section
    cavity=max(17,max(max(abs(p['origin'][k]),abs(p['origin'][k]+p['size'][k])) for p in d['parts'] for k in (0,1))+1)
    terrain=build_mountain_section(cavity_half=cavity,roof_z=levels*3.5+.5,extent=cavity+25)
    for field in ('parts','grounded','bearings','mounts','custom_contacts'):d.setdefault(field,[]).extend(terrain.get(field,[]))
    hidden.extend(terrain['display_hidden']);d['terrain_contract']=terrain['terrain_contract']
    # Resolve the actual visible foundation interface rather than treating each
    # building slab as an independent ground root above the geological surface.
    geology='mountain/subsurface-upper';foundation_contacts=[]
    building_roots=[key for key in d['grounded'] if key=='core-ground' or key.startswith('L0Z')]
    for key in building_roots:
        floor=by[key];bottom=floor['origin'][2]
        if abs(bottom+.4)<1e-6:
            attach_floor(key,geology);foundation_contacts.append({'slab':key,'on':geology})
        else:
            footing=key+'/foundation-contact'
            add(footing,'footing',[floor['origin'][0],floor['origin'][1],-.4],
                [floor['size'][0],floor['size'][1],bottom+.4],geology,semantic_role='continuous_foundation_contact')
            attach_floor(key,footing);foundation_contacts.append({'slab':key,'on':footing,'geology':geology})
        d['grounded'].remove(key)
    d['foundation_contacts']=foundation_contacts
    d['terrain_contract']['building_foundation_contacts']='Explicit footing solids close the -0.4 to -0.2 interval; the core slab directly contacts the upper geological band.'
    d['terrain_contract']['limits']=[x for x in d['terrain_contract']['limits'] if not x.startswith('subsurface band does not establish bearing')]
    d['terrain_contract']['limits'].append('Foundation contacts are geometric only; bearing capacity, settlement and reinforcement remain unverified.')
    d['support_contract_version']=1;d['relation_contract_version']=1
    d['ground_surfaces']=[];d['ground_contacts']=[]
    physical_parts={p['id']:p for p in d['parts']}
    for root in d['grounded']:
        p=physical_parts[root];x,y,z=p['origin'];w,h,_=p['size'];surface=root+'/ground-datum'
        d['ground_surfaces'].append({'id':surface,'type':'plane','point':[x,y,z],'normal':[0,0,1],
            'bounds':{'min':[x,y,z],'max':[x+w,y+h,z]},'scope':'explicit conceptual geological base datum; terrain stability is not simulated'})
        inset=min(.1,w/4,h/4)
        d['ground_contacts'].append({'part':root,'surface':surface,'points':[[x+inset,y+inset,z],[x+w-inset,y+inset,z],[x+w-inset,y+h-inset,z],[x+inset,y+h-inset,z]]})
    d['materialized_design']=material;d['expected_counts']=dict(Counter(p['kind'] for p in d['parts']))
    d['delivery_counts']={'level':levels,'stair':levels-1}
    stairs=[p['id'] for p in d['parts'] if p['kind']=='stair'];targets['CENTRAL STAIR']=stairs[0]
    d['callouts']=[{'id':str(i),'text':label,'target':target} for i,(label,target) in enumerate(targets.items())]
    d['detail_regions']=[]
    for label,target in targets.items():
        zone=target.split('/')[0];recipe=d['room_programs'].get(zone)
        if recipe:
            secondary=[v for v in recipe['detail_candidates'] if v!=target][:4]
            fine=recipe['fine_detail']
        else:
            secondary=['core-ground',d['core_levels']['1']['floor_parts'][-1],'core-stair-jamb-0']
            fine='Supported stair treads, landing contact, slab opening jamb and arrival rails; keep all connecting flights legible.'
        d['detail_regions'].append({'name':label,'primary':[target],'secondary':secondary,'microdetails':fine})
    d['camera_junctions']=[{'id':'stair-landing-'+str(i),'owners':[record['stair'],record['landing']],
        'point':[.8,3,(i+1)*3.5],'relation_id':'stair_landing:'+record['stair']+'->'+record['landing']}
        for i,record in enumerate(d['stair_access'])]
    d['visual_plan']={'objective':'Read the connected levels, supported stair chain and different occupied programs within a sectioned mountain',
        'primary':stairs,'secondary':list(dict.fromkeys(v for v in targets.values() if v not in stairs)),
        'critical_witnesses':[j['id'] for j in d['camera_junctions']],'readable':stairs,'full':stairs,'quiet':[],
        'layers':[{'name':'occupied fortress','ids':stairs,'role':'access continuity'},
                  {'name':'exposed geology','ids':['mountain/inner-west','mountain/inner-north','mountain/crown-3'],'role':'location and enclosure'}],
        'usage_size':[1800,1500],'view_intent':'cutaway'}
    d['visual_plan']['subject_framing']={'ids':[p['id'] for p in d['parts'] if not p['id'].startswith('mountain/')],
        'purpose':'The occupied levels and program assemblies must remain large enough to read independently of the geological envelope',
        'min_width_fraction':.58,'min_height_fraction':.30,'min_owned_area_fraction':.04,'require_in_frame':True}
    d['context_plan']={'mode':'situated','entities':[{'id':p['id'],'role':'support' if '/subsurface-' in p['id'] else 'location',
        'reason':'sectioned geological enclosure and foundation context','physical':True,'family':'mountain'} for p in terrain['parts']],
        'max_entities':len(terrain['parts']),'max_area_fraction':.8,'protected_ids':stairs,'exact_counts':{}}
    d['detail_budget']={'regions':[{'name':r['name'],'primary':r['primary'],'secondary':r['secondary'],
        'critical':r['primary'],'microdetails':[r['microdetails']]} for r in d['detail_regions']],'usage_size':[1800,1500]}
    d['light_material_plan']={'key_direction':[-.6,.8,1.5],'ambient':.7,'key_strength':.3,'shadow_strength':.12,
        'value_policy':'dark_interior','materials':{p['id']:{'family':p.get('material_family') or ('stone' if p['id'].startswith('mountain/') else 'cloth' if '/mattress' in p['id'] else 'wood' if '/bench-' in p['id'] and p['id'].endswith('/top') else 'concrete' if p['kind'] in ('wall','slab','footing','column') else 'matte_metal'),
        'origin':list(p['origin']),'axis':[0,0,1],'tangent':[1,0,0],'mapping':'planar','spacing':.12,'density':.12,'base_value':232,'mark':'auto'} for p in d['parts']}}
    d['display_hidden']=hidden
    d['materializer']={'version':'bunker-3','family':selected['family'],'supported_families':['hub','spine','branched'],'levels':levels,'seed':seed}
    from useful_camera import camera_options
    d['camera']=next(iter(camera_options(d).values()))
    return d

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--seed',type=int,default=None);parser.add_argument('--count',type=int,default=5);parser.add_argument('--levels',type=int,default=6);parser.add_argument('--family',choices=['hub','spine','branched','ring','stepped']);parser.add_argument('--no-render',action='store_true')
    args=parser.parse_args();out=args.output.resolve()
    if out==ROOT or ROOT in out.parents:raise ValueError('Run artifacts belong outside the skill')
    if out.exists():raise FileExistsError('Use a new output directory')
    seed=secrets.randbits(32) if args.seed is None else args.seed
    scene=build_scene(seed,args.count,args.levels,args.family);report=validation_report(scene);realized=realization_report(scene)
    out.mkdir(parents=True)
    for name,data in [('physical-scene',scene),('validation',report),('design-realization',realized)]:
        (out/(name+'.json')).write_text(json.dumps(data,indent=2),encoding='utf-8')
    if report['status']!='passed':raise ValueError('Physical validation failed; inspect validation.json')
    if realized['status']!='passed':raise ValueError('Design materialization failed; inspect design-realization.json')
    if not args.no_render:
        from useful_camera import select_useful_view,CameraSelectionError
        try:selected=select_useful_view(scene,width=1800,height=1500)
        except CameraSelectionError as exc:
            (out/'camera-selection.json').write_text(json.dumps(exc.selection,indent=2),encoding='utf-8')
            raise
        scene,display,r=selected['scene'],selected['display'],selected['renderer']
        selected['image'].save(out/'guide.png')
        (out/'camera-selection.json').write_text(json.dumps(selected['selection'],indent=2),encoding='utf-8')
        from view_contract import create
        (out/'view-contract.json').write_text(json.dumps(create(scene,display,r,out/'guide.png'),indent=2),encoding='utf-8')
    else:display=compile_cutaway(scene,hide_ids=scene['display_hidden'])
    (out/'physical-scene.json').write_text(json.dumps(scene,indent=2),encoding='utf-8')
    (out/'display-scene.json').write_text(json.dumps(display,indent=2),encoding='utf-8')
    print(json.dumps({'physical':'passed','guide':'not_run' if args.no_render else 'rendered; inspect before finish','output':str(out),'seed':seed,'revision':'2026-11-13.12'}))

if __name__=='__main__':main()
