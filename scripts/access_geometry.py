"""Check explicit railing segments at a declared landing entrance.

This narrow geometric check is not a circulation or building-code analysis.
"""
import math

EPS=1e-7


def profile_errors(volume,nodes):
    """A swept walking profile is explicit evidence, never a traversal exemption."""
    if 'walking_path' not in volume:return []
    try:
        points=volume['walking_path']
        if not isinstance(points,list) or len(points)<2:raise ValueError('walking_path needs at least two points')
        if any(not isinstance(p,(list,tuple)) or len(p)!=3 or any(type(x) not in (int,float) or not math.isfinite(x) for x in p) for p in points):raise ValueError('finite walking_path required')
        for k in ('body_below','body_above','half_width'):
            if type(volume[k]) not in (int,float) or not math.isfinite(volume[k]) or volume[k]<=0:raise ValueError('positive '+k+' required')
        for key,p in ((volume['from'],points[0]),(volume['to'],points[-1])):
            if key not in nodes or math.dist(nodes[key]['position'],p)>EPS:raise ValueError('walking_path endpoints disagree with access nodes')
        for p in points:
            for axis in range(3):
                low=volume['body_below'] if axis==2 else volume['half_width'];high=volume['body_above'] if axis==2 else volume['half_width']
                if p[axis]-low<volume['min'][axis]-EPS or p[axis]+high>volume['max'][axis]+EPS:raise ValueError('walking_path body leaves declared access bounds')
        if any(math.dist(a,b)<EPS for a,b in zip(points,points[1:])):raise ValueError('zero-length walking_path segment')
        return []
    except (KeyError,ValueError,TypeError,IndexError) as exc:return [str(exc)]


def _solids(part):
    """Native stair boxes and rail envelopes, consistent with components.py."""
    x,y,z=part['origin'];w,d,h=part['size']
    if part['kind']!='stair':return [(part['origin'],[x+w,y+d,z+h])]
    n=part['parameters']['steps'];reverse=part['parameters'].get('reverse',False);rise=h/n;tread=d/n
    boxes=[]
    for i in range(n):
        yy=y+(n-1-i if reverse else i)*tread
        boxes.append(([x,yy,z+i*rise],[x+w,yy+tread,z+(i+1)*rise]))
    # Rails are checked separately as swept segment envelopes.
    return boxes


def _rails(part):
    if part['kind']!='stair':return []
    x,y,z=part['origin'];w,d,h=part['size'];rise=h/part['parameters']['steps'];reverse=part['parameters'].get('reverse',False)
    lowy,highy=(y+d,y) if reverse else (y,y+d);segments=[]
    for xx in (x,x+w):
        segments.append(([xx,lowy,z+.05],[xx,highy,z+h-.05],.045))
        a=[xx,lowy,z+rise];b=[xx,highy,z+h];count=max(1,math.ceil(math.dist(a,b)/.8))
        for i in range(count+1):
            p=[a[k]+(b[k]-a[k])*i/count for k in range(3)];segments.append((p,[p[0],p[1],p[2]+1],.022))
        for dz in (.5,1):segments.append(([a[0],a[1],a[2]+dz],[b[0],b[1],b[2]+dz],.025))
    return segments


def _clip_inequalities(a,b,planes):
    """Intersect a segment with convex halfspaces n.p <= limit."""
    lo,hi=0.,1.
    for normal,limit in planes:
        start=sum(normal[k]*a[k] for k in range(3))-limit
        delta=sum(normal[k]*(b[k]-a[k]) for k in range(3))
        if abs(delta)<1e-12:
            if start>0:return False
        elif delta>0:hi=min(hi,-start/delta)
        else:lo=max(lo,-start/delta)
    return hi-lo>EPS


def _ramp_hit(part,a,b,rx,below,above):
    x,y,z=part['origin'];w,d,h=part['size'];slope=h/d
    if part.get('parameters',{}).get('reverse',False):slope=-slope;intercept=z+h-slope*y
    else:intercept=z-slope*y
    planes=[([-1,0,0],-(x-rx+EPS)),([1,0,0],x+w+rx-EPS),([0,-1,0],-(y-rx+EPS)),([0,1,0],y+d+rx-EPS),
            ([0,0,-1],-(z-above+EPS)),([0,0,1],z+h+below-EPS),([0,-slope,1],intercept+below+abs(slope)*rx-EPS)]
    return _clip_inequalities(a,b,planes)


