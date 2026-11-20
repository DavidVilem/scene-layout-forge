import unittest
import numpy as np
from PIL import Image, ImageDraw
from test_animation_workflow import plan
import test_animation_workflow as fixtures
import animation_workflow as a
from temporal_motion import state


class TemporalTests(unittest.TestCase):
    setUp = fixtures.AnimationTests.setUp
    tearDown = fixtures.AnimationTests.tearDown
    job = fixtures.AnimationTests.job
    fake_render = fixtures.AnimationTests.fake_render
    obs = fixtures.AnimationTests.obs
    def test_cloud_advances_and_tree_oscillates(self):
        e=plan()['effects'][0]; e.update(kind='drift',dx=4)
        x=[state(e,t)['dx'] for t in (0,.25,.5,.75,1)]
        self.assertEqual(x,[0,1,2,3,4])
        e['kind']='breeze'
        self.assertGreater(state(e,.25)['dx'],0); self.assertLess(state(e,.75)['dx'],0)
        self.assertEqual(state(e,1)['dx'],0)
    def test_cloud_pixels_do_not_return(self):
        p=plan();p['effects'][0].update(kind='drift',dx=4)
        r=a.Renderer(self.job(p))
        self.assertFalse(np.array_equal(np.asarray(r.frame(0)),np.asarray(r.frame(1))))
        self.assertTrue(np.array_equal(np.asarray(r.frame(0))[~r.union],np.asarray(r.frame(1))[~r.union]))
    def test_forward_cannot_be_disguised_as_loop(self):
        p=plan();p['timeline']='loop';p['effects'][0]['kind']='drift'
        with self.assertRaises(ValueError):self.job(p)
    def test_rotor_direction(self):
        e={'kind':'sprite','motion':'rotate','cycles':1,'direction':-1}
        self.assertEqual([state(e,t)['angle'] for t in (0,.25,.5,.75)], [0,-90,-180,-270])
    def test_inventory_missing_effect(self):
        p=plan();p.update(schema_version=2,inventory=[dict(id='tree',category='foliage',decision='animate',evidence='crown visible',reason='wind')])
        with self.assertRaises(ValueError):self.job(p)
        p['effects'][0].update(target='tree',category='foliage');self.job(p)
    def test_once_accepts_different_endpoints(self):
        j=self.job();self.fake_render(j)
        report=a.read(j/'render.json');report.update(timeline='once',periodic_endpoint_equal=False)
        (j/'render.json').write_text(__import__('json').dumps(report))
        self.assertTrue(a.accept(j,self.obs()).exists())
    def test_loop_rejects_different_endpoints(self):
        j=self.job();self.fake_render(j)
        report=a.read(j/'render.json');report.update(timeline='loop',periodic_endpoint_equal=False)
        (j/'render.json').write_text(__import__('json').dumps(report))
        with self.assertRaises(ValueError):a.accept(j,self.obs())
    def travel_assets(self):
        sprite=Image.new('RGBA',(32,32));ImageDraw.Draw(sprite).rectangle((12,12,15,15),fill='red')
        clean=Image.new('RGB',(32,32),'white');removal=Image.new('L',(32,32));ImageDraw.Draw(removal).rectangle((12,12,15,15),fill=255)
        for name,im in [('sprite',sprite),('clean',clean),('removal',removal)]:im.save(self.root/(name+'.png'))
        p=plan();p['effects'][0].update(kind='sprite',motion='travel',category='vehicle',sprite=str(self.root/'sprite.png'),
            clean_plate=str(self.root/'clean.png'),removal_mask=str(self.root/'removal.png'),pivot=[14,14],
            path=[[0,0,0,1],[1,5,0,1]],path_review='Clear straight lane, fixed scale; source removed, no entry/exit',feather=0)
        return p
    def test_vehicle_travels_without_double(self):
        r=a.Renderer(self.job(self.travel_assets()))
        self.assertEqual(r.frame(1).getpixel((12,13)),(255,255,255))
        self.assertEqual(r.frame(1).getpixel((18,13)),(255,0,0))
    def test_path_validation(self):
        for path in ([[0,0,0,1],[0,2,0,1]],[[0,0,0,1],[1,2,0,-1]],[[0,0,0,1],[1,float('nan'),0,1]]):
            p=self.travel_assets();p['effects'][0]['path']=path
            with self.assertRaises(ValueError):self.job(p)
    def test_walking_requires_poses(self):
        p=self.travel_assets();p['effects'][0]['category']='person'
        with self.assertRaises(ValueError):self.job(p)
    def test_pose_sequence_changes_pixels_while_travelling(self):
        p=self.travel_assets();e=p['effects'][0];frames=[]
        for i,color in enumerate(('red','blue','green','yellow')):
            im=Image.new('RGBA',(32,32));ImageDraw.Draw(im).rectangle((12,12,15,15),fill=color)
            path=self.root/f'pose-{i}.png';im.save(path);frames.append(str(path))
        e.update(category='person',frames=frames,gait_review='Synthetic frames test selection only; no realistic gait claim')
        r=a.Renderer(self.job(p))
        self.assertEqual(r.frame(0).getpixel((13,13)),(255,0,0))
        self.assertEqual(r.frame(.5).getpixel((16,13)),(0,128,0))
    def test_foreground_occludes_traveller(self):
        p=self.travel_assets();occ=Image.new('L',(32,32));ImageDraw.Draw(occ).rectangle((16,0,31,31),fill=255)
        path=self.root/'occluder.png';occ.save(path);p['effects'][0]['occluder_mask']=str(path)
        r=a.Renderer(self.job(p));self.assertEqual(r.frame(1).getpixel((18,13)),r.base.getpixel((18,13)))


if __name__=='__main__':unittest.main()
