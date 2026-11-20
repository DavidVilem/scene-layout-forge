"""Real Windows child-shell discovery tests; no image quality claims."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == 'nt', 'Windows runtime discovery')
class RuntimeStartupTests(unittest.TestCase):
    def invoke(self, *args):
        shell = Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
        env = os.environ.copy()
        env['PATH'] = ''
        env.pop('INDUSTRIAL_LAYOUT_PYTHON', None)
        return subprocess.run([str(shell), '-NoProfile', '-File',
                               str(ROOT / 'scripts/resolve_python.ps1'), *args],
                              env=env, capture_output=True, text=True, timeout=60)

    def test_discover_without_path_and_run_coordinator(self):
        with tempfile.TemporaryDirectory(prefix='layout project with spaces ') as directory:
            result = self.invoke('-Project', directory)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            runtime = json.loads(result.stdout)
            self.assertTrue(runtime['ready'])
            env = os.environ.copy()
            env['PATH'] = ''
            child = subprocess.run([runtime['executable'], '-B',
                                    str(ROOT / 'scripts/delivery_pipeline.py'), '--help'],
                                   env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(child.returncode, 0, child.stderr)
            self.assertIn('attach-explorer', child.stdout)

    def test_explicit_working_interpreter(self):
        result = self.invoke('-Python', sys.executable)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(Path(json.loads(result.stdout)['executable']), Path(sys.executable))

    def test_broken_override_does_not_silently_fallback(self):
        result = self.invoke('-Python', str(ROOT / 'missing-python.exe'))
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)['ready'])


if __name__ == '__main__':
    unittest.main()
