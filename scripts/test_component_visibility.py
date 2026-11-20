import unittest
import numpy as np
from render_scene import build,Renderer
from scene_model import make_part


class ComponentVisibilityTests(unittest.TestCase):
    def scene(self):
        return {'units':'m','parts':[
            make_part('inside','cabinet',[-.2,1.4,-.2],[.4,.4,.4]),
            make_part('shell','wall',[-1,1,-1],[2,2,2]),
            make_part('outside','cabinet',[2.3,2,-.3],[.4,.4,.8]),
            make_part('behind','cabinet',[0,-4,0],[1,1,1])]}

    def test_hidden_and_visible_members_are_distinguished_without_mutation(self):
        data=self.scene();mesh=build(data)
        r=Renderer(mesh,500,400,projection='perspective',camera_eye=[0,0,0],camera_target=[0,2,0],fov=110)
        r.draw(mesh);depth=r.z.copy();owner=r.owner.copy();rgb=r.rgb.copy()
        report=r.component_visibility(data)
        items={p['id']:p['visible_pixels'] for p in report['components']}
        self.assertEqual(items['inside'],0);self.assertEqual(items['behind'],0)
        self.assertGreater(items['outside'],0);self.assertGreater(items['shell'],0)
        self.assertEqual(report['by_kind']['cabinet'],{'total':3,'with_visible_surface':1,'without_visible_surface':2})
        np.testing.assert_array_equal(depth,r.z);np.testing.assert_array_equal(owner,r.owner);np.testing.assert_array_equal(rgb,r.rgb)
        self.assertEqual(sum(items.values()),int(np.count_nonzero(r.owner)))

    def test_missing_ownership_is_not_reported_as_hidden(self):
        data=self.scene();mesh=build(data);r=Renderer(mesh,400,400)
        del r.part_ids['inside']
        with self.assertRaisesRegex(ValueError,'Missing component ownership'):r.component_visibility(data)


if __name__=='__main__':unittest.main()
