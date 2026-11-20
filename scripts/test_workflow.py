import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image
from generate_design import generate
from connected_plant import fixture
from scene_model import make_part


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'scene.json'
        self.data = {'units': 'm', 'parts': [
            {'id': 'floor', 'kind': 'slab', 'origin': [0, 0, 0], 'size': [4, 4, .2]}]}
        self.save()

    def save(self):
        self.source.write_text(json.dumps(self.data), encoding='utf-8')

    def run_design(self):
        return generate(self.source, self.root / 'result', width=320, height=300,
                        supersample=1, shadows=False, title='')

    def test_success_preserves_history(self):
        original = self.source.read_bytes()
        report = self.run_design()
        self.assertEqual(report['visual_review'], 'pending')
        self.assertEqual(report['temporary_files'], 'retained')
        self.assertTrue((Path(report['history'])/'scene.json').is_file())
        self.assertEqual((Path(report['history'])/'selected/final.png').read_bytes(),Path(report['output']).read_bytes())
        self.assertEqual(report['component_visibility']['by_kind']['slab']['total'],1)
        self.assertGreater(report['component_visibility']['components'][0]['visible_pixels'],0)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ['history', 'result', 'scene.json'])
        self.assertEqual([p.name for p in (self.root / 'result').iterdir()], ['final.png'])
        with Image.open(report['output']) as image:
            image.load()
            self.assertEqual(image.size, (320, 300))
        self.assertEqual(self.source.read_bytes(), original)

    def test_invalid_scene_does_not_publish(self):
        self.data['parts'][0]['size'] = [-1, 4, .2]
        self.save()
        with self.assertRaises(ValueError):
            self.run_design()
        self.assertEqual([p.name for p in self.root.iterdir()], ['scene.json'])

    def test_closed_stair_entrance_is_rejected_before_publication(self):
        self.data=fixture()
        stair=next(p for p in self.data['parts'] if p['kind']=='stair')
        x,y,z=stair['origin'];width,run,height=stair['size']
        edge=y if stair['parameters'].get('reverse',False) else y+run
        self.data['parts'].append(make_part('blocked-opening','railing',[x,edge,z+height],[width,.05,1]))
        self.data.pop('expected_counts',None)
        self.save()
        original=self.source.read_bytes()
        with self.assertRaisesRegex(ValueError,'entrance blocked'):
            self.run_design()
        self.assertEqual(self.source.read_bytes(),original)
        self.assertEqual([p.name for p in self.root.iterdir()],['scene.json'])

    def test_render_failure_retains_evidence(self):
        sentinel = self.root / 'previous.png'
        sentinel.write_bytes(b'user-owned input')
        self.data['labels'] = [{'target': 'missing', 'text': 'TEST', 'position': [.1, .1]}]
        self.save()
        with self.assertRaises(RuntimeError):
            self.run_design()
        self.assertEqual(sentinel.read_bytes(), b'user-owned input')
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ['history', 'previous.png', 'scene.json'])

    def test_existing_output_is_preserved(self):
        output = self.root / 'result'
        output.mkdir()
        sentinel = output / 'final.png'
        sentinel.write_bytes(b'previous final')
        with self.assertRaises(FileExistsError):
            self.run_design()
        self.assertEqual(sentinel.read_bytes(), b'previous final')


if __name__ == '__main__':
    unittest.main()
