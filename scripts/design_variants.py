"""Explore cheap spatial graphs before geometry. No image generation or certification."""
import argparse, copy, hashlib, json, math, random
from pathlib import Path
from design_intent import DesignIntent, canonical, content_hash, seed_streams
from domain_grammar import DOMAINS,capability

VERSION='design-variants-3'
FAMILIES=('spine','hub','ring','branched','stepped')

def _intent(value): return value if isinstance(value,DesignIntent) else DesignIntent.from_data(value)

def _dist(a,b): return math.dist(a,b)

def fingerprint(candidate,semantic=True):
    """ID/order/translation/rotation invariant coarse graph-and-distance descriptor.

    WL colors plus normalized pair distances tolerate small metric edits. This is
    an approximate duplicate filter, not a proof of graph isomorphism. Family names,
    labels, seeds, camera and detail are deliberately excluded.
    """
    nodes=candidate['nodes'];by={n['id']:n for n in nodes};neighbors={key:[] for key in by}
    for e in candidate['edges']:
        neighbors[e['from']].append((e['to'],e['kind']));neighbors[e['to']].append((e['from'],e['kind']))
    colors={key:content_hash([by[key]['role'] if semantic else by[key].get('entity','space'),by[key].get('program') if semantic else None,by[key]['level'],len(neighbors[key])]) for key in by}
    for _ in range(min(6,len(nodes))):
        colors={key:content_hash([colors[key],sorted((kind,colors[other]) for other,kind in neighbors[key])]) for key in by}
    # Rotation and translation disappear under distances; scale differences are
    # normalized, so uniformly enlarging the same recipe does not count as novelty.
    pairs=[(_dist(a['center'],b['center']),tuple(sorted((colors[a['id']],colors[b['id']]))))
           for i,a in enumerate(nodes) for b in nodes[i+1:]]
    scale=max((d for d,_ in pairs),default=1) or 1
    distance_hist={}
    for distance,labels in pairs:
        key=(labels,int(round(distance/scale*8)))
        distance_hist[key]=distance_hist.get(key,0)+1
    signature={'domain':candidate.get('domain','building'),'colors':sorted(colors.values()),'distances':sorted((list(labels),bucket,count) for (labels,bucket),count in distance_hist.items())}
    return content_hash(signature)

