"""Circulation and human component adapters, metres, z up."""
import math
import numpy as np
def railing(m,a,b,height=1,spacing=.8):
    a=np.array(a,float);b=np.array(b,float);n=max(1,math.ceil(np.linalg.norm(b-a)/spacing))
    for t in np.linspace(0,1,n+1):
        p=a+(b-a)*t;m.sweep([p,p+[0,0,height]],.022,12)
    for z in [height*.5,height]:m.sweep([a+[0,0,z],b+[0,0,z]],.025,12)
def circulation(m,p):
    x,y,z=p.origin;w,d,h=p.size
    if p.kind=='stair':
        n=p.parameters['steps'];rise=h/n;tread=d/n;reverse=p.parameters.get('reverse',False)
        for i in range(n):m.box((x,y+(n-1-i if reverse else i)*tread,z+i*rise),(w,tread,rise))
        for xx in [x,x+w]:
            lowy,highy=(y+d,y) if reverse else (y,y+d)
            m.sweep([(xx,lowy,z+.05),(xx,highy,z+h-.05)],.045,12)
            railing(m,(xx,lowy,z+rise),(xx,highy,z+h))
        return True
    if p.kind=='railing':
        railing(m,p.parameters.get('start',[x,y,z]),p.parameters.get('end',[x+w,y,z]),h);return True
    if p.kind=='worker':
        if p.parameters.get('pose','standing')!='standing':
            from worker_pose import render
            render(m,p);return True
        def at(px,py,pz):return (x+w*px,y+d*py,z+h*pz)
        def oval(cx,cy,cz,rx,ry,rz):m.ellipsoid(at(cx,cy,cz),(w*rx,d*ry,h*rz))
        for a,b in [(.3,.38),(.7,.62)]:
            oval(a,.58,.035,.15,.28,.035)
            m.sweep([at(a,.5,.06),at(a,.48,.27),at(b,.5,.48)],w*.13,16)
        oval(.5,.5,.48,.28,.20,.09) # hips
        oval(.5,.5,.64,.34,.23,.16) # jacket and shoulders
        m.sweep([at(.5,.5,.76),at(.5,.5,.81)],w*.13,16)
        oval(.5,.5,.857,.22,.23,.068)
        oval(.5,.715,.85,.07,.07,.018) # nose, facing +Y
        if p.parameters.get('helmet',True):
            oval(.5,.5,.939,.29,.30,.061) # rounded helmet
            oval(.5,.52,.91,.36,.38,.012) # brim
        else:oval(.5,.5,.91,.22,.23,.09) # uncovered head reaches declared height
        for s in [-1,1]:
            m.sweep([at(.5+s*.28,.5,.73),at(.5+s*.4,.55,.60),at(.5+s*.34,.72,.53)],w*.10,12)
            oval(.5+s*.34,.72,.52,.10,.09,.027)
        # Jacket seam and pocket, on the visible front rather than floating.
        m.sweep([at(.5,.73,.58),at(.5,.73,.70)],w*.009,6)
        return True
    return False
