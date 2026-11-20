"""Retained geometry repairs; successful builds still require visual/browser acceptance."""
import json,tempfile
from pathlib import Path
from reconstruction_kernel import compile_spec,build
from explorer_workflow import digest,save

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))

def changes(before,after):
    a={p['id']:p for p in before['parts']};b={p['id']:p for p in after['parts']}
    keys=('parameters','origin','size','opacity')
    return sorted(k for k in a.keys()|b.keys() if k not in a or k not in b or
                  any(a[k].get(v)!=b[k].get(v) for v in keys) or
                  a[k].get('appearance',{}).get('opacity',1)!=b[k].get('appearance',{}).get('opacity',1))

def revise(project,parent,new_spec,issues,authorization,pair=None):
    parent=Path(parent).resolve()
    history=Path(project).resolve()/'output/history';history.mkdir(parents=True,exist_ok=True)
    audit=Path(tempfile.mkdtemp(prefix='geometry-repair-',dir=history))
    save(audit/'proposal.json',{'parent':str(parent),'issues':issues,'authorization':authorization})
    save(audit/'specification.json',new_spec)
    try:
        if not isinstance(authorization,str) or not authorization.strip():raise ValueError('Current repair authorization required')
        old=read(parent/'specification.json');request=read(parent/'request.json')
        retained=read(parent/'source.json');source=parent/('source'+Path(retained['path']).suffix.lower())
        if digest(source)!=retained['sha256']:raise ValueError('Retained source changed')
        if old.get('schema_version')==2 and new_spec.get('schema_version')!=2:
            raise ValueError('Repair cannot downgrade the fidelity schema')
        for key in ('contacts','connections'):
            for relation in old.get(key,[]):
                if relation not in new_spec.get(key,[]):raise ValueError('Repair cannot drop existing '+key+' checks')
        for key in ('features','protected_spaces'):
            old_ids={v['id'] for v in old.get('quality_contract',{}).get(key,[])}
            new_ids={v['id'] for v in new_spec.get('quality_contract',{}).get(key,[])}
            if old_ids-new_ids:raise ValueError('Repair cannot drop '+key)
        if old.get('access_network'):
            if set(old['access_network']['targets'])-set(new_spec.get('access_network',{}).get('targets',[])):
                raise ValueError('Repair cannot drop walking destinations')
        a,_,_=compile_spec(old);b,_,_=compile_spec(new_spec)
        changed=changes(a,b)
        if not issues or len({i['id'] for i in issues})!=len(issues):raise ValueError('Unique concrete repair issues required')
        all_ids={p['id'] for p in a['parts']}|{p['id'] for p in b['parts']}
        for i in issues:
            if not all(i.get(k) for k in ('id','components','observed','target','action','verification')):raise ValueError('Repair needs component IDs, target and verification view')
            if set(i['components'])-all_ids:raise ValueError('Unknown repair component')
            if not set(i['components'])&set(changed):raise ValueError('No geometry change for repair '+i['id'])
        # A changed caption, HTML hash or unrelated bolt is not geometric repair evidence.
        save(audit/'geometry-diff.json',{'changed_components':changed,'scope':'Compiled geometry/opacity only; not proof of visual fidelity'})
        run,job,html=build(project,new_spec,source,request['brief'],pair=pair,parent_history=parent,
                           operation='continue',reuse_reason=authorization)
        save(job/'pending-repairs.json',{'audit':str(audit),'issues':issues,'status':'needs_independent_review'})
        save(audit/'next.json',{'run':str(run),'job':str(job),'candidate':str(html),
             'next':'Render matched camera; inspect each target and connected neighbors; test actual candidate and call explorer accept. Unresolved issues require another geometry revision, not changed review wording.'})
        return audit,run,job,html
    except Exception as exc:
        save(audit/'failure.json',{'error':str(exc)});raise


def validate_review(job,review):
    job=Path(job);p=job/'pending-repairs.json'
    if not p.exists():return
    issues=read(p)['issues']
    if not isinstance(review,dict) or review.get('candidate_sha256')!=digest(job/'candidate.html'):
        raise ValueError('Repair review must bind the current candidate')
    observations=review.get('issues',{})
    if set(observations)!={i['id'] for i in issues}:raise ValueError('Review every pending repair')
    for item in observations.values():
        if item.get('status')!='resolved' or not item.get('source_evidence') or not item.get('model_evidence') or not item.get('neighbor_checks'):
            raise ValueError('Unresolved repair: revise geometry and inspect target plus adjoining components')