def _layout(family,n):
    if n==1:return [[0.,0.,0.]],[]
    if family=='hub':
        centers=[[0.,0.,0.]]+[[3*math.cos(2*math.pi*j/(n-1)),3*math.sin(2*math.pi*j/(n-1)),0.] for j in range(n-1)]
        links=[(0,j) for j in range(1,n)]
    elif family=='ring':
        centers=[[3*math.cos(2*math.pi*j/n),3*math.sin(2*math.pi*j/n),0.] for j in range(n)]
        links=[(j,(j+1)%n) for j in range(n)]
    elif family=='branched' and n==5:
        centers=[[0.,0.,0.],[3.,0.,0.],[-3.,0.,0.],[3.,3.,0.],[6.,0.,0.]]
        links=[(0,1),(0,2),(1,3),(1,4)]
    elif family=='branched':
        centers=[[0.,0.,0.]]
        for j in range(1,n):
            depth=int(math.log2(j+1));offset=j-(2**depth-1)
            centers.append([(offset-(2**depth-1)/2)*3,depth*2.,0.])
        links=[((j-1)//2,j) for j in range(1,n)]
    else:
        centers=[[j*3.,0.,0.] for j in range(n)];links=[(j,j+1) for j in range(n-1)]
    return centers,links

def generate_candidates(intent,seed=None,count=4):
    intent=_intent(intent)
    if type(count) is not int or not 3<=count<=5: raise ValueError('explore 3..5 candidates')
    streams=seed_streams(seed);rng=random.Random(streams['design'])
    levels=intent.constraints.get('levels',intent.choices.get('levels',1))
    if type(levels) is not int or not 1<=levels<=30: raise ValueError('chosen levels must be integer 1..30')
    grammar=DOMAINS[intent.domain]
    zones=intent.choices.get('component_count',intent.choices.get('zones_per_level',max(grammar['default_count'],len(intent.program_roles)+(1 if grammar['has_circulation'] else 0))))
    if type(zones) is not int or not 1<=zones<=30: raise ValueError('component/zone count must be integer 1..30')
    if intent.domain!='building' and levels!=1:raise ValueError('multilevel grammar is currently implemented for building domain only')
    assignment=intent.choices.get('program_assignment','level')
    if assignment not in ('level','zone'):raise ValueError('program_assignment must be level or zone')
    families=list(intent.choices.get('layout_families',FAMILIES))
    if len(set(families))<count or any(f not in FAMILIES for f in families): raise ValueError('provide enough distinct supported layout families')
    rng.shuffle(families)
    fixed=intent.constraints.get('layout_family')
    if fixed:
        if fixed not in families:raise ValueError('requested layout family is unavailable under current choices')
        families.remove(fixed);families.insert(0,fixed)
    result=[]
    for index,family in enumerate(families[:count]):
        centers,links=_layout(family,zones);nodes=[];edges=[]
        for level in range(levels):
            role=intent.program_roles[level%len(intent.program_roles)]
            for j,pos in enumerate(centers):
                center=[pos[0]+(level*1.5 if family=='stepped' else 0),pos[1],level*3.5]
                core=grammar['has_circulation'] and zones>1 and j==0
                zone_role='circulation' if core else role if j in (1,2) else 'service' if j==3 else 'support'
                program='circulation' if core else role
                if assignment=='zone':
                    program='circulation' if core else intent.program_roles[(j-1 if grammar['has_circulation'] else j)%len(intent.program_roles)]
                    zone_role='circulation' if core else program
                if not grammar['has_circulation']:
                    program=intent.program_roles[j%len(intent.program_roles)];zone_role=program
                nodes.append({'id':f'L{level}Z{j}','level':level,'role':zone_role,'program':program,'entity':grammar['entity'],'center':center,'extent':list(grammar['extent'])})
            for a,b in links:
                if not any(e['from']==f'L{level}Z{b}' and e['to']==f'L{level}Z{a}' for e in edges):
                    edges.append({'from':f'L{level}Z{a}','to':f'L{level}Z{b}','kind':grammar['relation'],'requires':list(grammar['requires'])})
            if level:
                edges.append({'from':f'L{level-1}Z0','to':f'L{level}Z0','kind':'vertical_access','requires':['supported_flight','landing','headroom','opening']})
        candidate={'version':VERSION,'id':f'candidate-{index+1}','intent_hash':intent.fingerprint,'family':family,
            'levels':levels,'domain':intent.domain,'features':list(intent.features),'nodes':nodes,'edges':edges,'seeds':streams.copy(),
            'capability':capability(intent.domain,family,intent.features,intent.choices.get('materializer'),levels,zones),
            'camera_seed':int.from_bytes(hashlib.sha256(f'{streams["camera"]}:{family}'.encode()).digest()[:8],'big'),
            'detail_seed':int.from_bytes(hashlib.sha256(f'{streams["detail"]}:{family}'.encode()).digest()[:8],'big'),
            'assumptions':['Conceptual zones and adjacency only; dimensions are relative layout units.',
                           'Every edge still requires realized geometry and connection validation.'],
            'geometry_status':'not_built'}
        candidate['fingerprint']=fingerprint(candidate);result.append(candidate)
    return result

def hard_errors(intent,candidate):
    intent=_intent(intent);errors=[];c=intent.constraints
    if candidate.get('intent_hash')!=intent.fingerprint:errors.append('intent mismatch')
    nodes=candidate.get('nodes',[]);edges=candidate.get('edges',[])
    ids=[n.get('id') for n in nodes]
    if not nodes or len(set(ids))!=len(ids):return errors+['missing or duplicate node IDs']
    by={n['id']:n for n in nodes};levels={n['level'] for n in nodes}
    requested_count=intent.choices.get('component_count',intent.choices.get('zones_per_level',max(DOMAINS[intent.domain]['default_count'],len(intent.program_roles)+(1 if DOMAINS[intent.domain]['has_circulation'] else 0))))
    expected_capability=capability(intent.domain,candidate.get('family',''),candidate.get('features',[]),intent.choices.get('materializer'),candidate.get('levels',1),requested_count)
    if candidate.get('capability')!=expected_capability:errors.append('materialization capability differs from registered adapter')
    if levels!=set(range(candidate.get('levels',0))):errors.append('level inventory is not continuous')
    if 'levels' in c and candidate.get('levels')!=c['levels']:errors.append('user level count changed')
    graph={key:set() for key in by}
    for edge in edges:
        a,b=edge.get('from'),edge.get('to')
        if a not in by or b not in by or a==b:errors.append('invalid edge endpoint');continue
        graph[a].add(b);graph[b].add(a)
        delta=abs(by[a]['level']-by[b]['level'])
        if delta and (edge.get('kind')!='vertical_access' or delta!=1):errors.append('invalid vertical adjacency')
    seen=set();pending=[ids[0]]
    while pending:
        key=pending.pop()
        if key not in seen:seen.add(key);pending.extend(graph[key]-seen)
    if c.get('connected',True) and len(seen)!=len(nodes):errors.append('disconnected circulation graph')
    if c.get('closed_loop') and any(len(v)<2 for v in graph.values()):errors.append('closed loop required; dangling node present')
    if candidate.get('domain','building')!=intent.domain:errors.append('domain mismatch')
    if intent.choices.get('require_materializable') and candidate.get('capability',{}).get('status')!='supported':errors.append('unsupported materialization capability')
    roles={n['role'] for n in nodes}|{n.get('program') for n in nodes}
    for role in c.get('required_roles',[]):
        if role not in roles:errors.append('required role absent: '+role)
    for role in c.get('forbidden_roles',[]):
        if role in roles:errors.append('forbidden role: '+role)
    features=set(candidate.get('features',[]))
    for name in c.get('required_features',[]):
        if name not in features:errors.append('required feature absent: '+name)
    for name in c.get('forbidden_features',[]):
        if name in features:errors.append('forbidden feature: '+name)
    if c.get('layout_family') and candidate.get('family')!=c['layout_family']:errors.append('user layout family changed')
    for node in nodes:
        center=node.get('center');extent=node.get('extent')
        if not isinstance(center,list) or len(center)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) for v in center):errors.append('invalid zone center')
        if not isinstance(extent,list) or len(extent)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in extent):errors.append('invalid zone extent')
    return errors

