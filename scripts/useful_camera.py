"""Fit and compare cameras around the occupied subject, independently of scenery.

This changes only the camera. Every candidate must retain required detail,
relations, framing and annotation targets before the highest score is selected.
"""
import copy
import math
import numpy as np

from visual_contract import compile_visual_contract, subject_metrics


class CameraSelectionError(ValueError):
    def __init__(self, records):
        self.selection={'selected':None,'candidates':records,'scope':'No camera passed every required guide gate'}
        super().__init__('No camera meets occupied framing, details, relations and annotations: '+
            '; '.join(record['name']+': '+', '.join(record.get('native_failures',record['failures'])[:4]) for record in records))


def subject_ids(scene):
    framing=scene.get('visual_plan',{}).get('subject_framing')
    if framing:return list(framing['ids'])
    return list(dict.fromkeys(scene.get('visual_plan',{}).get('primary',[])+scene.get('visual_plan',{}).get('secondary',[])))


def fit_camera(scene, identifiers, *, azimuth=-65, elevation=10, fov=36, aspect=1.2, fill=.80):
    """Pinhole fit of subject bounds with usable margins, unaffected by context."""
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in (azimuth,elevation,fov,aspect,fill)):
        raise ValueError('framing settings must be finite numbers')
    if not 0<fill<1 or not 10<=fov<=100 or not aspect>0 or not -85<=elevation<=85:raise ValueError('invalid framing settings')
    by={p['id']:p for p in scene['parts']}
    if not identifiers or any(key not in by for key in identifiers):raise ValueError('known occupied subject IDs required')
    vertices=np.array([np.asarray(by[key]['origin'])+np.asarray(by[key]['size'])*[x,y,z]
                       for key in identifiers for x in (0,1) for y in (0,1) for z in (0,1)],float)
    if not np.isfinite(vertices).all():raise ValueError('nonfinite occupied bounds')
    target=(vertices.min(0)+vertices.max(0))/2
    az,el=math.radians(azimuth),math.radians(elevation)
    sight=np.array([math.cos(az)*math.cos(el),math.sin(az)*math.cos(el),math.sin(el)])
    right=np.array([math.sin(az),-math.cos(az),0]);up=np.cross(right,sight)
    q=(vertices-target)@np.array([right,up,sight]).T
    tangent=math.tan(math.radians(fov)/2)
    distance=max(float(np.max(q[:,2]+abs(q[:,0])/(tangent*aspect*fill))),
                 float(np.max(q[:,2]+abs(q[:,1])/(tangent*fill))),1)
    eye=target+sight*distance
    return {'projection':'perspective','eye':eye.tolist(),'target':target.tolist(),'fov':fov,'near':.05}


def camera_options(scene, *, aspect=1.2):
    """A few supported views based on occupied shape and materialized family."""
    ids=subject_ids(scene)
    family=scene.get('materializer',{}).get('family','free')
    angles={'spine':[(-85,8),(-72,10),(-58,8),(-42,12)],
            'branched':[(-64,9),(-80,8),(-48,10),(-32,12)],
            'hub':[(-50,9),(-68,10),(-82,8),(-35,12)]}.get(family,[(-65,10),(-40,20),(-85,8)])
    result={f'occupied-{i}':fit_camera(scene,ids,azimuth=az,elevation=el,aspect=aspect)
            for i,(az,el) in enumerate(angles)}
    if family=='hub':
        # Broad wings can fill the remaining paper with contextual rock. Reserve
        # one wider view for notes, still subject to exactly the same framing gate.
        result['annotation-reserve']=fit_camera(scene,ids,azimuth=-50,elevation=9,aspect=aspect,fill=.68)
    return result


def renderer_options(camera):
    return {'projection':camera.get('projection','perspective'),'camera_eye':camera['eye'],
            'camera_target':camera['target'],'fov':camera.get('fov',50),'near':camera.get('near',.1)}


def select_useful_view(scene, *, width=1800, height=1500, preview_size=(900,750), options=None):
    """Compare owned guide evidence; return a selected scene/display/render bundle.

    The input scene is never mutated. Output `scene` has only a different camera.
    The final raster and annotation layout are rechecked, not inferred from preview.
    """
    from assembly_model import compile_cutaway
    from render_scene import build,Renderer
    from projection_review import review,rank
    from annotation_plan import create as annotations
    physical=copy.deepcopy(scene)
    display=compile_cutaway(physical,hide_ids=physical.get('display_hidden',[]))
    mesh=build(display);records=[];ids=subject_ids(scene)
    options=camera_options(scene,aspect=width/height) if options is None else options
    if not options:raise ValueError('camera search needs alternatives')
    for name,camera in options.items():
        renderer=Renderer(mesh,*preview_size,hatching=False,finish='graphite',**renderer_options(camera))
        renderer.draw(mesh)
        report=review(renderer,physical);visual=compile_visual_contract(physical,evidence=report)
        failures=list(visual['errors'])
        try:annotations(physical,renderer)
        except ValueError as exc:failures.append(str(exc))
        metrics=subject_metrics(report,ids)
        plan=physical.get('visual_plan',{})
        ranking=rank({name:report},required=plan.get('readable',[]),focus=plan.get('primary',ids),
                     full=plan.get('full',[]),readable=plan.get('readable',[]),
                     usage_size=plan.get('usage_size',[1024,1024]))[0]
        failures.extend(ranking['failures'])
        score=(ranking['score'] or 0)+.25*metrics['width_fraction']+.25*metrics['height_fraction']
        records.append({'name':name,'camera':camera,'admissible':not failures,'failures':list(dict.fromkeys(failures)),
                        'score':score if not failures else None,'subject_metrics':metrics})
    ordered=sorted((r for r in records if r['admissible']),key=lambda r:(r['score'],r['name']),reverse=True)
    for item in ordered:
        physical['camera']=item['camera']
        display=compile_cutaway(physical,hide_ids=physical.get('display_hidden',[]))
        # The display is rederived after camera binding; its geometry is unchanged.
        renderer=Renderer(mesh,width,height,finish='graphite',**renderer_options(item['camera']))
        image=renderer.draw(mesh);report=review(renderer,physical)
        failures=compile_visual_contract(physical,evidence=report)['errors']
        try:annotations(physical,renderer)
        except ValueError as exc:failures=failures+[str(exc)]
        if failures:
            item['native_failures']=failures;continue
        return {'scene':physical,'display':display,'renderer':renderer,'image':image,
                'selection':{'selected':item['name'],'preview_size':list(preview_size),'image_size':[width,height],
                             'candidates':records,'scope':'camera only; physical model preserved and every selected guide gate rechecked'}}
    raise CameraSelectionError(records)
