"""Optional 3D orchestration: image evidence -> authored specification -> checked meshes -> HTML.

The visual analysis is performed by the executing agent, not by this Python module.
"""
import argparse,json,math,shutil,tempfile
from pathlib import Path
import numpy as np
from PIL import Image
from reconstruction_geometry import component,vector
from registered_geometry import arrays,on_triangle
from scene_model import validation_report
from explorer_workflow import prepare,render,digest,save


def compile_spec(spec):
    if spec.get('schema_version') not in (1,2):raise ValueError('Reconstruction schema_version 1 or 2 required')
    if not spec.get('title') or not spec.get('limitations'):raise ValueError('Title and reconstruction limits required')
    if not spec.get('camera_notes'):raise ValueError('Source view and depth interpretation required')
    parts=spec.get('components',[]);ids=[p['id'] for p in parts]
    if not parts or len(set(ids))!=len(ids):raise ValueError('Unique nonempty components required')
    targets=spec.get('correspondence',[])
    if not targets:raise ValueError('Image correspondence targets required')
    mapped=set()
    for t in targets:
        if not t.get('evidence') or not t.get('parts') or set(t['parts'])-set(ids):raise ValueError('Correspondence requires known parts and pixel observations')
        b=t.get('image_bbox')
        if not isinstance(b,list) or len(b)!=4 or any(type(v) not in (int,float) or not math.isfinite(v) for v in b) or not (0<=b[0]<b[2]<=1 and 0<=b[1]<b[3]<=1):raise ValueError('Normalized image bounding box required')
        mapped.update(t['parts'])
    model=[]
    for p in parts:
        if p.get('provenance') not in ('observed','inferred','modeled') or not p.get('evidence'):raise ValueError('Every component needs provenance and evidence')
        if p['provenance']=='observed' and p['id'] not in mapped:raise ValueError('Observed component missing image correspondence: '+p['id'])
        if not p.get('hidden_assumptions'):raise ValueError('Record hidden shape assumptions, even for observed parts')
        if not p.get('support_note'):raise ValueError('Record support/attachment scope for each component')
        model.append(component(p))
    byid={p['id']:p for p in model};raw={p['id']:p for p in parts};contact_report=[]
    for relation in spec.get('contacts',[]):
        # Named anchors must coincide AND lie on both actual mesh surfaces.
        ends=[]
        for endpoint in (relation['from'],relation['to']):
            pid,port=endpoint.rsplit(':',1)
            if pid not in raw or port not in raw[pid].get('anchors',{}):raise ValueError('Unknown contact anchor: '+endpoint)
            point=vector(raw[pid]['anchors'][port]);p=byid[pid];v,f=arrays(p['parameters']);v+=vector(p['origin'])
            if not any(on_triangle(point,v[face[0]],v[face[1]],v[face[2]],tol=1e-4) for face in f):raise ValueError('Contact anchor misses actual surface: '+endpoint)
            ends.append(point)
        if np.linalg.norm(ends[0]-ends[1])>1e-4:raise ValueError('Contact gap: '+relation['from'])
        contact_report.append(dict(relation,status='passed',scope='named surface anchor coincidence only; no load or contact-area simulation'))
    scene={'units':'m','registered_geometry':True,'parts':model,'connections':spec.get('connections',[]),'attachments':spec.get('contacts',[])}
    # Pipe routes retain the original endpoint, curvature and self-clearance checks.
    coverage=validation_report(scene)
    if coverage.get('status')=='failed':raise ValueError('Geometry failed: '+json.dumps(coverage))
    assemblies=[dict(g) for g in spec.get('assemblies',[])]
    if not assemblies:raise ValueError('Assembly grouping required')
    for g in assemblies:
        assumptions=list(dict.fromkeys(raw[name]['hidden_assumptions'] for name in g.get('members',[]) if name in raw))
        if assumptions:g['evidence']=g.get('evidence','')+' Hidden-region assumptions: '+'; '.join(assumptions)
    checked_ids={v.rsplit(':',1)[0] for c in spec.get('contacts',[]) for v in (c['from'],c['to'])}
    unchecked=[pid for pid in ids if pid not in checked_ids]
    from access_network import inspect as inspect_access
    access=inspect_access(spec.get('access_network'),scene)
    from maquette_quality import inspect
    quality=inspect(spec,scene)
    config={'title':spec['title'],'assemblies':assemblies,'presentation':spec.get('presentation',{}),'quality':quality,'dimensions_verified':False,'limitations':spec['limitations']+[
        'ReconstrucciÃ³n conceptual desde evidencia visible; caras ocultas y proporciones inferidas.',
        'Los contactos comprobados son locales. No se simulan cargas ni desmontaje fÃ­sico.',
        f'{len(unchecked)} componentes sin comprobaciÃ³n numÃ©rica de contacto; consultar el historial y sus notas de apoyo.']}
    return scene,config,{'geometry':coverage,'access_network':access,'quality':quality,'contacts':contact_report,'components_without_checked_contact':unchecked,'correspondence':targets,'scope':'Agent-authored reconstruction, not automatic image-to-3D inference'}


