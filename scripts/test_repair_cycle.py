"""State-machine regressions, not artistic fidelity evaluations."""
import json
import tempfile
import unittest
from pathlib import Path
import explorer_repair_cycle as cycle


class RepairCycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def job(self, n):
        job = self.root/str(n)
        job.mkdir()
        (job/'candidate.html').write_text('synthetic geometry '+str(n))
        (job/'source.json').write_text(json.dumps({'images': {'coloreada.png': {'sha256': 'same source'}}}))
        (job/'comparison.txt').write_text('synthetic comparison '+str(n))
        return job

    def issue(self, progress='new', status='open'):
        return dict(id='roof', components=['roof-main'], observed='axis differs', target='match visible roof axis',
                    action='rebuild roof mesh', verification='source matched camera', priority='critical',
                    progress=progress, status=status, neighbor_checks='eaves meet columns')

    def record(self, job, issues, previous=None):
        return cycle.record(job, issues, 'fit camera then rebuild roof profile', [job/'comparison.txt'], previous)

    def test_first_defect_schedules_geometry_not_stop(self):
        j = self.job(0)
        self.assertEqual(cycle.next_step(j)['action'], 'capture_and_review')
        self.assertEqual(self.record(j, [self.issue()])['action'], 'revise_geometry')
        with self.assertRaises(ValueError): cycle.validate_acceptance(j)

    def test_stagnation_changes_strategy_not_acceptance(self):
        previous = self.job(0)
        self.record(previous, [self.issue()])
        for n in (1, 2):
            current = self.job(n)
            result = self.record(current, [self.issue('unchanged')], previous)
            previous = current
        self.assertEqual(result['action'], 'change_modeling_approach')
        with self.assertRaises(ValueError): cycle.validate_acceptance(current)

    def test_cannot_drop_issue_or_resolve_same_candidate(self):
        j = self.job(0)
        self.record(j, [self.issue()])
        with self.assertRaises(ValueError): self.record(j, [])
        with self.assertRaises(ValueError): self.record(j, [self.issue('resolved', 'resolved')])

    def test_resolved_revision_still_requires_existing_acceptance_gates(self):
        a, b = self.job(0), self.job(1)
        self.record(a, [self.issue()])
        result = self.record(b, [self.issue('resolved', 'resolved')], a)
        self.assertEqual(result['action'], 'validate_and_accept')
        self.assertFalse((b/'delivered.json').exists())
        cycle.validate_acceptance(b)

    def test_changed_evidence_rejected(self):
        j = self.job(0)
        self.record(j, [self.issue()])
        (j/'comparison.txt').write_text('replacement')
        with self.assertRaises(ValueError): cycle.next_step(j)

    def test_inherited_queue_cannot_be_skipped(self):
        a, b = self.job(0), self.job(1)
        self.record(a, [self.issue()])
        (b/'repair-parent.json').write_text(json.dumps({'job': str(a)}))
        with self.assertRaises(ValueError): cycle.validate_acceptance(b)
        with self.assertRaises(ValueError): self.record(b, [])
        self.record(b, [self.issue('unchanged')])
        with self.assertRaises(ValueError): self.record(b, [self.issue('resolved', 'resolved')])


if __name__ == '__main__':
    unittest.main()
