"""Near-plane clipping and realizable camera options; no preferred viewpoint."""
import math
import numpy as np


def candidates(scene, *, intent='free', requested=None, azimuths=(25, 125, 235), elevations=(25, 45, 65)):
    """Return renderer kwargs, preserving a requested camera exactly.

    This proposes cameras, never selects one without a rendered ownership report.
    Sections/cutaways require a separately registered display, never camera magic.
    """
    if requested is not None:
        if not isinstance(requested, dict): raise ValueError('requested camera must be an object')
        if requested.get('projection', 'orthographic') not in {'orthographic', 'perspective'}:
            raise ValueError('unsupported projection; provide a validated adapter')
        if intent == 'plan' and (requested.get('projection', 'orthographic') != 'orthographic' or requested.get('elevation', 90) != 90):
            raise ValueError('requested plan requires orthographic top view')
        return {'requested': dict(requested)}
    if intent not in {'free', 'plan', 'elevation', 'exterior', 'interior', 'section', 'cutaway', 'detail'}:
        raise ValueError('unknown camera intent')
    if not scene.get('parts'): raise ValueError('camera candidates require geometry')
    bounds = np.array([np.asarray(p['origin'], float) + np.asarray(p['size'], float)*np.array(v)
                       for p in scene['parts'] for v in [(0, 0, 0), (1, 1, 1)]])
    if not np.isfinite(bounds).all(): raise ValueError('nonfinite scene bounds')
    center = (bounds.min(axis=0)+bounds.max(axis=0))/2
    radius = max(float(np.linalg.norm(bounds.max(axis=0)-bounds.min(axis=0))/2), .1)
    if intent == 'plan': return {'plan': {'projection': 'orthographic', 'azimuth': 0, 'elevation': 90}}
    if intent in {'section', 'cutaway'} and scene.get('representation', {}).get('type') not in {'section', 'cutaway'}:
        raise ValueError('section/cutaway candidates require a registered display cut')
    if len(azimuths) != len(elevations) or not azimuths: raise ValueError('camera option arrays must have matching nonzero lengths')
    result = {}
    for index, (az, el) in enumerate(zip(azimuths, elevations)):
        if not math.isfinite(az) or not math.isfinite(el) or not -85 <= el <= 90: raise ValueError('invalid option angle')
        if intent == 'elevation': el = 0
        result['parallel-' + str(index)] = {'projection': 'orthographic', 'azimuth': az, 'elevation': el, 'allow_level': el < 5}
        if intent not in {'elevation', 'section'}:
            a, e = math.radians(az), math.radians(el)
            distance = radius * (2.8 + .35*index)
            eye = center + distance*np.array([math.cos(a)*math.cos(e), math.sin(a)*math.cos(e), math.sin(e)])
            result['perspective-' + str(index)] = {'projection': 'perspective', 'camera_eye': eye.tolist(),
                'camera_target': center.tolist(), 'fov': 48 + index*3, 'near': max(.01, radius*.001)}
    return result


def clip_polygon(points,eye,forward,near):
    pts=[np.asarray(p,float) for p in points];out=[]
    for a,b in zip(pts[-1:]+pts[:-1],pts):
        da=(a-eye)@forward-near;db=(b-eye)@forward-near
        if (da>=0)!=(db>=0):out.append(a+(b-a)*da/(da-db))
        if db>=0:out.append(b)
    return out


def clip_segment(a,b,eye,forward,near):
    a=np.asarray(a,float);b=np.asarray(b,float)
    da=(a-eye)@forward-near;db=(b-eye)@forward-near
    if da<0 and db<0:return None
    if da<0:a=a+(b-a)*da/(da-db)
    elif db<0:b=a+(b-a)*da/(da-db)
    return a,b


def clip_screen_line(a,b,width,height):
    a=np.asarray(a,float);b=np.asarray(b,float);delta=b-a;lo=0.;hi=1.
    for axis,maximum in [(0,width-1),(1,height-1)]:
        if abs(delta[axis])<1e-12:
            if not 0<=a[axis]<=maximum:return None
            continue
        t0=(0-a[axis])/delta[axis];t1=(maximum-a[axis])/delta[axis]
        lo=max(lo,min(t0,t1));hi=min(hi,max(t0,t1))
        if lo>hi:return None
    if lo==0 and hi==1:return a,b
    return a+delta*lo,a+delta*hi
