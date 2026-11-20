"""Persistent run history; no automatic deletion."""
import json,tempfile
from pathlib import Path
from contextlib import contextmanager
STAGES=('01-site','02-program','03-massing','04-structure','05-levels','06-systems','07-representation','08-finish')
@contextmanager
def preserved_directory(parent,prefix):
    history=Path(parent).resolve()/'history'
    if history.is_symlink():raise ValueError('history symlink forbidden')
    history.mkdir(exist_ok=True)
    yield tempfile.mkdtemp(prefix=prefix,dir=history)
def new_run(project,stem='layout',brief=None,operation='create',reuse_reason=None):
    from creation_identity import policy
    operation_record=policy(project,operation,reuse_reason)
    import re
    if not re.fullmatch(r'[A-Za-z0-9_-]+',stem):raise ValueError('portable stem required')
    output=Path(project).resolve()/'output'
    if output.is_symlink():raise ValueError('output symlink forbidden')
    output.mkdir(exist_ok=True)
    with preserved_directory(output,stem+'-') as folder:root=Path(folder)
    for stage in STAGES:(root/stage).mkdir()
    (root/'operation.json').write_text(json.dumps(operation_record,indent=2),encoding='utf-8')
    (root/'run.json').write_text(json.dumps({'stages':STAGES,'retention':'all attempts, including failures'},indent=2),encoding='utf-8')
    if brief is not None:
        if not isinstance(brief,str) or not brief.strip():raise ValueError('nonempty original brief required')
        (root/'01-site'/'brief.txt').write_text(brief,encoding='utf-8')
    return root

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,required=True);p.add_argument('--stem',default='layout');p.add_argument('--brief',required=True)
    a=p.parse_args();print(json.dumps({'run':str(new_run(a.project,a.stem,a.brief))}))

