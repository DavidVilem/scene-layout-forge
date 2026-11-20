"""Original procedural components. Coordinates in metres; no reference assets."""
import math
import numpy as np

def wedge(m,origin,size,reverse=False):
    x,y,z=origin;w,d,h=size
    p=np.array([[x,y,z],[x+w,y,z],[x,y+d,z],[x+w,y+d,z],
                [x,y+d,z+h],[x+w,y+d,z+h]],float)
    if reverse:p[:,1]=2*y+d-p[:,1]
    for ids in [(0,2,3,1),(0,1,5,4),(2,4,5,3),(0,4,2),(1,3,5)]:
        m.faces.append(([p[i] for i in ids],0))
    for a,b in [(0,1),(0,2),(1,3),(2,3),(2,4),(3,5),(4,5),(0,4),(1,5)]:m.edges.append((p[a],p[b]))

def architecture(m,p):
    x,y,z=p.origin;w,d,h=p.size
    if p.kind=='column' and p.parameters.get('profile')=='steel':
        t=min(h*.04,min(w,d)*.12)
        m.box((x,y,z),(w,d,t))
        m.box((x+w*.2,y+d*.2,z+t),(w*.6,d*.6,h-t))
        r=min(w,d)*.04
        for fx in [.1,.9]:
            for fy in [.1,.9]:m.sweep([(x+w*fx,y+d*fy,z+t),(x+w*fx,y+d*fy,z+t*1.6)],r,6)
        return True
    if p.kind=='wall' and 'panel_size' in p.parameters:
        pw,ph=p.parameters['panel_size']
        if not all(isinstance(v,(int,float)) and math.isfinite(v) and v>0 for v in [pw,ph]):raise ValueError('Positive panel_size required')
        if math.ceil(w/pw)+math.ceil(h/ph)>1000:raise ValueError('Panel grid exceeds 1000 lines')
        m.box(p.origin,p.size)
        for xx in np.arange(x+pw,x+w-1e-8,pw):m.edges.append((np.array([xx,y+d,z]),np.array([xx,y+d,z+h])))
        for zz in np.arange(z+ph,z+h-1e-8,ph):m.edges.append((np.array([x,y+d,zz]),np.array([x+w,y+d,zz])))
        if p.parameters.get('panel_faces')=='all':
            for xx in np.arange(x+pw,x+w-1e-8,pw):m.edges.append((np.array([xx,y,z]),np.array([xx,y,z+h])))
            for yy in np.arange(y+pw,y+d-1e-8,pw):
                for xx in (x,x+w):m.edges.append((np.array([xx,yy,z]),np.array([xx,yy,z+h])))
            for zz in np.arange(z+ph,z+h-1e-8,ph):
                m.edges.append((np.array([x,y,zz]),np.array([x+w,y,zz])))
                for xx in (x,x+w):m.edges.append((np.array([xx,y,zz]),np.array([xx,y+d,zz])))
        return True
    if p.kind=='landing' and p.parameters.get('surface')=='grating':
        spacing=p.parameters.get('grid_spacing',.12)
        if not isinstance(spacing,(int,float)) or not math.isfinite(spacing) or spacing<=0:raise ValueError('Positive grid_spacing required')
        if math.ceil(w/spacing)+math.ceil(d/spacing)>2000:raise ValueError('Grating grid exceeds 2000 lines')
        m.box(p.origin,p.size)
        # A surface pattern on a supported slab, not a perforated structural mesh.
        for xx in np.arange(x+spacing,x+w-1e-8,spacing):m.edges.append((np.array([xx,y,z+h]),np.array([xx,y+d,z+h])))
        for yy in np.arange(y+spacing,y+d-1e-8,spacing):m.edges.append((np.array([x,yy,z+h]),np.array([x+w,yy,z+h])))
        return True
    if p.kind in {'window','door','cabinet'}:
        t=min(w,h)*.06
        # Facade lies in XZ, with visible front at +Y.
        for xx in [x,x+w-t]:m.box((xx,y,z),(t,d,h))
        for zz in [z,z+h-t]:m.box((x+t,y,zz),(w-2*t,d,t))
        m.box((x+t,y,z+t),(w-2*t,d*.65,h-2*t),2 if p.kind=='window' else 0)
        if p.kind=='window':
            m.box((x+w*.5-t/2,y+d*.65,z+t),(t,d*.35,h-2*t))
            m.box((x+t,y+d*.65,z+h*.5-t/2),(w-2*t,d*.35,t))
        else:
            m.sweep([(x+w*.78,y+d*.8,z+h*.48),(x+w*.78,y+d*.8,z+h*.58)],t*.16,12)
            if p.kind=='cabinet':
                for i in range(5):m.box((x+w*.2,y+d*.65,z+h*(.15+i*.045)),(w*.6,d*.1,h*.012),2)
        return True
    if p.kind=='drain':
        t=min(w,d)*.08
        for xx in [x,x+w-t]:m.box((xx,y,z),(t,d,h))
        for yy in [y,y+d-t]:m.box((x+t,yy,z),(w-2*t,t,h))
        for yy in np.linspace(y+t,y+d-2*t,8):m.box((x+t,yy,z),(w-2*t,t*.5,h))
        return True
    if p.kind in {'ramp','corbel'}:
        if p.kind=='corbel' and p.parameters.get('top_flat',False):
            local=type(m)();wedge(local,(0,0,0),p.size,p.parameters.get('reverse',False))
            def place(v):return np.array([v[0]+x,v[1]+y,z+h-v[2]])
            m.faces.extend(([place(v) for v in reversed(face)],tone) for face,tone in local.faces)
            m.edges.extend((place(a),place(b)) for a,b in local.edges)
            return True
        wedge(m,p.origin,p.size,p.parameters.get('reverse',False));return True
    if p.kind=='brace':
        # A diagonal rod stays inside its declared bounding box.
        r=min(w,d,h)*.15
        m.sweep([(x+r,y+d/2,z+r),(x+w-r,y+d/2,z+h-r)],r,16);return True
    if p.kind=='bollard':
        r=min(w,d)/2;m.sweep([(x+w/2,y+d/2,z),(x+w/2,y+d/2,z+h)],r,32);return True
    if p.kind=='planter':
        t=min(w,d,h)*.1
        m.box((x,y,z),(w,d,t))
        for xx in [x,x+w-t]:m.box((xx,y,z+t),(t,d,h-t))
        for yy in [y,y+d-t]:m.box((x+t,yy,z+t),(w-2*t,t,h-t))
        m.box((x+t,y+t,z+h*.65),(w-2*t,d-2*t,t),2);return True
    if p.kind in {'cable_tray','duct'}:
        axis=p.parameters.get('orientation','y')
        if axis not in ('x','y','z'):raise ValueError('tray/duct orientation must be x, y or z')
        if axis!='y':
            from copy import copy
            order={'x':[1,0,2],'z':[0,2,1]}[axis]
            local=type(m)();q=copy(p);q.origin=np.zeros(3);q.size=np.array(p.size)[order]
            q.parameters=dict(p.parameters,orientation='y');architecture(local,q)
            def place(v):return np.array(v)[order]+p.origin
            m.faces.extend(([place(v) for v in face],tone) for face,tone in local.faces)
            m.edges.extend((place(a),place(b)) for a,b in local.edges)
            return True
        t=min(w,d,h)*.08
        # Long axis +Y, open ends. Tray has spaced crossbars; duct is hollow.
        for xx in [x,x+w-t]:m.box((xx,y,z),(t,d,h))
        if p.kind=='duct':
            for zz in [z,z+h-t]:m.box((x+t,y,zz),(w-2*t,d,t))
        else:
            n=max(2,math.ceil(d/.3))
            for yy in np.linspace(y,y+d-t,n):m.box((x+t,yy,z),(w-2*t,t,t))
        return True
    if p.kind=='flange':
        r=min(w,d,h)/3.2
        m.flange((x+w/2,y+d/2,z+h/2),p.parameters.get('axis',[0,1,0]),r);return True
    if p.kind=='valve':
        # +Y pipe axis, vertical stem, circular handwheel in XY plane.
        r=min(w,d,h)*.18;cx=x+w/2;cy=y+d/2
        m.sweep([(cx,y,z+h*.3),(cx,y+d,z+h*.3)],r,24)
        m.sweep([(cx,cy,z+h*.3),(cx,cy,z+h*.85)],r*.22,16)
        wheel=min(w,d)*.4
        pts=[(cx+wheel*math.cos(a),cy+wheel*math.sin(a),z+h*.85) for a in np.linspace(0,2*math.pi,33)]
        m.sweep(pts,r*.12,8,caps=False)
        for a in [0,math.pi/2,math.pi,3*math.pi/2]:
            m.sweep([(cx,cy,z+h*.85),(cx+wheel*math.cos(a),cy+wheel*math.sin(a),z+h*.85)],r*.1,8)
        return True
    return False
