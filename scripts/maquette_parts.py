"""Reusable construction families. Shapes remain ordinary reconstruction geometry.
No image inference, fixed building layout or acceptance override.
"""
import math

def box(at,size): return {'type':'box','at':list(at),'size':list(size)}
def rod(a,b,r=.025):return {'type':'sweep','points':[list(a),list(b)],'radius':r,'segments':12}
def quad(points):return {'type':'mesh','vertices':points,'faces':[[0,1,2],[0,2,3]]}

def wall_openings(width,height,depth,openings):
    """Local XZ facade, thickness along Y; openings=(x,z,w,h). Actual empty holes."""
    if min(width,height,depth)<=0:raise ValueError('Positive wall dimensions')
    for x,z,w,h in openings:
        if min(w,h)<=0 or x<0 or z<0 or x+w>width or z+h>height:raise ValueError('Opening outside wall')
    xs=sorted({0,width,*[v for x,z,w,h in openings for v in (x,x+w)]})
    zs=sorted({0,height,*[v for x,z,w,h in openings for v in (z,z+h)]})
    return [box([a,0,c],[b-a,depth,d-c]) for a,b in zip(xs,xs[1:]) for c,d in zip(zs,zs[1:])
            if not any(x<(a+b)/2<x+w and z<(c+d)/2<z+h for x,z,w,h in openings)]

def window(width,height,cols=3,rows=3,frame=.045):
    """Local XZ plane; separate mounting frame and inset glazing, no opaque placeholder."""
    if min(width,height,frame)<=0 or cols<1 or rows<1 or frame*2>=min(width/cols,height/rows):raise ValueError('Invalid glazing module')
    frames=[box([i*width/cols-frame/2,-.04,0],[frame,.08,height]) for i in range(cols+1)]
    frames += [box([0,-.04,j*height/rows-frame/2],[width,.08,frame]) for j in range(rows+1)]
    panes=[box([i*width/cols+frame/2,.005,j*height/rows+frame/2],[width/cols-frame,.012,height/rows-frame]) for i in range(cols) for j in range(rows)]
    return {'frame':frames,'glass':panes}

def pitched_roof(width,length,eave,rise,bays=8):
    if min(width,length,eave,rise)>0 and bays>=1:pass
    else:raise ValueError('Invalid roof')
    surfaces=[];ribs=[];seams=[]
    for x0,x1,z0,z1 in ((0,width/2,eave,eave+rise),(width/2,width,eave+rise,eave)):
        surfaces.append(quad([[x0,0,z0],[x1,0,z1],[x1,length,z1],[x0,length,z0]]))
        for j in range(bays+1):
            y=j*length/bays;ribs.append(rod([x0,y,z0],[x1,y,z1],.045))
        for j in range(1,9):
            x=x0+(x1-x0)*j/9;z=z0+(z1-z0)*j/9+.012
            seams.append(rod([x,0,z],[x,length,z],.012))
    ribs += [rod([x,0,z],[x,length,z],.045) for x,z in ((0,eave),(width/2,eave+rise),(width,eave))]
    return {'skin':surfaces,'structure':ribs,'seams':seams}

def canopy(width,length,height,bays=5):
    if min(width,length,height)<=0 or bays<1:raise ValueError('Invalid canopy')
    roof=pitched_roof(width,length,height,.12,bays)
    posts=[];braces=[];lights=[]
    for j in range(bays+1):
        y=j*length/bays;x=width/2
        posts += [box([x-.09,y-.09,0],[.18,.18,height]),box([x-.18,y-.18,0],[.36,.36,.10])]
        for side in (-1,1):braces.append(rod([x,y,height-.65],[x+side*(width/2-.12),y,height],.04))
        lights += [rod([x+.4,y,height],[x+.4,y,height-.5],.018),box([x+.29,y-.11,height-.58],[.22,.22,.08])]
    return {**roof,'posts':posts,'braces':braces,'lights':lights}

def vehicle_shell(width,length,height,base=.4):
    """Continuous rounded carriage shell with a sloped front, explicit glazing and running gear.
    Local longitudinal axis Y; caller adapts silhouette, never claims historical identity.
    """
    if min(width,length,height)<=0 or length<width*2:raise ValueError('Invalid vehicle proportions')
    rings=[]
    for y,scale,slant in ((0,.86,.18),(.65,.98,0),(1.3,1,0),(length,1,0)):
        ring=[]
        for i in range(40):
            t=i*2*math.pi/40;c=math.cos(t);s=math.sin(t)
            z=base+height/2+height/2*math.copysign(abs(s)**.5,s)
            ring.append([width/2+width/2*scale*math.copysign(abs(c)**.5,c),y+slant*(z-base),z])
        rings.append(ring)
    shell=[{'type':'loft','rings':rings,'caps':True}]
    z0,z1=base+height*.44,base+height*.84
    glass=[quad([[width*.16,.18*(z0-base)-.012,z0],[width*.84,.18*(z0-base)-.012,z0],[width*.82,.18*(z1-base)-.012,z1],[width*.18,.18*(z1-base)-.012,z1]])]
    trim=[];gear=[];lights=[]
    for x in (-.012,width+.006):
        for j in range(max(1,int((length-1.5)/1.05))):
            y=1.4+j*1.05;glass.append(box([x,y,z0],[.012,.7,z1-z0]))
        trim.append(box([x,1.3,base+height*.25],[.016,length-1.3,height*.10]))
    for y in (length*.2,length*.25,length*.78,length*.83):
        for x in (.13,width-.13):gear.append(rod([x-.06,y,base*.55],[x+.06,y,base*.55],base*.55))
    for y in (length*.2,length*.45,length*.7):trim.append(box([width*.2,y,base+height],[width*.6,.65,.17]))
    for x in (width*.2,width*.72):lights.append(box([x,.18*height*.25-.03,base+height*.25],[width*.08,.05,.09]))
    trim.append(box([width*.42,-.12,base*.85],[width*.16,.22,.15]))
    return {'shell':shell,'glass':glass,'trim':trim,'gear':gear,'lights':lights}

def translated(shapes,offset):
    import copy
    result=copy.deepcopy(shapes)
    for s in result:s['at']=[a+b for a,b in zip(s.get('at',[0,0,0]),offset)]
    return result
