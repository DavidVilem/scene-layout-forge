"""Situated static actors: legacy standing plus versioned seated/leaning templates.

Stature, task and typed surface contacts remain separate from visible silhouette.
These checks do not establish anatomy, force balance, grip or physical safety.
"""
from dataclasses import dataclass, field, asdict
import math


@dataclass(frozen=True)
class Actor:
    id: str
    task: str
    physical_height: float
    support: str
    pose: str = 'standing'
    tool: str = ''
    hand: str = ''
    seat: str = ''

    def __post_init__(self):
        for value in (self.id, self.task, self.support):
            if not isinstance(value, str) or not value.strip(): raise ValueError('actor ID, task and support required')
        if type(self.physical_height) not in (int, float) or not math.isfinite(self.physical_height) or self.physical_height <= 0:
            raise ValueError('actor physical height must be positive')
        if self.pose not in {'standing','seated','leaning'}: raise ValueError('unsupported pose; supply and test a registered pose adapter')
        if any(not isinstance(v,str) for v in (self.tool,self.hand,self.seat)):raise ValueError('actor seat, tool and hand must be string references')
        if self.pose=='seated' and not self.seat:raise ValueError('unsupported pose declaration: seated requires an explicit seat and fitted geometry')
        if self.pose!='seated' and self.seat:raise ValueError('seat reference requires the seated pose')
        if bool(self.tool) != bool(self.hand) or self.hand not in {'', 'left', 'right'}: raise ValueError('tool contact requires left/right hand')
        if self.pose=='leaning' and not self.tool:raise ValueError('leaning task requires an explicit hand/tool support')


@dataclass(frozen=True)
class ActorPlan:
    actors: list = field(default_factory=list)
    exact_count: int = 0
    version: int = 1

    def __post_init__(self):
        if type(self.version) != int or self.version not in (1,2): raise ValueError('unsupported ActorPlan version')
        if type(self.exact_count) != int or self.exact_count < 0: raise ValueError('actor exact_count must be nonnegative integer')
        actors = [Actor(**raw) for raw in self.actors]
        if self.version==1 and any(a.pose!='standing' for a in actors):raise ValueError('unsupported pose in ActorPlan v1; seated/leaning require version 2')
        if len({a.id for a in actors}) != len(actors): raise ValueError('duplicate actor ID')
        if self.exact_count != len(actors): raise ValueError('actor count differs from explicit plan')
        object.__setattr__(self, 'actors', [asdict(a) for a in actors])


def errors(scene, plan):
    from physical_support import surface_normals
    issues = []; by = {p['id']: p for p in scene.get('parts', [])}
    expected = {p['id'] for p in scene.get('parts', []) if p['kind'] == 'worker'}
    if {a['id'] for a in plan['actors']} != expected: issues.append('ActorPlan does not match every physical worker')
    for actor in plan['actors']:
        part, support = by.get(actor['id']), by.get(actor['support'])
        if part is None or part.get('kind') != 'worker' or support is None:
            issues.append('actor or supporting surface missing: ' + actor['id']); continue
        actual_pose=part.get('parameters',{}).get('pose','standing')
        if actor.get('pose','standing')!=actual_pose:
            issues.append('actor pose differs from rendered geometry: '+actor['id']);continue
        if actual_pose in ('seated','leaning'):
            if abs(part.get('parameters',{}).get('stature',0)-actor['physical_height'])>1e-6:issues.append('actor stature differs from physical pose geometry: '+actor['id'])
            try:
                from worker_pose import data
                data(part)
            except (KeyError,ValueError,TypeError) as exc:issues.append(actor['id']+': '+str(exc))
            if not any(c.get('part')==actor['id'] and c.get('on')==actor['support'] for c in scene.get('bearings',[])):
                issues.append('actor foot support absent from physical support graph: '+actor['id'])
            continue
        if abs(part['size'][2]-actor['physical_height']) > 1e-6: issues.append('actor height differs from physical geometry: ' + actor['id'])
        if not any(c.get('part') == actor['id'] and c.get('on') == actor['support'] for c in scene.get('bearings', []) + scene.get('surface_contacts', [])):
            issues.append('actor support absent from physical support graph: ' + actor['id'])
        x,y,z = part['origin']; w,d,h = part['size']
        for side in (.3, .7):
            point = [x+w*side, y+d*.58, z]
            normals = surface_normals(support, point)
            if not normals or not any(n[2] > .99 for n in normals): issues.append('actor foot lacks upward support surface: ' + actor['id'])
        if actor.get('tool'):
            tool = by.get(actor['tool']); side = .16 if actor['hand'] == 'left' else .84
            point = [x+w*side, y+d*.81, z+h*.52]
            if tool is None or not surface_normals(tool, point): issues.append('actor hand does not contact tool: ' + actor['id'])
    for check in contact_checks(scene,plan):
        if check['status']!='passed':issues.append(check['relation_id']+': '+check['message'])
    return issues


def _target_normals(part,point):
    """Actual native seat surface, or existing exact planar/registered adapters."""
    if part['kind']=='seat':
        if part.get('parameters',{}).get('orientation','y')!='y':return None
        x,y,z=part['origin'];w,d,h=part['size']
        if abs(point[2]-(z+h*.52))<=1e-6 and x-1e-6<=point[0]<=x+w+1e-6 and y+d*.14-1e-6<=point[1]<=y+d+1e-6:return [[0,0,1]]
        return []
    from physical_support import surface_normals
    return surface_normals(part,point)


