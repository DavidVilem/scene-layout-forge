"""Build a standalone 3D explorer from owned geometry, never infer hidden geometry from PNG bytes.

Pairs remain immutable. A separate example mode is for technical prototypes only.
"""
import argparse
import hashlib
import html
import json
import math
import shutil
import tempfile
from pathlib import Path
from PIL import Image
from render_scene import build
from scene_model import validation_report

ROOT = Path(__file__).resolve().parents[1]
KEYS = ('correspondence', 'assembled', 'section', 'views', 'interaction')


def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f: json.dump(v,f,ensure_ascii=False,allow_nan=False,indent=2)


def vec(v):
    if not isinstance(v,(list,tuple)) or len(v)!=3 or any(type(x) not in (int,float) or not math.isfinite(x) for x in v):
        raise ValueError('Finite XYZ required')
    return list(v)


def compile_scene(scene, config):
    """Reuse adapters and all their original checks; missing adapters are never replaced by boxes."""
    coverage=validation_report(scene)
    if coverage.get('status')=='failed' or any(c.get('status')=='failed' for c in coverage.get('checks',[])):
        raise ValueError('Assembled geometry failed: '+json.dumps(coverage))
    mesh=build(scene)
    groups=[dict(g) for g in config.get('assemblies',[])]; ids=set(); membership={}
    for g in groups:
        g['offset']=[0,0,0];g['fixed']=True;g.pop('phase',None);g['separation_note']='Fixed semantic group for selection and visibility only.'
    if not groups: raise ValueError('Explicit semantic assemblies required')
    for g in groups:
        if not isinstance(g.get('id'),str) or not g['id'] or g['id'] in ids: raise ValueError('Unique assembly IDs required')
        ids.add(g['id']);vec(g.get('offset'))
        phase=g.get('phase',[0,1])
        if len(phase)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) for v in phase) or not 0<=phase[0]<phase[1]<=1:
            raise ValueError('Separation phase must increase within 0..1')
        for field in ('label','evidence','separation_note'):
            if not isinstance(g.get(field),str) or not g[field].strip(): raise ValueError('Assembly needs '+field)
        if g.get('provenance') not in ('modeled','observed','inferred'): raise ValueError('Explicit assembly provenance required')
        if g.get('fixed') and any(g['offset']): raise ValueError('Fixed assembly cannot move')
        for name in g.get('members',[]):
            if name in membership: raise ValueError('Part belongs to multiple assemblies: '+name)
            membership[name]=g['id']
    owners=set(mesh.face_owners.values())
    if set(membership)!=owners: raise ValueError('Assembly membership must cover exact rendered owners: '+str(owners^set(membership)))
    if not config.get('limitations') or not isinstance(config['limitations'],list): raise ValueError('Explicit scope/limitations required')
    if not config.get('title'): raise ValueError('Title required')
    if config.get('dimensions_verified') and not config.get('dimensions_evidence'):raise ValueError('Measured dimensions need their actual source evidence')
    geometry={owner:[] for owner in sorted(owners)}
    for index,face in enumerate(mesh.faces):
        vertices=face[0];owner=mesh.face_owners.get(index)
        if owner not in geometry: raise ValueError('Unowned rendered face')
        if len(vertices)<3: raise ValueError('Invalid face')
        for i in range(1,len(vertices)-1):
            for v in (vertices[0],vertices[i],vertices[i+1]): geometry[owner].extend(vec(list(map(float,v))))
    if not any(geometry.values()): raise ValueError('No geometry')
    rawparts={p['id']:p for p in scene['parts']}
    parts=[]
    for owner,positions in geometry.items():
        p=rawparts.get(owner,{})
        appearance=p.get('appearance',{})
        color=appearance.get('color')
        if color is not None and (not isinstance(color,str) or not __import__('re').fullmatch(r'#[0-9a-fA-F]{6}',color)):raise ValueError('Invalid component color')
        opacity=appearance.get('opacity',1)
        if type(opacity) not in (int,float) or not math.isfinite(opacity) or not 0<opacity<=1:raise ValueError('Invalid component opacity')
        parts.append(dict(id=owner,assembly=membership[owner],kind=p.get('kind','connection'),positions=positions,color=color,opacity=opacity))
    connections=[]
    for i,c in enumerate(scene.get('connections',[])):
        name=mesh.connection_names[i]
        ends=[]
        for key in ('from','to'):
            pid,port=c[key].rsplit(':',1);p=rawparts[pid]
            anchor=[a+b for a,b in zip(p['origin'],p['ports'][port])]
            ends.append(dict(part=pid,assembly=membership[pid],point=anchor))
        # Route is a rigid, owned assembly. Disconnected ports get explanatory dashed guides.
        connections.append(dict(id=name,assembly=membership[name],ends=ends,route_ends=[c['route'][0],c['route'][-1]]))
    for i,c in enumerate(scene.get('attachments',[])):
        ends=[]
        for key in ('from','to'):
            pid,port=c[key].rsplit(':',1);p=rawparts[pid]
            anchor=[a+b for a,b in zip(p['origin'],p['ports'][port])]
            ends.append(dict(part=pid,assembly=membership[pid],point=anchor))
        connections.append(dict(id=f'attachment[{i}]',assembly=ends[0]['assembly'],ends=ends,route_ends=[ends[0]['point'],ends[0]['point']]))
    bounds=[[min(p['positions'][k::3]) for k in range(3)] for p in parts]
    maxima=[[max(p['positions'][k::3]) for k in range(3)] for p in parts]
    lo=[min(b[k] for b in bounds) for k in range(3)];hi=[max(b[k] for b in maxima) for k in range(3)]
    groups=[dict(g) for g in groups]
    presentation=config.get('presentation',{})
    if presentation:
        direction=vec(presentation.get('direction',[.82,1,.66]))
        if sum(x*x for x in direction)<1e-8:raise ValueError('View direction must be nonzero')
        zoom=presentation.get('zoom',1)
        if type(zoom) not in (int,float) or not math.isfinite(zoom) or not .3<=zoom<=3:raise ValueError('View zoom outside supported range')
    payload=dict(schema_version=1,title=config['title'],assemblies=groups,parts=parts,connections=connections,presentation=presentation,quality=config.get('quality',{}),
        bounds=[lo,hi],units=scene.get('units','relative'),dimensions_verified=bool(config.get('dimensions_verified',False)),
        limitations=config['limitations'],coverage=coverage,
        interaction_mode='fixed_geometry_visibility_only',
        section_mode='clipped surfaces, no inferred internal components or solid caps')
    return payload


