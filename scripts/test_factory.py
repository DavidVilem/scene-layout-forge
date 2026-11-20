import unittest,numpy as np
from factory import factory
from scene_model import validate
from render_scene import build,Renderer

class FactoryTests(unittest.TestCase):
    def test_enclosed_hall_keeps_network_and_supports_roof(self):
        for bays in [1,3]:
            scene=factory(bays,enclosed=True)
            self.assertEqual(validate(scene),[])
            self.assertEqual(scene['connections'],factory(bays)['connections'])
            roof=next(p for p in scene['parts'] if p['id']=='bay-0-roof')
            roof['origin'][2]+=.2
            self.assertTrue(any('bearing height mismatch' in e for e in validate(scene)))
    def test_scale_and_cross_bay_connections(self):
        for bays in [1,3,12]:
            scene=factory(bays);self.assertEqual(validate(scene),[])
            self.assertEqual(len(scene['connections']),4*bays+bays-1)
            self.assertEqual(len({p['id'] for p in scene['parts']}),len(scene['parts']))
    def test_broken_landing(self):
        scene=factory(2);next(p for p in scene['parts'] if p['id']=='bay-1-deck')['origin'][1]-=.1
        self.assertTrue(any('landing edge mismatch' in e for e in validate(scene)))
    def test_floating_beam(self):
        scene=factory(2);next(p for p in scene['parts'] if p['id']=='bay-0-hall-beam')['origin'][2]+=.1
        self.assertTrue(any('bearing height mismatch' in e for e in validate(scene)))
    def test_tray_pipe_collision_detected(self):
        scene=factory(2);next(p for p in scene['parts'] if p['id']=='bay-0-tray')['origin'][2]=4.0
        self.assertTrue(any('Route clearance' in e for e in validate(scene)))
    def test_post_pipe_collision_detected(self):
        scene=factory(2)
        post=next(p for p in scene['parts'] if p['id']=='bay-0-tray-support-1')
        post['origin'][:2]=[4.7,3.45]
        self.assertTrue(any('Route clearance' in e and 'tray-support-1' in e for e in validate(scene)))
    def test_three_bay_render(self):
        mesh=build(factory(3));im=Renderer(mesh,900,600).draw(mesh)
        self.assertEqual(im.size,(900,600))
    def test_pump_inlets_are_on_top_of_actual_casing(self):
        scene=factory(3)
        for pump in (p for p in scene['parts'] if p['kind']=='pump'):
            mesh=build({'units':'m','parts':[pump]})
            point=np.array(pump['origin'])+pump['ports']['in'];hits=[]
            for face,_ in mesh.faces:
                for i in range(1,len(face)-1):
                    a,b,c=np.array(face)[[0,i,i+1]];u=b-a;v=c-a;q=point-a
                    normal=np.cross(u,v);norm=np.linalg.norm(normal)
                    if norm<1e-12 or abs(q@normal)/norm>1e-7:continue
                    gram=np.array([[u@u,u@v],[u@v,v@v]])
                    weights=np.linalg.solve(gram,np.array([q@u,q@v]))
                    if min(weights)>=-1e-7 and sum(weights)<=1+1e-7:hits.append(abs(normal[2])/norm)
            self.assertTrue(hits,'Port does not touch the rendered pump surface')
            self.assertGreater(max(hits),.9,'Port is not on an upward-facing surface')

if __name__=='__main__':unittest.main()
