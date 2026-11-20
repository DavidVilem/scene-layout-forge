"""Evidence completeness for camera and rigid-object directions, not pixel recognition."""
import re

def validate(contract):
    if contract is None:
        return
    if contract.get('projection') not in ('perspective','orthographic','not_applicable'):
        raise ValueError('Declare perspective projection')
    if not contract.get('camera') or not contract.get('horizon'):
        raise ValueError('Camera and horizon scope required; horizon may be unknown or inapplicable with reason')
    groups=contract.get('groups',[])
    if contract['projection']!='not_applicable' and not groups:
        raise ValueError('Describe visible rigid groups and their axes')
    ids=[]
    for group in groups:
        key=group.get('id','')
        if not re.fullmatch(r'[a-z][a-z0-9_-]*',key) or key in ids:
            raise ValueError('Unique perspective group IDs required')
        ids.append(key)
        for field in ('orientation','families','exceptions'):
            if not group.get(field):raise ValueError('Group needs '+field)
        if not isinstance(group['families'],dict) or any(not v for v in group['families'].values()):
            raise ValueError('Name straight parallel edge families; distinguish slopes and curves')
    for pair in contract.get('relationships',[]):
        if len(pair.get('groups',[]))!=2 or not set(pair['groups'])<=set(ids) or not pair.get('reason'):
            raise ValueError('Perspective relationship needs two known groups and reason')
        if pair.get('alignment') not in ('parallel','rotated','unknown'):
            raise ValueError('Declare relative orientation without forcing shared vanishing points')

def keys(plan):
    c=plan.get('perspective_contract');validate(c)
    if c is None:return set()
    return {'perspective:camera','perspective:relationships'}|{'perspective:group:'+g['id'] for g in c.get('groups',[])}

def review(plan,observations):
    for key in keys(plan):
        item=observations.get(key,{})
        if not isinstance(item.get('evidence'),list) or not item['evidence'] or any(not isinstance(v,str) or not v.strip() for v in item['evidence']):
            raise ValueError('Perspective requires named pixel evidence: '+key)
        if key.startswith('perspective:group:') and item.get('status')=='visible_correct' and len(item['evidence'])<2:
            raise ValueError('Compare at least two visible edge observations; otherwise mark uncertainty')

def rules(plan):
    if plan.get('perspective_contract') is None:return ''
    return ('\nUse one camera for the entire scene. Rotated rigid objects may have different vanishing points; '
            'horizontal directions share the camera horizon. Within each named family preserve convergence '
            'or orthographic parallelism. Do not force curved, cambered or sloped edges into horizontal families. '
            'Preserve the planned relative orientations and detailed scene; do not draw diagnostic lines in the output.')
