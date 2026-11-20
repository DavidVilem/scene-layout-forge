"""Asset-free technical adapters. Local long axis is Y; oriented parts stay in their AABB."""
import math
import numpy as np

KINDS={'shell','ring_frame','bulkhead','truss','panel_array','console','seat',
       'gear','rotor','heat_exchanger','luminaire','instrument_panel'}

def parameter_errors(kind,params):
    errors=[]
    if kind in {'cable_tray','duct'}:
        return [] if params.get('orientation','y') in ('x','y','z') else ['orientation must be x, y or z']
    if kind not in KINDS:return errors
    if params.get('orientation','y') not in ('x','y','z'):errors.append('orientation must be x, y or z')
    for key,default,low,high in [('segments',48,12,128),('bays',4,1,40),('rows',6,1,100),('columns',12,1,100),('teeth',16,6,80),('blades',6,2,20)]:
        value=params.get(key,default)
        if type(value)!=int or not low<=value<=high:errors.append(f'{key}: integer {low}..{high} required')
    for key,default,low,high in [('inner_ratio',.78,.1,.95),('arc_degrees',360,30,360)]:
        value=params.get(key,default)
        if type(value) not in (int,float) or not math.isfinite(value) or not low<=value<=high:errors.append(f'{key}: finite number {low}..{high} required')
    if 'capped' in params and type(params['capped'])!=bool:errors.append('capped must be boolean')
    return errors

