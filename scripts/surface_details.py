"""Procedural line details mapped onto the existing cylindrical shell."""
import math
import numpy as np


def vessel_marks(mesh,part):
    x,y,z=part.origin;w,d,h=part.size
    r=min(w,d)/2;cx=x+w/2;cy=y+d/2
    def point(angle,height):
        return np.array([cx+r*math.cos(angle),cy+r*math.sin(angle),z+height])
    def stroke(uv):
        pts=[point(a,b) for a,b in uv]
        if not hasattr(mesh,'detail_edge_indices'):mesh.detail_edge_indices=set()
        mesh.detail_edge_indices.update(range(len(mesh.edges),len(mesh.edges)+len(pts)-1))
        mesh.edges.extend(zip(pts[:-1],pts[1:]))
    def bolt(angle,height):
        radius=min(r,h)*.015
        stroke([(angle+radius/r*math.cos(t),height+radius*math.sin(t))
                for t in np.linspace(0,2*math.pi,13)])
    count=part.parameters.get('seam_bolts',0)
    if type(count)!=int or not 0<=count<=64:
        raise ValueError('seam_bolts must be integer 0..64')
    for i in range(count):
        angle=2*math.pi*i/count
        for height in [h*.12,h*.94]:bolt(angle,height)
    hatch=part.parameters.get('inspection_hatch',False)
    if type(hatch)!=bool:raise ValueError('inspection_hatch must be boolean')
    if hatch:
        mid=math.pi/2;left=mid-.28;right=mid+.28
        for height in [h*.515,h*.685]:
            stroke([(a,height) for a in np.linspace(left,right,17)])
        for angle in [left,right]:stroke([(angle,h*.515),(angle,h*.685)])
        for angle in [mid-.34,mid+.34]:
            for height in [h*.50,h*.60,h*.70]:bolt(angle,height)
        for height in [h*.50,h*.70]:bolt(mid,height)
