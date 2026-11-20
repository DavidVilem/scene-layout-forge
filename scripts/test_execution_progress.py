import tempfile
import unittest
from pathlib import Path
from execution_progress import inspect


class ProgressTests(unittest.TestCase):
    def test_initialized_run_is_not_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'run.json').write_text('{}')
            (root/'01-site').mkdir()
            (root/'01-site'/'brief.txt').write_text('Create a museum')
            self.assertEqual(inspect([root])['state'], 'initialized_only')

    def test_only_explicitly_linked_histories_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current = root/'current'; current.mkdir()
            unrelated = root/'old'; unrelated.mkdir()
            (unrelated/'candidate.html').write_text('old')
            self.assertEqual(inspect([current])['state'], 'initialized_only')
            self.assertEqual(len(inspect([current, unrelated])['evidence']['candidates']), 1)

    def test_failure_and_candidate_are_not_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'failure.json').write_text('{}')
            (root/'candidate.html').write_text('draft')
            report = inspect([root])
            self.assertEqual(report['state'], 'artifacts_present')
            self.assertEqual(len(report['evidence']['failures']), 1)
            self.assertNotIn('complete', report)

    def test_missing_history_is_not_an_empty_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                inspect([Path(tmp)/'missing'])
