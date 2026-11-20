import unittest
import numpy as np
from render_scene import Mesh,Renderer

class ContourTests(unittest.TestCase):
    def test_tangent_contours_survive_subpixel_positions(self):
        for shift in [0,.013,.041,.079]:
            m=Mesh();m.box((-2,-2,-.2),(4,4,.2));m.sweep([[shift,0,0],[shift,0,3]],.5,64)
            r=Renderer(m,520,520);pixels=np.array(r.draw(m))
            contour=[(a,b) for a,b,n1,n2 in m.smooth_edges if (n1@r.basis[2])*(n2@r.basis[2])<=0]
            self.assertEqual(len(contour),2)
            for a,b in contour:
                hits=[]
                for t in np.linspace(.1,.9,100):
                    px,py,_=r.project(a*(1-t)+b*t);x,y=int(px),int(py)
                    hits.append(pixels[y-1:y+2,x-1:x+2,0].min()<130)
                self.assertGreater(np.mean(hits),.98,msg=f'Broken contour at offset {shift}')
    def test_fully_hidden_contours_stay_hidden(self):
        m=Mesh();m.box((-2,-2,-1),(4,4,5));a=np.array(Renderer(m,400,500).draw(m))
        m.sweep([[0,0,0],[0,0,3]],.5,64)
        b=np.array(Renderer(m,400,500).draw(m))
        np.testing.assert_array_equal(a,b)
    def test_foreground_crossing_hides_middle_of_contour(self):
        m=Mesh();m.sweep([[0,0,0],[0,0,3]],.5,64);m.box((-1,-1,1.1),(3,3,.8))
        r=Renderer(m,520,520);pixels=np.array(r.draw(m))
        contours=[(a,b) for a,b,n1,n2 in m.smooth_edges if (n1@r.basis[2])*(n2@r.basis[2])<=0]
        for a,b in contours:
            for t in [.46,.5,.54]:
                px,py,_=r.project(a*(1-t)+b*t);x,y=int(px),int(py)
                self.assertGreater(pixels[y-1:y+2,x-1:x+2,0].min(),130)

if __name__=='__main__':unittest.main()
