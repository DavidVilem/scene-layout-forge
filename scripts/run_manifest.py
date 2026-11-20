"""Compare recorded inputs and bind reviewed output without inferring service parity."""
import argparse, copy, hashlib, json, platform, re
from pathlib import Path
INPUTS=('scene_sha256','view_sha256','guide_sha256','brief_sha256','handoff_sha256')
CLIENT=('surface','reasoning_model','image_tool','image_model')
UNKNOWN={None,'','unknown','unreported','unrecorded'}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def is_sha(value):return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None

def image_errors(value):
    if not isinstance(value,dict):return ['image identity required']
    size=value.get('size')
    valid_size=isinstance(size,list) and len(size)==2 and all(type(x) is int and x>0 for x in size)
    return [] if value.get('format')=='PNG' and valid_size and all(is_sha(value.get(k)) for k in ('file_sha256','pixel_sha256')) else ['invalid PNG identity or dimensions']

def outcome_errors(value):
    if not isinstance(value,dict):return ['outcome must be an object']
    result=image_errors(value.get('image'))
    if not is_sha(value.get('review_sha256')):result.append('review identity required')
    if value.get('review_status') not in ('passed','limited','needs_correction'):result.append('invalid review status')
    if not isinstance(value.get('generation'),dict):result.append('observed generation facts required')
    native=value.get('generated_image');status=value.get('resolution_status')
    if native is None:
        if status!='native_resolution_unverified':result.append('native resolution cannot be verified without generated pixels')
    else:
        native_errors=image_errors(native);result.extend(native_errors)
        if not native_errors and not image_errors(value.get('image')):
            expected='native_pixels_preserved' if native['pixel_sha256']==value['image']['pixel_sha256'] else 'transformed_after_generation'
            if status!=expected:result.append('resolution claim contradicts pixel identity')
    return result

def source_identity(root):
    root=Path(root).resolve();files={}
    for path in sorted(root.rglob('*')):
        if not path.is_file() or any(p in {'.git','__pycache__'} for p in path.relative_to(root).parts):continue
        files[path.relative_to(root).as_posix()]=sha(path)
    revision=re.search(r'revision:\s*"([^"]+)"',(root/'SKILL.md').read_text(encoding='utf-8-sig'))
    return {'revision':revision.group(1) if revision else 'unknown',
            'source_sha256':hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest(),'files':files}

def manifest(root,lock,brief,prompt,guide=None,client=None,record_host=False):
    from finish_contract import check
    check(lock,lock['scene'])
    bound_guide=lock.get('view',{}).get('guide_sha256')
    if bound_guide and (guide is None or sha(guide)!=bound_guide):raise ValueError('guide differs from the locked view')
    result={'version':2,'skill':source_identity(root),'scene_sha256':lock['scene_sha256'],
        'view_sha256':lock.get('view_sha256'),'guide_sha256':sha(guide) if guide else None,
        'brief_sha256':hashlib.sha256(brief.encode()).hexdigest(),
        'handoff_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
        'client':dict(zip(CLIENT,('unrecorded','unreported','unreported','unreported'))),
        'scope':'Input identity only. Reasoning and image models are separate; equal inputs do not imply identical pixels.'}
    if client:result['client'].update({k:client[k] for k in CLIENT if k in client})
    if record_host:
        # Runtime diagnostics only; never copy these host paths into the distributable.
        result['execution']={'loaded_skill_root':str(Path(root).resolve()),'working_directory':str(Path.cwd()),
                             'platform':platform.system(),'python':platform.python_version()}
    return result

def errors(record):
    if not isinstance(record,dict):return ['manifest must be an object']
    issues=[]
    if type(record.get('version')) is not int or record['version'] not in (1,2):issues.append('unsupported manifest version')
    for key in INPUTS:
        value=record.get(key)
        if key in ('view_sha256','guide_sha256') and key in record and value is None:continue
        if not is_sha(value):issues.append('missing or invalid '+key)
    skill=record.get('skill')
    if not isinstance(skill,dict):issues.append('skill identity required');skill={}
    if not isinstance(skill.get('revision'),str) or skill.get('revision') in UNKNOWN:issues.append('known skill revision required')
    files=skill.get('files')
    if not isinstance(files,dict) or not files or any(not isinstance(k,str) or not k or not is_sha(v) for k,v in files.items()):
        issues.append('source file hashes required')
    elif skill.get('source_sha256')!=hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest():issues.append('source identity changed')
    client=record.get('client')
    if not isinstance(client,dict) or any(not isinstance(client.get(k),str) for k in CLIENT):issues.append('client facts or explicit unknown values required')
    if 'outcome' in record:
        outcome=record['outcome']
        try:matched=record.get('outcome_sha256')==digest(outcome)
        except (ValueError,TypeError):matched=False
        if not matched:issues.append('outcome record changed or is not finite JSON')
        issues.extend(outcome_errors(outcome))
    return issues

