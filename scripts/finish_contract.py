"""Freeze scene semantics across artistic corrections; pixels need separate review."""
import hashlib,json

def canonical(data):return json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(data):return hashlib.sha256(canonical(data).encode()).hexdigest()

def preflight(data):
    from scene_model import validate
    errors=validate(data)
    if errors:return errors
    from architecture_stages import preflight_errors
    errors.extend(preflight_errors(data))
    parts={p['id']:p for p in data.get('parts',[])}
    if data.get('validation_policy')=='strict':
        from design_realization import realization_errors
        from exterior_environment import errors as exterior_errors
        if 'exterior_environment' in data:
            errors.extend(exterior_errors(data))
        elif not all(k in data for k in ('design_intent','design_selection','materialized_design')):
            errors.append('strict finish requires design intent, selection and realization evidence')
        errors.extend(realization_errors(data))
    regions=data.get('detail_regions',[])
    if not isinstance(regions,list) or not regions:
        errors.append('detail regions must be a nonempty list');regions=[]
    for region in regions:
        if not isinstance(region,dict):errors.append('detail region must be object');continue
        primary=region.get('primary',[]);secondary=region.get('secondary',[])
        if not isinstance(region.get('name'),str) or not region['name'].strip():errors.append('detail region name required')
        if not all(isinstance(ids,list) and all(isinstance(key,str) for key in ids) for ids in (primary,secondary)):
            errors.append('detail component IDs must be lists of strings');continue
        if not primary:errors.append('detail region primary components missing')
        if not secondary and not region.get('quiet_reason'):errors.append('secondary assemblies or intentional quiet-region reason required')
        if set(primary)&set(secondary):errors.append('primary and secondary detail must be distinct')
        for key in primary+secondary:
            if key not in parts:errors.append('unregistered detail component: '+str(key))
        if not region.get('microdetails'):errors.append('region construction detail description missing')
    ids=set()
    for label in data.get('callouts',[]):
        if label.get('id') in ids:errors.append('duplicate callout ID')
        ids.add(label.get('id'))
        if label.get('target') not in parts:errors.append('callout target not registered')
    if data.get('workflow_version',2)>=3:
        from visual_contract import errors as visual_errors
        errors.extend(visual_errors(data))
        if not all(k in data for k in ('visual_plan','context_plan','detail_budget','light_material_plan')):
            errors.append('workflow v3 requires explicit visual/context/detail/light-material planning')
    for kind,value in data.get('delivery_counts',{}).items():
        if not isinstance(kind,str) or type(value) is not int or value<0:errors.append('delivery counts require named nonnegative integers')
    return errors

def freeze(data,view=None,stage_records=None):
    errors=preflight(data)
    if errors:raise ValueError('; '.join(errors))
    if data.get('validation_policy')=='strict' or view is not None:
        from view_contract import errors as view_errors
        errors.extend(view_errors(data,view))
    visual=None
    if any(k in data for k in ('visual_plan','context_plan','detail_budget','light_material_plan')):
        from visual_contract import compile_visual_contract
        projection=view.get('projection_review') if isinstance(view,dict) else None
        visual=compile_visual_contract(data,evidence=projection)
        if data.get('workflow_version',2)>=3:
            if not isinstance(view,dict) or view.get('version')!=2 or projection is None:errors.append('workflow v3 requires a bound v2 view with projection review')
            errors.extend(visual['errors'])
            if visual.get('guide_status')!='passed':errors.append('visual guide gate must pass before finishing')
    if errors:raise ValueError('; '.join(errors))
    # Copy prevents a caller mutating the original snapshot through aliases.
    from architecture_stages import enabled,records_errors,report
    if enabled(data):
        errors.extend(records_errors(data,stage_records,7,view))
        errors.extend(report(data,view)['representation']['errors'])
        if errors:raise ValueError('; '.join(errors))
    snapshot=json.loads(canonical(data))
    from scene_model import validation_report
    lock={'version':3 if data.get('workflow_version',2)>=3 else 2,'scene_sha256':digest(snapshot),'scene':snapshot,
          'validation':validation_report(data)}
    if view is not None:
        lock['view']=json.loads(canonical(view));lock['view_sha256']=digest(lock['view'])
    if visual is not None:
        lock['visual_contract']=visual
        lock['visual_contract_sha256']=digest(lock['visual_contract'])
    if enabled(data):
        lock['architecture_stages']=json.loads(canonical(stage_records))
        lock['architecture_stages_sha256']=digest(stage_records)
    return lock

