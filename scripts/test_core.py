import unittest, math
import design_core as c

class CoreTests(unittest.TestCase):
    def setUp(self):
        c.faces.clear();c.counts.clear();c.lines.clear();c.labels.clear()
    def test_stair_landing(self):
        for h,r,n in [(2.4,3,12),(3,4.2,18),(1.2,1.8,6)]:
            s=c.stair_steps(h,r,n)
            self.assertAlmostEqual(sum(x['rise'] for x in s),h)
            self.assertAlmostEqual(sum(x['tread'] for x in s),r)
            self.assertAlmostEqual(s[-1]['z']+s[-1]['rise'],h)
    def test_invalid_stairs(self):
        for args in [(0,3,12),(2,-1,12),(2,3,0),(2,3,1.5)]:
            with self.assertRaises(ValueError):c.stair_steps(*args)
    def test_parallel_projection(self):
        a,b=c.project((0,0,0)),c.project((1,0,0))
        d,e=c.project((3,4,2)),c.project((4,4,2))
        self.assertEqual((b[0]-a[0],b[1]-a[1]),(e[0]-d[0],e[1]-d[1]))
    def test_sample_counts_and_finite_geometry(self):
        c.scene()
        self.assertEqual(c.counts,dict(tanks=2,pump=1,stairs=1,platform=1,workers=2))
        self.assertTrue(all(math.isfinite(v) for _,ps,_ in c.faces for p in ps for v in p))
        self.assertEqual(len(c.labels),4)
    def test_tube_degenerate(self):
        with self.assertRaises(AssertionError):c.tube((0,0,0),(0,0,0))

if __name__=='__main__':unittest.main()