def prepare(project, scene, config, brief, pair=None, parent_history=None, example=False, source_image=None):
    if pair is None and source_image is None and not example: raise ValueError('Source image or complete illustrated/colored pair required before explorer delivery')
    history=Path(project).resolve()/'output/history';history.mkdir(parents=True,exist_ok=True)
    job=Path(tempfile.mkdtemp(prefix='explorer-',dir=history))
    save(job/'brief.json',{'brief':brief,'parent_history':str(parent_history) if parent_history else None,'example_only':example})
    save(job/'scene.json',scene);save(job/'assemblies.json',config)
    try:
        images={}
        if pair:
            pair=Path(pair).resolve()
            size=None
            for name in ('ilustrada.png','coloreada.png'):
                p=pair/name
                with Image.open(p) as im:
                    im.load()
                    if im.format!='PNG': raise ValueError('Actual PNG required')
                    if size and im.size!=size: raise ValueError('Image pair dimensions mismatch')
                    size=im.size
                shutil.copyfile(p,job/name)
                images[name]={'path':str(p),'sha256':digest(p)}
        if source_image is not None:
            if pair:raise ValueError('Use pair or single source, not both')
            p=Path(source_image).resolve()
            with Image.open(p) as im:im.load()
            name='source'+p.suffix.lower();shutil.copyfile(p,job/name)
            images[name]={'path':str(p),'sha256':digest(p)}
        # Record duplicate pixels independently of the revision building the HTML.
        lineage={}
        for name,value in images.items():
            matches=[]
            for other in (Path(project)/'output').glob('*/*.png'):
                if other.resolve()==Path(value['path']).resolve():continue
                if other.stat().st_size==Path(value['path']).stat().st_size and digest(other)==value['sha256']:matches.append(str(other.resolve()))
            lineage[name]={'sha256':value['sha256'],'identical_existing_outputs':matches,'image_revision':'unknown unless linked image-generation history establishes it','action':'existing_pixels_used_for_3d; not an image correction'}
        save(job/'image-lineage.json',lineage)
        payload=compile_scene(scene,config)
        payload['example_only']=example
        payload['has_images']=bool(pair)
        payload['single_source']=next(iter(images)) if source_image is not None else None
        save(job/'explorer-model.json',payload)
        save(job/'source.json',{'images':images,'skill_hash':digest(ROOT/'SKILL.md'),'builder_hash':digest(__file__),
            'revision':__import__('re').search(r'revision:\s*"([^"]+)"',(ROOT/'SKILL.md').read_text(encoding='utf-8')).group(1)})
        for name in ('explorer.bundle.js','explorer.html'):
            shutil.copyfile(ROOT/'assets/explorer'/name,job/name)
        shutil.copyfile(__file__,job/'builder-source.py')
        save(job/'receipt.json',{p.name:digest(p) for p in job.iterdir() if p.is_file()})
    except Exception as exc:
        save(job/'failure.json',{'error':str(exc)});raise
    return job


def verify(job):
    job=Path(job)
    for name,h in read(job/'receipt.json').items():
        if digest(job/name)!=h: raise ValueError('History changed: '+name)
    source=read(job/'source.json')
    for value in source['images'].values():
        if digest(value['path'])!=value['sha256']: raise ValueError('Source image changed')
    return source


