from kit import make_part as p

def scene():
    parts=[p('floor','slab',(0,0,-.15),(10,8,.15)),p('wall-north','wall',(0,7.85,0),(10,.15,2.8)),p('wall-west','wall',(0,0,0),(.15,8,2.8)),p('wall-east','wall',(9.85,0,0),(.15,8,2.8)),p('wall-front-a','wall',(0,0,0),(4,.15,2.8)),p('wall-front-b','wall',(6,0,0),(4,.15,2.8)),p('divider-a','wall',(4,.15,0),(.15,2.5,2.8)),p('divider-b','wall',(4,4.15,0),(.15,3.7,2.8)),p('controls','console',(5.5,6.5,0),(3,.8,1.2)),p('storage','cabinet',(.4,6.5,0),(2,.8,1.8)),p('seat-a','seat',(6,5.4,0),(.6,.6,1)),p('seat-b','seat',(7.5,5.4,0),(.6,.6,1))]
    return {'units':'m','parts':parts,'connections':[],'expected_counts':{'console':1,'cabinet':1,'seat':2,'worker':0},'clearance_pairs':[['seat-a','seat-b']], 'bearings':[{'part':item,'on':'floor'} for item in ['controls','storage','seat-a','seat-b']]}
