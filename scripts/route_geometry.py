"""Circular tangent bends for explicit world-space equipment routes."""
import math
import numpy as np


def rounded_route(points, bend_radius, steps_per_quarter=12):
    """Fillet a 3D polyline without moving endpoints or shrinking bend radius.

    Raises when bends cannot fit their adjacent segments. Clearance against
    other parts remains the scene validator's responsibility.
    """
    pts=np.asarray(points,dtype=float)
    if pts.ndim!=2 or pts.shape[1]!=3 or len(pts)<2 or not np.isfinite(pts).all():
        raise ValueError('Route needs at least two finite 3D points')
    if type(bend_radius) not in (int,float) or not math.isfinite(bend_radius) or bend_radius<=0:
        raise ValueError('Bend radius must be positive and finite')
    if type(steps_per_quarter)!=int or not 2<=steps_per_quarter<=128:
        raise ValueError('Steps per quarter must be integer 2..128')
    segments=np.diff(pts,axis=0);lengths=np.linalg.norm(segments,axis=1)
    if np.any(lengths<1e-8):raise ValueError('Repeated or too-close route points')
    directions=segments/lengths[:,None]
    cuts=np.zeros(len(pts));corners={}
    for i in range(1,len(pts)-1):
        u,v=directions[i-1:i+1];cosine=float(np.clip(u@v,-1,1))
        angle=math.acos(cosine)
        if angle<1e-7:continue
        if math.pi-angle<1e-7:raise ValueError('Route reverses direction')
        cuts[i]=bend_radius*math.tan(angle/2)
        axis=np.cross(u,v);axis/=np.linalg.norm(axis)
        start=pts[i]-u*cuts[i]
        center=start+np.cross(axis,u)*bend_radius
        corners[i]=(start,center,axis,angle)
    if np.any(cuts[:-1]+cuts[1:]>lengths+1e-9):
        raise ValueError('Bend radius does not fit adjacent route segments')
    result=[pts[0].copy()]
    def append(point):
        if np.linalg.norm(point-result[-1])>=1e-8:result.append(point)
    for i in range(1,len(pts)-1):
        if i not in corners:append(pts[i].copy());continue
        start,center,axis,angle=corners[i];radial=start-center
        count=max(2,math.ceil(angle/(math.pi/2)*steps_per_quarter))
        for j in range(count+1):
            a=angle*j/count
            append(center+radial*math.cos(a)+np.cross(axis,radial)*math.sin(a))
    append(pts[-1].copy())
    # Keep exact user endpoints instead of a numerically equivalent arc point.
    result[0]=pts[0].copy();result[-1]=pts[-1].copy()
    return [p.tolist() for p in result]
