"""Two static, situated worker templates; no anatomy, motion or load simulation.

One local primitive specification drives the rendered solids, bounds, and contact
anchors. Stature is independent of the shorter seated/leaning envelope. Legacy
standing workers continue to use components.py unchanged.
"""
import itertools
import math
import numpy as np

POSES={'seated','leaning'}
EPS=1e-6


def _rotation(yaw,tilt=0):
    a,b=math.radians(yaw),math.radians(tilt)
    rz=np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])
    rx=np.array([[1,0,0],[0,math.cos(b),-math.sin(b)],[0,math.sin(b),math.cos(b)]])
    return rz@rx


def _positive(value,name):
    if type(value) not in (int,float) or not math.isfinite(value) or value<=0:raise ValueError(name+' must be positive and finite')
    return value


def specification(parameters):
    """Original schematic proportions and finite reach ranges, not human norms."""
    pose=parameters.get('pose');height=_positive(parameters.get('stature'),'stature')
    if pose not in POSES or type(parameters.get('pose_version'))!=int or parameters.get('pose_version')!=1:raise ValueError('unsupported worker pose adapter/version')
    if 'helmet' in parameters and type(parameters['helmet'])!=bool:raise ValueError('actor helmet must be boolean')
    yaw=parameters.get('yaw',0)
    if type(yaw) not in (int,float) or not math.isfinite(yaw):raise ValueError('finite actor yaw required')
    solids=[];anchors={};h=height
    def ellipsoid(name,center,radii,tilt=0):solids.append(dict(name=name,type='ellipsoid',center=np.array(center)*h,radii=np.array(radii)*h,tilt=tilt))
    def box(name,lo,size):solids.append(dict(name=name,type='box',origin=np.array(lo)*h,size=np.array(size)*h))
    def limb(name,points,radius):
        # Separate straight capped segments avoid an unjustified bend/sweep
        # solver at knees/elbows. Their joint overlaps stay inside this actor.
        for index,(a,b) in enumerate(zip(points,points[1:])):
            solids.append(dict(name=name+':'+str(index),type='capsule_bound',points=np.array([a,b])*h,radius=radius*h))
    def anchor(name,point,normal=(0,0,-1),patch=None):
        anchors[name]=dict(point=np.array(point)*h,normal=np.array(normal,float),patch=None if patch is None else np.array(patch)*h)
    if pose=='seated':
        seat=_positive(parameters.get('seat_height'),'seat_height')/h
        if not .18<=seat<=.45:raise ValueError('seat height outside this seated template reach range (0.18..0.45 of stature)')
        for side,label in ((-1,'left'),(1,'right')):
            xx=side*.10;lo=[xx-.065,.28,0];size=[.13,.22,.07]
            box(label+'_boot',lo,size)
            anchor(label+'_foot',[xx,.39,0],patch=[[xx+dx,yy,0] for dx,yy in ((-.05,.30),(.05,.30),(.05,.47),(-.05,.47))])
            limb(label+'_leg',[[side*.09,.035,seat+.10],[xx,.34,seat+.075],[xx,.34,.11]],.042)
            shoulder=[side*.14,.015,seat+.34];elbow=[side*.20,.12,seat+.20];wrist=[side*.14,.23,seat+.15]
            limb(label+'_arm',[shoulder,elbow,wrist],.035)
            lo=[side*.14-.05,.20,seat+.115];box(label+'_glove',lo,[.10,.11,.04])
            anchor(label+'_hand',[side*.14,.255,seat+.115],patch=[[side*.14+dx,yy,seat+.115] for dx,yy in ((-.04,.215),(.04,.215),(.04,.295),(-.04,.295))])
        ellipsoid('pelvis',[0,0,seat+.055],[.135,.09,.055]);anchor('pelvis',[0,0,seat])
        ellipsoid('torso',[0,.015,seat+.23],[.16,.10,.16])
        limb('neck',[[0,.015,seat+.37],[0,.015,seat+.405]],.055)
        ellipsoid('head',[0,.025,seat+.465],[.10,.09,.09])
        ellipsoid('nose',[0,.112,seat+.455],[.035,.028,.025])
        if parameters.get('helmet',False):ellipsoid('helmet',[0,.025,seat+.535],[.12,.115,.045])
    else:
        hand=_positive(parameters.get('hand_height',.56*h),'hand_height')/h
        if not .4<=hand<=.75:raise ValueError('hand height outside this leaning template reach range (0.4..0.75 of stature)')
        for side,label in ((-1,'left'),(1,'right')):
            xx=side*.10;box(label+'_boot',[xx-.065,-.075,0],[.13,.22,.07])
            anchor(label+'_foot',[xx,.035,0],patch=[[xx+dx,yy,0] for dx,yy in ((-.05,-.055),(.05,-.055),(.05,.125),(-.05,.125))])
            limb(label+'_leg',[[side*.09,0,.49],[xx,.015,.27],[xx,.015,.11]],.042)
            limb(label+'_arm',[[side*.14,.18,.78],[side*.22,.30,hand+.13],[side*.16,.42,hand+.065]],.035)
            box(label+'_glove',[side*.16-.05,.365,hand],[.10,.11,.04])
            anchor(label+'_hand',[side*.16,.42,hand],patch=[[side*.16+dx,yy,hand] for dx,yy in ((-.04,.38),(.04,.38),(.04,.46),(-.04,.46))])
        ellipsoid('pelvis',[0,0,.49],[.135,.10,.075])
        ellipsoid('torso',[0,.115,.65],[.16,.11,.17],tilt=-25)
        limb('neck',[[0,.18,.78],[0,.235,.83]],.055)
        ellipsoid('head',[0,.265,.87],[.10,.09,.09],tilt=-15)
        ellipsoid('nose',[0,.353,.85],[.035,.028,.025])
        if parameters.get('helmet',False):ellipsoid('helmet',[0,.26,.94],[.12,.115,.045],tilt=-15)
    return solids,anchors,_rotation(yaw)


