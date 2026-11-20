from kit import make_part as p

def scene():
    parts=[p('habitat','shell',(-2,0,1),(4,14,4),parameters={'capped':True},ports={'right':[4,7,2],'left':[0,7,2],'dock':[2,14,2]}),
           p('docking-collar','ring_frame',(-1.2,14,1.8),(2.4,.5,2.4),ports={'in':[1.2,0,1.2]}),
           p('lab-module','shell',(-1.5,-6,1.5),(3,6,3),parameters={'capped':True})]
    attachments=[{'from':'habitat:dock','to':'docking-collar:in'}]
    for side,x in [('left',-12),('right',2)]:
        parts.append(p(side+'-truss','truss',(x,6.6,2.6),(10,.8,.8),parameters={'orientation':'x','bays':6},ports={'hub':[10 if side=='left' else 0,.4,.4]}))
        attachments.append({'from':'habitat:'+side,'to':side+'-truss:hub'})
        for j,y in enumerate([-.4,7.4]):
            # Panel edges meet the truss surface at y=6.6 or 7.4.
            parts.append(p(side+f'-array-{j}','panel_array',(x+1,y,2.9),(8,7,.2),parameters={'rows':10,'columns':12},ports={'mount':[4,7 if j==0 else 0,.1]}))
            truss=parts[-2] if j==0 else next(a for a in parts if a['id']==side+'-truss')
            truss['ports']['array-'+str(j)]=[5,0 if j==0 else .8,.4]
            attachments.append({'from':side+f'-array-{j}:mount','to':side+f'-truss:array-{j}'})
    for j,y in enumerate([1,4,10,13]):parts.append(p(f'hull-ring-{j}','ring_frame',(-2.05,y,.95),(4.1,.12,4.1),parameters={'inner_ratio':.95}))
    return {'units':'m','parts':parts,'attachments':attachments,'connections':[], 'expected_counts':{'shell':2,'truss':2,'panel_array':4,'ring_frame':5,'worker':0,'vessel':0,'pump':0},'clearance_pairs':[['left-array-0','left-array-1'],['right-array-0','right-array-1']]}