def check(lock,data):
    if digest(lock['scene'])!=lock['scene_sha256']:raise ValueError('finish lock itself was modified')
    if digest(data)!=lock['scene_sha256']:raise ValueError('scene changed: revise geometry, revalidate and create a new finish lock')
    if 'view' in lock and digest(lock['view'])!=lock.get('view_sha256'):raise ValueError('finish view evidence was modified')
    if 'visual_contract' in lock and digest(lock['visual_contract'])!=lock.get('visual_contract_sha256'):raise ValueError('finish visual contract was modified')
    from architecture_stages import enabled,records_errors
    if enabled(data):
        records=lock.get('architecture_stages')
        if digest(records)!=lock.get('architecture_stages_sha256') or records_errors(data,records,7,lock.get('view')):raise ValueError('architectural stage evidence missing or changed')

def invariants(lock):
    check(lock,lock['scene']);s=lock['scene'];parts={p['id']:p for p in s['parts']}
    lines=['Keep the same registered scene, counts, contacts, routes and boundary meanings.']
    for i,c in enumerate(s.get('connections',[])):
        lines.append(f'route-{i}: {c["from"]} -> {c["to"]}; preserve both endpoints and its complete route.')
    for p in parts.values():
        for name,spec in p.get('interfaces',{}).items():
            if spec.get('termination'):
                lines.append(f'{p["id"]}:{name}: {spec["role"]}, {spec["medium"]}, {spec["termination"]}; '+
                             spec.get('meaning','continuation outside the modeled scope, unverified')+'. Do not replace its meaning or destination.')
                if spec['termination']=='external':
                    lines.append('This is an external continuation, NOT a sealed end: do not add a blind flange, plug or closed cap. If the continuation cannot be depicted clearly, revise the registered boundary geometry before finishing; do not invent a destination.')
    for c in s.get('custom_contacts',[]):lines.append(f'{c["part"]} contacts {c["on"]} on its registered surface patch.')
    return '\n'.join(lines)

def handoff(lock):
    lines=[invariants(lock),'Planned detail regions:']
    for region in lock['scene']['detail_regions']:
        lines.append(f'{region["name"]}: primary={region["primary"]}; secondary={region["secondary"]}; fine detail={region["microdetails"]}')
    lines.append('Exact callouts: '+json.dumps(lock['scene'].get('callouts',[])))
    # IDs alone cannot tell an image model which visible shape is being referenced.
    scene=lock['scene'];named={x['target'] for x in scene.get('callouts',[])}
    for region in scene['detail_regions']:named.update(region['primary']+region['secondary'])
    for route in scene.get('connections',[]):named.update(ref.split(':')[0] for ref in (route['from'],route['to']))
    lines.append('Component identity map (world coordinates locate shapes, not dimensions to print):')
    for part in scene['parts']:
        if part['id'] in named:
            lines.append(f'{part["id"]}: {part["kind"]}, origin={part["origin"]}, extent={part["size"]}.')
    if scene.get('camera'):lines.append('Chosen camera: '+json.dumps(scene['camera'])+'. Keep the supplied guide framing; do not add sky margins or expand the floor.')
    if lock.get('view'):
        lines.append('Visible guide annotation anchors, normalized XY from top left: '+json.dumps(lock['view']['annotations'])+'. End each arrow on the same named visible surface. Coordinates locate the calculated guide; inspect the finished image independently and follow the actual corresponding surface if linework drifts.')
    if scene.get('design_selection'):
        evidence=scene['design_selection']
        selected=next((c for c in evidence.get('candidates',[]) if c['id']==evidence.get('selected_id')),None)
        if selected:lines.append('Selected spatial organization: '+json.dumps({'family':selected['family'],'nodes':selected['nodes'],'edges':selected['edges']})+'. Keep program differences and circulation, not merely different cabinet labels.')
    if lock.get('visual_contract'):
        lines.append('Structured visual plan (preserve physical invariants; enrich only planned surfaces and context): '+canonical(lock['visual_contract']))
    return '\n'.join(lines)

