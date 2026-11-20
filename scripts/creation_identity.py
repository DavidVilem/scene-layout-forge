"""Operation and decoded-pixel provenance; not a semantic originality detector."""
import hashlib,json
from pathlib import Path
from PIL import Image

def pixels(path):
    with Image.open(path) as im:
        im.load(); im=im.convert('RGBA')
        return hashlib.sha256(str(im.size).encode()+im.tobytes()).hexdigest()

def policy(project, operation='create', reuse_reason=None):
    if operation not in ('create','edit','reconstruct','continue'):
        raise ValueError('Unknown operation')
    if operation!='create' and not (isinstance(reuse_reason,str) and reuse_reason.strip()):
        raise ValueError('Explicit user authorization for reuse required')
    previous=[]; unreadable=[]
    for p in (Path(project)/'output').glob('*/*.png'):
        if p.is_symlink(): continue
        try: previous.append({'path':str(p.resolve()),'pixels':pixels(p)})
        except (OSError,ValueError): unreadable.append(str(p))
    return dict(operation=operation,reuse_reason=reuse_reason,previous=previous,unreadable=unreadable)

def check(image, record):
    if record.get('operation')!='create': return
    value=pixels(image)
    matches=[p['path'] for p in record['previous'] if p['pixels']==value]
    if matches: raise ValueError('New creation reused previous pixels. Generate a fresh design; retain this rejected attempt. Sources: '+', '.join(matches))

def check_attempt(attempt,image):
    p=Path(attempt)/'operation.json'
    if p.exists(): check(image,json.loads(p.read_text(encoding='utf-8')))

def pair_evidence(attempt,source,brief):
    from illustration_workflow import verify,read
    from pixel_review import image_identity
    attempt=Path(attempt).resolve();verify(attempt)
    if (attempt.parent.parent/'01-site/brief.txt').read_text(encoding='utf-8')!=brief:
        raise ValueError('3D brief must match this creation run')
    identity=image_identity(source)
    for p in attempt.glob('color-*/delivered.json'):
        d=read(p)
        if d.get('colored')==identity and Path(d['coloreada']).resolve()==Path(source).resolve():
            original=Path(d['ilustrada'])
            if image_identity(original)!=d['source']: raise ValueError('Illustration changed after coloring')
            check_attempt(attempt,original)
            return {'attempt':str(attempt),'delivery':str(p),'source':identity}
    raise ValueError('3D source is not the colored delivery of the current illustration attempt. Complete illustration/coloring first, or explicitly request reconstruction of an existing image.')
