"""Non-overwriting run paths and explicit, bounded cleanup plans (no deletion)."""
import hashlib, re, tempfile
from pathlib import Path


def new_output(project,stem,filename='final.png'):
    project=Path(project).resolve()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',stem):raise ValueError('portable output stem required')
    if Path(filename).name!=filename or not filename.lower().endswith('.png'):raise ValueError('simple PNG filename required')
    output=project/'output'
    if output.is_symlink():raise ValueError('output root must not be a symlink')
    output.mkdir(exist_ok=True)
    number=1
    while True:
        target=output/f'{stem}-{number:02d}'
        try:target.mkdir();return target/filename
        except FileExistsError:number+=1


def new_temporary(project):
    project=Path(project).resolve();work=project/'work'
    if work.is_symlink():raise ValueError('temporary parent must not be a symlink')
    work.mkdir(exist_ok=True)
    return Path(tempfile.mkdtemp(prefix='layout-run-',dir=work))


def owned_record(temp_root,path):
    root=Path(temp_root).resolve();path=Path(path)
    if path.is_symlink():raise ValueError('owned file must not be a symlink')
    resolved=path.resolve()
    if root not in resolved.parents or not resolved.is_file():raise ValueError('owned file must be a regular file inside this run')
    return {'relative_path':resolved.relative_to(root).as_posix(),'sha256':hashlib.sha256(resolved.read_bytes()).hexdigest()}


def cleanup_plan(temp_root,owned,final):
    from pixel_review import image_identity
    image_identity(final)  # A valid deliverable is required before cleanup.
    root=Path(temp_root).resolve();final=Path(final).resolve()
    if root in final.parents:raise ValueError('final must be outside temporary directory')
    result=[]
    for item in owned:
        relative=Path(item['relative_path'])
        if relative.is_absolute() or '..' in relative.parts:raise ValueError('cleanup path escapes run')
        candidate=root/relative
        if candidate.is_symlink() or any(parent.is_symlink() for parent in candidate.parents if parent!=root and root in parent.parents):raise ValueError('cleanup symlink forbidden')
        path=candidate.resolve()
        if root not in path.parents:raise ValueError('cleanup path escapes run')
        if path==final:raise ValueError('cannot remove final')
        if path.exists():
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('owned file changed; review before cleanup')
            result.append(str(path))
    return sorted(set(result))
