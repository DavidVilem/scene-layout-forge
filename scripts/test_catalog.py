import unittest
import numpy as np
from scene_model import LIBRARIES,make_part
from render_scene import build,Renderer

def catalog():
    parts=[]
    for i,kind in enumerate(k for group in LIBRARIES.values() for k in group):
        origin=[(i%6)*3,(i//6)*3,0];params={}
        if kind=='stair':params={'steps':8}
        if kind in {'pipe','conduit'}:params={'points':[origin,[origin[0]+1,origin[1]+1,1]],'radius':.1}
        parts.append(make_part(kind,kind,origin,[1.5,1.8,1.5],parameters=params))
    return {'units':'m','parts':parts,'connections':[]}

class CatalogTests(unittest.TestCase):
    def test_every_declared_kind_builds_finite_geometry(self):
        for part in catalog()['parts']:
            with self.subTest(kind=part['kind']):
                mesh=build({'units':'m','parts':[part]})
                vertices=np.array([v for f,_ in mesh.faces for v in f])
                self.assertGreater(len(vertices),0)
                self.assertTrue(np.isfinite(vertices).all())
                # Every polygon has a usable plane, not a collapsed triangle.
                for f,_ in mesh.faces:self.assertGreater(np.linalg.norm(np.cross(f[1]-f[0],f[2]-f[0])),1e-10)
    def test_catalog_render(self):
        mesh=build(catalog());r=Renderer(mesh,1000,800);im=r.draw(mesh)
        self.assertEqual(im.size,(1000,800))
        self.assertGreater(np.isfinite(r.z).sum(),20000)

if __name__=='__main__':unittest.main()
