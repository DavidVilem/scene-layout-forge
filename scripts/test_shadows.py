import unittest,numpy as np
from render_scene import Mesh,Renderer

class ShadowTests(unittest.TestCase):
    def test_shadow_preserves_depth_and_ownership(self):
        m=Mesh();m.box((-3,-3,-.2),(6,6,.2));m.box((0,0,0),(1,1,2))
        a=Renderer(m,500,500,shadows=False);b=Renderer(m,500,500,shadows=True)
        plain=np.array(a.draw(m));shaded=np.array(b.draw(m))
        np.testing.assert_array_equal(a.z,b.z);np.testing.assert_array_equal(a.owner,b.owner)
        self.assertGreater(np.count_nonzero(plain!=shaded),100)
        self.assertTrue(np.all(shaded.astype(int)<=plain.astype(int)))
        np.testing.assert_array_equal(plain[~np.isfinite(a.z)],shaded[~np.isfinite(b.z)])
    def test_floor_shadow_lies_away_from_light(self):
        m=Mesh();m.box((-3,-3,-.2),(6,6,.2));m.box((0,0,0),(1,1,2))
        r=Renderer(m,600,600);r.draw(m);mask=r.shadow_mask(m)
        # Light from -X,+Y: a point beyond the box toward +X,-Y is shaded.
        for point,expected in [([1.2,-.3,0],True),([-1,2,0],False)]:
            x,y,_=r.project(point);self.assertEqual(bool(mask[int(y),int(x)]),expected)
    def test_no_caster_has_no_top_surface_shadow(self):
        m=Mesh();m.box((-3,-3,-.2),(6,6,.2));r=Renderer(m,500,500);r.draw(m)
        mask=r.shadow_mask(m)
        # Slab side faces can legitimately self-shadow; the unobstructed top cannot.
        for x in [-2,-1,0,1,2]:
            for y in [-2,-1,0,1,2]:
                px,py,_=r.project([x,y,0]);self.assertFalse(mask[int(py),int(px)])

if __name__=='__main__':unittest.main()
