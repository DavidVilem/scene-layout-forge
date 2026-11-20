"""Original bounded fixtures for the sixteen worked evaluation questions.

An existing component study is never relabeled a complete subject materializer.
All scopes and intentionally legacy adapters remain visible in the registry.
"""
from copy import deepcopy
from scene_model import make_part
from assembly_model import RigidTransform

def room(program):
    from room_programs import place_program
    s=dict(units='m',schema_version=2,validation_policy='strict',registered_geometry=True,
        parts=[make_part('floor','slab',[-4,-4,-.2],[8,8,.2]),make_part('north','wall',[-4,3.7,0],[8,.2,3.3])],
        grounded=['floor'],bearings=[dict(part='north',on='floor')],mounts=[],assemblies=[])
    kit=place_program(program,'room',floor_id='floor',wall_parts={'north':['north']},scene_parts=s['parts'],seed=52)
    for field in ('parts','bearings','mounts','assemblies'):s[field]+=kit.get(field,[])
    s['assemblies'].append(kit['assembly']);s['detail_recipe']=kit['program_recipe']
    s['camera']={'projection':'orthographic','azimuth':315,'elevation':35}
    return s

def ramp():
    s=dict(units='m',schema_version=2,validation_policy='strict',grounded=['floor'],
        parts=[make_part('floor','slab',[-1,-1,-.2],[4,6,.2]),make_part('ramp','ramp',[0,0,0],[1,3,1]),
            make_part('landing','slab',[0,3,.8],[1,1,.2]),make_part('post','column',[0,3,0],[1,1,.8])],
        bearings=[dict(part='ramp',on='floor'),dict(part='post',on='floor'),dict(part='landing',on='post')],
        ramp_access=[dict(ramp='ramp',landing='landing')],access_nodes=[dict(id='a',position=[.5,.3,1.3]),dict(id='b',position=[.5,3.5,2.2])],access_roots=['a'])
    s['access_volumes']=[{'id':'walk','min':[.4,.2,.4],'max':[.6,3.6,3.2],'from':'a','to':'b',
        'walking_path':[[.5,.3,1.3],[.5,3.5,2.2]],'body_below':.9,'body_above':1.,'half_width':.1}]
    return s

def site():
    s=dict(units='m',schema_version=2,validation_policy='strict',grounded=['site'],
        parts=[make_part('site','slab',[-1,-1,-.2],[12,9,.2])],bearings=[])
    for i,(x,y,h) in enumerate([(0,0,3),(5,0,4),(3,5,2)]):
        wall=f'block-{i}';roof=f'roof-{i}'
        s['parts']+=[make_part(wall,'wall',[x,y,0],[2,2,h],semantic_role=['workplace','residential','services'][i]),make_part(roof,'slab',[x,y,h],[2,2,.2])]
        s['bearings'] +=[dict(part=wall,on='site'),dict(part=roof,on=wall)]
    for i,(o,size) in enumerate([([0,3,0],[9,1,.1]),([8,0,0],[1,7,.1])]):
        p=f'path-{i}';s['parts'].append(make_part(p,'slab',o,size));s['bearings'].append(dict(part=p,on='site'))
    # The two street strips intersect at one intended junction; split instead
    # of introducing an overlap exception.
    s['parts'][-1]['size'][1]=3
    p='path-2';s['parts'].append(make_part(p,'slab',[8,4,0],[1,3,.1]));s['bearings'].append(dict(part=p,on='site'))
    return s

def material_scene():
    s=dict(units='m',schema_version=2,validation_policy='strict',grounded=['floor'],
        parts=[make_part('floor','slab',[-2,-2,-.2],[7,7,.2]),make_part('body','wall',[0,0,0],[2,1,2]),
            make_part('detail','cabinet',[2.3,.1,0],[.8,.8,1.1]),make_part('context','wall',[-1,3,0],[4,.2,2.4])],
        bearings=[dict(part=p,on='floor') for p in ('body','detail','context')],callouts=[dict(id='one',target='body',text='ENCLOSURE')],
        light_material_plan=dict(key_direction=[-.6,.8,1.5],ambient=.55,key_strength=.45,shadow_strength=.12,
            materials={'body':dict(family='wood',origin=[0,0,0],axis=[0,0,1],tangent=[1,0,0],density=.3)}))
    return s

def isolated_valve():
    # Valve rendering exists; strict valve support/functional adapter is not
    # registered. This original fixture deliberately retains legacy scope.
    return dict(units='m',schema_version=1,parts=[make_part('base','slab',[-.2,-.2,-.2],[1.4,1.4,.2]),
        make_part('valve','valve',[0,0,0],[1,1,1])],bearings=[dict(part='valve',on='base')],
        grounded=['base'],context_plan={'mode':'isolated'},expected_counts={'valve':1})

def load(fixture):
    if fixture.startswith('example:'):
        from run_example import load_example
        return load_example(fixture.split(':',1)[1])[0]
    if fixture.startswith('room:'):return room(fixture.split(':',1)[1])
    if fixture=='bunker':
        from build_bunker import build_scene
        return build_scene(52,levels=3,family='branched')
    if fixture=='seated':
        from worker_pose_examples import seated_scene
        return seated_scene()
    if fixture=='contacts':
        from worker_pose_examples import contact_atlas_scene
        return contact_atlas_scene()
    if fixture=='plant':
        from typed_water_plant import scene
        return scene()
    return {'ramp':ramp,'site':site,'materials':material_scene,'valve':isolated_valve}[fixture]()