def render(job):
    job=Path(job);verify(job);model=read(job/'explorer-model.json')
    # Data cannot close its JSON script element. No executable content comes from model strings.
    data=json.dumps(model,ensure_ascii=False,separators=(',',':'),allow_nan=False).replace('<','\\u003c').replace('&','\\u0026')
    page=(job/'explorer.html').read_text(encoding='utf-8').replace('@@TITLE@@',html.escape(model['title']))
    page=page.replace('@@MODEL@@',data).replace('@@RUNTIME@@',(job/'explorer.bundle.js').read_text(encoding='utf-8').replace('</script','<\\/script'))
    path=job/'candidate.html'
    with path.open('x',encoding='utf-8') as f:f.write(page)
    save(job/'render.json',{'sha256':digest(path),'model_hash':digest(job/'explorer-model.json'),
        'owners':len(model['parts']),'assemblies':len(model['assemblies']),'external_network_required':False})
    return path


def accept(job, observations, browser_report, destination=None, feature_review=None, comparison=None, repair_review=None):
    from explorer_repair_cycle import validate_acceptance
    validate_acceptance(job)
    job=Path(job);source=verify(job);report=read(job/'render.json')
    if digest(job/'candidate.html')!=report['sha256']: raise ValueError('Candidate changed')
    save(job/('acceptance-attempt-'+str(len(list(job.glob('acceptance-attempt-*.json')))+1)+'.json'),
         {'candidate_sha256':report['sha256'],'observations':observations,'feature_review':feature_review,
          'browser_report':browser_report,'comparison':str(comparison) if comparison else None})
    from reconstruction_repair import validate_review
    if (job/'pending-repairs.json').exists():
        save(job/('repair-review-'+str(len(list(job.glob('repair-review-*.json')))+1)+'.json'),repair_review)
    validate_review(job,repair_review)
    observations={k:v for k,v in observations.items() if k!='separation'}
    if set(observations)!=set(KEYS): raise ValueError('Five visual/function reviews required; separation is removed')
    for key,v in observations.items():
        if v.get('status') not in ('passed','failed','uncertain') or not v.get('notes'): raise ValueError('Review evidence required: '+key)
    save(job/('review-'+str(len(list(job.glob('review-*.json')))+1)+'.json'),observations)
    if any(v['status']=='failed' for v in observations.values()):raise ValueError('Known defect; retain and correct a new attempt')
    checks=('webgl','selection','fixed_assemblies','reset','views','section','visibility','keyboard','offline','mobile')
    if browser_report.get('candidate_sha256')!=report['sha256'] or any(browser_report.get(k) is not True for k in checks) or browser_report.get('errors'):
        raise ValueError('Actual browser evidence missing or mismatched')
    quality=read(job/'explorer-model.json').get('quality',{})
    if quality.get('status')=='passed_applicable':
        features=quality['features'];required={f['id'] for f in features}
        if not isinstance(feature_review,dict) or set(feature_review)!=required:raise ValueError('Independent feature-by-feature visual review required')
        for f in features:
            review=feature_review[f['id']]
            if review.get('status') not in ('visible','simplified','unverified') or not review.get('notes'):raise ValueError('Feature review needs actual observations')
            if f.get('critical') and review['status']!='visible':raise ValueError('Critical feature not visually confirmed: '+f['id'])
    images=source['images']
    if images:
        from fidelity_review import validate as validate_fidelity
        validate_fidelity(job,quality.get('features',[]),feature_review,comparison)
        if observations['correspondence']['status']!='passed':
            raise ValueError('Image/model correspondence must be established; unresolved critical features remain a draft')
    # Do not poison a retry with exclusive success records before all checks pass.
    if 'coloreada.png' in images:
        target=Path(images['coloreada.png']['path']).with_name('explorador.html')
        if destination is not None and Path(destination).resolve()!=target.resolve(): raise ValueError('Explorer belongs beside pair')
    else:
        if (not images and not read(job/'brief.json')['example_only']) or destination is None:raise ValueError('Explicit destination required for standalone reconstruction or example')
        target=Path(destination).resolve()
        if images:
            for name,value in images.items():
                target.parent.mkdir(parents=True,exist_ok=True)
                image_target=target.parent/name
                if image_target.exists():
                    if digest(image_target)!=value['sha256']:raise ValueError('Existing source reference differs')
                else:shutil.copyfile(value['path'],image_target)
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():raise FileExistsError('Do not overwrite explorer')
    save(job/'browser-review.json',browser_report)
    if feature_review is not None:save(job/'feature-review.json',feature_review)
    if comparison:save(job/'comparison-review.json',{'record':str(Path(comparison).resolve()),'sha256':digest(comparison)})
    with target.open('xb') as f:f.write((job/'candidate.html').read_bytes())
    save(job/'delivered.json',{'path':str(target),'sha256':digest(target),'limitations':read(job/'explorer-model.json')['limitations'],
        'review_limits':[v['notes'] for v in observations.values() if v['status']=='uncertain']})
    return target


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',required=True);p.add_argument('--scene',required=True)
    p.add_argument('--config',required=True);p.add_argument('--pair');p.add_argument('--brief',required=True);p.add_argument('--example',action='store_true')
    a=p.parse_args();j=prepare(a.project,read(a.scene),read(a.config),a.brief,a.pair,example=a.example);print(render(j))
