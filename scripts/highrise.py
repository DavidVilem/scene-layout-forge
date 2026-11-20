"""Detailed original tower assembly with entrance, site and roof equipment."""
import argparse,json
from pathlib import Path
from scene_model import tower,make_part as part,validate

def highrise(floors=24,bays=3):
    if type(bays)!=int or not 2<=bays<=12:raise ValueError('Detailed tower requires 2..12 bays')
    data=tower(floors,bays);p=data['parts'];width=bays*4;roof_z=floors*3.4+.25
    door_bay=bays//2;door_x=door_bay*4+.3;door_w=3.1
    replaced=f'panel-0-1-{door_bay}'
    p[:]=[item for item in p if item['id']!=replaced]
    data['expected_counts']['curtain_panel']-=1
    p.append(part('entrance','door',(door_x,width-.15,.25),(door_w,.15,2.85),parent='slab-0'))
    p.append(part('plaza','paving',(-4,-4,-.15),(width+8,width+8,.15)))
    p.append(part('entry-landing','landing',(door_x,width,0),(door_w,1,.25)))
    p.append(part('entry-ramp','ramp',(door_x,width+1,0),(door_w,2.5,.25),parameters={'reverse':True}))
    p.append(part('entry-canopy','slab',(door_x-.1,width,3.1),(door_w+.2,1.2,.15)))
    for i,xx in enumerate([door_x,door_x+door_w-.12]):
        p.append(part(f'canopy-post-{i}','column',(xx,width+.85,.25),(.12,.12,2.85),parameters={'profile':'steel'}))
    bearings=[{'part':'entrance','on':'slab-0'},{'part':'entry-landing','on':'plaza'},{'part':'entry-ramp','on':'plaza'}]
    for i in range(2):
        bearings.extend([{'part':f'canopy-post-{i}','on':'entry-landing'},{'part':'entry-canopy','on':f'canopy-post-{i}'}])
    for i,(origin,size) in enumerate([
        ((0,0,roof_z),(width,.18,.9)),((0,width-.18,roof_z),(width,.18,.9)),
        ((0,.18,roof_z),(.18,width-.36,.9)),((width-.18,.18,roof_z),(.18,width-.36,.9))]):
        p.append(part(f'parapet-{i}','parapet',origin,size,parent='roof'));bearings.append({'part':f'parapet-{i}','on':'roof'})
    for i,x in enumerate([1.2,width-3.2]):
        p.append(part(f'roof-service-{i}','cabinet',(x,1.2,roof_z),(2,1.5,1.4),parent='roof'))
        bearings.append({'part':f'roof-service-{i}','on':'roof'})
    for i,x in enumerate([-2,width+1]):
        p.append(part(f'planter-{i}','planter',(x,width+1,0),(1,2,.6),parent='plaza'))
        bearings.append({'part':f'planter-{i}','on':'plaza'})
    for i,x in enumerate([0,2,width-2,width]):
        p.append(part(f'bollard-{i}','bollard',(x,width+3.6,0),(.15,.15,.85),parent='plaza'))
        bearings.append({'part':f'bollard-{i}','on':'plaza'})
    # Vertical facade fins attach at each floor slab rather than floating across it.
    for level in range(floors):
        for bay in range(bays+1):
            p.append(part(f'fin-{level}-{bay}','mullion',(bay*4-.06,width-.12,level*3.4+.25),(.12,.24,3.15),parent=f'slab-{level}'))
            bearings.append({'part':f'fin-{level}-{bay}','on':f'slab-{level}'})
    data['bearings']=bearings
    data['ramp_access']=[{'ramp':'entry-ramp','landing':'entry-landing'}]
    data['expected_counts'].update({'door':1,'ramp':1,'landing':1,'parapet':4,'cabinet':2,'planter':2,'bollard':4,'slab':floors+2,'column':floors*(bays+1)**2+2,'mullion':floors*(bays+1)})
    data['clearance_pairs']=[['entry-ramp','planter-0'],['entry-ramp','planter-1'],['roof-service-0','roof-service-1']]
    errors=validate(data)
    if errors:raise ValueError('\n'.join(errors))
    return data

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--floors',type=int,default=24);ap.add_argument('--bays',type=int,default=3);ap.add_argument('--out',required=True)
    args=ap.parse_args();Path(args.out).write_text(json.dumps(highrise(args.floors,args.bays),indent=2))
