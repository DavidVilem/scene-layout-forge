"""Deterministic architectural pencil renderer. Units metres; z up. Pillow only."""
import math, random, json, argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W,H=2400,1600
R=random.Random(73)
faces=[]; lines=[]; labels=[]; counts={}
def project(p):
    x,y,z=p
    return (1200+105*(x-y*.72),1180+47*(x+y*.90)-115*z)
def depth(p): return .72*p[0]+p[1]+.703*p[2]
def poly(ps,tone=0): faces.append((sum(depth(p) for p in ps)/len(ps),ps,tone))
def line(a,b,width=1): lines.append((a,b,width))
def box(x,y,z,w,d,h):
    a=(x,y,z); b=(x+w,y,z); c=(x+w,y+d,z); e=(x,y+d,z)
    top=[(p[0],p[1],z+h) for p in [a,b,c,e]]
    poly([b,c,top[2],top[1]],2); poly([c,e,top[3],top[2]],1);poly(top,0)
def tube(a,b,r=.07,n=16):
    v=[b[i]-a[i] for i in range(3)]; length=math.sqrt(sum(q*q for q in v)); assert length>0
    v=[q/length for q in v]; seed=[0,0,1] if abs(v[2])<.9 else [1,0,0]
    u=[v[1]*seed[2]-v[2]*seed[1],v[2]*seed[0]-v[0]*seed[2],v[0]*seed[1]-v[1]*seed[0]]
    q=math.sqrt(sum(t*t for t in u));u=[t/q for t in u]
    t=[v[1]*u[2]-v[2]*u[1],v[2]*u[0]-v[0]*u[2],v[0]*u[1]-v[1]*u[0]]
    rings=[[tuple(c[j]+r*(u[j]*math.cos(i*2*math.pi/n)+t[j]*math.sin(i*2*math.pi/n)) for j in range(3)) for i in range(n)] for c in [a,b]]
    for i in range(n): poly([rings[0][i],rings[0][(i+1)%n],rings[1][(i+1)%n],rings[1][i]], .5+1.1*(1+math.sin(i*2*math.pi/n)))
    poly(rings[1],0)
def rail(a,b):
    length=math.dist(a,b);n=math.ceil(length/.8)
    for i in range(n+1):
        p=tuple(a[j]+(b[j]-a[j])*i/n for j in range(3)); tube(p,(p[0],p[1],p[2]+1),.025,8)
    for dz in [.48,1]:tube((a[0],a[1],a[2]+dz),(b[0],b[1],b[2]+dz),.026,8)
def stair_steps(height,run,count,width=1):
    if min(height,run,width)<=0 or not isinstance(count,int) or count<1:
        raise ValueError('Stair dimensions and integer step count must be positive')
    return [{'rise':height/count,'tread':run/count,'z':i*height/count,'width':width} for i in range(count)]
def flange(p,axis,r):
    a=tuple(p[i]-.045*axis[i] for i in range(3));b=tuple(p[i]+.045*axis[i] for i in range(3));tube(a,b,r)
def worker(x,y,z,pose=0):
    counts['workers']=counts.get('workers',0)+1
    # Boots, articulated trouser legs, torso, sleeves, head and safety helmet.
    for dx in [-.12,.12]:
        box(x+dx-.065,y-.08,z,.13,.23,.09)
        tube((x+dx,y,z+.12),(x+dx*.65,y,z+.79),.075,10)
    tube((x,y,z+.78),(x,y,z+1.25),.17,12)
    tube((x,y,z+1.29),(x,y,z+1.49),.105,12)
    tube((x,y,z+1.48),(x,y,z+1.58),.145,16)
    for s in [-1,1]:
        shoulder=(x+s*.17,y,z+1.18);elbow=(x+s*.25,y+.05,z+.94)
        hand=(x+s*.15,y+.27,z+1.0) if pose else (x+s*.27,y+.04,z+.77)
        tube(shoulder,elbow,.055,8);tube(elbow,hand,.048,8)
    if pose:box(x-.18,y+.18,z+.97,.36,.28,.025)