CASES=[
 dict(id='E01',name='Connected mountain bunker',domain='building',difficulty='integration',fixture='bunker',scope='complete registered pilot',negative='stair_support',target='core-stair-0'),
 dict(id='E02',name='Water-treatment chain',domain='process',difficulty='integration',fixture='example:typed-water-hall',scope='existing typed process fixture; partial coverage retained',negative='route_endpoint',target='m0-pump'),
 dict(id='E03',name='Instrumentation workshop',domain='building',difficulty='program',fixture='room:workshop',scope='registered occupied-room component kit; active facility not inferred',negative='wall_mount',target='room/toolboard'),
 dict(id='E04',name='Drawbridge transmission study',domain='mechanism',difficulty='boundary',fixture='example:supported-drive',scope='legacy shaft/bearing component study; complete drawbridge unsupported',negative='shaft_alignment',target='input-shaft'),
 dict(id='E05',name='Vehicle cabin seated contact',domain='vehicle',difficulty='program',fixture='seated',scope='registered seated task/contact fixture; complete train cabin unsupported',negative='seat_gap',target='seated-operator'),
 dict(id='E06',name='Sloped access/landing study',domain='building',difficulty='boundary',fixture='ramp',scope='registered ramp/landing access; stepped residence materializer unsupported',negative='blocked_access',target='ramp'),
 dict(id='E07',name='Observatory mount transmission',domain='mechanism',difficulty='boundary',fixture='example:supported-drive',scope='legacy mounted transmission study; complete observatory unsupported',negative='attachment',target='coupling'),
 dict(id='E08',name='Station module attachment',domain='vehicle',difficulty='boundary',fixture='example:space-station',scope='legacy curved-module attachment fixture; occupied microgravity interior unsupported',negative='attachment',target='habitat'),
 dict(id='E09',name='Site blocks and access',domain='environment',difficulty='program',fixture='site',scope='registered three-block site component study; full district generator unsupported',negative='roof_gap',target='block-1'),
 dict(id='E10',name='Curved hull support study',domain='vehicle',difficulty='boundary',fixture='example:dry-dock',scope='registered dry-dock hull/contact fixture with partial coverage; airship/mooring unsupported',negative='hull_gap',target='ship'),
 dict(id='E11',name='Occupied control room',domain='building',difficulty='program',fixture='room:control',scope='registered occupied-room kit; activity poses require separate actor plan',negative='furniture_support',target='room/communications-rack'),
 dict(id='E12',name='Controlled material chart',domain='cross-domain',difficulty='ablation',fixture='materials',scope='registered fixed-geometry value/material/context fixture',negative='label_target',target='body'),
 dict(id='E13',name='Situated contact atlas',domain='cross-domain',difficulty='adversarial',fixture='contacts',scope='registered seated/leaning contact examples, not biomechanics',negative='seat_gap',target='seated-operator'),
 dict(id='E14',name='Narrow process service study',domain='process',difficulty='adversarial',fixture='plant',scope='existing typed plant routes/access with partial coverage; full gallery generator unsupported',negative='route_endpoint',target='pump'),
 dict(id='E15',name='Isolated valve assembly',domain='mechanism',difficulty='boundary',fixture='valve',scope='legacy valve primitive; strict support and functional valve adapter unsupported',negative='extra_context',target='valve'),
 dict(id='E16',name='Same pump plant at night',domain='process',difficulty='ablation',fixture='plant',scope='existing plant geometry held fixed for value comparison; partial coverage retained',negative='route_endpoint',target='pump')]

def mutate(scene,kind):
    s=deepcopy(scene)
    if kind in ('stair_support','furniture_support'):
        target='core-stair-0' if kind=='stair_support' else 'room/communications-rack'
        s['bearings']=[b for b in s.get('bearings',[]) if b['part']!=target]
        if kind=='stair_support':s['mounts']=[m for m in s.get('mounts',[]) if m['part']!=target]
    elif kind=='wall_mount':s['mounts']=[m for m in s['mounts'] if m['part']!='room/toolboard']
    elif kind=='route_endpoint':s['connections'][0]['route'][0][0]+=.3
    elif kind=='shaft_alignment':
        target=s['shaft_bearings'][0]['bearing'];next(p for p in s['parts'] if p['id']==target)['origin'][0]+=.05
    elif kind=='attachment':
        name,port=s['attachments'][0]['to'].split(':',1);next(p for p in s['parts'] if p['id']==name)['ports'][port][0]+=.3
    elif kind=='seat_gap':next(p for p in s['parts'] if p['id']=='seat')['origin'][2]+=.1
    elif kind=='roof_gap':next(p for p in s['parts'] if p['id']=='roof-1')['origin'][2]+=.2
    elif kind=='hull_gap':next(p for p in s['parts'] if p['id']=='ship')['origin'][2]+=.2
    elif kind=='blocked_access':
        s['parts'].append(make_part('obstruction','wall',[0,2,0],[1,.15,3]));s['bearings'].append(dict(part='obstruction',on='floor'))
    elif kind=='extra_context':s['context_plan']['entities']=[{'id':'base','role':'location','reason':'unrequested backdrop'}]
    elif kind=='label_target':s['callouts'][0]['target']='absent-object'
    else:raise ValueError('unknown evaluation mutation: '+kind)
    return s
