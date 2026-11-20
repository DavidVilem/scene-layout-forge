"""Connected assembly with explicit ports and access."""
import json,argparse,math
from pathlib import Path
from scene_model import make_part as part
from industrial_fixture import elbow
from route_geometry import rounded_route
def fixture():
    p=[part('floor','slab',(-2,-1,-.2),(10,8,.2)),part('wall','wall',(-2,-1,0),(10,.15,5.5),parameters={'panel_size':[2,1.8]})];links=[]
    for i,x in enumerate([0,3]):
        p.append(part(f'tank-{i}','vessel',(x,0,0),(1.7,1.7,3.6),ports={'out':[.85,1.7,1.1]},parameters={'inspection_hatch':True,'seam_bolts':16}))
        route=[[x+.85,1.7,1.1]]+elbow((x+.85,2,.75),.35,math.pi/2,0)+[[x+.85,2.35,.5]]
        links.append({'from':f'tank-{i}:out','to':f'header:branch-{i}','route':route,'radius':.09})
    p.append(part('header','manifold',(.85,2.25,.3),(3,.2,.2),ports={'branch-0':[0,.1,.2],'branch-1':[3,.1,.2],'pump':[1.2,.2,.1]}))
    # Top casing port is on the actual cylinder surface, visible from above.
    p.append(part('pump','pump',(1.675,3.5,0),(1.5,.8,.8),ports={'in':[.375,.4,.64],'out':[.375,.56,.4]}))
    inlet=rounded_route([[2.05,2.45,.4],[2.05,3.4,.4],[2.05,3.4,.9],[2.05,3.9,.9],[2.05,3.9,.64]],.12)
    links.append({'from':'header:pump','to':'pump:in','route':inlet,'radius':.075})
    p.append(part('return','drain',(2,5.2,0),(.3,.3,.05),ports={'in':[.15,.15,.05]}))
    discharge=rounded_route([[2.05,4.06,.4],[2.05,4.5,.4],[2.15,4.9,.4],[2.15,5.35,.4],[2.15,5.35,.05]],.15)
    links.append({'from':'pump:out','to':'return:in','route':discharge,'radius':.06})
    p.append(part('deck','landing',(-1.4,-.8,2.25),(7,.8,.15),parameters={'surface':'grating','grid_spacing':.12}))
    for i,x in enumerate([-1.2,2,5.3]):p.append(part(f'deck-leg-{i}','column',(x,-.65,0),(.12,.12,2.25),parameters={'profile':'steel'}))
    p.append(part('stairs','stair',(-1.4,0,0),(1,3,2.4),parameters={'steps':12,'reverse':True}))
    p.append(part('back-rail','railing',(-1.4,-.8,2.4),(7,.05,1)))
    p.append(part('front-rail','railing',(-.4,-.05,2.4),(6,.05,1)))
    p.append(part('inspector','worker',(4.5,-.6,2.4),(.45,.45,1.7),parent='deck'))
    p.append(part('operator','worker',(3.7,4,0),(.45,.45,1.7),parent='floor'))
    for i,x in enumerate([-1.7,6.5]):p.append(part(f'hall-column-{i}','column',(x,-.8,0),(.3,.3,4.9),parameters={'profile':'steel'}))
    p.append(part('hall-beam','beam',(-1.7,-.8,4.9),(8.5,.3,.3)))
    for link in links:link['fittings']=True
    bearings=[{'part':name,'on':'floor'} for name in ['tank-0','tank-1','pump','stairs','hall-column-0','hall-column-1']]
    bearings += [{'part':'hall-beam','on':f'hall-column-{i}'} for i in range(2)]
    bearings += [{'part':'deck','on':f'deck-leg-{i}'} for i in range(3)]
    return {'units':'m','parts':p,'connections':links,'expected_counts':{'vessel':2,'pump':1,'worker':2,'stair':1,'landing':1},'clearance_pairs':[['tank-0','tank-1'],['pump','operator'],['deck','tank-0'],['deck','tank-1']], 'bearings':bearings,'stair_access':[{'stair':'stairs','landing':'deck'}]}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();Path(a.out).write_text(json.dumps(fixture(),indent=2))
