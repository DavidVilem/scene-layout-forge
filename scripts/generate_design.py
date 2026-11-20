"""Validate and render one calculated design without overwriting prior outputs."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil
from history_run import preserved_directory

from PIL import Image
from scene_model import validate,validation_report
from typed_interfaces import coverage


def generate(scene, out_dir, *, width=1400, height=1000, supersample=2,
             projection='perspective', azimuth=45, elevation=25,
             title='ARCHITECTURAL STUDY', shadows=True, finish='technical',eye=None,target=None,fov=50,near=.1):
    source = Path(scene).resolve(strict=True)
    destination = Path(out_dir).absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('Choose a new output directory; prior results are preserved')
    data = json.loads(source.read_text(encoding='utf-8-sig'))
    errors = validate(data)
    if errors:
        raise ValueError('Invalid scene: ' + '; '.join(errors))
    rendered=data
    if data.get('display_hidden'):
        from assembly_model import compile_cutaway
        rendered=compile_cutaway(data,hide_ids=data['display_hidden'])
    destination.parent.mkdir(parents=True, exist_ok=True)
    parent = destination.parent.resolve(strict=True)
    destination = parent / destination.name
    # Retain every attempt in an exclusive history directory. Resolve and
    # check containment before rendering. No automatic deletion.
    with preserved_directory(parent, '.design-run-') as tmp:
        owned = Path(tmp).resolve(strict=True)
        if owned.parent != parent / "history":
            raise RuntimeError('Temporary directory escaped output parent')
        staged = owned / 'selected'
        staged.mkdir()
        snapshot = owned / 'scene.json'
        snapshot.write_text(json.dumps(rendered), encoding='utf-8')
        (owned / 'physical-scene.json').write_text(json.dumps(data), encoding='utf-8')
        final = staged / 'final.png'
        command = [sys.executable, '-B', str(Path(__file__).with_name('render_scene.py')),
                   '--scene', str(snapshot), '--out', str(final),
                   '--width', str(width), '--height', str(height),
                   '--supersample', str(supersample), '--projection', projection,
                   '--azimuth', str(azimuth), '--elevation', str(elevation), '--title', title,
                   '--finish', finish]
        if eye is not None:command.extend(['--eye',*[str(v) for v in eye]])
        if target is not None:command.extend(['--target',*[str(v) for v in target]])
        command.extend(['--fov',str(fov),'--near',str(near)])
        if not shadows:
            command.append('--no-shadows')
        (owned / 'render-command.json').write_text(json.dumps(command), encoding='utf-8')
        result = subprocess.run(command, capture_output=True, text=True)
        (owned / 'render-stdout.txt').write_text(result.stdout, encoding='utf-8')
        (owned / 'render-stderr.txt').write_text(result.stderr, encoding='utf-8')
        if result.returncode:
            raise RuntimeError('Rendering failed: ' + result.stderr.strip())
        render_report = json.loads(result.stdout)
        with Image.open(final) as image:
            image.verify()
        with Image.open(final) as image:
            image.load()
            if image.format != 'PNG' or image.size != (width, height):
                raise ValueError('Unexpected rendered format or dimensions')
        # Preserve historical raster; copy only to a new destination.
        if destination.exists() or destination.is_symlink():
            raise FileExistsError('Output directory appeared during rendering')
        shutil.copytree(staged, destination)
    return {'output': str(destination / 'final.png'),
            'scene_validation': validation_report(data)['status'], 'validation_report':validation_report(data), 'coverage': coverage(data), 'png_decode': 'passed',
            'representation': rendered.get('representation',{'type':'complete physical scene'}),
            'visual_review': 'pending', 'temporary_files': 'retained', 'history': str(owned),
            'connections': render_report['connections'],
            'component_visibility': render_report['component_visibility'],
            'visibility_raster_size': render_report['visibility_raster_size']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scene', required=True)
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--width', type=int, default=1400)
    parser.add_argument('--height', type=int, default=1000)
    parser.add_argument('--supersample', type=int, choices=[1, 2, 3], default=2)
    parser.add_argument('--projection', choices=['orthographic', 'perspective'], default='perspective')
    parser.add_argument('--azimuth', type=float, default=45)
    parser.add_argument('--elevation', type=float, default=25)
    parser.add_argument('--title', default='ARCHITECTURAL STUDY')
    parser.add_argument('--no-shadows', action='store_true')
    parser.add_argument('--finish', choices=['technical','graphite'], default='technical')
    parser.add_argument('--eye',nargs=3,type=float)
    parser.add_argument('--target',nargs=3,type=float)
    parser.add_argument('--fov',type=float,default=50)
    parser.add_argument('--near',type=float,default=.1)
    args = vars(parser.parse_args())
    args['shadows'] = not args.pop('no_shadows')
    print(json.dumps(generate(**args)))


if __name__ == '__main__':
    main()
