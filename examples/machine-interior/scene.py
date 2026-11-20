from kit import make_part as p

def scene():
    parts=[p('base','slab',(0,0,-.2),(5,4,.2)),p('gear-large','gear',(.5,1,.4),(1.8,.35,1.8)),p('gear-small','gear',(2.4,1,.7),(1.1,.35,1.1)),p('rotor','rotor',(3.7,1.8,.3),(.9,1.8,.9)),p('cooler','heat_exchanger',(.3,2.3,0),(2.6,1.2,.8)),p('control','console',(3.5,.2,0),(1.2,.8,1.2))]
    bearings=[{'part':name,'on':'base'} for name in ['control','cooler']]
    for i,(x,y,z,end) in enumerate([(1.4,.2,1.3,1.5),(2.95,.2,1.25,1.5),(4.15,1.3,.75,2.7)]):
        parts.extend([p(f'pedestal-{i}','column',(x-.18,y,0),(.36,.4,z-.18)),
                      p(f'bearing-{i}','ring_frame',(x-.18,y,z-.18),(.36,.4,.36),parameters={'inner_ratio':.45}),
                      p(f'shaft-{i}','conduit',(x-.08,y,z-.08),(.16,end-y,.16),parameters={'points':[[x,y,z],[x,end,z]],'radius':.08})])
        bearings.extend([{'part':f'pedestal-{i}','on':'base'},{'part':f'bearing-{i}','on':f'pedestal-{i}'}])
    return {'units':'m','parts':parts,'connections':[],'expected_counts':{'gear':2,'rotor':1,'heat_exchanger':1,'console':1,'worker':0},'bearings':bearings}
