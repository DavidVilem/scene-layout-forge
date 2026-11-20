"""Persist a checked handoff before generation and require it for delivery.

Evidence integrity inside the skill workflow, not a sandbox around arbitrary
agent/tool calls. It cannot prevent an agent from ignoring the skill entirely.
"""
import json,shutil,uuid
from pathlib import Path
from finish_contract import check,digest,freeze
from annotation_policy import errors as annotation_errors
from run_manifest import manifest,sha

def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def save(path,value):
    with Path(path).open('x',encoding='utf-8') as f:
        if isinstance(value,str):f.write(value)
        else:json.dump(value,f,indent=2,ensure_ascii=False)

def current_errors(lock):
    if not isinstance(lock,dict) or not isinstance(lock.get('scene'),dict):return ['validated finish lock required; direct image generation is incomplete']
    s=lock['scene'];result=[]
    if s.get('schema_version')!=2 or s.get('validation_policy')!='strict' or s.get('registered_geometry') is not True:
        result.append('current delivery requires strict registered schema-v2 geometry in every domain')
    if s.get('workflow_version') not in (3,4) or lock.get('version')!=3:result.append('current delivery requires v3/v4 physical and visual workflow')
    if s.get('design_intent',{}).get('domain')=='building' and s.get('workflow_version')!=4:result.append('new building delivery requires architectural workflow v4')
    if lock.get('view',{}).get('version')!=2:result.append('bound calculated guide/view required')
    result.extend(annotation_errors(s,required=True))
    return result

def preserve(lock,run,guide,brief,prompt,*,sources,client=None):
    run=Path(run).resolve();guide=Path(guide).resolve()
    issues=current_errors(lock)
    if issues:raise ValueError('; '.join(issues))
    check(lock,lock['scene'])
    # Revalidate actual geometry and bound visual plan, not a hand-written pass.
    freeze(lock['scene'],lock['view'],stage_records=lock.get('architecture_stages'))
    if not (run/'run.json').is_file():raise ValueError('start persistent history before preparing generation')
    if (run/'01-site/brief.txt').read_text(encoding='utf-8')!=brief:raise ValueError('brief differs from original run request')
    if not sources or any(not Path(p).is_file() for p in sources):raise ValueError('retain the actual scene-builder source files')
    if not isinstance(prompt,str) or not prompt.strip():raise ValueError('exact tool prompt required')
    root=Path(__file__).resolve().parents[1]
    record=manifest(root,lock,brief,prompt,guide,client,record_host=True)
    folder=run/'08-finish'/('attempt-'+uuid.uuid4().hex[:12]);folder.mkdir()
    save(folder/'finish-lock.json',lock);save(folder/'scene.json',lock['scene']);save(folder/'view.json',lock['view'])
    from finish_contract import compile_handoff
    save(folder/'handoff.json',compile_handoff(lock))
    save(folder/'finishing-prompt.txt',prompt);save(folder/'run-manifest.json',record)
    shutil.copyfile(guide,folder/'guide.png')
    source_dir=folder/'sources';source_dir.mkdir()
    for i,path in enumerate(sources):shutil.copyfile(path,source_dir/(str(i)+'-'+Path(path).name))
    save(folder/'tool-request.json',{'prompt':prompt,'referenced_image_paths':[str(folder/'guide.png')],'transparent_background':False})
    files={p.relative_to(run).as_posix():sha(p) for p in folder.rglob('*') if p.is_file()}
    files['01-site/brief.txt']=sha(run/'01-site/brief.txt')
    save(folder/'receipt.json',{'version':1,'scene_sha256':lock['scene_sha256'],'view_sha256':lock['view_sha256'],
        'lock_sha256':digest(lock),'files':files,'status':'prepared_not_generated','scope':'Generated pixels still require separate review; this receipt does not certify engineering.'})
    return folder

def errors(lock,run):
    issues=current_errors(lock)
    if issues:return issues
    run=Path(run).resolve()
    if not (run/'run.json').is_file():return ['persistent run history missing']
    failures=[]
    for path in sorted((run/'08-finish').glob('attempt-*/receipt.json')):
        try:
            r=read(path)
            if r.get('lock_sha256')!=digest(lock):continue
            expected={'finish-lock.json','scene.json','view.json','guide.png','finishing-prompt.txt','run-manifest.json','tool-request.json'}
            files=r.get('files',{})
            if not isinstance(files,dict) or not expected<={Path(k).name for k in files} or '01-site/brief.txt' not in files or not any('/sources/' in k for k in files):raise ValueError('incomplete history receipt')
            for name,value in files.items():
                p=(run/name).resolve()
                if run not in p.parents or not p.is_file() or sha(p)!=value:raise ValueError('history file missing or changed: '+name)
            if read(path.parent/'finish-lock.json')!=lock:raise ValueError('history lock differs')
            if sha(path.parent/'guide.png')!=lock['view']['guide_sha256']:raise ValueError('history guide differs')
            if read(path.parent/'scene.json')!=lock['scene'] or read(path.parent/'view.json')!=lock['view']:raise ValueError('history geometry/view differs')
            if read(path.parent/'tool-request.json').get('prompt')!=(path.parent/'finishing-prompt.txt').read_text(encoding='utf-8'):raise ValueError('tool request differs from retained prompt')
            return []
        except (OSError,ValueError,KeyError,TypeError) as exc:failures.append(str(exc))
    return failures or ['no matching prepared history: missing guide, source, prompt or validated contract; delivery is incomplete']

def retain_attempt(run,image,request,review=None):
    """Retain original PNG and actual request for EACH generation/correction."""
    from pixel_review import image_identity
    run=Path(run).resolve()
    if not (run/'run.json').is_file():raise ValueError('persistent run required')
    image_identity(image)
    folder=run/'08-finish'/('generated-'+uuid.uuid4().hex[:12]);folder.mkdir()
    shutil.copyfile(image,folder/'original.png');save(folder/'tool-request.json',request)
    if review is not None:save(folder/'pixel-review.json',review)
    return folder/'original.png'
