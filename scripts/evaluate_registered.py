"""Execute balanced staged regressions; never convert them into an art score."""
import argparse,copy,hashlib,json
from pathlib import Path
from collections import Counter
import numpy as np
from evaluation_fixtures import CASES,load,mutate,material_scene
from scene_model import validate,validation_report
from render_scene import build,Renderer
from assembly_model import compile_cutaway,compose_assembly,RigidTransform

ROOT=Path(__file__).resolve().parents[1]
VERSION='registered-evaluation-1'

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def physical_identity(scene):
    return digest({k:v for k,v in scene.items() if k not in {'camera','light_material_plan','visual_plan','context_plan','detail_budget','callouts'}})

def render(scene,width=320,height=240,style_seed=0):
    display=compile_cutaway(scene,hide_ids=scene['display_hidden']) if scene.get('display_hidden') else scene
    mesh=build(display)
    camera=dict(scene.get('camera',{}))
    for key in ('width','height','finish','shadows','style_seed'):camera.pop(key,None)
    for old,new in (('eye','camera_eye'),('target','camera_target')):
        if old in camera:camera[new]=camera.pop(old)
    if 'camera_eye' in camera:camera.setdefault('projection','perspective')
    renderer=Renderer(mesh,width,height,finish='graphite',shadows=True,style_seed=style_seed,**camera)
    rgb=np.asarray(renderer.draw(mesh))
    return renderer,rgb

def guide_observation(scene,target,width=320,height=240):
    r,rgb=render(scene,width,height);pid=r.part_ids.get(target)
    pixels=int(np.count_nonzero(r.owner==pid)) if pid is not None else 0
    return {'status':'observed' if pixels else 'target_occluded','size':[width,height],
        'target':target,'owned_pixels':pixels,'rgb_sha256':hashlib.sha256(rgb.tobytes()).hexdigest(),
        'visible_component_count':len(set(np.unique(r.owner))-{0}),
        'scope':'Calculated ownership observation only; not a full view-contract or recognition pass.'}

def rejection_errors(scene,kind):
    if kind=='extra_context':
        from visual_contract import errors
        return errors(scene)
    if kind=='label_target':
        from annotation_plan import create
        r,_=render(scene,400,300)
        try:create(scene,r)
        except ValueError as exc:return [str(exc)]
        return []
    return validate(scene)

def rule_observation(case,scene):
    if case['domain']=='cross-domain':
        return {'status':'not_applicable','scope':'A cross-domain material/contact fixture has no invented subject planning domain; physical contracts are exercised below.'}
    from design_intent import DesignIntent
    from design_variants import generate_candidates,choose_candidate,verify_selection
    if scene.get('design_selection'):
        intent=DesignIntent.from_data(scene['design_intent']);evidence=scene['design_selection']
        selected=verify_selection(intent,evidence['candidates'],evidence)
    else:
        choices={'zones_per_level':2} if case['domain']=='building' else {'component_count':2}
        intent=DesignIntent.from_data({'domain':case['domain'],'subject':case['name'],'choices':choices,'program_roles':['primary','service']})
        candidates=generate_candidates(intent,52,3);selected,evidence=choose_candidate(intent,candidates)
        verify_selection(intent,candidates,evidence)
    return {'status':'passed','intent_sha256':intent.fingerprint,'entity_kinds':sorted({n['entity'] for n in selected['nodes']}),
        'relation_kinds':sorted({e['kind'] for e in selected['edges']}),'materialization_capability':selected['capability'],
        'scope':'Domain grammar and selection recomputed; component-fixture validity below cannot upgrade complete-subject capability.'}

def run_case(case,with_guide=True):
    scene=load(case['fixture']);before=digest(scene);errors=validate(scene);report=validation_report(scene)
    bad=mutate(scene,case['negative']);negative_errors=rejection_errors(bad,case['negative'])
    if digest(scene)!=before:raise AssertionError('evaluation mutation changed baseline')
    result={**case,'physical_sha256':physical_identity(scene),
        'rules':rule_observation(case,scene),
        'geometry':{'validation_errors':errors,'coverage_status':report['status'],
            'baseline_expected_valid':not errors,'scope':case['scope']},
        'negative':{'mutation':case['negative'],'status':'rejected' if negative_errors else 'missed','errors':negative_errors},
        'guide':guide_observation(scene,case['target']) if with_guide else {'status':'not_run'},
        'finished_pixels':{'status':'not_run','reason':'No image model or final-image observer invoked by this regression runner.'}}
    result['regression_status']='passed' if not errors and negative_errors and result['guide']['status']!='target_occluded' else 'failed'
    return result