def _descriptors(candidate):
    """Rotation/translation/scale invariant, separately inspectable dimensions."""
    nodes=candidate['nodes'];size=max(1,len(nodes));degree={n['id']:0 for n in nodes}
    for e in candidate['edges']:degree[e['from']]+=1;degree[e['to']]+=1
    degree_hist=[sum(d==i for d in degree.values())/size for i in range(6)]
    degree_hist.append(sum(d>=6 for d in degree.values())/size)
    pairs=sorted(math.dist(a['center'],b['center']) for i,a in enumerate(nodes) for b in nodes[i+1:])
    maximum=max(pairs,default=1) or 1
    quantiles=[pairs[round((len(pairs)-1)*q)]/maximum if pairs else 0 for q in (0,.25,.5,.75,1)]
    programs={}
    for n in nodes:programs[n.get('program',n['role'])]=programs.get(n.get('program',n['role']),0)+1/size
    # Program adjacency distinguishes assignment from merely listing the inventory.
    by={n['id']:n for n in nodes};adj={}
    for e in candidate['edges']:
        k='|'.join(sorted((by[e['from']].get('program',''),by[e['to']].get('program',''))))
        adj[k]=adj.get(k,0)+1/max(1,len(candidate['edges']))
    elevations=[n['center'][2] for n in nodes];span=max(elevations)-min(elevations)
    return {'organization':degree_hist+[max(0,len(candidate['edges'])-size+1)/size],
            'program':programs,'program_adjacency':adj,'silhouette':quantiles,
            'section':[candidate['levels']/30,span/maximum],
            'view':{'excluded_from_design_novelty':True}}

