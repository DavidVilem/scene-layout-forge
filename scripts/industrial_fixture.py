"""Small render fixture; an assembly study rather than a hydraulic simulation."""
import json,argparse,math
from pathlib import Path
from scene_model import make_part as part

def elbow(center,radius,start,end,plane='yz',steps=20):
    if radius<=0 or steps<2:raise ValueError('Positive bend radius and at least two steps required')
    result=[]
    for i in range(steps+1):
        a=start+(end-start)*i/steps;p=list(center)
        axes={'xy':(0,1),'xz':(0,2),'yz':(1,2)}[plane]
        p[axes[0]]+=radius*math.cos(a);p[axes[1]]+=radius*math.sin(a);result.append(p)
    return result

def fixture():
    p=[part('floor','slab',(-1,-1,-.2),(8,5,.2)),part('wall','wall',(-1,-1,0),(8,.15,5))]
    for i,x in enumerate([0,3]):
        p.append(part('vessel-'+str(i),'vessel',(x,0,0),(1.7,1.7,3.6)))
        # Outlet starts at shell tangent, runs to a quarter-circle bend and drops.
        arc=elbow((x+.85,2.0,.75),.35,math.pi/2,0)
        points=[[x+.85,1.7,1.1]]+arc+[[x+.85,2.35,.25]]
        p.append(part('outlet-'+str(i),'pipe',(x+.7,1.5,.1),(.3,1,1.2),parameters={'points':points,'radius':.09}))
    p.append(part('pump','pump',(1.4,2.5,0),(1.5,.8,.8)))
    for i,x in enumerate([-.6,5.5]):
        p.append(part('column-'+str(i),'column',(x,-.9,0),(.3,.3,4.8)))
    p.append(part('beam','beam',(-.6,-.9,4.5),(6.4,.3,.3)))
    return {'units':'m','parts':p,'expected_counts':{'vessel':2,'pump':1,'pipe':2}}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();Path(a.out).write_text(json.dumps(fixture(),indent=2))