def request(lock,brief,art_direction,max_chars=30000):
    from annotation_policy import instruction
    """Short user input and written style feed the same full scene handoff."""
    if not isinstance(brief,str) or not brief.strip():raise ValueError('user brief required')
    if not isinstance(art_direction,str) or not art_direction.strip():raise ValueError('written art direction required')
    scene=lock['scene']
    text='\n\n'.join([
        'User request: '+brief,
        'Create ONE finished PNG. The supplied image is the current calculated layout, not a style reference. No earlier images or history are needed.',
        'Preserve camera, topology and supports. Physical component inventory (includes parts hidden by registered cuts/occlusion, not a demand to expose every one): '+json.dumps(scene.get('expected_counts',{})),
        'Requested delivery counts to inspect in the final image: '+json.dumps(scene.get('delivery_counts',{}))+'. Do not infer extra people from a generic workplace.',
        canonical(compile_handoff(lock)) if lock.get('version',2)>=3 else handoff(lock),
        'Interpret unknown interface destinations only as the external boundaries named above. Never invent missing process routes. Domain-specific boundary meanings apply only to their declared components.',
        'The guide establishes primary and secondary assemblies. Develop their listed fine details without adding unregistered major machinery, buildings or cranes. Subordinate landscape/sky marks may establish context. Natural figures must keep correct scale and contacts.',
        art_direction, instruction(lock['scene'])])
    if len(text)>max_chars:raise ValueError('Compiled finish request exceeds character budget; simplify optional descriptions or split scene scope, never truncate physical invariants')
    return text


def compile_handoff(lock):
    """Ordered semantic layers; no inferred hidden machinery or copied composition."""
    check(lock,lock['scene']);s=lock['scene'];parts={p['id']:p for p in s['parts']}
    named={c['target'] for c in s.get('callouts',[])}
    for region in s.get('detail_regions',[]):named.update(region['primary']+region['secondary'])
    for route in s.get('connections',[]):named.update(ref.split(':')[0] for ref in (route['from'],route['to']))
    boundaries=[]
    for p in parts.values():
        for key,spec in p.get('interfaces',{}).items():
            if spec.get('termination'):boundaries.append({'interface':p['id']+':'+key,**spec})
    selection=s.get('design_selection',{});selected=next((c for c in selection.get('candidates',[]) if c['id']==selection.get('selected_id')),None)
    nodes={n['id']:n for n in selected.get('nodes',[])} if selected else {}
    semantic_targets=[]
    for label in s.get('callouts',[]):
        part=parts[label['target']];node=nodes.get(part.get('design_node'),{})
        spec={'label_id':label['id'],'text':label['text'],'component':label['target'],'kind':part['kind'],
              'meaning':part.get('semantic_role',part.get('design_program',part['kind']))}
        if 'level' in node:spec['occupied_level_from_bottom']=node['level']+1
        if part.get('design_program'):spec['room_program']=part['design_program']
        semantic_targets.append(spec)
    visual=json.loads(canonical(lock.get('visual_contract')))
    if visual:
        plans=visual.get('plans',{})
        framing=plans.get('visual_plan',{}).get('subject_framing')
        if framing:
            framing_ids=framing.pop('ids',[])
            framing['registered_subject_parts']=len(framing_ids)
            framing['subject_bounds']={'min':[min(parts[k]['origin'][axis] for k in framing_ids) for axis in range(3)],
                                       'max':[max(parts[k]['origin'][axis]+parts[k]['size'][axis] for k in framing_ids) for axis in range(3)]} if framing_ids else None
            framing['instruction']='Frame the occupied architecture inside these bounds as in the inspected guide; scenery must not shrink it.'
        context=plans.get('context_plan',{})
        groups={}
        for entity in context.pop('entities',[]):
            key=canonical({k:v for k,v in entity.items() if k!='id'})
            groups.setdefault(key,[]).append(entity['id'])
        context['entity_groups']=[{**json.loads(key),'registered_count':len(ids),'named_focal_ids':[i for i in ids if i in named]} for key,ids in sorted(groups.items())]
        light=visual.get('plans',{}).get('light_material_plan',{})
        materials=light.get('materials',{})
        # Full per-part material frames remain in the immutable lock. The image
        # handoff carries named focal surfaces and semantic defaults, not hundreds
        # of repeated numeric records that obscure priorities.
        families={};distribution={}
        for key,spec in materials.items():
            kind=parts[key]['kind'];family=spec['family'];families.setdefault(kind,set()).add(family)
            distribution[(kind,family)]=distribution.get((kind,family),0)+1
        light['material_default_by_kind']={k:next(iter(v)) for k,v in sorted(families.items()) if len(v)==1}
        light['material_distribution']=[{'kind':k,'family':f,'count':n} for (k,f),n in sorted(distribution.items())]
        focal_groups={}
        for key,spec in materials.items():
            if key not in named:continue
            compact={field:spec[field] for field in ('family','axis','tangent','mapping','density','mark') if field in spec}
            focal_groups.setdefault(canonical(compact),[]).append(key)
        light.pop('materials',None)
        light['focal_material_groups']=[{'surface':json.loads(spec),'owners':sorted(owners)} for spec,owners in sorted(focal_groups.items())]
        light['scope']='Named focal surface specifications plus kind/family defaults; full physical/material mapping is fixed in the lock and current guide.'
    result={'version':1,'priority':['physical_invariants','view','visible_identity','visual_plan','annotations','permitted_refinement'],
            'physical_invariants':{'scene_sha256':lock['scene_sha256'],'inventory':s.get('expected_counts',{}),'delivery_counts':s.get('delivery_counts',{}),
                'routes':s.get('connections',[]),'boundaries':boundaries,
                'contact_pairs':[[c['part'],c['on']] for c in s.get('custom_contacts',[])],
                'contact_rule':'Every pair names part and supporting object. Preserve its registered physical patch shown in the guide; full samples remain in the immutable scene.',
                'relations':s.get('relations',[]),
                'rule':'Keep registered openings, support, routes, scale and physical topology. External continuation is not a sealed end.'},
            'view':{'camera':s.get('camera'),'view_sha256':lock.get('view_sha256'),'family':selected['family'] if selected else None,
                'rule':'Preserve this inspected framing and display cut; no new viewpoint or invented disconnected rooms.'},
            'visible_identity':[{**{'id':p['id'],'kind':p['kind'],'origin':p['origin'],'size':p['size']},
                                 **{k:p[k] for k in ('semantic_role','design_program') if k in p}} for p in s['parts'] if p['id'] in named],
            'visual_plan':visual,'detail_regions':[] if visual and visual.get('plans',{}).get('detail_budget') else s.get('detail_regions',[]),
            'critical_interface_witnesses':s.get('camera_junctions',[]),
            'annotations':{'exact_labels':s.get('callouts',[]),'visible_anchors':lock.get('view',{}).get('annotations',[]),
                'semantic_targets':semantic_targets,
                'policy':s.get('annotation_policy',{'mode':'legacy_fixture'}),
                'rule':__import__('annotation_policy').instruction(s)},
            'permitted_refinement':{'allowed':['surface-following pencil marks','listed local fasteners and seams','subordinate context within the declared plan'],
                'forbidden':['new major machinery','new access or support topology','unrequested people','replacement of geometry by texture']}}
    from pattern_rules import select_patterns
    selected_rules=select_patterns(s)
    if s.get('architecture_contract'):
        result['architectural_identity']={k:s['architecture_contract'].get(k) for k in ('site','spaces','witnesses')}
    if s.get('exterior_environment'):
        from exterior_environment import handoff as exterior_handoff
        result['exterior_scope']=exterior_handoff(s)
    result['conditional_drawing_rules']={'rules':[{'id':r['id'],'principle':r['principle'],'mode':r['mode'],'limits':r['limits']} for r in selected_rules['rules']],
                                         'scope':selected_rules['scope'],'unknown_facts':selected_rules['unknown_facts']}
    if s.get('room_programs'):
        recipes=s['room_programs']
        result['room_programs']={'programs':{r['program']:r['description'] for r in recipes.values()},
            'registered_variants':{room:{'program':r['program'],'variant':r['variant']} for room,r in recipes.items()},
            'rule':'Develop the different functional compounds already registered in each room. Preserve their per-room arrangement; do not collapse every room into two generic tables or add unsupported major equipment.'}
    return json.loads(canonical(result))