def _descriptor_distance(a,b):
    components={}
    for key in ('organization','silhouette','section'):
        components[key]=math.dist(a[key],b[key])/math.sqrt(len(a[key]))
    components['program']=math.fsum(abs(a['program'].get(k,0)-b['program'].get(k,0)) for k in sorted(set(a['program'])|set(b['program'])))/2
    components['program_adjacency']=math.fsum(abs(a['program_adjacency'].get(k,0)-b['program_adjacency'].get(k,0)) for k in sorted(set(a['program_adjacency'])|set(b['program_adjacency'])))/2
    return sum(components.values())/len(components),components

def evaluate_candidates(intent,candidates,prior_fingerprints=()):
    intent=_intent(intent);result=[];valid=[];prior=set(prior_fingerprints)
    if len({c.get('id') for c in candidates})!=len(candidates):raise ValueError('duplicate candidate IDs')
    for candidate in candidates:
        errors=hard_errors(intent,candidate)
        report={'id':candidate.get('id'),'valid':not errors,'hard_errors':errors,'geometry_status':'not_built',
                'capability':copy.deepcopy(candidate.get('capability',{'status':'unsupported'}))}
        if not errors:
            fp=fingerprint(candidate);desc=_descriptors(candidate)
            graph={n['id']:set() for n in candidate['nodes']}
            for e in candidate['edges']:graph[e['from']].add(e['to']);graph[e['to']].add(e['from'])
            total=0;count=0
            for start in graph:
                distance={start:0};queue=[start]
                for key in queue:
                    for other in sorted(graph[key]):
                        if other not in distance:distance[other]=distance[key]+1;queue.append(other)
                total+=sum(distance.values());count+=len(distance)-1
            # Feasibility and program coverage are explicit; compactness is not
            # assumed desirable. A requested travel preference is separately named.
            quality=1. if intent.choices.get('quality_objective')!='shortest_travel' else 1/(1+total/max(count,1))
            report.update(fingerprint=fp,structural_fingerprint=fingerprint(candidate,semantic=False),
                          quality=quality,mean_adjacency_hops=total/max(count,1),descriptors=desc,
                          quality_basis='explicit shortest_travel preference' if intent.choices.get('quality_objective')=='shortest_travel' else 'verified planning requirements')
            valid.append(report)
        result.append(report)
    # Every valid candidate is measured against the complete valid set. Duplicate
    # equivalence classes have a stable representative independent of input order.
    groups={}
    for r in valid:groups.setdefault(r['fingerprint'],[]).append(r)
    for fp,group in groups.items():
        representative=min(group,key=lambda r:r['id'])
        neighbors=[r for r in valid if r['fingerprint']!=fp]
        distances=[_descriptor_distance(representative['descriptors'],r['descriptors'])[0] for r in neighbors]
        novelty=min(distances,default=1.)
        for r in group:
            duplicate=fp in prior or r is not representative
            r.update(duplicate=duplicate,novelty=novelty,
                     internal_diversity=novelty,history_novelty='exact_repeat' if fp in prior else 'no_exact_repeat',
                     diversity_neighbors=sorted(set(n['fingerprint'] for n in neighbors)))
    return result

