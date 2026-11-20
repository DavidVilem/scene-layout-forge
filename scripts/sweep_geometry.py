"""Local tube-curvature guard, independent of rendering and image assets."""
import math


def segment_distance(a,b,c,d):
    """Return distance and closest fractions along two finite segments."""
    dot=lambda u,v:sum(x*y for x,y in zip(u,v))
    u=[b[k]-a[k] for k in range(3)];v=[d[k]-c[k] for k in range(3)]
    w=[a[k]-c[k] for k in range(3)]
    aa,bb,cc=dot(u,u),dot(u,v),dot(v,v)
    if aa==0 or cc==0:raise ValueError('Zero-length segment')
    dd,ee=dot(u,w),dot(v,w)
    clamp=lambda x:max(0.,min(1.,x))
    candidates=[(0.,clamp(ee/cc)),(1.,clamp((ee+bb)/cc)),
                (clamp(-dd/aa),0.),(clamp((bb-dd)/aa),1.)]
    den=aa*cc-bb*bb
    if den>aa*cc*1e-14:
        s,t=(bb*ee-cc*dd)/den,(aa*ee-bb*dd)/den
        if 0<=s<=1 and 0<=t<=1:candidates.append((s,t))
    return min((math.hypot(*(w[k]+s*u[k]-t*v[k] for k in range(3))),s,t) for s,t in candidates)


def check_route_self_clearance(points,radius):
    """Conservative distant-segment check, excluding local tube neighbourhoods.

    Uses centreline capsules, not mesh intersection. Neighbours separated by
    at most pi*radius along the route are excluded; curvature is checked
    separately. Closed centreline seams use cyclic arc distance.
    """
    segments=list(zip(points,points[1:]))
    lengths=[math.dist(a,b) for a,b in segments]
    if any(length==0 for length in lengths):raise ValueError('Zero-length segment')
    starts=[0.]
    for length in lengths:starts.append(starts[-1]+length)
    closed=math.dist(points[0],points[-1])<=1e-9
    limit=2*radius
    for i,(a,b) in enumerate(segments):
        for j in range(i+2,len(segments)):
            c,d=segments[j]
            if any(max(min(a[k],b[k]),min(c[k],d[k]))-min(max(a[k],b[k]),max(c[k],d[k]))>=limit for k in range(3)):continue
            distance,s,t=segment_distance(a,b,c,d)
            arc=starts[j]+t*lengths[j]-starts[i]-s*lengths[i]
            if closed:arc=min(arc,starts[-1]-arc)
            if arc>math.pi*radius and distance<limit*(1-1e-9):
                raise ValueError(f'Route self-clearance: distant segments {i} and {j} overlap tube envelopes')


def check_tube_curvature(points,radius):
    """Reject sampled bends whose local circumradius is no larger than tube radius.

    This detects locally folded tubes, not global self-intersections. Straight
    samples have infinite radius. Call after finite/nonduplicate checks.
    """
    for index,(a,b,c) in enumerate(zip(points,points[1:],points[2:]),1):
        u=[b[i]-a[i] for i in range(3)]
        v=[c[i]-b[i] for i in range(3)]
        cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        area2=math.hypot(*cross)
        lengths=math.hypot(*u)*math.hypot(*v)
        if lengths==0 or area2<=lengths*1e-12:continue
        bend_radius=lengths*math.dist(a,c)/(2*area2)
        if radius>=bend_radius*(1-1e-9):
            raise ValueError(f'Tube folds at sample {index}: tube radius must be smaller than local bend radius')


def outside_box(a,b,lo,hi):
    """Portions of a segment outside a declared junction envelope."""
    entry,leave=0.,1.
    for k in range(3):
        delta=b[k]-a[k]
        if abs(delta)<1e-12:
            if a[k]<lo[k] or a[k]>hi[k]:return [(a,b)]
        else:
            t0,t1=sorted(((lo[k]-a[k])/delta,(hi[k]-a[k])/delta))
            entry=max(entry,t0);leave=min(leave,t1)
    if entry>leave:return [(a,b)]
    point=lambda t:[a[k]+t*(b[k]-a[k]) for k in range(3)]
    return ([(a,point(entry))] if entry>1e-9 else [])+([(point(leave),b)] if leave<1-1e-9 else [])


def route_pair_conflicts(connections,junction_boxes=None):
    """Capsule intersections outside bounded declared junction zones.

    Radius covers pipe body, not wider endpoint fittings. Local port zones
    permit meeting branches but do not exempt their remote route segments.
    """
    conflicts=[]
    junction_boxes=junction_boxes or {}
    bounds=[([min(p[k] for p in link['route']) for k in range(3)],
             [max(p[k] for p in link['route']) for k in range(3)]) for link in connections]
    for i,left in enumerate(connections):
        for j in range(i+1,len(connections)):
            right=connections[j]
            shared_ports={left['from'],left['to']} & {right['from'],right['to']}
            if len(left['route'])==len(right['route']) and any(
                all(math.dist(a,b)<=1e-9 for a,b in zip(left['route'],candidate))
                for candidate in [right['route'],right['route'][::-1]]):
                conflicts.append((i,j));continue
            limit=left['radius']+right['radius']
            if any(max(bounds[i][0][k],bounds[j][0][k])-min(bounds[i][1][k],bounds[j][1][k])>=limit for k in range(3)):continue
            shared_parts={left['from'].split(':')[0],left['to'].split(':')[0]} & {right['from'].split(':')[0],right['to'].split(':')[0]}
            port_positions={left['from']:left['route'][0],left['to']:left['route'][-1]}
            def segments(link):
                result=list(zip(link['route'],link['route'][1:]))
                padding=2*max(left['radius'],right['radius'])
                for name in sorted(shared_ports):
                    point=port_positions[name]
                    lower=[v-padding for v in point];upper=[v+padding for v in point]
                    result=[segment for a,b in result for segment in outside_box(a,b,lower,upper)]
                for name in sorted(shared_parts):
                    if name not in junction_boxes:continue
                    lo,hi=junction_boxes[name];padding=max(left['radius'],right['radius'])
                    lower=[v-padding for v in lo];upper=[v+padding for v in hi]
                    result=[segment for a,b in result for segment in outside_box(a,b,lower,upper)]
                return result
            left_segments,right_segments=segments(left),segments(right)
            found=False
            for a,b in left_segments:
                for c,d in right_segments:
                    if any(max(min(a[k],b[k]),min(c[k],d[k]))-min(max(a[k],b[k]),max(c[k],d[k]))>=limit for k in range(3)):continue
                    if segment_distance(a,b,c,d)[0]<limit*(1-1e-9):
                        conflicts.append((i,j));found=True;break
                if found:break
    return conflicts
