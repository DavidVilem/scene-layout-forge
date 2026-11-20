"""Six-level-compatible circulation fragment with real stairwell apertures.

Same-direction stacked flights provide constant vertical headroom. Floor return
circuits run beside the stairwell. Reversing flights in one stacked bay would
reduce headroom and is intentionally not presented as a valid alternative.
"""
from assembly_model import cut_host


def build_access_core(levels=6,height=3.5):
    if type(levels)!=int or not 2<=levels<=12 or height<3.2:raise ValueError('2..12 levels and height >=3.2 required')
    s={'units':'m','schema_version':2,'validation_policy':'strict','parts':[],'bearings':[],
       'mounts':[],'stair_access':[],'hosts':[],'openings':[],'grounded':['core-ground'],
       'access_nodes':[],'access_volumes':[],'access_roots':['core-0'],
       'core_levels':{},'core_vertical_edges':{}}
    def part(id,kind,o,sz):
        p={'id':id,'kind':kind,'origin':list(o),'size':list(sz)};s['parts'].append(p);return p
    def node(id,p):s['access_nodes'].append({'id':id,'position':list(p)});return id
    positions={}
    def addnode(id,p):positions[id]=p;return node(id,p)
    def route(id,a,b,walk=(),width=.5):
        pa,pb=positions[a],positions[b]
        v={'id':id,'from':a,'to':b,
           'min':[min(pa[0],pb[0])-width/2,min(pa[1],pb[1])-width/2,min(pa[2],pb[2])-.9],
           'max':[max(pa[0],pb[0])+width/2,max(pa[1],pb[1])+width/2,max(pa[2],pb[2])+1.0],
           'traversable_parts':list(walk),'walking_path':[list(pa),list(pb)],
           'body_below':.9,'body_above':1.0,'half_width':width/2,'walking_offset':1.2}
        s['access_volumes'].append(v);return id
    part('core-ground','slab',[-3.3,-5.3,-.4],[6.6,10.6,.4])
    floors={0:[s['parts'][0]]}
    for level in range(1,levels):
        z=level*height
        host={'id':f'core-floor-{level}','kind':'slab','origin':[-3.3,-5.3,z-.2],'size':[6.6,10.6,.2]}
        cut=cut_host(host,[{'id':f'core-opening-{level}','origin':[-.05,-3,z-.2],'size':[1.7,6,.2]}],'z')
        floors[level]=cut['parts'];s['parts'].extend(cut['parts']);s['hosts'].extend(cut['hosts']);s['openings'].extend(cut['openings'])
        for index,p in enumerate(cut['parts']):
            x,y,_=p['origin'];w,d,_=p['size']
            for n,(xx,yy) in enumerate(((x+.09,y+.09),(x+w-.21,y+d-.21))):
                c=part(f'core-support-{level}-{index}-{n}','column',[xx,yy,(level-1)*height],[.12,.12,height-.2])
                lower=next(q for q in floors[level-1] if q['origin'][0]-1e-6<=xx and xx+.12<=q['origin'][0]+q['size'][0]+1e-6 and q['origin'][1]-1e-6<=yy and yy+.12<=q['origin'][1]+q['size'][1]+1e-6)
                s['bearings'] += [{'part':c['id'],'on':lower['id']},{'part':p['id'],'on':c['id']}]
    for level in range(levels):
        z=level*height; center=addnode(f'core-{level}',[-1.5,0,z+1.2]);ports={}
        for name,p in [('west',[-3.3,0,z+1.2]),('north',[-1.5,5.3,z+1.2]),('south',[-1.5,-5.3,z+1.2])]:
            ports[name]=addnode(f'core-{level}-{name}',p)
            route(f'core-{level}-to-{name}',center,ports[name])
        n=addnode(f'core-{level}-north-turn',[-1.5,4.2,z+1.2])
        e=addnode(f'core-{level}-east-turn',[2.5,4.2,z+1.2])
        ec=addnode(f'core-{level}-east-corridor',[2.5,0,z+1.2])
        ports['east']=addnode(f'core-{level}-east',[3.3,0,z+1.2])
        for i,(a,b) in enumerate(((center,n),(n,e),(e,ec),(ec,ports['east']))):route(f'core-{level}-east-return-{i}',a,b)
        s['core_levels'][str(level)]={'floor_parts':[p['id'] for p in floors[level]],'node':center,'ports':ports,'z':z}
    for level in range(levels-1):
        z=level*height;stair=part(f'core-stair-{level}','stair',[0,-3,z],[1.6,6,height]);stair['parameters']={'steps':20}
        upper=next(p for p in floors[level+1] if abs(p['origin'][0]+.05)<1e-6 and abs(p['origin'][1]-3)<1e-6)
        lower=next(p for p in floors[level] if p['origin'][0]<=-.2 and p['origin'][0]+p['size'][0]>=-.05 and p['origin'][1]<=-2.9 and p['origin'][1]+p['size'][1]>=-2.7)
        bracket=part(f'core-stair-jamb-{level}','column',[-.2,-2.9,z],[.2,.2,height-.2])
        s['bearings'].append({'part':bracket['id'],'on':lower['id']})
        s['mounts'] += [{'part':stair['id'],'on':bracket['id'],'axis':'x','side':1},
                       {'part':stair['id'],'on':upper['id'],'axis':'y','side':-1}]
        s['stair_access'].append({'stair':stair['id'],'landing':upper['id']})
        path=[s['core_levels'][str(level)]['node']]
        for label,p in [('start-return',[-1.5,-4.2,z+1.2]),('start-turn',[.8,-4.2,z+1.2]),('start',[.8,-3.35,z+1.2])]:
            path.append(addnode(f'core-stair-{level}-{label}',p))
        for step in range(20):path.append(addnode(f'core-stair-{level}-step-{step}',[.8,-3+(step+.5)*.3,z+(step+1)*height/20+1.2]))
        for label,p in [('end',[.8,3.35,z+height+1.2]),('end-turn',[.8,4.2,z+height+1.2]),('end-return',[-1.5,4.2,z+height+1.2])]:
            path.append(addnode(f'core-stair-{level}-{label}',p))
        path.append(s['core_levels'][str(level+1)]['node'])
        s['core_vertical_edges'][str(level)]=[route(f'core-stair-{level}-walk-{i}',a,b,[stair['id'],upper['id']],.4) for i,(a,b) in enumerate(zip(path,path[1:]))]
    s['core_description']={'circulation':'same-direction stacked flights with clear lateral return','headroom_basis':'tread geometry + walking envelope checked; floor height exceeds 2.15 m envelope','limits':['conceptual support topology; no structural loads or code compliance']}
    return s
