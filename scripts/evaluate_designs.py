"""Cross-domain design-graph matrix. Does not generate artwork or validate geometry."""
import argparse,copy,hashlib,json,math
from pathlib import Path
from design_intent import DesignIntent
from design_variants import generate_candidates,choose_candidate,fingerprint,verify_selection

VERSION='design-evaluation-2'
DEFAULT_SEEDS=(0,1,2,3)

def cases():
    """Program inventories are domain-specific; counts describe design strata only."""
    specifications=[
        ('bunker','sectioned mountain research bunker',6,
         ['utilities','storage','workshops','quarters','medical','command'],'level',['section']),
        ('urban','urban district organized around public space',1,
         ['building_blocks','public_space','street_network','services'],'zone',['site_context']),
        ('airship','scientific airship gondola interior',1,
         ['navigation','atmospheric_lab','maintenance','life_support'],'zone',['curved_enclosure']),
        ('waterplant','water treatment installation',1,
         ['treatment','pumping','service_access','controls'],'zone',['service_network']),
        ('winch','stationary winch maintenance assembly',1,
         ['drive','drum_support','brake','controls'],'zone',['mechanism']),
        ('observatory','mountain observatory complex',1,
         ['instrument','mount','maintenance','control_room'],'zone',['terrain_context'])]
    return [{'id':name,'intent':DesignIntent.from_data({
        'domain':{'bunker':'building','urban':'environment','airship':'vehicle','waterplant':'process','winch':'mechanism','observatory':'building'}[name],
        'subject':subject,'constraints':{'levels':levels,'connected':True,'required_roles':programs,'required_features':features},
        'program_roles':programs,'features':features,
        'choices':{'program_assignment':assignment,**({'zones_per_level':5} if name in ('bunker','observatory') else {'component_count':len(programs)})}}).to_data()}
        for name,subject,levels,programs,assignment,features in specifications]

def topology_signature(candidate):
    """Separate adjacency/program variation from metric spatial arrangement."""
    value=copy.deepcopy(candidate)
    for node in value['nodes']:node['center']=[0.,0.,0.]
    return fingerprint(value)

def camera_only_duplicate_check(candidate):
    changed=copy.deepcopy(candidate);changed['id']='another-label'
    changed['camera_seed']=changed.get('camera_seed',0)+1
    changed['detail_seed']=changed.get('detail_seed',0)+1
    theta=.08
    for node in changed['nodes']:
        x,y,z=node['center']
        node['center']=[x*math.cos(theta)-y*math.sin(theta)+11,x*math.sin(theta)+y*math.cos(theta)-7,z+2]
    return fingerprint(candidate)==fingerprint(changed)

def run_matrix(seeds=DEFAULT_SEEDS,count=4,case_specs=None):
    if not isinstance(seeds,(tuple,list)) or len(seeds)<2 or len(set(seeds))!=len(seeds):raise ValueError('use at least two distinct root seeds')
    domains=[]
    for spec in cases() if case_specs is None else case_specs:
        intent=DesignIntent.from_data(spec['intent']);runs=[]
        for seed in seeds:
            candidates=generate_candidates(intent,seed,count)
            selected,evidence=choose_candidate(intent,candidates)
            verified=verify_selection(intent,candidates,evidence)
            replay=generate_candidates(intent,seed,count);reselected,reevidence=choose_candidate(intent,replay)
            # Optional history is content-only fingerprints, no images or paths.
            alternatives,alt_evidence=choose_candidate(intent,candidates,[fingerprint(selected)])
            runs.append({'seed':seed,'family':selected['family'],'selected_fingerprint':fingerprint(selected),
                'topology_signature':topology_signature(selected),
                'valid_candidates':sum(r['valid'] for r in evidence['reports']),
                'distinct_candidates':len({r['fingerprint'] for r in evidence['reports'] if r['valid']}),
                'reproducible':candidates==replay and selected==reselected and evidence==reevidence,
                'selection_verified':verified==selected,
                'camera_only_duplicate_detected':camera_only_duplicate_check(selected),
                'prior_exact_fingerprint_excluded':fingerprint(alternatives)!=fingerprint(selected),
                'declared_levels':selected['levels'],'selected_node_count':len(selected['nodes']),
                'geometry_validation':'not_run','artistic_validation':'not_run',
                'materialization_capability':selected['capability'],
                'relation_kinds':sorted({e['kind'] for e in selected['edges']}),
                'evidence':evidence})
        distinct_topologies=len({r['topology_signature'] for r in runs})
        distinct_designs=len({r['selected_fingerprint'] for r in runs})
        gates={'all_candidates_satisfy_supported_intent_checks':all(r['valid_candidates']==count for r in runs),
               'reproducible':all(r['reproducible'] and r['selection_verified'] for r in runs),
               'at_least_two_selected_topologies':distinct_topologies>=2,
               'at_least_two_distinct_candidates_per_run':all(r['distinct_candidates']>=2 for r in runs),
               'camera_or_detail_change_not_counted_as_design_novelty':all(r['camera_only_duplicate_detected'] for r in runs),
               'prior_exact_repeats_can_be_excluded':all(r['prior_exact_fingerprint_excluded'] for r in runs)}
        domains.append({'id':spec['id'],'intent':intent.to_data(),'runs':runs,
                        'selected_design_count':distinct_designs,'selected_topology_count':distinct_topologies,
                        'acceptance':gates,'design_graph_status':'passed' if all(gates.values()) else 'needs_review'})
    return {'version':VERSION,'seeds':list(seeds),'candidates_per_run':count,'domains':domains,
            'design_graph_status':'passed' if all(d['design_graph_status']=='passed' for d in domains) else 'needs_review',
            'limits':['These are graph/planning probes, not finished or physically validated structures.',
                      'Required features and programs are declared inventory; their actual shapes still require realization.',
                      'No image model was called. No conclusion about visual detail, pipe joints, stairs, walls or loads follows.',
                      'Four seed trials are a regression sample, not a statistical diversity guarantee.']}