def volume_obstructed(part,volume):
    """Conservative body sweep against solids. Traversable IDs grant no skip.

    Stair treads are exact boxes; ramp is its convex wedge. Rail cylinders use
    conservative boxes. Other adapters retain conservative envelope occupancy.
    """
    if 'walking_path' in volume:
        path=volume['walking_path'];rx=volume['half_width'];below=volume['body_below'];above=volume['body_above']
    else:
        lo,hi=volume['min'],volume['max'];center=[(a+b)/2 for a,b in zip(lo,hi)]
        # Static AABB query uses its native rectangular footprint below.
        if part['kind']=='ramp':
            px,py,pz=part['origin'];w,d,h=part['size'];x0=max(lo[0],px);x1=min(hi[0],px+w);y0=max(lo[1],py);y1=min(hi[1],py+d)
            if x1-x0<=EPS or y1-y0<=EPS or hi[2]<=pz+EPS:return False
            top=pz+h*((py+d-y0)/d if part.get('parameters',{}).get('reverse',False) else (y1-py)/d)
            return min(top,hi[2])-max(lo[2],pz)>EPS
        for a,b in _solids(part):
            if all(min(hi[k],b[k])-max(lo[k],a[k])>EPS for k in range(3)):return True
        return any(segment_box(a,b,[lo[k]-r+EPS for k in range(3)],[hi[k]+r-EPS for k in range(3)]) for a,b,r in _rails(part))
    for a,b in zip(path,path[1:]):
        if part['kind']=='ramp':
            if _ramp_hit(part,a,b,rx,below,above):return True
            continue
        for lo,hi in _solids(part):
            expanded_lo=[lo[0]-rx+EPS,lo[1]-rx+EPS,lo[2]-above+EPS]
            expanded_hi=[hi[0]+rx-EPS,hi[1]+rx-EPS,hi[2]+below-EPS]
            if segment_box(a,b,expanded_lo,expanded_hi):return True
        for c,d,r in _rails(part):
            # Conservative local segment envelope: never an exemption for rails.
            lo=[min(c[k],d[k])-r for k in range(3)];hi=[max(c[k],d[k])+r for k in range(3)]
            if segment_box(a,b,[lo[0]-rx+EPS,lo[1]-rx+EPS,lo[2]-above+EPS],[hi[0]+rx-EPS,hi[1]+rx-EPS,hi[2]+below-EPS]):return True
    return False


def segment_box(a,b,lo,hi):
    entry,leave=0.,1.
    for axis in range(3):
        delta=b[axis]-a[axis]
        if abs(delta)<1e-12:
            if a[axis]<lo[axis] or a[axis]>hi[axis]:return False
        else:
            t0,t1=sorted(((lo[axis]-a[axis])/delta,(hi[axis]-a[axis])/delta))
            entry=max(entry,t0);leave=min(leave,t1)
    return entry<=leave


def railing_blocks_access(rail,access):
    lo,hi=access.bounds()
    edge=lo[1] if access.parameters.get('reverse',False) else hi[1]
    # Leave the side-rail junctions outside the central walking aperture.
    margin=min(.06,access.size[0]*.1)
    portal_lo=(lo[0]+margin,edge-.03,hi[2]+.10)
    portal_hi=(hi[0]-margin,edge+.03,hi[2]+1.8)
    a=rail.parameters.get('start',rail.origin)
    b=rail.parameters.get('end',(rail.origin[0]+rail.size[0],rail.origin[1],rail.origin[2]))
    h=rail.size[2]
    segments=[((a[0],a[1],a[2]+z),(b[0],b[1],b[2]+z)) for z in (h*.5,h)]
    count=max(1,math.ceil(math.dist(a,b)/.8))
    for i in range(count+1):
        p=tuple(a[k]+(b[k]-a[k])*i/count for k in range(3))
        segments.append((p,(p[0],p[1],p[2]+h)))
    # Match renderer's tube radii conservatively around the centreline.
    expanded_lo=tuple(v-.025 for v in portal_lo)
    expanded_hi=tuple(v+.025 for v in portal_hi)
    return any(segment_box(a,b,expanded_lo,expanded_hi) for a,b in segments)