def scene():
    # Back wall, footing and regular structural bays.
    for x in range(-5,5):
        for y in range(-3,4):box(x,y,-.28,1,1,.28)
    for x in range(-5,5):
        for z in range(6):box(x,-3,z,1,.16,1)
    for x in [-4.5,0,4.5]:
        box(x-.24,-2.9,0,.48,.55,.25);box(x-.13,-2.8,.25,.26,.28,5.75)
        box(x-.25,-2.9,5.65,.5,6.5,.25)
        for y in [-1,1.5,3.4]: tube((x,y,5.9),(x,y,5.3),.018,6)
    box(-4.6,-2.8,5.85,9.2,.36,.32)
    for x in [-3,-1.5,1.5,3]:box(x,-2.8,5.9,.09,6.2,.17)
    # Inspection platform behind tanks, clear access at left.
    box(-3.7,-1.65,2.25,6.9,1.0,.15)
    for x in [-3.5,-.6,2.9]:
        box(x-.07,-1.45,0,.14,.14,2.25)
        tube((x,-1.4,1.7),(x+.38,-1.4,2.25),.045,8)
    rail((-3.7,-1.65,2.4),(3.2,-1.65,2.4));rail((3.2,-1.65,2.4),(3.2,-.65,2.4))
    # Stair top joins platform y=-.65, with tread pitch .25 and rise .20.
    for i,s in enumerate(stair_steps(2.4,3,12)):box(-3.7,2.35-(i+1)*s['tread'],s['z'],s['width'],s['tread'],s['rise'])
    for x in [-3.7,-2.7]:
        tube((x,2.35,.1),(x,-.65,2.3),.055,8)
        rail((x,2.35,.2),(x,-.65,2.4))
    # Two identical vessels with grounded legs, seams and top hatch.
    counts['tanks']=2;counts['pump']=1;counts['stairs']=1;counts['platform']=1
    for x in [-1.4,1.5]:
        y=-.05
        for dx in [-.49,.49]:
            for dy in [-.49,.49]:box(x+dx-.07,y+dy-.07,0,.14,.14,.55)
        tube((x,y,.5),(x,y,3.65),.78,48)
        for z in [.58,1.45,2.65,3.57]:tube((x,y,z),(x,y,z+.035),.793,48)
        tube((x,y,3.65),(x,y,3.75),.62,40);tube((x,y,3.75),(x,y,3.85),.25,24)
        # Independent inlet and outlet pipes, with flanges at wall port.
        tube((x,.73,1.05),(x,1.35,1.05),.115,20);flange((x,.92,1.05),(0,1,0),.19)
        tube((x,1.35,1.05),(x,1.35,.45),.115,20)
        tube((x-.02,1.35,.45),(x+.02,1.35,.45),.16,16)
    # Common header, three-way branch to single pump.
    tube((-1.4,1.35,.45),(1.5,1.35,.45),.115,24)
    tube((.1,1.35,.45),(.1,2.3,.45),.115,20)
    for x in [-1.0,1.1]:box(x-.08,1.27,0,.16,.16,.33)
    box(-.5,2.25,0,1.8,.8,.18)
    tube((.1,2.3,.45),(.1,2.65,.45),.28,32)
    tube((.35,2.65,.45),(1.05,2.65,.45),.23,24)
    for x in [.45,.55,.65,.75,.85,.95]:tube((x,2.65,.45),(x+.018,2.65,.45),.25,24)
    tube((.1,2.65,.7),(.1,2.65,.94),.08,16)
    tube((.1,2.65,.94),(2.8,2.65,.94),.08,16)
    tube((2.8,2.65,.94),(2.8,2.65,.1),.08,16)
    flange((2.8,2.65,.12),(0,0,1),.17)
    # Architectural detailing: electrical cabinet, conduits, floor drain, bricks.
    box(3.65,-2.55,.55,.65,.25,1.2)
    for x in [3.8,4.0,4.2]:tube((x,-2.39,1.8),(x,-2.39,4.9),.02,8)
    for x in range(-4,5):
        for y in range(-2,4):
            line((x,y,.003),(x+1,y,.003),.5);line((x,y,.003),(x,y+1,.003),.5)
    for i in range(32):box(3.3,-1.7+i*.14,.01,.32,.025,.015)
    worker(-3.15,-1.15,2.4,1);worker(1.8,3.05,0,0)
    labels.extend([('FILTER VESSELS',(-1.4,-.05,3.85),(420,245)),('INSPECTION DECK',(-3.7,-1.2,2.4),(150,620)),('CIRCULATION PUMP',(.1,2.6,.45),(430,1395)),('SERVICE CONDUITS',(4,-2.4,3),(1810,310))])
def render(out):
    faces.clear();lines.clear();labels.clear();counts.clear();R.seed(73)
    scene();im=Image.new('RGB',(W,H),(241,233,214));d=ImageDraw.Draw(im)
    # Paper grain is deterministic and never alters geometric edges.
    for _ in range(130000):
        x=R.randrange(W);y=R.randrange(H);v=R.randrange(213,246);d.point((x,y),fill=(v,min(250,v+2),max(0,v-10)))
    for _,ps,t in sorted(faces,key=lambda f:f[0]):
        pts=[project(p) for p in ps];v=int(239-t*9)
        d.polygon(pts,fill=(v,v-5,v-17));d.line(pts+[pts[0]],fill=(89,84,73),width=1)
    # Floor lines only on the exposed foreground strip.
    for a,b,width in lines:
        if a[1]>=3: d.line([project(a),project(b)],fill=(174,164,144),width=1)
    def font(size):
        for name in ['DejaVuSansMono.ttf','consola.ttf']:
            try:return ImageFont.truetype(name,size)
            except OSError:pass
        return ImageFont.load_default(size=size)
    small=font(15);mainfont=font(21)
    for txt,p,anchor in labels:
        end=project(p);d.text(anchor,txt,font=mainfont,fill=(75,71,62));start=(anchor[0]+40,anchor[1]+30)
        d.line([start,(start[0]+45,start[1]+20),end],fill=(111,103,87),width=1);d.ellipse([end[0]-3,end[1]-3,end[0]+3,end[1]+3],fill=(80,74,65))
    d.text((110,85),'UTILITY HALL / STUDY 01',font=font(30),fill=(70,65,55))
    d.text((110,128),'Twin filtration vessels - maintenance access',font=small,fill=(110,101,85))
    d.rectangle((35,35,W-35,H-35),outline=(166,153,128),width=1)
    Path(out).parent.mkdir(parents=True,exist_ok=True); im.save(out)
    assert counts==dict(tanks=2,pump=1,stairs=1,platform=1,workers=2),counts
    print(json.dumps({'output':out,'components':counts,'faces':len(faces),'projection':'fixed orthographic axonometric'},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);render(p.parse_args().out)
