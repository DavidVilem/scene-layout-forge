"""Explicit request-driven annotation policy, independent of drawing style."""
import copy

def configure(scene, *, requested=False, request_excerpt=''):
    """Planner supplies intent; this does not guess language from keywords."""
    if type(requested) is not bool:raise ValueError('requested must be boolean')
    if requested and not request_excerpt.strip():raise ValueError('quote the annotation request')
    result=copy.deepcopy(scene)
    result['annotation_policy']={'mode':'requested' if requested else 'none','request_excerpt':request_excerpt}
    if not requested:
        result['callouts']=[];result['labels']=[]
    result.setdefault('delivery_counts',{})['annotations']=len(result.get('callouts',[]))
    return result

def errors(scene,required=False):
    p=scene.get('annotation_policy')
    if p is None:return ['explicit annotation_policy required for new delivery'] if required else []
    if not isinstance(p,dict) or p.get('mode') not in ('none','requested'):return ['annotation_policy.mode must be none or requested']
    labels=scene.get('callouts',[])
    if not isinstance(labels,list):return ['callouts must be an array']
    result=[]
    if p['mode']=='none' and (labels or scene.get('labels')):result.append('annotations disabled but labels/callouts remain')
    if p['mode']=='requested':
        if not isinstance(p.get('request_excerpt'),str) or not p['request_excerpt'].strip():result.append('annotation request excerpt required')
        if not labels:result.append('requested annotations require mapped callouts')
    if scene.get('delivery_counts',{}).get('annotations')!=len(labels):result.append('annotation delivery count differs from policy/callouts')
    return result

def instruction(scene):
    # Existing fixtures remain readable; production history requires explicit policy.
    enabled=scene.get('annotation_policy',{}).get('mode')=='requested' if 'annotation_policy' in scene else bool(scene.get('callouts'))
    return ('Include only the exact requested callouts and their mapped arrows; do not add titles or extra labels.' if enabled else
            'ANNOTATIONS OFF: no explanatory labels, leader arrows, caption boxes, titles or decorative text. Keep construction detail, composition and context equally rich; absence of labels is not a simplification request.')
