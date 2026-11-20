"""Portable exterior district composer. Does not model hidden building interiors.

Fresh seeds choose spatial organization and tiered envelopes. The guide preserves
facade rhythm, roof equipment, streets and depth; ImageGen supplies listed surface
refinement. No private images, paths, historical prompts or fixed camera required.
"""
import argparse
import json
import random
import secrets
from pathlib import Path
from scene_model import make_part, validate
from annotation_policy import configure
from exterior_environment import LIMITS, errors as scope_errors


def scene(seed=None, family=None, annotations=False, camera=None):
    seed = secrets.randbits(32) if seed is None else seed
    rng = random.Random(seed)
    family = family or rng.choice(['avenue','staggered','courtyard'])
    if family not in ('avenue','staggered','courtyard'): raise ValueError('unknown district organization')
    s = dict(units='m',schema_version=2,workflow_version=3,validation_policy='strict',registered_geometry=True,
             parts=[],bearings=[],grounded=['site'],detail_regions=[],callouts=[])
    roles={};envelopes=[];roads=[]
    def add(key,kind,o,size,role,on=None,**kwargs):
        s['parts'].append(make_part(key,kind,o,size,**kwargs));roles[key]=role
        if on:s['bearings'].append(dict(part=key,on=on))
        return key
    add('site','slab',[-200,-45,-1],[1100,1400,1],'terrain')
    # Roads split at junctions: no overlap exemptions. All form one coplanar graph.
    xs=[-65,-15,35,85,135,185,235,285];ys=[12,62,112,162,212,262,312,352]
    for j,y in enumerate(ys):
        roads.append(add('cross-'+str(j),'paving',[xs[0],y,0],[xs[-1]-xs[0]+6,6,.12],'street','site'))
    for i,x in enumerate(xs):
        for j in range(len(ys)-1):
            roads.append(add(f'avenue-{i}-{j}','paving',[x,ys[j]+6,0],[6,ys[j+1]-ys[j]-6,.12],'street','site'))
    def tower(key,x,y,w,d,h,tiers=1):
        base=add(key+'-base','slab',[x,y,0],[w,d,.5],'roof','site')
        z=.5;below=base;layers=[]
        for level in range(tiers):
            hh=h/tiers
            body=add(f'{key}-body-{level}','wall',[x,y,z],[w,d,hh],'envelope',below,
                     parameters={'panel_size':[rng.choice([2.,2.5,3.]),3.3],'panel_faces':'all'},
                     semantic_role='exterior building envelope')
            envelopes.append(body);z+=hh
            roof=add(f'{key}-roof-{level}','slab',[x,y,z],[w,d,.35],'roof',body)
            z+=.35;below=roof;layers.append((body,roof))
            x+=2.5;y+=2.5;w-=5;d-=5
        o=next(p for p in s['parts'] if p['id']==below)['origin']
        add(key+'-penthouse','cabinet',[o[0]+2,o[1]+2,z],[4,4,2.5],'roof_equipment',below,
            semantic_role='mechanical penthouse with louvered service enclosure')
        return layers
    # Observation roof belongs to an exterior envelope; its unseen rooms are not invented.
    fg=tower('observation',18,-20,32,28,75)
    roof=fg[0][1];rz=75.85
    add('roof-edge','wall',[18,7.7,rz],[32,.3,1.1],'edge_protection',roof)
    add('roof-equipment','cabinet',[28,1,rz],[6,4,2.5],'roof_equipment',roof,semantic_role='rooftop ventilation plant on supported casing')
    add('garden-bed','slab',[40,1,rz],[8,6,.55],'landscape',roof,semantic_role='raised rooftop garden bed')
    from context_geometry import add_tree
    for i in range(3):
        key='roof-tree-'+str(i);add_tree(s,key,'garden-bed',[40.2+2.4*i,2],[2.2,3,3.8],seed=seed+i);roles[key]='landscape'
    towers=[]
    for row in range(6):
        for col in range(6):
            # A visible civic void and different parcel omissions change topology,
            # not merely camera or component names.
            if (row,col) in {(0,2),(1,2)}:continue
            if family=='courtyard' and (row,col) in {(2,2),(2,3),(3,2),(3,3)}:continue
            if family=='staggered' and (row+col)%5==0:continue
            x=xs[col]+10+rng.uniform(0,4);y=ys[row]+11+rng.uniform(0,4)
            w=rng.uniform(24,31);d=rng.uniform(23,30);h=rng.uniform(35,95)
            if row<2:h=min(h,67)
            tiers=rng.choice([1,2,3]);towers.append(tower(f'tower-{row}-{col}',x,y,w,d,h,tiers))
    for row in range(2):
        for col in range(10):
            towers.append(tower(f'distant-{row}-{col}',-160+col*100+rng.uniform(0,15),
                420+row*380+rng.uniform(0,80),rng.uniform(25,48),rng.uniform(25,40),rng.uniform(50,130),1))
    plaza=add('plaza','slab',[47,23,0],[30,36,.12],'plaza','site',semantic_role='public plaza connected to avenue')
    for i in range(3):
        key='plaza-tree-'+str(i);add_tree(s,key,plaza,[49+i*9,53],[3,3,6],seed=seed+10+i);roles[key]='landscape'
    # Fixed semantic landmark with genuinely receding tiers, independently of random towers.
    steps=tower('terraced',48,74,30,28,48,3)
    add('terrace-garden','slab',[48.1,76,16.85],[2.2,8,.45],'landscape',steps[0][1],semantic_role='raised rooftop garden on stepped terrace')
    for i in range(2):
        key='terrace-tree-'+str(i);add_tree(s,key,'terrace-garden',[48.25,76.5+i*4],[1.8,2,3],seed=seed+20+i);roles[key]='landscape'
    camera=camera or {'projection':'perspective','camera_eye':[30,7.5,79],
                     'camera_target':[70,130,18], 'fov':76}
    s['camera']=camera
    focal=['terraced-penthouse','terrace-garden',steps[0][1],plaza,'avenue-2-0']
    region_specs=[('roof assemblies',[steps[-1][1]],['terraced-penthouse','terrace-garden'],['parapet caps and joints','cabinet vents, bases and fasteners','planted beds and paving joints']),
                  ('district facade rhythm',[steps[-1][0]],[steps[0][1],steps[1][1]],['floor bands aligned around corners','window bays and mullions','setback parapets and terrace paving']),
                  ('public ground',[plaza],['avenue-2-0','plaza-tree-0'],['crosswalks within existing streets','plaza paving and seat edges','receding curb lines and street furniture'])]
    for name,primary,secondary,micro in region_specs:
        s['detail_regions'].append(dict(name=name,primary=primary,secondary=secondary,microdetails=micro))
    s['visual_plan']={'objective':'A broad city from an observation roof, varied silhouettes, visible streets and terraces, depth to a distant skyline',
        'view_intent':'exterior','primary':[steps[-1][0]],'secondary':['roof-equipment'],
        'readable':focal,'layers':[dict(name='foreground',ids=[roof],role='observer location'),
            dict(name='district',ids=[a[-1][0] for a in towers[:8]],role='main architectural variety'),
            dict(name='distance',ids=[a[-1][0] for a in towers[-6:]],role='city continuation')],
        'usage_size':[1536,1024]}
    s['context_plan']={'mode':'landscape','max_entities':20,'entities':[], 'protected_ids':[]}
    s['detail_budget']={'regions':s['detail_regions'],'usage_size':[1536,1024]}
    s['light_material_plan']={'value_policy':'open_air','materials':{},'line_weights':[1.8,1,.55]}
    s['exterior_environment']={'version':1,'mode':'urban_exterior','seed':seed,'selected':family,
        'alternatives':[dict(id='avenue',organization='continuous avenue and civic opening',reason='long street sightline'),
                        dict(id='staggered',organization='offset occupied parcels with distributed voids',reason='varied roof exposure'),
                        dict(id='courtyard',organization='perimeter groups around a larger civic void',reason='visible shared public space')],
        'envelopes':envelopes,'roads':roads,'roles':roles,'focal':focal,'unverified':list(LIMITS)}
    if annotations:
        s['callouts']=[dict(id='note-'+str(i),target=k,text=text) for i,(k,text) in enumerate(zip(focal,
            ['MECHANICAL PENTHOUSE','ROOFTOP GARDEN','STEPPED TERRACES','PUBLIC PLAZA','MAIN AVENUE']))]
    s=configure(s,requested=annotations,request_excerpt='five English annotations' if annotations else '')
    issues=validate(s)+scope_errors(s)
    if issues:raise ValueError('; '.join(issues))
    return s


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,default=Path.cwd());p.add_argument('--brief',type=Path,required=True)
    p.add_argument('--seed',type=int);p.add_argument('--family',choices=['avenue','staggered','courtyard'])
    p.add_argument('--camera',type=Path,help='Optional renderer camera JSON; actual visibility gates still apply')
    p.add_argument('--annotations',action='store_true');a=p.parse_args()
    from history_run import new_run
    from execution_history import save,preserve
    from render_scene import build,Renderer
    from view_contract import create
    from finish_contract import freeze,request
    run=new_run(a.project,'urban-exterior',a.brief.read_text(encoding='utf-8-sig'))
    print(str(run),flush=True)
    try:
        save(run/'01-site/execution-input.json',{'seed':a.seed,'family':a.family,'annotations':a.annotations,
             'scope':'urban_exterior','status':'planning; no generation or validation yet'})
        s=scene(a.seed,a.family,a.annotations,json.loads(a.camera.read_text(encoding='utf-8-sig')) if a.camera else None)
        save(run/'02-program/representation.json',{'domain':'environment','mode':'urban_exterior',
             'objective':s['visual_plan']['objective'],'focal':s['exterior_environment']['focal']})
        save(run/'03-massing/scene.json',s)
        save(run/'03-massing/scope.json',s['exterior_environment'])
        from scene_model import validation_report
        save(run/'04-structure/represented-geometry-checks.json',validation_report(s))
        save(run/'05-levels/coverage.json',{'mode':'exterior envelopes and supported setbacks',
             'occupied_floor_checks':'not_applicable: no interior/cutaway geometry requested or modeled',
             'unverified':s['exterior_environment']['unverified']})
        save(run/'06-systems/roof-assemblies.json',{'parts':[p['id'] for p in s['parts']
             if s['exterior_environment']['roles'][p['id']]=='roof_equipment'],
             'scope':'mounted exterior enclosures; internal services and operation unverified'})
        mesh=build(s);r=Renderer(mesh,1536,1024,hatching=False,**s['camera'])
        guide=run/'07-representation/guide.png';r.draw(mesh).save(guide)
        v=create(s,s,r,guide);save(run/'07-representation/view.json',v)
        lock=freeze(s,v)
        art=(Path(__file__).resolve().parents[1]/'references/art-direction.md').read_text(encoding='utf-8')
        prompt=request(lock,a.brief.read_text(encoding='utf-8-sig'),art)
        attempt=preserve(lock,run,guide,a.brief.read_text(encoding='utf-8-sig'),prompt,
                        sources=[Path(__file__),Path(__file__).with_name('exterior_environment.py')])
        print(json.dumps({'run':str(run),'attempt':str(attempt),'status':'prepared_not_generated','scope':'exterior only'}))
    except Exception as exc:
        save(run/'preparation-failed.json',{'error':str(exc)});raise


if __name__=='__main__':main()
