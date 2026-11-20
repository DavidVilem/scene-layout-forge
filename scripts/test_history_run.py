import tempfile,unittest
from pathlib import Path
from history_run import new_run,preserved_directory,STAGES
class HistoryTests(unittest.TestCase):
    def test_runs_are_distinct_and_keep_prior_files(self):
        with tempfile.TemporaryDirectory() as d:
            a=new_run(d,'station');b=new_run(d,'station')
            self.assertNotEqual(a,b)
            for name in STAGES:self.assertTrue((a/name).is_dir())
            file=a/STAGES[0]/'brief.txt';file.write_text('original')
            new_run(d,'station')
            self.assertEqual(file.read_text(),'original')
    def test_exception_retains_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(RuntimeError):
                with preserved_directory(d,'attempt-') as folder:
                    file=Path(folder)/'failure.txt';file.write_text('failure evidence')
                    raise RuntimeError('failed')
            self.assertEqual(file.read_text(),'failure evidence')
    def test_bad_stem_cannot_escape(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):new_run(d,'../escape')

