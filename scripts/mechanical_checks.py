"""Limited geometry checks for straight shafts inside annular bearings, not dynamics."""
import numpy as np

def shaft_bearing_errors(data):
    errors=[];parts={p['id']:p for p in data.get('parts',[])}
    pairs=data.get('shaft_bearings',[])
    if not isinstance(pairs,list):return ['shaft_bearings must be a list']
    for i,pair in enumerate(pairs):
        prefix=f'shaft_bearings[{i}]'
        try:
            if not isinstance(pair,dict):raise ValueError('expected object')
            shaft=parts[pair['shaft']];bearing=parts[pair['bearing']]
            if shaft['kind']!='conduit' or bearing['kind']!='ring_frame':raise ValueError('requires straight conduit shaft and ring_frame bearing')
            pts=np.array(shaft['parameters']['points'],float);radius=shaft['parameters']['radius']
            if pts.shape!=(2,3) or not np.isfinite(pts).all():raise ValueError('shaft requires two finite world endpoints')
            if type(radius) not in (float,int) or not np.isfinite(radius) or radius<=0:raise ValueError('invalid shaft radius')
            delta=pts[1]-pts[0];length=np.linalg.norm(delta)
            if length<1e-9:raise ValueError('zero shaft length')
            direction=delta/length
            params=bearing.get('parameters',{});axis={'x':0,'y':1,'z':2}[params.get('orientation','y')]
            size=np.array(bearing['size'],float);origin=np.array(bearing['origin'],float);center=origin+size/2
            if abs(abs(direction[axis])-1)>1e-7:raise ValueError('shaft and bearing axes are not parallel')
            radial=[j for j in range(3) if j!=axis]
            if np.linalg.norm((pts[0]-center)[radial])>1e-7:raise ValueError('shaft misses bearing centreline')
            if min(pts[:,axis])>origin[axis]+1e-7 or max(pts[:,axis])<origin[axis]+size[axis]-1e-7:raise ValueError('shaft does not span bearing thickness')
            aperture=min(size[radial])*params.get('inner_ratio',.82)/2
            if radius>aperture+1e-7:raise ValueError('shaft radius exceeds bearing aperture')
        except (KeyError,TypeError,ValueError,IndexError) as e:errors.append(prefix+': '+str(e))
    return errors
