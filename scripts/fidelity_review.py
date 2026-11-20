"""Source/model comparison evidence. No automatic semantic image matching."""
import json,hashlib,uuid
from pathlib import Path
from PIL import Image

AXES=('shape','proportions','orientation','placement','connections')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))

def record_browser_comparison(job,folder):
    """Bind an actual browser capture produced by capture_explorer_comparison.mjs."""
    from explorer_workflow import verify
    job=Path(job).resolve();folder=Path(folder).resolve();source=verify(job)
    if job not in folder.parents:raise ValueError('Retain comparison in explorer history')
    capture=read(folder/'capture.json')
    if capture.get('errors') or capture['candidate_sha256']!=sha(job/'candidate.html') or capture['model_sha256']!=sha(folder/'model.png'):
        raise ValueError('Browser capture changed or failed')
    image=source['images'].get('coloreada.png',next(iter(source['images'].values())))
    with Image.open(folder/'model.png') as im:model=im.convert('RGB')
    with Image.open(image['path']) as im:original=im.convert('RGB');original.thumbnail(model.size)
    canvas=Image.new('RGB',model.size,'white');canvas.paste(original,((model.width-original.width)//2,(model.height-original.height)//2));canvas.save(folder/'source.png')
    sheet=Image.new('RGB',(model.width*2,model.height),'white');sheet.paste(canvas,(0,0));sheet.paste(model,(model.width,0));sheet.save(folder/'side-by-side.png')
    record={'camera':capture['requested_camera'],'candidate_sha256':sha(job/'candidate.html'),'scene_sha256':sha(job/'scene.json'),'source_sha256':image['sha256'],
      'files':{n:sha(folder/n) for n in ['source.png','model.png','side-by-side.png']},'renderer':'actual_browser_candidate','capture_sha256':sha(folder/'capture.json'),
      'scope':'Actual retained candidate with all assemblies visible, assembled and uncut. Manual semantic comparison, not automatic similarity.'}
    (folder/'record.json').write_text(json.dumps(record,indent=2),encoding='utf-8');return folder/'record.json'

def render_comparison(job,camera):
    from explorer_workflow import verify
    from render_scene import build,Renderer
    job=Path(job);source=verify(job)
    if not source['images']:raise ValueError('Comparison needs source pixels')
    image=source['images'].get('coloreada.png',next(iter(source['images'].values())))
    projection=camera.get('projection')
    if projection not in ('perspective','orthographic') or not camera.get('rationale'):
        raise ValueError('Declare comparable projection and camera rationale')
    if projection=='perspective' and (not camera.get('eye') or not camera.get('target')):
        raise ValueError('Perspective comparison needs explicit eye and target')
    with Image.open(image['path']) as im:
        original=im.convert('RGB');original.thumbnail((960,960));w,h=original.size
        if min(w,h)<200:
            scale=200/min(w,h);w,h=round(w*scale),round(h*scale)
            original=original.resize((w,h))
    mesh=build(read(job/'scene.json'))
    kwargs=dict(projection=projection,finish='technical',shadows=False)
    if projection=='perspective':kwargs.update(camera_eye=camera['eye'],camera_target=camera['target'],fov=camera.get('fov',50),near=camera.get('near',.1))
    else:kwargs.update(azimuth=camera.get('azimuth',45),elevation=camera.get('elevation',35))
    rendered=Renderer(mesh,w,h,**kwargs).draw(mesh)
    folder=job/('comparison-'+uuid.uuid4().hex[:10]);folder.mkdir()
    original.save(folder/'source.png');rendered.save(folder/'model.png')
    sheet=Image.new('RGB',(w*2,h),'white');sheet.paste(original,(0,0));sheet.paste(rendered,(w,0));sheet.save(folder/'side-by-side.png')
    record={'camera':camera,'candidate_sha256':sha(job/'candidate.html'),'scene_sha256':sha(job/'scene.json'),
            'source_sha256':image['sha256'],'files':{n:sha(folder/n) for n in ['source.png','model.png','side-by-side.png']},
            'scope':'Same retained geometry, manual camera matching; visual correspondence is not inferred by code.'}
    (folder/'record.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    return folder/'record.json'

def validate(job,features,reviews,comparison):
    job=Path(job)
    if not comparison:raise ValueError('Comparable source/model render required')
    record_path=Path(comparison).resolve()
    if job.resolve() not in record_path.parents:raise ValueError('Comparison must be retained in this job')
    r=read(record_path);source=read(job/'source.json')
    if r.get('renderer')=='actual_browser_candidate' and r.get('capture_sha256')!=sha(record_path.parent/'capture.json'):
        raise ValueError('Browser capture evidence changed')
    if r['candidate_sha256']!=sha(job/'candidate.html') or r['scene_sha256']!=sha(job/'scene.json'):
        raise ValueError('Comparison belongs to different geometry')
    if r['source_sha256'] not in {v['sha256'] for v in source['images'].values()}:raise ValueError('Different source image')
    if set(r['files'])!={'source.png','model.png','side-by-side.png'}:raise ValueError('Incomplete comparison files')
    for name,digest in r['files'].items():
        if sha(record_path.parent/name)!=digest:raise ValueError('Comparison image changed')
    if not features or not isinstance(reviews,dict) or set(reviews)!={f['id'] for f in features}:
        raise ValueError('Explicit feature fidelity inventory required')
    for f in features:
        item=reviews[f['id']]
        if set(item.get('fidelity',{}))!=set(AXES):raise ValueError('Presence is not fidelity: compare five aspects for '+f['id'])
        for axis,check in item['fidelity'].items():
            if check.get('status') not in ('matched','mismatch','uncertain','not_applicable') or not check.get('source_evidence') or not check.get('model_evidence'):
                raise ValueError('Source and model observations required: '+axis)
            if check['status']=='mismatch':raise ValueError('Known correspondence mismatch: '+f['id']+'/'+axis)
            if check['status']=='not_applicable' and (axis!='connections' or not check.get('reason')):
                raise ValueError('Only inapplicable connections can be exempted with a reason')
            if f.get('critical') and check['status']=='uncertain':raise ValueError('Critical visible feature unresolved: '+f['id']+'/'+axis)
    return r