def ablations():
    """Separate physical identity, display omission and fill-only changes."""
    base=material_scene();identity=physical_identity(base);renderer,rgb=render(base,400,300)
    variants=[]
    for name in ('material_off','opposite_light','context_off','detail_off','style_seed'):
        scene=copy.deepcopy(base);seed=0;omitted=[]
        if name=='material_off':scene['light_material_plan']['materials']['body'].update(family='matte_metal',density=0)
        if name=='opposite_light':scene['light_material_plan']['key_direction']=[.6,-.8,1.5]
        if name=='context_off':omitted=['context']
        if name=='detail_off':omitted=['detail']
        if name=='style_seed':seed=17
        fixed=physical_identity(scene)==identity;physical_errors=validate(scene)
        display=copy.deepcopy(scene)
        if omitted:
            display=compile_cutaway(scene,hide_ids=omitted)
            # Physical identity is checked before this declared view-only cut.
        r,image=render(display,400,300,seed)
        same_depth=np.array_equal(renderer.z,r.z);same_ownership=np.array_equal(renderer.owner,r.owner)
        fill_only=not omitted
        changes=int(np.count_nonzero(np.any(rgb!=image,axis=2)))
        passed=fixed and not physical_errors and changes>0 and (not fill_only or (same_depth and same_ownership))
        variants.append({'variant':name,'physical_sha256':identity,'physical_geometry_unchanged':fixed,
            'physical_errors':physical_errors,'display_omissions':omitted,'changed_pixels':changes,
            'depth_unchanged':same_depth,'ownership_unchanged':same_ownership,
            'status':'passed' if passed else 'failed','visual_preference':'not_observed'})
    # A real pumping fixture, not a cube renamed as a night plant.
    plant=load('plant');night=copy.deepcopy(plant)
    plant['light_material_plan']={'ambient':.78,'key_strength':.22,'value_policy':'open_air'}
    night['light_material_plan']={'ambient':.28,'key_strength':.65,'value_policy':'dark_interior','key_direction':[1,-1,1]}
    a,ia=render(plant);b,ib=render(night)
    changed=int(np.count_nonzero(np.any(ia!=ib,axis=2)))
    variants.append({'variant':'same_pump_plant_night','physical_geometry_unchanged':physical_identity(plant)==physical_identity(night),
        'depth_unchanged':np.array_equal(a.z,b.z),'ownership_unchanged':np.array_equal(a.owner,b.owner),
        'changed_pixels':changed,'status':'passed' if changed and np.array_equal(a.z,b.z) and np.array_equal(a.owner,b.owner) else 'failed',
        'visual_preference':'not_observed','geometry_coverage':validation_report(plant)['status']})
    return variants

def properties():
    scene=material_scene();scene.pop('light_material_plan');scene.pop('callouts')
    renamed=compose_assembly(scene,prefix='renamed/')
    # This fixture uses the legacy z=0 ground datum, so its admissible rigid
    # transform preserves that datum. Explicit moved terrain is tested elsewhere.
    moved=compose_assembly(scene,RigidTransform((8,-4,0)))
    original=np.array([p['origin'] for p in scene['parts']]);translated=np.array([p['origin'] for p in moved['parts']])
    return {'id_renaming_preserves_validity':not validate(renamed),
        'rigid_translation_preserves_validity':not validate(moved),
        'rigid_translation_preserves_relative_positions':bool(np.allclose(translated-original,[8,-4,0])),
        'source_unchanged':scene==material_scene_without_style()}

def material_scene_without_style():
    scene=material_scene();scene.pop('light_material_plan');scene.pop('callouts');return scene

def run(case_ids=None,with_guides=True,with_ablations=True,progress=None):
    known={c['id'] for c in CASES};wanted=known if case_ids is None else set(case_ids)
    if not wanted or not wanted<=known:raise ValueError('choose known nonempty case IDs')
    source_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ('evaluate_registered.py','evaluation_fixtures.py')}
    rows=[]
    for case in CASES:
        if case['id'] not in wanted:continue
        if progress:progress(case['id'],'running')
        rows.append(run_case(case,with_guides))
        if progress:progress(case['id'],rows[-1]['regression_status'])
    variations=ablations() if with_ablations else []
    invariants=properties()
    failed=sum(r['regression_status']=='failed' for r in rows)
    return {'version':VERSION,'cases':rows,'balance':dict(Counter(r['domain'] for r in rows)),
        'ablations':variations,'properties':invariants,
        'critical_failure_rate':failed/len(rows),'negative_mutation_misses':sum(r['negative']['status']=='missed' for r in rows),
        'physical_coverage_counts':dict(Counter(r['geometry']['coverage_status'] for r in rows)),
        'partial_geometry_case_count':sum(r['geometry']['coverage_status']!='passed' for r in rows),
        'visual_preference':{'status':'not_observed','score':None},
        'status':'passed' if not failed and all(x['status']=='passed' for x in variations) and all(invariants.values()) else 'failed',
        'scope':'Passed means staged regression expectations passed; partial legacy coverage and unsupported complete subjects remain explicit. No final artistic claim.',
        'source_hashes':source_hashes}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--case',action='append',choices=[c['id'] for c in CASES]);parser.add_argument('--output',type=Path)
    parser.add_argument('--no-guides',action='store_true');parser.add_argument('--no-ablations',action='store_true')
    args=parser.parse_args();result=run(args.case,not args.no_guides,not args.no_ablations,lambda case,status:print(case+': '+status,flush=True))
    if args.output:
        output=args.output.resolve()
        if output==ROOT or ROOT in output.parents:raise ValueError('evaluation evidence must stay outside package')
        if output.exists():raise FileExistsError('evaluation output already exists')
        output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('cases','source_hashes')},indent=2))
    if result['status']!='passed':raise SystemExit(1)

if __name__=='__main__':main()
