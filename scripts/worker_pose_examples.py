"""Original seated and leaning contact fixtures, reusable in evaluations."""
from collections import Counter
from actor_plan import add_actor
from worker_pose import make_worker_pose
from assembly_model import workbench,compose_assembly,RigidTransform


def _base():
    return dict(units='m',schema_version=2,validation_policy='strict',registered_geometry=True,
        relation_contract_version=1,parts=[dict(id='floor',kind='slab',origin=[-3,-2,-.2],size=[6,4,.2])],grounded=['floor'],bearings=[],
        actor_plan=dict(version=2,actors=[],exact_count=0),actor_contacts=[])


def _seated(scene,x=0,stature=1.8):
    scale=stature/1.8;seat=dict(id='seat',kind='seat',origin=[x-.35*scale,-.30*scale,0],size=[.7*scale,.65*scale,.9*scale])
    scene['parts'].append(seat);scene['bearings'].append(dict(part='seat',on='floor'))
    worker=make_worker_pose('seated-operator','seated',position=[x,0,0],stature=stature,seat_height=seat['size'][2]*.52,helmet=False)
    add_actor(scene,worker,task='review a local instrument while seated',support='floor',seat='seat')


def _leaning(scene,x=0,stature=1.8):
    height=.56*stature;scale=stature/1.8
    bench=compose_assembly(workbench('bench',width=1.4*scale,depth=.7*scale,height=height),RigidTransform((x-.7*scale,.65*scale,0)))
    scene['parts'].extend(bench['parts']);scene['bearings'].extend(bench['bearings']);scene.setdefault('assemblies',[]).append(bench['assembly'])
    scene['bearings'] += [dict(part=p,on='floor') for p in bench['assembly']['ground_contacts']]
    worker=make_worker_pose('leaning-operator','leaning',position=[x,0,0],stature=stature,hand_height=height,helmet=False)
    add_actor(scene,worker,task='inspect a work surface with a supported left hand',support='floor',tool='bench/top',hand='left')


def _finish(scene):
    scene['expected_counts']=dict(Counter(p['kind'] for p in scene['parts']))
    scene['camera_junctions']=[dict(id=c['id'],relation_id=c['id'],relation_type=c['type'],point=c['point'],owners=[c['actor'],c['target']],critical=True) for c in scene['actor_contacts']]
    scene['pose_scope']='Static, parameterized task templates with real foot/seat/hand contacts; no anatomy, balance, grip-force, accessibility or dynamic claim.'
    return scene


def seated_scene(stature=1.8):
    scene=_base();_seated(scene,stature=stature);return _finish(scene)


def leaning_scene(stature=1.8):
    scene=_base();_leaning(scene,stature=stature);return _finish(scene)


def contact_atlas_scene():
    scene=_base();_seated(scene,-1.35);_leaning(scene,1.25);return _finish(scene)
