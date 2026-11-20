"""Portable example loader and calculated guide builder. No image-generation API calls."""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys
from history_run import preserved_directory

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from kit import generate,validate
from typed_interfaces import coverage

def names():
    return sorted(p.name for p in (ROOT/'examples').iterdir() if p.is_dir() and (p/'recipe.json').is_file())

def load_example(name):
    if name not in names():raise ValueError('Unknown bundled example: '+name)
    folder=ROOT/'examples'/name
    recipe=json.loads((folder/'recipe.json').read_text(encoding='utf-8'))
    spec=importlib.util.spec_from_file_location('example_'+name.replace('-','_'),folder/'scene.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    data=module.scene();errors=validate(data)
    counts=Counter(p['kind'] for p in data['parts'])
    for kind,expected in recipe['counts'].items():
        if counts[kind]!=expected:errors.append(f'{kind}: expected {expected}, got {counts[kind]}')
    ids={p['id'] for p in data['parts']}
    for label in recipe['labels']:
        if label['target'] not in ids:errors.append('Unknown label target: '+label['target'])
    if errors:raise ValueError('; '.join(errors))
    return data,recipe

def main(fixed_example=None):
    parser=argparse.ArgumentParser(description=__doc__)
    if fixed_example is None:parser.add_argument('example',choices=names())
    parser.add_argument('--validate-only',action='store_true')
    parser.add_argument('--out-dir',type=Path)
    parser.add_argument('--width',type=int,default=1400)
    parser.add_argument('--height',type=int,default=1000)
    parser.add_argument('--supersample',type=int,choices=[1,2,3],default=2)
    args=parser.parse_args();name=fixed_example or args.example
    data,recipe=load_example(name)
    if args.validate_only:
        print(json.dumps({'example':name,'geometry':'passed','coverage':coverage(data),'counts':recipe['counts'],'visual_review':'not_run'}));return
    if args.out_dir is None:parser.error('--out-dir is required for rendering')
    destination=args.out_dir.resolve()
    if destination==ROOT or ROOT in destination.parents:parser.error('Output must be outside the installed skill')
    if destination.exists():parser.error('Output already exists; choose a new folder')
    destination.parent.mkdir(parents=True,exist_ok=True)
    with preserved_directory(destination.parent, '.example-scene-') as tmp:
        owned=Path(tmp).resolve()
        if owned.parent!=destination.parent / "history":raise RuntimeError('Temporary path escaped output parent')
        source=owned/'scene.json';source.write_text(json.dumps(data),encoding='utf-8')
        camera=data.get('camera',recipe['camera']) if recipe.get('pipeline')=='physical-cutaway' else recipe['camera']
        report=generate(source,destination,width=args.width,height=args.height,supersample=args.supersample,
                        finish='graphite',title='',shadows=False,**camera)
    report.update({'source_history':str(owned),'example':name,'artifact_role':'calculated-guide','artistic_finish':'not_run',
                   'labels':'planned in recipe; place and verify arrows during artistic finish'})
    print(json.dumps(report))

if __name__=='__main__':main()