def correction(lock,current_scene,edits,*,review=None,image_path=None,correction_index=1):
    check(lock,current_scene);lines=[invariants(lock),'Only these visual corrections are authorized:']
    if type(correction_index) is not int or not 1<=correction_index<=2:raise ValueError('maximum two targeted corrections for one scene')
    requires_pixels=lock.get('version',2)>=3 or any('extra_at' in e for e in edits)
    # Validate coordinates first, including legacy callers, before identity checks.
    for edit in edits:
        if 'extra_at' in edit:
            import math
            point=edit['extra_at']
            if not isinstance(point,list) or len(point)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1 for v in point):raise ValueError('extra_at requires normalized finite image XY')
    if requires_pixels or review is not None:
        if image_path is None or review is None:raise ValueError('localized/v3 corrections require the inspected PNG and bound pixel review')
        from pixel_review import errors as pixel_errors
        issues=pixel_errors(lock,image_path,review)
        if issues:raise ValueError('; '.join(issues))
        lines.append('Correct only inspected PNG file SHA256='+review['image']['file_sha256']+'. This edit needs a new independent pixel review; earlier visual passes do not transfer.')
    parts={p['id'] for p in current_scene['parts']};labels={x['id'] for x in current_scene.get('callouts',[])}
    for edit in edits:
        permitted={'kind','target'}
        if edit.get('kind')=='count':permitted.add('extra_at')
        if not {'kind','target'}<=set(edit) or set(edit)-permitted:raise ValueError('correction accepts kind and target only except count pixel evidence; topology edits require rebuild')
        kind,target=edit['kind'],edit['target']
        if kind=='annotation' and target in labels:
            label=next(x for x in current_scene['callouts'] if x['id']==target)
            lines.append(f'Redirect {label["text"]} leader onto a visible surface of {label["target"]}; preserve text and all geometry.')
            if review is not None:
                observed=next((o for o in review['observations'] if o['target']=='callout:'+target),None)
                if observed:
                    lines.append('Current-PNG annotation observation: '+observed['note'])
                    if observed.get('desired_tip_xy'):
                        lines.append('Observed intended visible surface in this exact PNG, normalized XY from top left: '+canonical(observed['desired_tip_xy'])+'. Use one thin leader and one arrowhead ending on this corresponding named surface; remove the erroneous old leader, never alter the component to fit the arrow.')
            part=next(p for p in current_scene['parts'] if p['id']==label['target'])
            if part['kind']=='pump':lines.append('For this pump label, end on the pump casing, not the attached electric motor.')
        elif kind=='count' and target in {**current_scene.get('expected_counts',{}),**current_scene.get('delivery_counts',{})}:
            selected=[p for p in current_scene['parts'] if p['kind']==target]
            count=current_scene.get('delivery_counts',{}).get(target,current_scene.get('expected_counts',{}).get(target))
            lines.append(f'Restore exactly {count} requested {target} instances as in the current guide; never expose physically hidden inventory merely to increase a visible count. Remove only invented extras or restore omitted instances; keep contracted positions and contacts: '+json.dumps([{'id':p['id'],'origin':p['origin'],'size':p['size']} for p in selected]))
            if 'extra_at' in edit:
                point=edit['extra_at']
                if not isinstance(point,list) or len(point)!=2 or any(type(v) not in (int,float) or not 0<=v<=1 for v in point):raise ValueError('extra_at requires normalized finite image XY')
                observed=next((o for o in review['observations'] if o['target']=='count:'+target),None)
                if observed is None or observed['state']!='visible_error' or 'region' not in observed:raise ValueError('extra_at requires a visible count error with a localized observed region')
                x0,y0,x1,y1=observed['region']
                if not (x0<=point[0]<=x1 and y0<=point[1]<=y1):raise ValueError('extra_at is outside the observed error region')
                lines.append(f'Pixel review identified an invented extra {target} centered at normalized image XY={point} (origin top-left). Remove that extra instance only; preserve the other contracted instances and restore the underlying background. This is observed image evidence, not a new scene component.')
        elif kind=='interface_clarity' and target in parts:
            lines.append(f'Clarify visible interfaces of {target} without moving, adding, removing or redirecting any route. Preserve exact port roles and boundaries above.')
            if review is not None:
                observed=next((o for o in review['observations'] if o['target']=='part:'+target),None)
                if observed:lines.append('Current-PNG interface observation: '+observed['note'])
        elif kind=='annotation_extras' and target=='all' and current_scene.get('annotation_policy',{}).get('mode')=='none':
            observed=next((o for o in review['observations'] if o['target']=='global:annotations'),None) if review else None
            if not observed or observed['state']!='visible_error':raise ValueError('extra annotation removal requires observed pixel error')
            lines.append('Remove unsolicited explanatory labels, caption boxes and leader arrows; restore underlying drawing without changing the scene. Observed evidence: '+observed['note'])
        elif kind=='tone' and target=='paper':lines.append('Restore near-white neutral paper and selective graphite shading; preserve geometry and labels.')
        elif kind=='detail_region' and any(r['name']==target for r in current_scene.get('detail_regions',[])):
            region=next(r for r in current_scene['detail_regions'] if r['name']==target)
            lines.append('Restore only the planned construction detail in region '+target+': '+canonical(region)+'. Keep contacts, counts, camera, materials and all route destinations.')
            if review is not None:
                observed=next((o for o in review['observations'] if o['target']=='region:'+target),None)
                if observed:lines.append('Current-PNG detail observation: '+observed['note'])
        elif kind=='material' and target in parts and current_scene.get('light_material_plan'):
            lines.append('Restore the declared surface/light intent on '+target+' without changing its geometry, opacity-related visibility requirements or interfaces: '+canonical(current_scene['light_material_plan']))
        else:raise ValueError('unsupported correction kind or target')
    lines.append('Preserve contracted counts, poses, access, support, camera and flow. Review generated pixels independently; this lock does not enforce pixel geometry.')
    return '\n'.join(lines)
