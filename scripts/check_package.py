"""Audit distribution hygiene and local documentation links; not a security sandbox."""
import argparse
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
TEXT={'.py','.md','.json','.yaml','.yml','.txt','.js','.mjs','.html'}
ART={'.png','.jpg','.jpeg','.webp','.gif','.bmp','.tif','.tiff','.ico','.svg','.pdf','.zip','.pyc','.mp4','.webm','.mov','.avi','.mp3','.wav'}

def audit(root):
    root=Path(root).resolve();issues=[]
    for name in ['SKILL.md','README.md','requirements.txt','kit/__init__.py','evals/evals.json','evals/rubric.json','references/art-direction.md']:
        if not (root/name).is_file():issues.append('Missing '+name)
    for path in root.rglob('*'):
        relative=path.relative_to(root)
        if '.git' in relative.parts:continue
        if path.is_symlink():issues.append('Symlink: '+str(relative));continue
        if '__pycache__' in relative.parts:issues.append('Cache: '+str(relative));continue
        if not path.is_file():continue
        if path.suffix.lower() in ART:issues.append('Generated/binary artifact: '+str(relative))
        if path.suffix.lower() not in TEXT:continue
        try:text=path.read_text(encoding='utf-8-sig')
        except UnicodeDecodeError:
            issues.append('Invalid UTF-8 text: '+str(relative));continue
        if re.search(r'[A-Za-z]:[/\\](?:Users|Codex)[/\\]|/(?:Users|home)/[^/\s]+/',text):issues.append('Personal absolute path: '+str(relative))
        if re.search(r'data:image/[^;]+;base64,',text):issues.append('Embedded image: '+str(relative))
        if path.suffix=='.md':
            for target in re.findall(r'\]\(([^)]+)\)',text):
                if '://' in target or target.startswith('#'):continue
                if not (path.parent/target.split('#')[0]).exists():issues.append('Broken link: '+str(relative)+' -> '+target)
    return sorted(set(issues))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',nargs='?',type=Path,default=ROOT)
    issues=audit(parser.parse_args().root)
    print(json.dumps({'package_audit':'failed' if issues else 'passed','issues':issues},indent=2))
    raise SystemExit(bool(issues))
