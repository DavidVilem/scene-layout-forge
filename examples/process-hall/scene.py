from kit import factory, make_part

def scene():
    data=factory(3)
    # Original open-front service hall: all enrichment exists before finishing.
    for bay in range(3):
        dx=10*bay; prefix=f'bay-{bay}-'
        post=prefix+'service-post'; beam=prefix+'service-beam'
        duct=prefix+'ventilation-duct'
        data['parts'].extend([
            make_part(post,'column',(dx+6.5,5.2,0),(.3,.3,5.2),parameters={'profile':'steel'}),
            make_part(beam,'beam',(dx+6.5,-.8,5.2),(.3,6.3,.2)),
            make_part(duct,'duct',(dx+6.5,-.5,4.6),(.3,5.5,.3)),
            make_part(prefix+'brace','brace',(dx-1.4,-.75,3.5),(1.4,.1,1.4)),
            make_part(prefix+'cabinet-feed','conduit',(dx+6.08,-.36,1.8),(.05,.05,2.5),parameters={'points':[[dx+6.08,-.36,1.8],[dx+6.08,-.36,4.3]],'radius':.025})])
        data['bearings'].extend([{'part':post,'on':prefix+'floor'}, {'part':beam,'on':post},{'part':beam,'on':prefix+'hall-beam'}])
        data['route_obstacles'].extend([post,duct])
        for index,y in enumerate([0,4.5]):
            data['parts'].append(make_part(prefix+f'duct-hanger-{index}','conduit',(dx+6.65,y,4.9),(.036,.036,.3),parameters={'points':[[dx+6.65,y,4.9],[dx+6.65,y,5.2]],'radius':.018}))
        worker=next(p for p in data['parts'] if p['id']==prefix+'inspector')
        worker['origin']=[dx+7.1,4.5,0];worker['parent']=prefix+'floor'
    workers=[p for p in data['parts'] if p['kind']=='worker']
    for worker in workers:
        data['route_obstacles'].append(worker['id'])
        for part in data['parts']:
            if part['kind'] in ['worker','vessel','pump','column','cabinet'] and part['id']!=worker['id']:
                data['clearance_pairs'].append([worker['id'],part['id']])
    return data
