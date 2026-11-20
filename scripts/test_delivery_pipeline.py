"""Synthetic orchestration tests, not artistic image or browser evaluations."""
import unittest
from pathlib import Path
from PIL import Image
import delivery_pipeline as flow
import color_workflow as color
import illustration_workflow as illustration
import explorer_workflow as explorer
import test_color_workflow as color_tests
import test_explorer_workflow as explorer_tests


class DeliveryPipelineTests(unittest.TestCase):
    def test_repair_queue_survives_candidate_replacement(self):
        import explorer_repair_cycle
        p = flow.start(self.case.attempt, requested_3d=True)
        self.colored(p)
        scene, config = explorer_tests.fixture()
        old = explorer.prepare(self.case.root, scene, config, 'Synthetic queue', pair=self.case.illustrated.parent)
        explorer.render(old)
        flow.attach_explorer(p, old)
        issue = dict(id='roof-axis', components=['roof'], observed='Synthetic axis mismatch',
                     target='Source axis', action='Change roof mesh', verification='Matched view',
                     priority='critical', status='open', progress='new')
        explorer_repair_cycle.record(old, [issue], 'Initial mesh', [old/'candidate.html'])
        self.assertEqual(flow.advance(p)['repair_step']['action'], 'revise_geometry')
        new = explorer.prepare(self.case.root, scene, config, 'Synthetic replacement', pair=self.case.illustrated.parent)
        explorer.render(new)
        flow.attach_explorer(p, new)
        self.assertEqual(flow.advance(p)['repair_step']['previous_job'], str(old))
        with self.assertRaises(ValueError): explorer_repair_cycle.validate_acceptance(new)
        with self.assertRaises(ValueError): explorer_repair_cycle.record(new, [], 'Cannot drop defect', [new/'candidate.html'])

    def setUp(self):
        self.case = color_tests.ColorTests(); self.case.setUp()
    def tearDown(self):
        self.case.tearDown()
    def colored(self, pipeline):
        pending = flow.advance(pipeline)
        job = Path(pending['job'])
        review = self.case.reviewed(job)
        self.assertEqual(flow.advance(pipeline)['action'], 'review_color')
        accepted = color.accept(job, review)
        self.assertEqual(accepted['next_action'], flow.advance(pipeline))
    def test_accepted_illustration_prepares_real_color_request_and_resumes(self):
        p = flow.start(self.case.attempt, requested_3d=True)
        first = flow.advance(p)
        self.assertEqual(first['action'], 'edit_color')
        self.assertFalse(first['complete'])
        self.assertTrue(Path(first['request']).is_file())
        self.assertEqual(flow.advance(p), first)
        self.assertEqual(len(list(self.case.attempt.glob('color-*'))), 1)
    def test_pair_completes_only_when_3d_not_requested(self):
        p = flow.start(self.case.attempt)
        self.colored(p)
        result = flow.advance(p)
        self.assertTrue(result['complete'])
        self.assertEqual(set(result['outputs']), {'ilustrada','coloreada'})
        with self.assertRaises(ValueError):flow.attach_explorer(p, self.case.root)
    def test_complete_chain_requires_accepted_html_not_candidate(self):
        p = flow.start(self.case.attempt, requested_3d=True)
        self.colored(p)
        self.assertEqual(flow.advance(p)['action'], 'build_3d')
        scene, config = explorer_tests.fixture()
        j = explorer.prepare(self.case.root, scene, config, 'Synthetic integration', pair=self.case.illustrated.parent)
        explorer.render(j)
        flow.attach_explorer(p, j)
        self.assertEqual(flow.advance(p)['action'], 'review_or_repair_3d')
        # Existing acceptance validators are exercised with explicitly synthetic
        # evidence. This tests plumbing, not real fidelity or browser behavior.
        checks = explorer_tests.ExplorerTests()
        explorer.accept(j, checks.review(), checks.browser(j), **checks.fidelity(j))
        result = flow.advance(p)
        self.assertTrue(result['complete'])
        self.assertEqual(set(result['outputs']), {'ilustrada','coloreada','explorador'})
        Path(result['outputs']['explorador']).write_text('modified')
        with self.assertRaises(ValueError):flow.advance(p)
    def test_raw_generation_is_not_accepted_illustration(self):
        from test_illustration_workflow import plan
        a = illustration.prepare(self.case.root,'fresh','Fresh scene',plan())
        p = flow.start(a, requested_3d=True)
        self.assertEqual(flow.advance(p)['action'], 'generate_illustration')
        src = self.case.root/'fresh.png';Image.new('RGB',(24,16),'green').save(src)
        original = illustration.retain(a,src,illustration.read(a/'request.json'))
        self.assertEqual(flow.advance(p)['action'], 'review_illustration')
        notes = {k:{'status':'visible_correct','notes':'Synthetic integration fixture'}
                 for k in (*illustration.BASE_REVIEW,'wall_mount')}
        review = illustration.review(a,original,notes)
        accepted = illustration.accept(a,original,review,self.case.root/'output/fresh-01/ilustrada.png')
        self.assertEqual(accepted['next_action']['action'], 'edit_color')
        self.assertTrue(Path(accepted['next_action']['request']).is_file())
        self.assertTrue(list(a.glob('pipeline-step-*.json')))
    def test_unchanged_scope_and_source_integrity(self):
        p = flow.start(self.case.attempt, requested_3d=True)
        with self.assertRaises(ValueError):flow.start(self.case.attempt)
        Image.new('RGB',(24,16),'black').save(self.case.illustrated)
        with self.assertRaises(ValueError):flow.advance(p)
    def test_grayscale_only_is_an_explicit_choice(self):
        p = flow.start(self.case.attempt,color=False)
        self.assertEqual(set(flow.advance(p)['outputs']), {'ilustrada'})
    def test_color_correction_resumes_latest_job_without_accepting_original(self):
        p = flow.start(self.case.attempt)
        first = flow.advance(p)
        job = Path(first['job'])
        self.case.reviewed(job)
        corrected = color.prepare(self.case.attempt,self.case.illustrated,
                                  previous=job,correction='Synthetic correction')
        pending = flow.advance(p)
        self.assertEqual(pending['job'], str(corrected))
        self.assertEqual(pending['action'], 'edit_color')
        self.assertFalse(pending['complete'])
    def test_foreign_explorer_rejected_and_repaired_candidate_can_attach(self):
        p = flow.start(self.case.attempt,requested_3d=True)
        self.colored(p)
        scene, config = explorer_tests.fixture()
        foreign = self.case.root/'foreign'; foreign.mkdir()
        for name in ('ilustrada.png','coloreada.png'):
            Image.new('RGB',(24,16),'red').save(foreign/name)
        wrong = explorer.prepare(self.case.root,scene,config,'Foreign',pair=foreign)
        with self.assertRaises(ValueError):flow.attach_explorer(p,wrong)
        for i in range(2):
            job = explorer.prepare(self.case.root,scene,config,'Synthetic repair',pair=self.case.illustrated.parent)
            explorer.render(job)
            flow.attach_explorer(p,job)
        self.assertEqual(flow.advance(p)['job'],str(job))
        self.assertFalse(flow.advance(p)['complete'])
