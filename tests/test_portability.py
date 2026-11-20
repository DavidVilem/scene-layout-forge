import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_package import audit
from check_examples import check

def hashes(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}

class PortableSkillTests(unittest.TestCase):
    def test_bundled_examples_and_invalid_controls(self):
        results=check()
        self.assertEqual(len(results),13)
        for name in ('bunker-spine','bunker-branched'):
            self.assertEqual(next(r for r in results if r['example']==name)['coverage']['validation_policy'],'strict')
        self.assertEqual(next(r for r in results if r['example']=='typed-water-hall')['coverage']['mode'],'typed-v2')

    def test_relocation_external_cwd_and_nonoverwrite(self):
        with tempfile.TemporaryDirectory(prefix='layout-portability-') as temporary:
            base=Path(temporary).resolve();package=base/'installed skill';project=base/'unrelated project'
            shutil.copytree(ROOT,package,ignore=shutil.ignore_patterns('__pycache__','.git'))
            project.mkdir();before=hashes(package)
            def run(*args):
                return subprocess.run([sys.executable,'-B',str(package/'scripts/run_example.py'),*args],cwd=project,capture_output=True,text=True)
            for name in ['twin-vessels','process-hall','service-building','space-station','machine-interior','technical-plan','supported-drive','typed-water-hall','dry-dock','connected-mountain-bunker','bunker-spine','bunker-branched','situated-workers']:
                result=run(name,'--validate-only');self.assertEqual(result.returncode,0,result.stderr)
            output=project/'output'/'trial'
            result=run('twin-vessels','--out-dir',str(output),'--width','420','--height','340','--supersample','1')
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads(result.stdout);self.assertEqual(report['artistic_finish'],'not_run')
            self.assertEqual(report['png_decode'],'passed')
            final=output/'final.png';original=final.read_bytes()
            refused=run('twin-vessels','--out-dir',str(output))
            self.assertNotEqual(refused.returncode,0);self.assertEqual(original,final.read_bytes())
            refused=run('twin-vessels','--out-dir',str(package/'output'))
            self.assertNotEqual(refused.returncode,0)
            self.assertEqual(before,hashes(package))
            self.assertEqual(sorted(p.name for p in output.iterdir()),['final.png'])
            self.assertFalse(list(output.parent.glob('.example-scene-*')))
            self.assertEqual(audit(package),[])

    def test_package_hygiene_detects_private_artifact_and_broken_link(self):
        with tempfile.TemporaryDirectory(prefix='layout-audit-') as temporary:
            base=Path(temporary);shutil.copytree(ROOT,base/'package',ignore=shutil.ignore_patterns('__pycache__','.git'))
            package=base/'package';self.assertEqual(audit(package),[])
            (package/'reference.png').write_bytes(b'not really an image')
            private_path='/'.join([chr(67)+':','Users','example','private.png'])
            (package/'private.md').write_text('Personal input: '+private_path+'\n[missing](absent.md)',encoding='utf-8')
            found=audit(package)
            self.assertTrue(any('artifact' in x for x in found))
            self.assertTrue(any('Personal absolute' in x for x in found))
            self.assertTrue(any('Broken link' in x for x in found))

if __name__=='__main__':unittest.main()
