import copy
import unittest

import numpy as np

from useful_camera import fit_camera,camera_options,renderer_options,subject_ids
from visual_contract import compile_visual_contract,subject_metrics
from scene_model import make_part
from render_scene import build,Renderer
from projection_review import review


class UsefulCameraTests(unittest.TestCase):
    def scene(self):
        return {'units':'m','parts':[make_part('occupied','wall',[8,0,0],[44,8,21])],
            'visual_plan':{'objective':'Read six occupied levels','primary':['occupied'],
                'subject_framing':{'ids':['occupied'],'purpose':'Legible occupied architecture',
                                  'min_width_fraction':.58,'min_height_fraction':.3,'min_owned_area_fraction':.04}},
            'materializer':{'family':'spine'}}

    def test_remote_context_does_not_change_subject_fit(self):
        scene=self.scene();camera=fit_camera(scene,['occupied'])
        scene['parts'].append(make_part('huge-mountain','wall',[-1000,500,0],[2000,100,100]))
        self.assertEqual(camera,fit_camera(scene,['occupied']))
        self.assertNotEqual(camera['target'],[0,0,0])

    def test_real_pinhole_fit_retains_full_occupied_bounds(self):
        scene=self.scene();mesh=build(scene)
        for camera in camera_options(scene).values():
            renderer=Renderer(mesh,600,500,hatching=False,**renderer_options(camera))
            renderer.draw(mesh);report=review(renderer,scene)
            self.assertTrue(report['components']['occupied']['fully_in_frame'])
            self.assertGreater(subject_metrics(report,['occupied'])['width_fraction'],.58)
            self.assertEqual(compile_visual_contract(scene,evidence=report)['errors'],[])

    def test_large_context_cannot_pass_tiny_architecture(self):
        scene=self.scene()
        report={'image_size':[900,750],'components':{
            'occupied':{'visible_pixels':12000,'fully_in_frame':True,'bbox':[330,320,570,440],
                        'width_fraction':.268,'height_fraction':.161,'area_fraction':12000/(900*750)},
            'mountain':{'visible_pixels':400000,'bbox':[0,0,899,749],'area_fraction':.8}}}
        errors=compile_visual_contract(scene,evidence=report)['errors']
        self.assertTrue(any('subject framing too small: width_fraction' in e for e in errors))
        self.assertTrue(any('subject framing too small: height_fraction' in e for e in errors))

    def test_unknown_subject_and_invalid_optics_rejected(self):
        scene=self.scene()
        for identifiers,kwargs in [([] ,{}),(['missing'],{}),(['occupied'],{'fill':1.2}),(['occupied'],{'fov':180})]:
            with self.assertRaises(ValueError):fit_camera(scene,identifiers,**kwargs)


class MaterializedFamilyFramingTests(unittest.TestCase):
    def test_three_actual_family_guides_use_occupied_bbox(self):
        from build_bunker import build_scene
        from assembly_model import compile_cutaway
        for family in ('hub','spine','branched'):
            with self.subTest(family=family):
                scene=build_scene(27,5,6,family)
                display=compile_cutaway(scene,hide_ids=scene['display_hidden'])
                mesh=build(display);renderer=Renderer(mesh,600,500,hatching=False,**renderer_options(scene['camera']))
                renderer.draw(mesh);report=review(renderer,scene)
                metrics=subject_metrics(report,subject_ids(scene))
                self.assertGreaterEqual(metrics['width_fraction'],.58)
                self.assertGreaterEqual(metrics['height_fraction'],.30)
                self.assertTrue(all(report['components'][key]['fully_in_frame'] for key in subject_ids(scene)))
                # Selection still needs detail/relations/annotations; size alone is insufficient.


if __name__=='__main__':unittest.main()
