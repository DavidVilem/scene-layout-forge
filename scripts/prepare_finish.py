"""Prepare a persistent, validated image handoff in every subject domain."""
import argparse,json,uuid
from pathlib import Path
from finish_contract import freeze,request
from execution_history import preserve,save,read
from history_run import new_run

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scene',type=Path,required=True);p.add_argument('--brief',required=True)
    p.add_argument('--view',type=Path,required=True);p.add_argument('--guide',type=Path,required=True)
    p.add_argument('--project',type=Path,default=Path.cwd());p.add_argument('--run',type=Path)
    p.add_argument('--stem',default='layout');p.add_argument('--source',type=Path,action='append',required=True)
    p.add_argument('--stage-records',type=Path,help='Ordered seven approvals required for architectural v4')
    p.add_argument('--client',default='unrecorded');p.add_argument('--reasoning-model',default='unreported')
    p.add_argument('--image-tool',default='unreported');p.add_argument('--image-model',default='unreported')
    a=p.parse_args();root=Path(__file__).resolve().parents[1]
    run=a.run.resolve() if a.run else new_run(a.project,a.stem,a.brief)
    if run==root or root in run.parents:raise ValueError('history must stay outside the skill')
    try:
        scene=read(a.scene);view=read(a.view)
        from view_contract import errors
        issues=errors(scene,view,a.guide)
        if issues:raise ValueError('; '.join(issues))
        lock=freeze(scene,view,stage_records=read(a.stage_records) if a.stage_records else None)
        prompt=request(lock,a.brief,(root/'references/finish-style.txt').read_text(encoding='utf-8'))
        folder=preserve(lock,run,a.guide,a.brief,prompt,sources=a.source,client={'surface':a.client,
            'reasoning_model':a.reasoning_model,'image_tool':a.image_tool,'image_model':a.image_model})
        print(json.dumps({'run':str(run),'attempt':str(folder),'tool_request':str(folder/'tool-request.json'),
                          'scope':'Ready for tool call; not a generated or reviewed final image'}))
    except Exception as exc:
        if (run/'08-finish').is_dir():save(run/'08-finish'/('preparation-failed-'+uuid.uuid4().hex+'.json'),{'status':'failed','error':str(exc)})
        raise

if __name__=='__main__':main()
