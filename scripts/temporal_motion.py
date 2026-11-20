"""Temporal laws and semantic inventory checks, not an object detector or pose generator."""
import math

DEFAULT_MOTION = {'drift': 'advance', 'breeze': 'oscillate', 'light': 'oscillate',
                  'plume': 'flow', 'sprite': 'oscillate'}
ALLOWED = {'drift': {'advance'}, 'breeze': {'oscillate'}, 'light': {'oscillate','advance'},
           'plume': {'flow'}, 'sprite': {'oscillate','travel','rotate','sequence'}}


def law(effect):
    return effect.get('motion', DEFAULT_MOTION[effect['kind']])


def state(effect, phase):
    """Normalized time is never globally reversed or wrapped; only cyclic processes wrap."""
    t = min(1., max(0., float(phase)))
    mode = law(effect)
    sine = math.sin(2*math.pi*effect.get('cycles',1)*(t % 1))
    progress = sine if mode == 'oscillate' else t
    result = {'dx': effect.get('dx',0)*progress, 'dy': effect.get('dy',0)*progress,
              'angle': effect.get('angle',0)*progress, 'scale':1., 'light':progress}
    if mode == 'rotate':
        # Integer turns make a rotor cyclic without reversing its angular velocity.
        result['angle'] = effect.get('direction',1)*360*effect.get('cycles',1)*(t % 1)
    if mode == 'travel':
        points=effect['path']
        for left,right in zip(points,points[1:]):
            if t <= right[0]:
                u=(t-left[0])/(right[0]-left[0])
                result.update(zip(('dx','dy','scale'),(a+(b-a)*u for a,b in zip(left[1:],right[1:]))))
                break
        result['angle']=0.
    return result


def validate_temporal(plan, size):
    timeline=plan.get('timeline','once')
    if timeline not in ('once','loop'): raise ValueError('timeline must be once or loop')
    for e in plan.get('effects',[]):
        mode=law(e)
        if mode not in ALLOWED[e['kind']]: raise ValueError('Inappropriate temporal law for effect kind')
        if mode=='advance' and timeline=='loop':
            raise ValueError('Forward drift/light ramp needs timeline=once; never reverse it to close a loop')
        if mode=='rotate' and e.get('direction',1) not in (-1,1): raise ValueError('Rotation direction must be -1 or 1')
        if mode=='travel':
            points=e.get('path',[])
            if len(points)<2 or any(not isinstance(p,list) or len(p)!=4 or
               not all(isinstance(v,(int,float)) and math.isfinite(v) for v in p) for p in points):
                raise ValueError('Travel path requires [time, dx, dy, scale] points')
            if points[0][0]!=0 or points[-1][0]!=1 or any(a[0]>=b[0] for a,b in zip(points,points[1:])):
                raise ValueError('Path time must increase strictly from 0 to 1')
            if any(not .25<=p[3]<=4 or abs(p[1])>size[0]*2 or abs(p[2])>size[1]*2 for p in points):
                raise ValueError('Path displacement/scale outside supported bounds')
            if timeline=='loop' and points[0][1:]!=points[-1][1:]:
                raise ValueError('Open travel path cannot loop; use once without teleport or reverse')
            if not e.get('path_review'): raise ValueError('Record path clearance, perspective and entry/exit review')
        if mode=='sequence' and not e.get('frames'): raise ValueError('Sequence requires prepared pose/content frames')
        if e.get('frames') and len(e['frames'])<2: raise ValueError('At least two frames required')
        if e.get('category')=='person' and mode=='travel':
            if len(e.get('frames',[]))<4 or not e.get('gait_review'):
                raise ValueError('Walking requires >=4 registered poses and foot-contact/gait review, not a sliding cutout')
    if plan.get('schema_version')==2:
        inventory=plan.get('inventory',[])
        if not inventory: raise ValueError('Inspect source and record motion candidates before rendering')
        byid={}
        for item in inventory:
            if not item.get('id') or item['id'] in byid: raise ValueError('Inventory IDs must be unique')
            if item.get('decision') not in ('animate','fixed','deferred') or not all(item.get(k) for k in ('category','evidence','reason')):
                raise ValueError('Inventory needs visual evidence and a justified decision')
            byid[item['id']]=item
        used=set()
        for e in plan['effects']:
            item=byid.get(e.get('target'))
            if not item or item['decision']!='animate': raise ValueError('Effect must target an inspected, selected object')
            if e.get('category')!=item['category']: raise ValueError('Effect category must match inventory')
            used.add(item['id'])
            mode=law(e)
            if item['category'] in ('cloud','vehicle') and mode=='oscillate':
                raise ValueError('Cloud/vehicle travel cannot use ping-pong motion')
            if item['category']=='foliage' and mode!='oscillate': raise ValueError('Anchored foliage needs oscillation')
        if used!={k for k,v in byid.items() if v['decision']=='animate'}:
            raise ValueError('Selected movement missing; implement or explicitly defer with reason')
