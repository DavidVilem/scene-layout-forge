"""Bind independent visual observations to the actual PNG, never to a guide pass.

This module checks evidence identity and coverage. It does not perform visual
recognition: the caller must inspect the image and supply honest observations.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
from PIL import Image

STATES={'visible_correct','visible_error','occluded','uncertain'}
GLOBAL=('subject','projection','focus','detail','paper_tone','light','context')

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def image_identity(path):
    path=Path(path)
    with Image.open(path) as im:
        if im.format!='PNG':raise ValueError('Final image must decode as PNG')
        im.verify()
    with Image.open(path) as im:
        im.load();size=list(im.size);pixels=im.convert('RGBA').tobytes()
    return {'file_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'pixel_sha256':hashlib.sha256(json.dumps(size).encode()+pixels).hexdigest(),
            'size':size,'format':'PNG'}

def requirements(lock):
    scene=lock['scene'];result=['global:'+name for name in GLOBAL]
    if 'annotation_policy' in scene:result.append('global:annotations')
    result += ['count:'+key for key in scene.get('delivery_counts',{})]
    result += ['callout:'+c['id'] for c in scene.get('callouts',[])]
    result += ['region:'+r['name'] for r in scene.get('detail_regions',[])]
    result += ['route:'+str(i) for i,_ in enumerate(scene.get('connections',[]))]
    result += ['part:'+p['id'] for p in scene.get('parts',[]) if p.get('visual_critical')]
    result += ['relation:'+r['id'] for r in scene.get('relations',[]) if r.get('critical',True)]
    result += ['witness:'+j['id'] for j in scene.get('camera_junctions',[])]
    result += ['support:'+key for key in scene.get('visual_plan',{}).get('primary',[])]
    result += ['architecture:'+w['id'] for w in scene.get('architecture_contract',{}).get('witnesses',[])]
    if scene.get('exterior_environment'):
        result += ['exterior:'+name for name in ('envelopes','setbacks','streets','roof_equipment','scope')]
    return sorted(set(result))

def observation_errors(lock, observations):
    if not isinstance(observations,list):return ['observations must be a list']
    errors=[];seen=set();allowed=set(requirements(lock))
    scene=lock['scene'];allowed|={'part:'+p['id'] for p in scene.get('parts',[])}
    allowed|={'count:'+k for k in scene.get('expected_counts',{})}
    for item in observations:
        if not isinstance(item,dict):errors.append('observation must be object');continue
        key=item.get('target')
        if not isinstance(key,str) or key not in allowed:errors.append('unknown review target: '+str(key))
        if isinstance(key,str):
            if key in seen:errors.append('duplicate review target: '+key)
            seen.add(key)
        if item.get('state') not in STATES:errors.append('invalid observed state: '+str(key))
        if not isinstance(item.get('note'),str) or not item['note'].strip():errors.append('observed explanation required: '+str(key))
        tip=item.get('desired_tip_xy')
        if tip is not None:
            if not isinstance(key,str) or not key.startswith('callout:') or not isinstance(tip,list) or len(tip)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) or not 0<v<1 for v in tip):
                errors.append('desired annotation tip requires a callout and finite interior XY: '+str(key))
        region=item.get('region')
        if region is not None:
            if not isinstance(region,list) or len(region)!=4 or any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1 for v in region):
                errors.append('region must be finite normalized x0,y0,x1,y1: '+str(key))
            elif region[2]<=region[0] or region[3]<=region[1]:errors.append('region must have positive area: '+str(key))
    errors.extend('missing independent pixel observation: '+key for key in set(requirements(lock))-seen)
    return sorted(set(errors))

def create_review(lock,image_path,observations,reviewer):
    from finish_contract import check
    check(lock,lock['scene'])
    issues=observation_errors(lock,observations)
    if not isinstance(reviewer,str) or not reviewer.strip():issues.append('reviewer required')
    if issues:raise ValueError('; '.join(issues))
    states={o['state'] for o in observations}
    status='needs_correction' if 'visible_error' in states else 'limited' if states & {'occluded','uncertain'} else 'passed'
    record={'version':1,'image':image_identity(image_path),'scene_sha256':lock['scene_sha256'],
            'view_sha256':lock.get('view_sha256'),'reviewer':reviewer,
            'observations':json.loads(json.dumps(observations,allow_nan=False)),
            'status':status,'scope':'Independent supplied pixel observations; identity/coverage checked, not automated recognition or engineering certification.'}
    record['review_sha256']=digest(record)
    return record

def errors(lock,image_path,record):
    if not isinstance(record,dict):return ['pixel review record required']
    result=[]
    copy={k:v for k,v in record.items() if k!='review_sha256'}
    if record.get('review_sha256')!=digest(copy):result.append('pixel review record changed')
    if record.get('scene_sha256')!=lock.get('scene_sha256') or record.get('view_sha256')!=lock.get('view_sha256'):
        result.append('pixel review belongs to another scene/view')
    if record.get('image')!=image_identity(image_path):result.append('pixel review belongs to another PNG')
    result.extend(observation_errors(lock,record.get('observations')))
    observations=record.get('observations')
    states={o.get('state') for o in observations if isinstance(o,dict)} if isinstance(observations,list) else set()
    expected='needs_correction' if 'visible_error' in states else 'limited' if states & {'occluded','uncertain'} else 'passed'
    if record.get('status')!=expected:result.append('pixel review status contradicts observations')
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--lock',required=True,type=Path);p.add_argument('--image',required=True,type=Path)
    p.add_argument('--observations',required=True,type=Path);p.add_argument('--reviewer',required=True)
    p.add_argument('--out',required=True,type=Path);a=p.parse_args()
    root=Path(__file__).resolve().parents[1];out=a.out.resolve()
    if out==root or root in out.parents:raise ValueError('review artifacts must stay outside skill')
    if out.exists():raise FileExistsError('do not overwrite another review')
    result=create_review(json.loads(a.lock.read_text(encoding='utf-8-sig')),a.image,
                         json.loads(a.observations.read_text(encoding='utf-8-sig')),a.reviewer)
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'status':result['status'],'image':result['image'],'review':str(out),'scope':result['scope']}))

if __name__=='__main__':main()
