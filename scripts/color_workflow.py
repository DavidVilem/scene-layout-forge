"""Retained image-to-image coloring of an accepted ilustrada.png.

These helpers bind evidence; actual image generation and side-by-side visual
inspection are performed by the agent. Never claim geometry preservation from
hashes alone. No generated media belongs in the skill package.
"""
from pathlib import Path
import uuid
import shutil
from illustration_workflow import read, save, verify
from pixel_review import image_identity
from run_manifest import sha, source_identity

ROOT=Path(__file__).resolve().parents[1]
KEYS={'composition','linework','connections','annotations','detail','palette'}

def prepare(attempt, illustrated, palette=None, previous=None, correction=None):
    attempt=Path(attempt).resolve();verify(attempt)
    illustrated=Path(illustrated).resolve();identity=image_identity(illustrated)
    if illustrated.name!='ilustrada.png':raise ValueError('Color the selected ilustrada.png')
    selections=[read(p) for p in attempt.glob('selected-*.json')]
    if not any(s.get('final')==str(illustrated) and s.get('image')==identity for s in selections):
        raise ValueError('Illustration must be selected and reviewed before coloring')
    matching=[s for s in selections if s.get('final')==str(illustrated) and s.get('image')==identity]
    for selected in matching:
        record=read(selected['review'])
        errors=[k for k,v in record['observations'].items() if k.startswith(('perspective','architecture:')) and v.get('status')=='visible_error']
        if errors:
            kind='perspective' if any(k.startswith('perspective') for k in errors) else 'architecture'
            raise ValueError('Known '+kind+' defect: retain the illustration and repair before coloring')
    index=0;references=[]
    if previous is not None:
        previous=Path(previous).resolve();_verify(previous)
        old=read(previous/'source.json')
        if old['illustrated']!=str(illustrated) or old['identity']!=identity:raise ValueError('Correction source changed')
        index=old['correction_index']+1
        if index>2:raise ValueError('Maximum two color corrections; retain and report unresolved defects')
        if not correction or not list(previous.glob('review-*.json')):raise ValueError('Review previous color result before correction')
        image_identity(previous/'original.png')
        references.append(str(previous/'original.png'))
    job=attempt/('color-'+uuid.uuid4().hex[:12]);job.mkdir()
    shutil.copyfile(illustrated,job/'illustrated-source.png')
    references.append(str(job/'illustrated-source.png'))
    direction=palette or 'Restrained anime-background colors: cool blue-gray steel, subtle warm concrete/stone, muted material accents, soft natural lighting. Preserve neutral near-white paper in unpainted areas; no global yellow or sepia wash.'
    prompt=('EDIT the supplied illustration into ONE colored PNG of the SAME scene. '
        'Do not redesign or regenerate a different composition. Preserve the original framing, aspect ratio, '
        'pixel dimensions, perspective, every structural part, silhouettes, pipe starts/ends, joints, supports, '
        'people/counts and any existing annotations exactly. Add no text if none exists. '
        'Apply color beneath readable graphite/fine-ink linework, selective soft shading and differentiated materials. '
        'Keep dense construction detail and readable depth; no glossy photorealistic 3D finish. '
        'Do not remove, simplify, invent or move equipment to make coloring easier. '+direction)
    if previous is not None:prompt+=' The first image is the color attempt to correct; the last image is the authoritative illustrated original. Local correction: '+correction
    request={'prompt':prompt,'referenced_image_paths':references,'transparent_background':False}
    save(job/'request.json',request)
    save(job/'source.json',{'illustrated':str(illustrated),'identity':identity,'correction_index':index,
                           'skill':source_identity(ROOT),'palette':direction})
    files={p.name:sha(p) for p in job.iterdir() if p.is_file()}
    save(job/'receipt.json',files)
    return job

def _verify(job):
    job=Path(job).resolve()
    verify(job.parent)
    for name,expected in read(job/'receipt.json').items():
        p=job/name
        if p.parent!=job or not p.is_file() or sha(p)!=expected:raise ValueError('Color input changed')
    source=read(job/'source.json')
    if image_identity(source['illustrated'])!=source['identity']:raise ValueError('Selected illustration changed')
    return source

def retain(job, image, actual_request):
    job=Path(job);_verify(job)
    if actual_request!=read(job/'request.json'):raise ValueError('Color request differs from prepared edit')
    identity=image_identity(image)
    with (job/'original.png').open('xb') as f:f.write(Path(image).read_bytes())
    save(job/'generation.json',{'request':actual_request,'image':identity})
    return job/'original.png'

def review(job, observations):
    job=Path(job);source=_verify(job);identity=image_identity(job/'original.png')
    if identity!=read(job/'generation.json')['image']:raise ValueError('Generated color pixels changed')
    if set(observations)!=KEYS:raise ValueError('Compare composition, linework, connections, annotations, detail and palette')
    for item in observations.values():
        if item.get('status') not in {'preserved','changed','uncertain'} or not item.get('notes','').strip():
            raise ValueError('Actual comparative observations required')
    path=job/('review-'+uuid.uuid4().hex[:12]+'.json')
    save(path,{'source':source['identity'],'colored':identity,'observations':observations})
    return path

def accept(job, review_path):
    job=Path(job).resolve();source=_verify(job);record=read(review_path)
    original=Path(source['illustrated']);destination=original.with_name('coloreada.png')
    identity=image_identity(job/'original.png');generation=read(job/'generation.json')
    if generation['request']!=read(job/'request.json') or generation['image']!=identity or record['colored']!=identity or record['source']!=source['identity']:
        raise ValueError('Color evidence no longer matches')
    if identity['size']!=source['identity']['size']:raise ValueError('Color edit changed image dimensions; correct without silent resampling')
    if identity['pixel_sha256']==source['identity']['pixel_sha256']:raise ValueError('Unchanged illustration is not a colored output')
    observations=record['observations']
    if set(observations)!=KEYS or any(v.get('status') not in {'preserved','changed','uncertain'} or not v.get('notes','').strip() for v in observations.values()):raise ValueError('Invalid comparative review')
    changed=[k for k,v in observations.items() if v['status']=='changed']
    if changed:raise ValueError('Correct observed changes before delivering colored output: '+', '.join(changed))
    with destination.open('xb') as f:f.write((job/'original.png').read_bytes())
    result={'ilustrada':str(original),'coloreada':str(destination),'source':source['identity'],'colored':identity,
            'limitations':[k+': '+v['notes'] for k,v in observations.items() if v['status']=='uncertain']}
    save(job/'delivered.json',result)
    if (job.parent/'delivery-pipeline.json').is_file():
        from delivery_pipeline import checkpoint
        result['next_action'] = checkpoint(job.parent/'delivery-pipeline.json')
    return result