def _world_bounds(solids,rotation):
    lows=[];highs=[]
    for s in solids:
        if s['type']=='ellipsoid':
            r=rotation@_rotation(0,s['tilt']);c=rotation@s['center'];extent=np.sqrt((r*r)@(s['radii']**2))
            lo,hi=c-extent,c+extent
        elif s['type']=='box':
            points=np.array([rotation@(s['origin']+s['size']*np.array(v)) for v in itertools.product((0,1),repeat=3)])
            lo,hi=points.min(axis=0),points.max(axis=0)
        else:
            points=s['points']@rotation.T;lo,hi=points.min(axis=0)-s['radius'],points.max(axis=0)+s['radius']
        lows.append(lo);highs.append(hi)
    return np.min(lows,axis=0),np.max(highs,axis=0)


def make_worker_pose(id,pose,position=(0,0,0),stature=1.8,yaw=0,seat_height=None,hand_height=None,helmet=False,parent=None):
    """Place the template frame at position (feet plane); return one worker ID."""
    if len(position)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) for v in position):raise ValueError('finite actor frame position required')
    parameters=dict(pose=pose,pose_version=1,stature=stature,yaw=yaw,helmet=helmet)
    if seat_height is not None:parameters['seat_height']=seat_height
    if hand_height is not None:parameters['hand_height']=hand_height
    solids,_,rotation=specification(parameters);lo,hi=_world_bounds(solids,rotation)
    part=dict(id=id,kind='worker',origin=(np.asarray(position)+lo).tolist(),size=(hi-lo).tolist(),parameters=parameters)
    if parent:part['parent']=parent
    return part


def data(part):
    raw=part if isinstance(part,dict) else dict(id=part.id,kind=part.kind,origin=part.origin,size=part.size,parameters=part.parameters)
    solids,anchors,rotation=specification(raw['parameters']);lo,hi=_world_bounds(solids,rotation)
    if any(abs(float(raw['size'][k])-(hi-lo)[k])>EPS for k in range(3)):raise ValueError('posed worker bounds differ from generated template')
    translation=np.asarray(raw['origin'],float)-lo
    return raw,solids,anchors,rotation,translation


def contact_anchors(part):
    _,_,anchors,rotation,translation=data(part);result={}
    for name,a in anchors.items():
        result[name]=dict(point=(rotation@a['point']+translation).tolist(),normal=(rotation@a['normal']).tolist())
        if a['patch'] is not None:result[name]['patch']=(a['patch']@rotation.T+translation).tolist()
    return result


def render(mesh,part):
    """Emit actual pose geometry through the ordinary worker owner registration."""
    _,solids,_,rotation,translation=data(part)
    for s in solids:
        local=type(mesh)()
        if s['type']=='box':local.box(s['origin'],s['size']);local_rotation=rotation
        elif s['type']=='ellipsoid':
            local.ellipsoid([0,0,0],s['radii']);r=_rotation(0,s['tilt'])
            # Translate after local ellipsoid rotation, before scene placement.
            for i,(face,tone) in enumerate(local.faces):local.faces[i]=([r@p+s['center'] for p in face],tone)
            local.smooth_edges=[(r@a+s['center'],r@b+s['center'],r@n1,r@n2) for a,b,n1,n2 in local.smooth_edges]
            local_rotation=rotation
        else:local.sweep(s['points'],s['radius'],16);local_rotation=rotation
        point=lambda v:local_rotation@np.asarray(v)+translation
        mesh.faces.extend(([point(p) for p in face],tone) for face,tone in local.faces)
        mesh.edges.extend((point(a),point(b)) for a,b in local.edges)
        mesh.smooth_edges.extend((point(a),point(b),local_rotation@n1,local_rotation@n2) for a,b,n1,n2 in local.smooth_edges)


