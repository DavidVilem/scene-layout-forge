from kit import make_part as p

def scene():
    parts=[p('base','slab',(0,0,-.15),(2,5.2,.15))]
    bearings=[{'part':'reducer','on':'reducer-support'}]
    def cylinder(name,a,b,radius):
        parts.append(p(name,'conduit',(1-radius,a,1-radius),(2*radius,b-a,2*radius),parameters={'points':[[1,a,1],[1,b,1]],'radius':radius},ports={'in':[radius,0,radius],'out':[radius,b-a,radius]}))
    cylinder('motor',.2,1.4,.4)
    cylinder('input-shaft',1.4,1.8,.07)
    cylinder('coupling',1.8,2.2,.14)
    parts.append(p('reducer','column',(.55,2.2,.55),(.9,1,.9),ports={'in':[.45,0,.45],'out':[.45,1,.45]}))
    cylinder('output-shaft',3.2,4.9,.07)
    for name,y,h,width,depth in [('motor',.3,.6,.6,.8),('reducer',2.2,.55,.9,1),('bearing-a',3.4,.7,.6,.35),('bearing-b',4.5,.7,.6,.35)]:
        parts.append(p(name+'-support','column',(1-width/2,y,0),(width,depth,h)))
        bearings.append({'part':name+'-support','on':'base'})
    for name,y in [('bearing-a',3.4),('bearing-b',4.5)]:
        parts.append(p(name,'ring_frame',(.7,y,.7),(.6,.35,.6),parameters={'inner_ratio':.4}))
        bearings.append({'part':name,'on':name+'-support'})
    parts.append(p('rotor','rotor',(.35,3.95,.35),(1.3,.3,1.3),parameters={'blades':5}))
    return {'units':'m','parts':parts,'connections':[],'expected_counts':{'rotor':1,'ring_frame':2,'worker':0},'bearings':bearings,
            'attachments':[{'from':a+':out','to':b+':in'} for a,b in [('motor','input-shaft'),('input-shaft','coupling'),('coupling','reducer'),('reducer','output-shaft')]],
            'shaft_bearings':[{'shaft':'output-shaft','bearing':b} for b in ['bearing-a','bearing-b']]}
