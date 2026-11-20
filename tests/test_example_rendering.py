"""Exercise recipe-to-generate camera kwargs and a real relocated CLI render."""
import inspect
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from generate_design import generate
from run_example import load_example,names


class ExampleRenderingTests(unittest.TestCase):
    def test_every_effective_example_camera_matches_generation_api(self):
        for name in names():
            with self.subTest(example=name):
                scene,recipe=load_example(name)
                camera=scene.get('camera',recipe['camera']) if recipe.get('pipeline')=='physical-cutaway' else recipe['camera']
                # This is the actual API boundary in run_example.main, not the
                # separate Renderer signature used by direct guide inspection.
                inspect.signature(generate).bind('scene.json','new-output',**camera)

    def test_situated_workers_relocated_render_and_nonoverwrite(self):
        with tempfile.TemporaryDirectory(prefix='situated-example-render-') as temporary:
            base=Path(temporary).resolve();package=base/'portable skill';project=base/'different cwd'
            self.assertEqual(package.parent,base);self.assertEqual(project.parent,base)
            shutil.copytree(ROOT,package,ignore=shutil.ignore_patterns('__pycache__','.git'))
            project.mkdir();output=project/'new output'
            command=[sys.executable,'-B',str(package/'examples/situated-workers/build.py'),
                '--out-dir',str(output),'--width','420','--height','340','--supersample','1']
            result=subprocess.run(command,cwd=project,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads(result.stdout)
            self.assertEqual(report['scene_validation'],'passed')
            self.assertEqual(report['png_decode'],'passed')
            self.assertEqual(report['artistic_finish'],'not_run')
            final=output/'final.png';before=final.read_bytes()
            with Image.open(final) as image:
                image.load();self.assertEqual(image.format,'PNG');self.assertEqual(image.size,(420,340))
            refused=subprocess.run(command,cwd=project,capture_output=True,text=True)
            self.assertNotEqual(refused.returncode,0);self.assertEqual(final.read_bytes(),before)
            self.assertEqual(sorted(p.name for p in output.iterdir()),['final.png'])
            self.assertFalse(list(project.glob('.example-scene-*')))
            self.assertFalse(list(project.glob('.design-run-*')))
            self.assertFalse((package/'output').exists())


if __name__=='__main__':unittest.main()