def technical(m,p):
    if p.kind not in KINDS:return False
    errors=parameter_errors(p.kind,p.parameters)
    if errors:raise ValueError(p.id+': '+'; '.join(errors))
    local=type(m)();params=p.parameters
    order={'y':[0,1,2],'x':[1,0,2],'z':[0,2,1]}[params.get('orientation','y')]
    w,d,h=np.array(p.size)[order];n=params.get('segments',48)
    def rod(a,b,r):local.sweep([a,b],r,12)
    def quad(a,b,c,e,tone=0):local.faces.append(([np.array(v,float) for v in [a,b,c,e]],tone))
    def ellipse(y,ratio=1,arc=360):
        start=math.pi/2-math.radians(arc)/2
        return [np.array([w/2+w/2*ratio*math.cos(t),y,h/2+h/2*ratio*math.sin(t)]) for t in np.linspace(start,start+math.radians(arc),n+1)]
    def ring(inner,outer_a,outer_b):
        ia=ellipse(0,inner);ib=ellipse(d,inner)
        for i in range(n):
            quad(outer_a[i],outer_a[i+1],outer_b[i+1],outer_b[i])
            quad(ia[i+1],ia[i],ib[i],ib[i+1])
            quad(outer_a[i],ia[i],ia[i+1],outer_a[i+1])
            quad(outer_b[i+1],ib[i+1],ib[i],outer_b[i])
        for points in [outer_a,outer_b,ia,ib]:local.edges.extend(zip(points[:-1],points[1:]))
    if p.kind=='shell':
        arc=params.get('arc_degrees',360);a=ellipse(0,arc=arc);b=ellipse(d,arc=arc)
        for i in range(n):quad(a[i],a[i+1],b[i+1],b[i])
        local.edges.extend(zip(a[:-1],a[1:]));local.edges.extend(zip(b[:-1],b[1:]))
        if arc<360:local.edges.extend([(a[0],b[0]),(a[-1],b[-1])])
        elif params.get('capped',False):
            for y,points in [(0,a),(d,b)]:
                center=np.array([w/2,y,h/2])
                for i in range(n):local.faces.append(([center,points[i],points[i+1]],0))
    elif p.kind=='ring_frame':ring(params.get('inner_ratio',.82),ellipse(0),ellipse(d))
    elif p.kind=='bulkhead':
        def perimeter(y):
            points=[]
            for t in np.linspace(-math.pi/2,3*math.pi/2,n+1):
                dx,dz=w/2*math.cos(t),h/2*math.sin(t)
                scale=min((w/2)/max(abs(dx),1e-12),(h/2)/max(abs(dz),1e-12))
                points.append(np.array([w/2+dx*scale,y,h/2+dz*scale]))
            return points
        ring(params.get('inner_ratio',.65),perimeter(0),perimeter(d))
    elif p.kind=='truss':
        r=min(w,d,h)*.045;ys=np.linspace(r,d-r,params.get('bays',4)+1)
        for x in [r,w-r]:
            for z in [r,h-r]:rod([x,r,z],[x,d-r,z],r)
        for y in ys:
            for x in [r,w-r]:rod([x,y,r],[x,y,h-r],r)
            for z in [r,h-r]:rod([r,y,z],[w-r,y,z],r)
        for i,(a,b) in enumerate(zip(ys[:-1],ys[1:])):
            for x in [r,w-r]:rod([x,a,r if i%2==0 else h-r],[x,b,h-r if i%2==0 else r],r*.75)
    elif p.kind=='panel_array':
        local.box((0,0,0),(w,d,h),1)
        for x in np.linspace(0,w,params.get('columns',12)+1):local.edges.append((np.array([x,0,h]),np.array([x,d,h])))
        for y in np.linspace(0,d,params.get('rows',6)+1):local.edges.append((np.array([0,y,h]),np.array([w,y,h])))
    elif p.kind=='console':
        local.box((0,0,0),(w,d*.7,h*.55))
        # Sloping control surface, higher at the back, faces +Y.
        top=[[0,0,h],[w,0,h],[w,d,h*.55],[0,d,h*.55]]
        bottom=[[0,0,h*.45],[w,0,h*.45],[w,d,h*.45],[0,d,h*.45]]
        quad(*top);quad(*bottom)
        for i in range(4):j=(i+1)%4;quad(top[i],top[j],bottom[j],bottom[i])
        for y in [.15*d,.55*d]:
            z=h-.45*h*y/d
            local.edges.append((np.array([.1*w,y,z]),np.array([.9*w,y,z])))
        local.edges.extend((np.array(top[i]),np.array(top[(i+1)%4])) for i in range(4))
    elif p.kind=='seat':
        local.box((0,0,h*.42),(w,d,h*.1))
        local.box((0,0,h*.52),(w,d*.14,h*.48))
        for x in [.12*w,.88*w]:
            for y in [.12*d,.88*d]:rod([x,y,0],[x,y,h*.42],min(w,d)*.04)
    elif p.kind=='gear':
        teeth=params.get('teeth',16);points=[]
        for i in range(teeth*4):
            t=2*math.pi*i/(teeth*4);r=1 if i%4 in [1,2] else .85
            points.append(np.array([w/2+w*.5*r*math.cos(t),0,h/2+h*.5*r*math.sin(t)]))
        for i,a in enumerate(points):
            b=points[(i+1)%len(points)];a1=a+[0,d,0];b1=b+[0,d,0]
            quad(a,b,b1,a1)
            local.faces.extend([([np.array([w/2,0,h/2]),b,a],0),([np.array([w/2,d,h/2]),a1,b1],0)])
            local.edges.extend([(a,b),(a1,b1)])
    elif p.kind=='rotor':
        radius=min(w,h)*.12;rod([w/2,0,h/2],[w/2,d,h/2],radius)
        for t in np.linspace(0,2*math.pi,params.get('blades',6),endpoint=False):
            a=np.array([math.cos(t),0,math.sin(t)]);b=np.array([-math.sin(t),0,math.cos(t)])
            center=np.array([w/2,d*.5,h/2]);r=min(w,h)*.46
            corners=[center+a*radius-b*r*.09,center+a*r-b*r*.15,center+a*r+b*r*.15,center+a*radius+b*r*.09]
            quad(*corners);local.edges.extend(zip(corners,corners[1:]+corners[:1]))
    elif p.kind=='heat_exchanger':
        for x in [0,w*.9]:local.box((x,0,0),(w*.1,d,h))
        r=min(d,h)*.035
        for yy in np.linspace(r,d-r,4):
            for zz in np.linspace(r,h-r,4):rod([w*.1,yy,zz],[w*.9,yy,zz],r)
    elif p.kind=='luminaire':
        local.box((0,0,0),(w,d,h*.35))
        local.box((w*.07,d*.07,h*.35),(w*.86,d*.86,h*.65),2)
    elif p.kind=='instrument_panel':
        local.box((0,0,0),(w,d*.75,h))
        for xx in [.25*w,.75*w]:
            for zz in [.3*h,.7*h]:rod([xx,d*.75,zz],[xx,d,zz],min(w,h)*.14)
    # Permutation is orthogonal, so transformed normals retain contour validity.
    origin=np.array(p.origin,float)
    def point(v):return np.asarray(v)[order]+origin
    for face,tone in local.faces:m.faces.append(([point(v) for v in face],tone))
    m.edges.extend((point(a),point(b)) for a,b in local.edges)
    m.smooth_edges.extend((point(a),point(b),np.asarray(n1)[order],np.asarray(n2)[order]) for a,b,n1,n2 in local.smooth_edges)
    return True