def finalize(record,lock,image,review,generation=None,native_image=None):
    """Bind supplied observations and decode actual PNG; do not infer native resolution."""
    from pixel_review import errors as review_errors, image_identity
    from finish_contract import check
    if not isinstance(lock,dict) or not isinstance(lock.get('scene'),dict):raise ValueError('finish lock with scene required')
    check(lock,lock['scene'])
    issues=errors(record)
    if not isinstance(record,dict):raise ValueError('; '.join(issues))
    if record.get('scene_sha256')!=lock.get('scene_sha256') or record.get('view_sha256')!=lock.get('view_sha256'):issues.append('manifest belongs to another scene/view')
    bound_guide=lock.get('view',{}).get('guide_sha256')
    if bound_guide and record.get('guide_sha256')!=bound_guide:issues.append('manifest guide differs from the locked view')
    issues.extend(review_errors(lock,image,review))
    if issues:raise ValueError('; '.join(issues))
    if generation is not None and not isinstance(generation,dict):raise ValueError('generation facts must be an object')
    facts={'model':'unreported','requested_size':'unreported','quality':'unreported','seed':'unreported',
           'reference_use':'unreported','reference_sha256':[],'tool':'unreported',
           'prompt_sha256':'unreported','correction_index':'unreported'}
    for key,value in (generation or {}).items():
        if key not in facts:raise ValueError('unsupported generation fact: '+key)
        facts[key]=value
    if not isinstance(facts['reference_sha256'],list) or any(not is_sha(x) for x in facts['reference_sha256']):raise ValueError('reference hashes must be SHA256')
    if facts['prompt_sha256']!='unreported' and not is_sha(facts['prompt_sha256']):raise ValueError('prompt hash must be SHA256 or unreported')
    index=facts['correction_index']
    if index!='unreported' and (type(index) is not int or not 0<=index<=2):raise ValueError('correction index must be 0, 1, 2 or unreported')
    json.dumps(facts,allow_nan=False)
    final=image_identity(image);native=image_identity(native_image) if native_image else None
    outcome={'image':final,'review_sha256':review['review_sha256'],'review_status':review['status'],
             'generation':facts,'generated_image':native,
             'resolution_status':('native_pixels_preserved' if native['pixel_sha256']==final['pixel_sha256'] else 'transformed_after_generation') if native else 'native_resolution_unverified',
             'scope':'Encoded dimensions verified. Supplied visual observations, not automated engineering certification.'}
    result=copy.deepcopy(record);result['outcome']=outcome;result['outcome_sha256']=digest(outcome)
    return result

def compare(left,right):
    validation={'left':errors(left),'right':errors(right)}
    if not isinstance(left,dict):left={}
    if not isinstance(right,dict):right={}
    differences={key:{'left':left.get(key),'right':right.get(key)} for key in INPUTS if left.get(key)!=right.get(key)}
    for key in ('revision','source_sha256'):
        lv=left.get('skill',{});rv=right.get('skill',{})
        a=lv.get(key) if isinstance(lv,dict) else None;b=rv.get(key) if isinstance(rv,dict) else None
        if a!=b:differences['skill.'+key]={'left':a,'right':b}
    missing=[k for k in INPUTS if not is_sha(left.get(k)) or not is_sha(right.get(k))]
    lc=left.get('client',{});rc=right.get('client',{})
    lc=lc if isinstance(lc,dict) else {};rc=rc if isinstance(rc,dict) else {}
    unknown=[k for k in CLIENT if not isinstance(lc.get(k),str) or not isinstance(rc.get(k),str) or lc.get(k) in UNKNOWN or rc.get(k) in UNKNOWN]
    execution_differences={k:{'left':lc.get(k),'right':rc.get(k)} for k in CLIENT if lc.get(k)!=rc.get(k)}
    return {'same_recorded_inputs':not any(validation.values()) and not differences,
            'complete_input_evidence':not missing and not any(validation.values()),'unreported_inputs':missing,
            'same_known_execution':not unknown and not execution_differences and not any(validation.values()),
            'unreported_client_facts':unknown,'validation':validation,'differences':differences,
            'execution_differences':execution_differences,
            'scope':'No quality verdict, service equivalence or deterministic pixel guarantee. Unknown facts are not equality evidence.'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('left',type=Path,nargs='?');p.add_argument('right',type=Path,nargs='?')
    p.add_argument('--finalize',type=Path);p.add_argument('--lock',type=Path)
    p.add_argument('--image',type=Path);p.add_argument('--native-image',type=Path)
    p.add_argument('--review',type=Path);p.add_argument('--generation',type=Path);p.add_argument('--out',type=Path)
    args=p.parse_args()
    def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
    if args.finalize:
        if not all((args.lock,args.image,args.review,args.out)):p.error('finalize requires lock, image, review and out')
        root=Path(__file__).resolve().parents[1];out=args.out.resolve()
        if out==root or root in out.parents:p.error('runtime records must stay outside the skill')
        result=finalize(read(args.finalize),read(args.lock),args.image,read(args.review),read(args.generation) if args.generation else None,args.native_image)
        with out.open('x',encoding='utf-8') as handle:json.dump(result,handle,indent=2)
        print(json.dumps({'outcome':result['outcome']}))
    else:
        if not args.left or not args.right:p.error('provide two manifests to compare')
        print(json.dumps(compare(read(args.left),read(args.right)),indent=2))
if __name__=='__main__':main()