def choose_candidate(intent,candidates,prior_fingerprints=()):
    intent=_intent(intent)
    reports=evaluate_candidates(intent,candidates,prior_fingerprints)
    feasible=[r for r in reports if r['valid'] and not r['duplicate']]
    if not feasible:raise ValueError('no feasible distinct design; unsupported capabilities or constraints require a new adapter/design')
    frontier=[r for r in feasible if not any(other['quality']>=r['quality'] and other['novelty']>=r['novelty'] and
                (other['quality']>r['quality'] or other['novelty']>r['novelty']) for other in feasible)]
    # Diversity describes the candidate set, not a universal preference for its
    # most isolated member. With equal functional quality, keep every distinct
    # feasible organization eligible unless maximum novelty was explicitly asked.
    best_quality=max(r['quality'] for r in feasible)
    eligible=[r for r in feasible if r['quality']==best_quality]
    novelty_objective=intent.choices.get('novelty_objective')
    if novelty_objective not in (None,'maximize'):raise ValueError('unsupported novelty objective')
    policy='quality_then_seeded_content'
    if novelty_objective=='maximize':
        best_novelty=max(r['novelty'] for r in eligible)
        eligible=[r for r in eligible if r['novelty']==best_novelty]
        policy='quality_then_explicit_max_novelty'
    streams={c['seeds']['design'] for c in candidates}
    if len(streams)!=1:raise ValueError('candidate design seed streams must agree')
    stream=next(iter(streams))
    selected=min(eligible,key=lambda r:content_hash([VERSION,stream,r['fingerprint']]))
    candidate=next(copy.deepcopy(c) for c in candidates if c['id']==selected['id'])
    evidence={'version':VERSION,'descriptor_version':'domain-separated-1','intent_hash':_intent(intent).fingerprint,
              'candidate_hashes':{c['id']:content_hash(c) for c in candidates},
              'candidates':copy.deepcopy(candidates),'prior_fingerprints':sorted(set(prior_fingerprints)),
              'selected_id':candidate['id'],'reports':reports,'pareto_ids':sorted(r['id'] for r in frontier),
              'eligible_ids':sorted(r['id'] for r in eligible),'selection_policy':policy,
              'limits':'Graph feasibility and coarse diversity only. Realize openings/supports/clearance and review geometry before freezing.'}
    return candidate,evidence

def verify_selection(intent,candidates,evidence):
    """Recompute selection evidence; never treat a claimed 'valid' flag as proof."""
    if not isinstance(evidence,dict):raise ValueError('selection evidence must be an object')
    if evidence.get('candidates')!=candidates:raise ValueError('candidate snapshot differs')
    if len({c.get('id') for c in candidates})!=len(candidates):raise ValueError('duplicate candidate IDs')
    selected,expected=choose_candidate(intent,candidates,evidence.get('prior_fingerprints',[]))
    if canonical(expected)!=canonical(evidence):raise ValueError('selection evidence changed or is stale')
    return selected

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--intent',type=Path,required=True)
    parser.add_argument('--out-dir',type=Path,required=True);parser.add_argument('--seed',type=int);parser.add_argument('--count',type=int,default=4)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1];out=args.out_dir.resolve()
    if out==root or root in out.parents:raise ValueError('trial evidence belongs outside the installed skill')
    intent=DesignIntent.from_data(json.loads(args.intent.read_text(encoding='utf-8-sig')))
    candidates=generate_candidates(intent,args.seed,args.count);selected,evidence=choose_candidate(intent,candidates)
    out.mkdir(parents=True,exist_ok=False)
    for name,data in [('intent',intent.to_data()),('candidates',candidates),('selected',selected),('selection-evidence',evidence)]:
        (out/(name+'.json')).write_text(json.dumps(data,indent=2),encoding='utf-8')
    print(json.dumps({'selected':selected['id'],'family':selected['family'],'root_seed':selected['seeds']['root'],'evidence':str(out/'selection-evidence.json')}))

if __name__=='__main__':main()