def contact_checks(scene,plan=None):
    """Each required/declarative posed contact has its own geometric result."""
    from worker_pose import contact_anchors
    by={p['id']:p for p in scene.get('parts',[])};plan=plan or scene.get('actor_plan',{});records=scene.get('actor_contacts',[]);out=[];expected={};seen=set()
    for actor in plan.get('actors',[]):
        if actor.get('pose','standing') not in ('seated','leaning'):continue
        for anchor,kind,target in [('left_foot','foot_support',actor['support']),('right_foot','foot_support',actor['support'])]+([('pelvis','seat_support',actor['seat'])] if actor['pose']=='seated' else [])+([(actor['hand']+'_hand','hand_tool',actor['tool'])] if actor.get('tool') else []):
            expected[(actor['id'],anchor)]=(kind,target)
    if not isinstance(records,list):return [dict(relation_id='actor_contacts',status='failed',message='actor_contacts must be a list',owners=[],region=None,critical=True,type='actor_contact')]
    for index,record in enumerate(records):
        rid=record.get('id',f'actor_contact[{index}]') if isinstance(record,dict) else f'actor_contact[{index}]';status='passed';message='Template contact meets the actual target surface';owners=[];region=None;kind=record.get('type') if isinstance(record,dict) else None
        try:
            if not isinstance(record,dict):raise ValueError('Contact record must be an object')
            actor=record['actor'];anchor=record['anchor'];owners=[actor,record['target']];key=(actor,anchor)
            if rid in seen or key in seen:raise ValueError('Duplicate actor contact ID or anchor')
            seen.add(rid);seen.add(key)
            if key not in expected or (kind,record['target'])!=expected[key]:raise ValueError('Contact type/target differs from situated task')
            geometry=contact_anchors(by[actor])[anchor]
            for field in ('point','normal'):
                value=record[field]
                if not isinstance(value,(list,tuple)) or len(value)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) for v in value):raise ValueError('Actor contact '+field+' requires three finite coordinates')
            if math.dist(record['point'],geometry['point'])>1e-6:raise ValueError('Actor contact point is stale or detached from rendered pose')
            if math.dist(record['normal'],geometry['normal'])>1e-6:raise ValueError('Actor contact normal differs from rendered pose')
            target=by[record['target']]
            for point in [geometry['point']]+geometry.get('patch',[]):
                normals=_target_normals(target,point)
                if normals is None:status='unsupported';message='Actor target surface has no supported adapter';break
                if not normals or not any(math.dist(n,[-v for v in geometry['normal']])<1e-6 for n in normals):raise ValueError('Actor '+anchor+' is detached from its actual '+kind+' surface')
            points=geometry.get('patch',[geometry['point']]);region={'min':[min(p[k] for p in points)-1e-6 for k in range(3)],'max':[max(p[k] for p in points)+1e-6 for k in range(3)]}
        except (KeyError,ValueError,TypeError,IndexError) as exc:status='failed';message=str(exc)
        out.append(dict(relation_id=rid,type=kind,status=status,message=message,owners=owners,region=region,critical=True))
    for key,(kind,target) in expected.items():
        if key not in seen:out.append(dict(relation_id=key[0]+'/'+key[1],type=kind,status='failed',message='Required posed contact is missing',owners=[key[0],target],region=None,critical=True))
    return out


def scene_errors(scene):
    posed=any(p.get('kind')=='worker' and p.get('parameters',{}).get('pose','standing')!='standing' for p in scene.get('parts',[]))
    raw=scene.get('actor_plan')
    if raw is None:return ['Posed worker requires ActorPlan version 2 and typed contacts'] if posed else []
    try:
        plan=asdict(ActorPlan(**raw))
        return errors(scene,plan)
    except (KeyError,TypeError,ValueError) as exc:return ['ActorPlan: '+str(exc)]


def add_actor(scene,part,*,task,support,seat='',tool='',hand=''):
    """Bind a generated pose to actual scene targets; never synthesize a seat."""
    from worker_pose import contact_anchors
    if part.get('parameters',{}).get('pose') not in ('seated','leaning'):raise ValueError('add_actor expects a registered seated/leaning worker')
    actor=Actor(part['id'],task,part['parameters']['stature'],support,part['parameters']['pose'],tool,hand,seat)
    if part['id'] in {p['id'] for p in scene.get('parts',[])}:raise ValueError('Actor ID already exists')
    plan=scene.setdefault('actor_plan',dict(version=2,actors=[],exact_count=0))
    if plan.get('version')!=2:raise ValueError('Explicit ActorPlan v2 required when adding a posed worker')
    part=dict(part,parent=support);scene.setdefault('parts',[]).append(part);scene.setdefault('bearings',[]).append(dict(part=part['id'],on=support))
    plan['actors'].append(asdict(actor));plan['exact_count']=len(plan['actors']);anchors=contact_anchors(part)
    contacts=[('left_foot','foot_support',support),('right_foot','foot_support',support)]
    if seat:contacts.append(('pelvis','seat_support',seat))
    if tool:contacts.append((hand+'_hand','hand_tool',tool))
    for name,kind,target in contacts:
        a=anchors[name];scene.setdefault('actor_contacts',[]).append(dict(id=part['id']+'/'+name,type=kind,actor=part['id'],anchor=name,target=target,point=a['point'],normal=a['normal']))
    return part
