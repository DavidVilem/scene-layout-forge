import unittest
import numpy as np
from render_scene import build, Renderer
from scene_model import make_part


class RouteVisibilityTests(unittest.TestCase):
    def scene(self, hidden=False):
        scene={'units':'m','parts':[
            make_part('left','column',(0,0,0),(.2,.2,1),ports={'out':[.1,.1,.5]}),
            make_part('right','column',(3,0,0),(.2,.2,1),ports={'in':[.1,.1,.5]})],
            'connections':[{'from':'left:out','to':'right:in',
                            'route':[[.1,.1,.5],[3.1,.1,.5]],'radius':.07}]}
        if hidden:
            scene['parts'].append(make_part('occluder','wall',(-1,-1,-1),(6,3,3)))
        return scene

    def test_visible_and_enclosed_routes(self):
        for hidden in [False,True]:
            data=self.scene(hidden);mesh=build(data)
            renderer=Renderer(mesh,500,400,azimuth=90,elevation=25)
            renderer.draw(mesh)
            report=renderer.connection_visibility(mesh,data)[0]
            if hidden:
                self.assertEqual(report['visible_pixels'],0)
                self.assertEqual(report['endpoint_neighborhood_pixels'],[0,0])
            else:
                self.assertGreater(report['visible_pixels'],100)
                self.assertTrue(all(x>0 for x in report['endpoint_neighborhood_pixels']))

    def test_owner_metadata_does_not_change_image_or_depth(self):
        data=self.scene();mesh=build(data)
        a=Renderer(mesh,500,400);image=np.array(a.draw(mesh));depth=a.z.copy()
        mesh.face_owners={}
        b=Renderer(mesh,500,400)
        np.testing.assert_array_equal(image,np.array(b.draw(mesh)))
        np.testing.assert_array_equal(depth,b.z)

    def test_visible_route_can_have_a_hidden_endpoint(self):
        data=self.scene()
        data['parts'].append(make_part('cover','wall',(-.5,-.5,0),(1.2,1.2,1.2)))
        mesh=build(data);renderer=Renderer(mesh,500,400,azimuth=90,elevation=25)
        renderer.draw(mesh);report=renderer.connection_visibility(mesh,data)[0]
        self.assertGreater(report['visible_pixels'],100)
        self.assertEqual(report['endpoint_neighborhood_pixels'][0],0)
        self.assertGreater(report['endpoint_neighborhood_pixels'][1],0)

    def test_synthetic_name_cannot_steal_part_ownership(self):
        data=self.scene()
        data['parts'].append(make_part('connection[0]','column',(1,2,0),(.2,.2,1)))
        mesh=build(data)
        self.assertNotEqual(mesh.connection_names[0],'connection[0]')
        renderer=Renderer(mesh,500,400,projection='perspective')
        renderer.draw(mesh)
        self.assertGreater(renderer.connection_visibility(mesh,data)[0]['visible_pixels'],0)
        self.assertTrue(np.any(renderer.owner==renderer.part_ids['connection[0]']))


if __name__=='__main__':unittest.main()