def build(project,spec,source,brief,pair=None,parent_history=None,illustration_attempt=None,operation='create',reuse_reason=None,spatial_snapshot=None):
    source=Path(source).resolve();project=Path(project).resolve()
    history=project/'output/history';history.mkdir(parents=True,exist_ok=True)
    run=Path(tempfile.mkdtemp(prefix='reconstruction-',dir=history))
    save(run/'request.json',{'brief':brief,'source':str(source),'parent_history':str(parent_history) if parent_history else None})
    save(run/'specification.json',spec)
    try:
        from creation_identity import pair_evidence
        if operation=='create':
            if illustration_attempt is None: raise ValueError('New creation requires current illustration_attempt; do not copy a previous pair. Generate the new illustrations first.')
            save(run/'creation-evidence.json',pair_evidence(illustration_attempt,source,brief))
            if spatial_snapshot is not None:
                # Retain strict binding for explicitly supplied legacy design-first work.
                from kernel3d.workflow import check_binding
                save(run/'spatial-design.json',check_binding(spatial_snapshot,illustration_attempt,spec))
            else:
                save(run/'reconstruction-route.json',{'mode':'image_first','source':'accepted colored image','hidden_geometry':'inferred; review required'})
        elif operation in ('reconstruct','edit','continue') and isinstance(reuse_reason,str) and reuse_reason.strip():
            save(run/'reuse-authorization.json',{'operation':operation,'user_request':reuse_reason})
        else: raise ValueError('Explicit reuse authorization required')
        with Image.open(source) as im:im.load();size=im.size
        source_hash=digest(source);shutil.copyfile(source,run/('source'+source.suffix.lower()))
        save(run/'source.json',{'sha256':source_hash,'size':size,'path':str(source)})
        if pair and digest(Path(pair)/'coloreada.png')!=source_hash:raise ValueError('Use the actual colored source from the selected pair')
        scene,config,checks=compile_spec(spec)
        save(run/'checks.json',checks);save(run/'scene.json',scene);save(run/'assemblies.json',config)
        job=prepare(project,scene,config,brief,pair=pair,parent_history=run,source_image=None if pair else source)
        candidate=render(job)
        save(run/'next.json',{'explorer_history':str(job),'candidate':str(candidate),'next':'Run real browser checks, inspect source/model correspondence, then accept. Planning is not delivery.'})
        return run,job,candidate
    except Exception as error:
        save(run/'failure.json',{'error':str(error)});raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',required=True);p.add_argument('--source',required=True)
    p.add_argument('--spec',required=True);p.add_argument('--pair');p.add_argument('--history');p.add_argument('--brief',required=True);p.add_argument('--illustration-attempt');p.add_argument('--spatial-snapshot');p.add_argument('--operation',choices=['create','edit','reconstruct','continue'],default='create');p.add_argument('--reuse-reason')
    a=p.parse_args();print(build(a.project,json.loads(Path(a.spec).read_text(encoding='utf-8')),a.source,a.brief,a.pair,a.history,a.illustration_attempt,a.operation,a.reuse_reason,a.spatial_snapshot)[2])
