"""Inspect alternate partial-section cameras; keep doors and roof evidence."""
import copy,json
import uuid
from pathlib import Path
from assembly_model import compile_cutaway
from render_scene import build,Renderer
from view_contract import create,errors
from architecture_stages import report
from visual_contract import compile_visual_contract

def candidates(scene,run):
    root=Path(run)/'07-representation'/('attempt-'+uuid.uuid4().hex[:12]);root.mkdir()
    hidden=[p['id'] for p in scene['parts'] if p['id'].startswith('machine-front/') and p['origin'][0]<3.3]
    hidden+=['workshop-front/cell-0','workshop-front/cell-1']
    hidden += [p['id'] for p in scene['parts'] if p['id'].startswith('machine-front/') and p['origin'][2]>=4.8]
    cuts=[dict(host=p['id'],axis='z',value=3.3,keep='lower') for p in scene['parts'] if p['id'].startswith('machine-front/') and p['id'] not in hidden and p['origin'][2]==3.0]
    cuts+=[dict(host='machine-roof',axis='y',value=8,keep='upper')]
    cuts+=[dict(host='workshop-roof',axis='x',value=8.5,keep='lower')]
    cuts+=[dict(host=k,axis='x',value=17.6,keep='upper') for k in ['workshop-front/cell-3','workshop-front/cell-4']]
    cuts+=[dict(host='boarding-roof',axis='y',value=-7.7,keep='lower')]
    outputs=[]
    for az,el in [(315,23),(300,28),(335,26)]:
        s=copy.deepcopy(scene);s['camera']=dict(azimuth=az,elevation=el,projection='orthographic')
        display=compile_cutaway(s,hidden,cuts);mesh=build(display)
        renderer=Renderer(mesh,1800,1400,azimuth=az,elevation=el,hatching=False,finish='graphite')
        stem=f'view-{az}-{el}';guide=root/(stem+'.png');renderer.draw(mesh).save(guide)
        (root/(stem+'-scene.json')).write_text(json.dumps(s),encoding='utf-8')
        (root/(stem+'-display.json')).write_text(json.dumps(display),encoding='utf-8')
        try:
            view=create(s,display,renderer,guide)
            issues=errors(s,view,guide,renderer=renderer)+report(s,view)['representation']['errors']
            issues+=compile_visual_contract(s,evidence=view['projection_review'])['errors']
            (root/(stem+'-view.json')).write_text(json.dumps(view),encoding='utf-8')
        except ValueError as exc:issues=[str(exc)]
        outputs.append(dict(stem=stem,folder=str(root),issues=issues))
        print(stem,issues,flush=True)
    (root/'camera-candidates.json').write_text(json.dumps(outputs,indent=2),encoding='utf-8')
    return outputs
