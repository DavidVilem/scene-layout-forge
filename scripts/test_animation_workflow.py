import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from PIL import Image
import animation_workflow as a


def plan():
    return {'seconds': 2, 'fps': 12, 'effects': [{'id': 'leaf', 'kind': 'breeze',
        'polygon': [[8,8],[23,8],[23,23],[8,23]], 'dx': 2, 'dy': 0, 'feather': 2,
        'reason': 'wind', 'anchor': 'fixed trunk', 'occlusion': 'no foreground overlap', 'limits': 'local motion only'}]}


class AnimationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.folder = self.root/'output'/'sample-01'; self.folder.mkdir(parents=True)
        arr = np.zeros((32,32,3), dtype='uint8'); arr[:,:,0] = np.arange(32)*7; arr[:,:,1] = 90
        Image.fromarray(arr).save(self.folder/'coloreada.png')
        Image.fromarray(arr).convert('L').save(self.folder/'ilustrada.png')
        self.source = self.folder/'coloreada.png'
    def tearDown(self): self.tmp.cleanup()
    def job(self, p=None): return a.prepare(self.root, self.source, p or plan(), 'Animate source')
    def test_periodic_and_protected_pixels(self):
        j = self.job(); r = a.Renderer(j); zero = np.asarray(r.frame(0)); quarter = np.asarray(r.frame(.25))
        self.assertTrue(np.array_equal(zero, np.asarray(r.frame(1))))
        self.assertTrue(np.array_equal(zero[~r.union], quarter[~r.union]))
        self.assertFalse(np.array_equal(zero, quarter))
    def test_pair_is_unchanged(self):
        before = {p.name:a.digest(p) for p in self.folder.iterdir()}; self.job()
        self.assertEqual(before, {p.name:a.digest(p) for p in self.folder.iterdir()})
    def test_source_tampering(self):
        j = self.job(); Image.new('RGB',(32,32)).save(self.source)
        with self.assertRaises(ValueError): a.Renderer(j)
    def test_plan_tampering(self):
        j = self.job(); (j/'plan.json').write_text('{}')
        with self.assertRaises(ValueError): a.Renderer(j)
    def test_mask_tampering(self):
        j = self.job(); Image.new('L',(32,32)).save(j/'mask-0.png')
        with self.assertRaises(ValueError): a.Renderer(j)
    def test_protected_overlap_retains_failure(self):
        p=plan(); protected=self.root/'protected.png'; Image.new('L',(32,32),255).save(protected); p['protected_mask']=str(protected)
        with self.assertRaises(ValueError): self.job(p)
        self.assertEqual(len(list((self.root/'output/history').glob('*/failure.json'))),1)
    def test_reject_bad_plans(self):
        for mutate in (lambda p:p.update(seconds=float('nan')), lambda p:p['effects'][0].update(cycles=.5),
                       lambda p:p['effects'][0].update(dx=99), lambda p:p['effects'][0].update(kind='walk'),
                       lambda p:p['effects'][0].update(kind='sprite'), lambda p:p.update(effects=[])):
            p=plan(); mutate(p)
            with self.assertRaises(ValueError): self.job(p)
    def test_empty_and_outside_masks(self):
        p=plan(); p['effects'][0]['polygon']=[[99,99],[99,100],[100,100]]
        with self.assertRaises(ValueError): self.job(p)
    def fake_render(self, j):
        (j/'candidate.mp4').write_bytes(b'fixture-not-real-video')
        a.write(j/'render.json', {'candidate_hash':a.digest(j/'candidate.mp4'), 'periodic_endpoint_equal':True})
    def obs(self): return {k:{'status':'passed','notes':'Synthetic control-flow fixture only'} for k in a.REVIEW_KEYS}
    def test_missing_review_and_changed_candidate(self):
        j=self.job(); self.fake_render(j)
        with self.assertRaises(ValueError): a.accept(j,{})
        (j/'candidate.mp4').write_bytes(b'changed')
        with self.assertRaises(ValueError): a.accept(j,self.obs())
    def test_failed_visual_review_preserved(self):
        j=self.job(); self.fake_render(j); obs=self.obs(); obs['motion']['status']='failed'
        with self.assertRaises(ValueError): a.accept(j,obs)
        self.assertTrue((j/'review-1.json').exists()); self.assertFalse((self.folder/'animada.mp4').exists())
    def test_no_overwrite(self):
        j=self.job(); self.fake_render(j); (self.folder/'animada.mp4').write_bytes(b'old')
        with self.assertRaises(FileExistsError): a.accept(j,self.obs())
        self.assertEqual((self.folder/'animada.mp4').read_bytes(),b'old')
    def test_light_and_plume_periodicity(self):
        for kind in ('light','plume'):
            p=plan();p['effects'][0].update(kind=kind, origin=[16,20], dy=-8, strength=.15)
            r=a.Renderer(self.job(p))
            self.assertTrue(np.array_equal(np.asarray(r.frame(0)),np.asarray(r.frame(1))))
            self.assertFalse(np.array_equal(np.asarray(r.frame(0)),np.asarray(r.frame(.23))))
    def test_sprite_removes_old_position(self):
        from PIL import ImageDraw
        base=Image.new('RGB',(32,32),'white');d=ImageDraw.Draw(base);d.rectangle((13,13,16,16),fill='red');base.save(self.source)
        sprite=Image.new('RGBA',(32,32));ImageDraw.Draw(sprite).rectangle((13,13,16,16),fill='red')
        clean=Image.new('RGB',(32,32),'white');removal=Image.new('L',(32,32));ImageDraw.Draw(removal).rectangle((13,13,16,16),fill=255)
        for name,im in [('sprite',sprite),('clean',clean),('removal',removal)]: im.save(self.root/(name+'.png'))
        p=plan();p['effects'][0].update(kind='sprite',sprite=str(self.root/'sprite.png'),clean_plate=str(self.root/'clean.png'),
            removal_mask=str(self.root/'removal.png'),pivot=[15,15],dx=5,feather=0)
        frame=a.Renderer(self.job(p)).frame(.25)
        self.assertEqual(frame.getpixel((13,14)),(255,255,255))
        self.assertEqual(frame.getpixel((19,14)),(255,0,0))


if __name__ == '__main__': unittest.main()