def _segment_box_distance(a,b,lo,hi):
    delta=b-a;cuts=[0.,1.]
    for k in range(3):
        if abs(delta[k])>EPS:
            cuts.extend(t for bound in (lo[k],hi[k]) if 0<(t:=(bound-a[k])/delta[k])<1)
    cuts=sorted(set(cuts));best=float('inf')
    for left,right in zip(cuts,cuts[1:]):
        mid=a+delta*((left+right)/2);offset=np.zeros(3);slope=np.zeros(3)
        for k in range(3):
            if mid[k]<lo[k]:offset[k]=a[k]-lo[k];slope[k]=delta[k]
            elif mid[k]>hi[k]:offset[k]=a[k]-hi[k];slope[k]=delta[k]
        den=np.dot(slope,slope);t=max(left,min(right,-np.dot(offset,slope)/den)) if den>EPS else left
        for candidate in (left,right,t):
            p=a+delta*candidate;nearest=np.minimum(hi,np.maximum(lo,p));best=min(best,float(np.linalg.norm(p-nearest)))
    return best


def _ellipsoid_box(center,radii,rotation,lo,hi):
    """Convex box-constrained quadratic minimum, using all 27 active sets."""
    matrix=rotation@np.diag(1/(radii*radii))@rotation.T;best=float('inf')
    for active in itertools.product((-1,0,1),repeat=3):
        fixed=[k for k in range(3) if active[k]];free=[k for k in range(3) if not active[k]];p=center.copy()
        for k in fixed:p[k]=lo[k] if active[k]<0 else hi[k]
        if free:
            ff=matrix[np.ix_(free,free)];rhs=-matrix[np.ix_(free,fixed)]@(p[fixed]-center[fixed]) if fixed else np.zeros(len(free))
            p[free]=center[free]+np.linalg.solve(ff,rhs)
        if np.all(p>=lo-EPS) and np.all(p<=hi+EPS):best=min(best,float((p-center)@matrix@(p-center)))
    return best<1-EPS


def _target_boxes(part):
    """Actual planar target solids; other kinds stay explicitly unsupported."""
    from physical_support import PLANAR
    x,y,z=part['origin'];w,d,h=part['size']
    if part['kind'] in PLANAR:return [(np.array([x,y,z]),np.array([x+w,y+d,z+h]))]
    if part['kind']=='seat' and part.get('parameters',{}).get('orientation','y')=='y':
        boxes=[([x,y,z+h*.42],[x+w,y+d,z+h*.52]),([x,y,z+h*.52],[x+w,y+d*.14,z+h])]
        # Conservative cylinders' envelopes for the four actual seat legs.
        r=min(w,d)*.04
        boxes += [([x+w*xx-r,y+d*yy-r,z],[x+w*xx+r,y+d*yy+r,z+h*.42]) for xx in (.12,.88) for yy in (.12,.88)]
        return [(np.array(a),np.array(b)) for a,b in boxes]
    return None


def collision_status(actor,other):
    """Narrow phase against declared native boxes/seat; no global skip pair."""
    boxes=_target_boxes(other)
    if boxes is None:return 'unsupported','Posed actor collision target has no narrow-phase adapter'
    _,solids,_,rotation,translation=data(actor);unresolved=[]
    for s in solids:
        for lo,hi in boxes:
            if s['type']=='ellipsoid':
                center=rotation@s['center']+translation;r=rotation@_rotation(0,s['tilt'])
                if _ellipsoid_box(center,s['radii'],r,lo,hi):return 'failed','Posed actor ellipsoid penetrates target solid: '+s['name']
            elif s['type']=='box':
                points=np.array([rotation@(s['origin']+s['size']*np.array(v))+translation for v in itertools.product((0,1),repeat=3)])
                # Exact for quarter turns; arbitrary yaw remains conservative.
                hit=np.all(np.minimum(points.max(axis=0),hi)-np.maximum(points.min(axis=0),lo)>EPS)
                if hit:
                    aligned=abs(actor['parameters'].get('yaw',0)/90-round(actor['parameters'].get('yaw',0)/90))<EPS
                    if aligned:return 'failed','Posed actor box intersects target solid: '+s['name']
                    unresolved.append('Posed actor box intersects target envelope: '+s['name'])
            else:
                a,b=s['points']@rotation.T+translation
                if _segment_box_distance(a,b,lo,hi)<s['radius']-EPS:unresolved.append('Limb capsule intersects target; exact capped-cylinder refinement required: '+s['name'])
    if unresolved:return 'unsupported','; '.join(unresolved)
    return 'passed','Posed actor solids are clear of actual target boxes; contacts may touch'
