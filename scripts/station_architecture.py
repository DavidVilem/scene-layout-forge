"""Bounded example adapter: contour arrival, L-shaped occupied floor, partial sections.

This is one inspectable station example, not the default floorplan for a subject.
No strength, wind, rope dynamics or passenger-system certification is performed.
"""
import copy
from architecture_stages import digest
from kit import make_part

def upgrade(s,save):
    s=copy.deepcopy(s);s['workflow_version']=4
    parts={p['id']:p for p in s['parts']}
    parts['boarding-controls']['origin'][1]=-1.4
    parts['mechanic']['origin']=[12,-3.3,.5]
    parts['mechanic']['parent']='arrival-path'
    for actor in s['actor_plan']['actors']:
        if actor['id']=='mechanic':actor.update(support='arrival-path',task='consult maintenance tablet beside the contour arrival')
    if abs(parts['workshop-rear']['origin'][0]-8)>1e-6:
        raise ValueError('This regression adapter implements the east service-wing candidate; another selected layout needs its own realization')
    def add(k,kind,o,size,on):
        p=make_part(k,kind,o,size);s['parts'].append(p);parts[k]=p
        for support in ([on] if isinstance(on,str) else on):s['bearings'].append(dict(part=k,on=support))
    # Occupied slab follows the building and boarding edge; arrival is a separate surface.
    for k in ('foundation','floor'):
        parts[k]['origin'][:2]=[-6.7,-.6];parts[k]['size'][:2]=[25.2,12.1]
    add('boarding-foundation','footing',[4.1,-9.5,0],[6.3,8.9,.25],'bedrock')
    add('boarding-floor','slab',[4.1,-9.5,.25],[6.3,8.9,.25],'boarding-foundation')
    add('arrival-foundation','footing',[10.4,-3.5,0],[17,2.9,.25],'bedrock')
    add('arrival-path','slab',[10.4,-3.5,.25],[17,2.9,.25],'arrival-foundation')
    for b in s['bearings']:
        if b['part']=='boarding-platform':b['on']='boarding-floor'
        if b['part']=='mechanic':b['on']='arrival-path'
    # A larger contour bench is explicitly registered. Its outer irregular skirt
    # represents exposed rock, not additional occupied floor or a decorative slab.
    from render_scene import Mesh
    import numpy as np
    top=[[-7,-10,0],[10.4,-10,0],[10.4,-3.7,0],[28,-3.7,0],[28,12,0],[-7,12,0]]
    bottom=[[-9,-12,-3],[12,-12,-3],[12,-5.7,-3],[30,-5.7,-3],[30,14,-3],[-9,14,-3]]
    # Concave top uses explicit rectangles, avoiding fan triangulation outside L.
    faces=[([[-7,-10,0],[10.4,-10,0],[10.4,12,0],[-7,12,0]],0),
           ([[10.4,-3.7,0],[28,-3.7,0],[28,12,0],[10.4,12,0]],0),
           ([[-9,-12,-3],[-9,14,-3],[12,14,-3],[12,-12,-3]],0),
           ([[12,-5.7,-3],[12,14,-3],[30,14,-3],[30,-5.7,-3]],0)]
    for i in range(6):j=(i+1)%6;faces.append(([top[i],bottom[i],bottom[j],top[j]],0))
    vertices=[];indices=[];edges=[]
    for face,_ in faces:
        ids=list(range(len(vertices),len(vertices)+len(face)));vertices+=face;indices.append(ids)
        edges.extend([[ids[i],ids[(i+1)%len(ids)]] for i in range(len(ids))])
    v=np.array(vertices);lo=v.min(0);hi=v.max(0)
    parts['bedrock'].update(origin=lo.tolist(),size=(hi-lo).tolist(),parameters=dict(adapter='contour-bench-v2',vertices=(v-lo).tolist(),faces=indices,edges=edges,limitations='Piecewise level bench and exposed rock skirt; no geotechnical calculation'))
    s['ground_surfaces'][0]['bounds']={'min':[-35,-25,-3],'max':[35,25,-3]}
    # Register a coarse mountain slope behind the contour bench. Fine trees and
    # rock marks may be enriched later, but the setting's main mass is not invented.
    rv=[[-7,12,-3],[22,12,-3],[22,19,-3],[-7,19,-3],[-7,16,2],[-2,19,6],[5,17,4],[15,19,7],[22,17,3]]
    rv=[[x,y+2,z] for x,y,z in rv]
    rf=[[0,3,2,1],[0,1,8,6],[0,6,5,4],[6,8,7],[0,4,3],[3,4,5],[3,5,6],[3,6,7,2],[2,7,8],[1,2,8]]
    vv=np.array(rv);lo=vv.min(0)
    ridge=make_part('mountain-slope','custom',lo.tolist(),(vv.max(0)-lo).tolist(),parameters=dict(adapter='mountain-slope-v1',vertices=(vv-lo).tolist(),faces=rf,edges=[],limitations='Coarse terrain mass; rock and vegetation finish is illustrative'))
    s['parts'].append(ridge);parts[ridge['id']]=ridge;s['grounded'].append(ridge['id'])
    s['ground_surfaces'][0]['bounds']['max'][1]=35
    s['ground_contacts'].append(dict(part='mountain-slope',surface='subsurface',points=[[-5,16,-3],[20,16,-3],[20,20,-3]]))
    # Continuous supported framing below all roofs. Multiple declared contacts
    # must be real geometry; the existing strict engine checks them separately.
    s['bearings']=[b for b in s['bearings'] if not b['part'].endswith('-roof')]
    schemes=[]
    for room,x,y,z,w,d,supports in [('machine',-6.5,.7,6.5,13,10.3,['machine-west','machine-east']),('workshop',8,1,4.3,10,10,['workshop-west','workshop-east'])]:
        beams=[]
        for i,yy in enumerate([y+.6,y+d/2,y+d-.6]):
            k=room+'-roof-beam-'+str(i);add(k,'beam',[x,yy,z],[w,.25,.3],supports);beams.append(k)
        roof=parts[room+'-roof'];roof['origin'][2]=z+.3
        s['bearings'] += [dict(part=roof['id'],on=k) for k in beams]
        schemes.append(dict(roof=roof['id'],supports=beams))
    beams=[]
    for i,yy in enumerate([-9,-.8]):
        k='canopy-beam-'+str(i);add(k,'beam',[4.25,yy,6.5],[5.5,.3,.3],['canopy-post'+str(i*2),'canopy-post'+str(i*2+1)]);beams.append(k)
    parts['boarding-roof']['origin'][2]=6.8
    s['bearings'] += [dict(part='boarding-roof',on=k) for k in beams]
    schemes.append(dict(roof='boarding-roof',supports=beams))
    for k,y in [('entrance-post-south',-3.35),('entrance-post-north',-.85)]:add(k,'column',[10.6,y,.5],[.2,.2,3],'arrival-path')
    add('entrance-lintel','beam',[10.6,-3.35,3.5],[.2,2.7,.25],['entrance-post-south','entrance-post-north'])
    for k,o,size,on,axis in [
        ('approach-guard',[10.9,-3.45,.5],[16.3,.1,1.1],'arrival-path','x'),
        ('boarding-front-guard',[4.6,-8.95,.65],[4.7,.1,1.1],'boarding-platform','x'),
        ('boarding-side-guard',[9.65,-8.6,.65],[.1,4.8,1.1],'boarding-platform','y')]:
        add(k,'railing',o,size,on)
        if axis=='y':parts[k]['parameters']={'start':[o[0]+.05,o[1]+.05,o[2]],'end':[o[0]+.05,o[1]+size[1]-.05,o[2]]}
    # Public route starts beyond building extents on the contour approach.
    s['access_nodes']=[n for n in s['access_nodes'] if n['id'] not in ('entry','entry-turn')]
    s['access_volumes']=[v for v in s['access_volumes'] if not v['id'].startswith('entry-access')]
    nodes=[('exterior-arrival',[25,-2,1.5]),('entry',[10.7,-2,1.5])]
    s['access_nodes'] += [dict(id=k,position=p) for k,p in nodes];s['access_roots']=['exterior-arrival']
    for k,a,b,pa,pb in [('approach','exterior-arrival','entry',[25,-2,1.5],[10.7,-2,1.5]),('entry-to-boarding','entry','L0Z0',[10.7,-2,1.5],[6,-2,1.5])]:
        s['access_volumes'].append(dict(id=k,**{'from':a,'to':b},min=[min(pa[0],pb[0])-.4,-2.4,.8],max=[max(pa[0],pb[0])+.4,-1.6,2.8],critical=True))
    # Keep floor-to-roof volume mapping synchronized with constructed frames.
    mat=s['materialized_design']
    mat['zones']['L0Z0']['max'][2]=7.1;mat['zones']['L0Z1']['max'][2]=7.1;mat['zones']['L0Z2']['max'][2]=4.9
    for node,prefix in [('L0Z0','canopy-beam-'),('L0Z1','machine-roof-beam-'),('L0Z2','workshop-roof-beam-')]:
        mat['nodes'][node]+=[k for k in parts if k.startswith(prefix)]
    # Actual window apertures retain masonry piers under every visible beam.
    # Cutting the entire wall low would visually leave those beams floating.
    from assembly_model import cut_host
    for wall,node,intervals in [('machine-east','L0Z1',[(1.8,5.5),(6.2,10.0)]),('workshop-east','L0Z2',[(2.0,5.6),(6.4,10.0)])]:
        old=parts[wall];x,y,z=old['origin'];dx,dy,dz=old['size']
        holes=[dict(id=wall+'-window-'+str(i),origin=[x,a,1.2],size=[dx,b-a,z+dz-1.6]) for i,(a,b) in enumerate(intervals)]
        cut=cut_host(old,holes,'x');fragments=cut['parts']
        s['parts']=[p for p in s['parts'] if p['id']!=wall]+fragments
        s['hosts']+=cut['hosts'];s['openings']+=cut['openings']
        old_bearings=[b for b in s['bearings'] if b['on']==wall and b['part']!=wall]
        s['bearings']=[b for b in s['bearings'] if b['on']!=wall and b['part']!=wall]
        done=[];pending=list(fragments)
        while pending:
            progress=False
            for p in pending[:]:
                o=p['origin'];size=p['size'];on=None;mount=False
                if abs(o[2]-.5)<1e-6:on='floor'
                else:
                    for b in done:
                        bo=b['origin'];bs=b['size']
                        if abs(bo[2]+bs[2]-o[2])<1e-6 and min(bo[1]+bs[1],o[1]+size[1])-max(bo[1],o[1])>1e-6:on=b['id'];break
                    if on is None:
                        for b in done:
                            bo=b['origin'];bs=b['size']
                            if abs(bo[1]+bs[1]-o[1])<1e-6 and min(bo[2]+bs[2],o[2]+size[2])-max(bo[2],o[2])>1e-6:on=b['id'];mount=True;break
                if on:
                    s['mounts' if mount else 'bearings'].append(dict(part=p['id'],on=on,**({'axis':'y','side':1} if mount else {})))
                    done.append(p);pending.remove(p);progress=True
            if not progress:raise ValueError('window lintel has no supported neighbor')
        for bearing in old_bearings:
            beam=parts[bearing['part']]
            matches=[p for p in fragments if abs(p['origin'][2]+p['size'][2]-beam['origin'][2])<1e-6 and min(p['origin'][1]+p['size'][1],beam['origin'][1]+beam['size'][1])-max(p['origin'][1],beam['origin'][1])>1e-6]
            if not matches:raise ValueError('beam lost its wall pier')
            for p in matches:s['bearings'].append(dict(part=beam['id'],on=p['id']))
        mat['nodes'][node]=[k for k in mat['nodes'][node] if k!=wall]+[p['id'] for p in fragments]
        parts.pop(wall);parts.update({p['id']:p for p in fragments})
    # Explicit architectural alternatives accompany graph alternatives. Their
    # envelopes/sections differ; this example selects the contour arrival scheme.
    alternatives=[
        dict(id='contour-L',volumes=[dict(size=[13,10.3,6.8],roof='flat-frame'),dict(size=[10,10,4.6],roof='flat-frame'),dict(size=[5.6,8.5,6.8],roof='canopy')],arrival='east contour path',tradeoff='single-level arrival; exposed downhill rope bay'),
        dict(id='terraced',volumes=[dict(size=[10,8,6],roof='shed'),dict(size=[8,6,3.5],roof='shed')],arrival='uphill landing and internal stair',tradeoff='smaller bench; vertical service transfer'),
        dict(id='longitudinal',volumes=[dict(size=[10,22,6],roof='gable')],arrival='rear circulation spine',tradeoff='compact unified roof; longer passenger route')]
    roofs=['machine-roof','workshop-roof','boarding-roof']
    for volume,node in zip(alternatives[0]['volumes'],['L0Z1','L0Z2','L0Z0']):
        ids=[k for k in mat['nodes'][node] if parts[k]['kind'] in ('wall','beam','column','slab') and not k.startswith('shop/')]
        volume['parts']=ids;volume['size']=[max(parts[k]['origin'][i]+parts[k]['size'][i] for k in ids)-min(parts[k]['origin'][i] for k in ids) for i in range(3)]
    alternatives[0].update(realized_by=roofs+['floor','boarding-floor','arrival-path'],geometry_sha256=digest([parts[k] for k in roofs+['floor','boarding-floor','arrival-path']]))
    witnesses=[dict(id=k,role=role,parts=ids,min_area_fraction=.0003) for k,role,ids in [
        ('contour-arrival','arrival',['arrival-path']),('public-entry','entrance',['entrance-lintel']),
        ('retained-roofs','envelope',roofs),('rope-departure','operation',['suspended-cabin-and-ropes']),('rock-implantation','context',['bedrock'])]]
    spaces=[]
    for key,activity,fixtures,doors,enclosed in [('L0Z0','boarding and controlled threshold',['boarding-controls','waiting-seat'],[],False),('L0Z1','drive inspection and operating clearance',['control-panel'],['machine-door'],True),('L0Z2','bench repairs and storage',['shop/bench-0/top','shop/toolboard'],['workshop-door'],True)]:
        z=mat['zones'][key]
        spaces.append(dict(id=key,activity=activity,area_reason='equipment footprint plus a separate clear circulation lane',access_node=key,bounds=dict(min=z['min'],max=z['max']),fixtures=fixtures,doors=doors,enclosed=enclosed))
    members=['drive-unit','suspended-cabin-and-ropes','left-rope-interface','right-rope-interface']
    s['architecture_contract']=dict(version=1,mode='building',site=dict(terrain=['bedrock'],placement_reason='Contour-side entrance on east; occupied floor follows service wing and downhill boarding finger, leaving rope corridor free',operating_direction='two haul rope legs continue toward downhill south boundary',approach=dict(root='exterior-arrival',entry='entry',surfaces=['arrival-path'])),
        occupied_floors=['floor','boarding-floor'],spaces=spaces,alternatives=alternatives,selected='contour-L',envelope=dict(roofs=roofs),roof_supports=schemes,
        required_systems=['ropeway'],systems=[dict(id='ropeway',members=members,links=[[c['part'],c['on']] for c in s['surface_contacts']],limits='Static mesh-contact chain and original endpoint/axis tests; no rope tension, dynamics, capacity or code compliance')],witnesses=witnesses)
    s['visual_plan']['primary']+=['entrance-lintel','machine-roof','workshop-roof','boarding-roof']
    s['visual_plan']['readable']+=['entrance-lintel','arrival-path']
    s['visual_plan']['subject_framing']['ids']+=roofs+['arrival-path']
    s['visual_plan']['objective']='Read a built mountain terminal, contour arrival and doors, with a selective local section revealing the integrated mechanism and workshop'
    architecture=dict(name='architecture and arrival',primary=['entrance-lintel','machine-roof'],secondary=['workshop-roof','boarding-roof','arrival-path','canopy-beam-0','machine-roof-beam-0','approach-guard','boarding-front-guard','boarding-side-guard'],microdetails=['roof edge flashing and frame joints','door reveals, threshold, stone retaining joints and contour approach','railing posts, rail joints and anchored feet; keep entrance gaps open'])
    s['detail_budget']['regions'].append(architecture)
    s['detail_regions'].append({**architecture,'microdetails':'; '.join(architecture['microdetails'])})
    s['context_plan']['entities'].append(dict(id='arrival-path',role='access',reason='Actual contour approach connects exterior root to building entrance'))
    s['context_plan']['entities'].append(dict(id='mountain-slope',role='location',reason='Registered uphill mountain mass sets station contour and valley-facing departure'))
    s['light_material_plan']['materials'].update({k:dict(family='matte_metal') for k in roofs})
    s['callouts']=[c if c['id']!='tools' else dict(id='entry',text='STATION ENTRANCE',target='entrance-lintel') for c in s['callouts']]
    save('01-site','site-architecture-v2.json',s['architecture_contract']['site'])
    save('02-program','space-program-v2.json',spaces)
    save('03-massing','envelope-alternatives-v2.json',alternatives)
    return s
