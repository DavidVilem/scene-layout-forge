"""Append-only repair tasks with artifact identity. A finding is work, not completion."""
import json,uuid,hashlib
from pathlib import Path
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def record(folder,artifact,issues,parent=None):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    if not issues:raise ValueError('Record concrete repair tasks')
    for i in issues:
        if not all(i.get(k) for k in ('id','component','observed','target','action')):raise ValueError('Issue requires component, observed difference, target and repair action')
    path=folder/('repair-'+uuid.uuid4().hex[:10]+'.json')
    data={'artifact':str(Path(artifact).resolve()),'sha256':digest(artifact),'issues':issues,'parent':str(parent) if parent else None}
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8');return path
def resolve(record_path,artifact,observations):
    p=Path(record_path);r=json.loads(p.read_text(encoding='utf-8'))
    if digest(artifact)==r['sha256']:raise ValueError('Unchanged artifact cannot resolve a geometric repair')
    if set(observations)!={i['id'] for i in r['issues']}:raise ValueError('Review each repair')
    for o in observations.values():
        if o.get('status') not in ('resolved','unresolved') or not o.get('evidence'):raise ValueError('New artifact evidence required')
    result={'source_record':str(p),'artifact':str(Path(artifact).resolve()),'sha256':digest(artifact),'observations':observations,'complete':all(o['status']=='resolved' for o in observations.values())}
    out=p.with_name('resolution-'+uuid.uuid4().hex[:10]+'.json');out.write_text(json.dumps(result,indent=2),encoding='utf-8');return out
