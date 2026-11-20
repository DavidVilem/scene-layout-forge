"""Build and verify a source-only ZIP; no installation or publication side effects."""
import argparse,hashlib,json,zipfile
from pathlib import Path
from check_package import audit,ART


def manifest(root):
    root=Path(root).resolve();issues=audit(root)
    if issues:raise ValueError('; '.join(issues))
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file() and '.git' not in p.relative_to(root).parts}


def verify(archive,expected):
    with zipfile.ZipFile(archive) as z:
        names=z.namelist();prefix='scene-layout-forge/'
        if len(set(names))!=len(names):raise ValueError('duplicate ZIP entries')
        if any(not n.startswith(prefix) or '..' in Path(n).parts or '\\' in n for n in names):raise ValueError('invalid ZIP path')
        actual={n[len(prefix):]:hashlib.sha256(z.read(n)).hexdigest() for n in names}
    if actual!=expected:raise ValueError('ZIP contents differ from source manifest')
    return {'files':len(actual),'source_and_zip_identical':True}


def build(root,out):
    root=Path(root).resolve();out=Path(out).resolve()
    if out==root or root in out.parents:raise ValueError('ZIP must stay outside skill')
    if out.suffix.lower()!='.zip':raise ValueError('ZIP suffix required')
    if out.exists() or out.with_suffix('.manifest.json').exists():raise FileExistsError('release output already exists')
    expected=manifest(root);out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name in expected:z.write(root/name,'scene-layout-forge/'+name)
    result=verify(out,expected)
    out.with_suffix('.manifest.json').write_text(json.dumps({'files':expected,**result},indent=2),encoding='utf-8')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(json.dumps(build(a.source,a.out)))