def materialization_requirements(selected):
    """Checklist for another validator, deliberately not a geometry pass flag."""
    return {'design_fingerprint':fingerprint(selected),
            'zone_ids':[n['id'] for n in selected['nodes']],
            'required_links':[{'from':e['from'],'to':e['to'],'kind':e['kind'],'requires':e.get('requires',[])} for e in selected['edges']],
            'status':'unverified_until_realized_geometry_checked'}

def run_bunker_materialization_matrix(seed=1,levels=6):
    """Exercise every declared complete bunker adapter with unchanged strict gates."""
    from build_bunker import build_scene
    from domain_grammar import BUNKER_FAMILIES
    from scene_model import validation_report
    from design_realization import realization_report
    rows=[]
    for family in BUNKER_FAMILIES:
        scene=build_scene(seed=seed,levels=levels,family=family)
        physical=validation_report(scene);realized=realization_report(scene)
        selected=verify_selection(scene['design_intent'],scene['design_selection']['candidates'],scene['design_selection'])
        rows.append({'family':family,'seed':seed,'levels':levels,'parts':len(scene['parts']),
            'fingerprint':fingerprint(selected),'topology_signature':topology_signature(selected),
            'physical_status':physical['status'],'realization_status':realized['status'],
            'physical_errors':[v for v in physical['checks'] if v['status'] in ('failed','unsupported') and v.get('critical',True)],
            'realization_errors':realized['errors'],'guide_review':'not_run','final_pixels':'not_run'})
    return {'version':VERSION,'families':rows,'status':'passed' if all(r['physical_status']==r['realization_status']=='passed' for r in rows) else 'failed',
            'distinct_topologies':len({r['topology_signature'] for r in rows}),
            'scope':'strict geometry and complete selected-graph realization; no structural certification or final-pixel claim'}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out-dir',type=Path,required=True)
    parser.add_argument('--seeds',type=int,nargs='+',default=list(DEFAULT_SEEDS));parser.add_argument('--count',type=int,default=4)
    args=parser.parse_args();out=args.out_dir.resolve();root=Path(__file__).resolve().parents[1]
    if out==root or root in out.parents:raise ValueError('evaluation evidence must stay outside the installed skill')
    if out.exists():raise FileExistsError('choose a new evidence directory')
    matrix=run_matrix(args.seeds,args.count)
    matrix['source_hashes']={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                             for name in ['design_intent.py','design_variants.py','evaluate_designs.py']}
    out.mkdir(parents=True)
    (out/'design-matrix.json').write_text(json.dumps(matrix,indent=2),encoding='utf-8')
    summary={k:v for k,v in matrix.items() if k!='domains'}
    summary['domains']=[{k:v for k,v in d.items() if k not in ('intent','runs')} for d in matrix['domains']]
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary))

if __name__=='__main__':main()
