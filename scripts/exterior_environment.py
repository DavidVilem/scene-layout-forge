"""Bounded exterior composition, not an occupied-building or engineering model.

The contract permits assembly from supported parts without a whole-city factory.
It does not exempt any represented geometry from scene_model.validate. Road
connectivity uses touching coplanar rectangles; envelopes are opaque masses,
never evidence of hidden columns, rooms, foundations or internal circulation.
"""
LIMITS = ['unseen interiors', 'subsurface foundations', 'load capacity',
          'hidden services', 'facade fabrication details']


def _errors(scene):
    if 'exterior_environment' not in scene:
        return []
    c = scene['exterior_environment']
    if not isinstance(c, dict):
        return ['exterior environment contract must be an object']
    issues = []
    def require(ok, message):
        if not ok: issues.append('exterior environment: ' + message)
    require(c.get('version') == 1 and c.get('mode') == 'urban_exterior', 'unsupported scope')
    require(scene.get('workflow_version') == 3 and scene.get('schema_version') == 2
            and scene.get('validation_policy') == 'strict' and scene.get('registered_geometry') is True,
            'strict registered v3 geometry required')
    require(not any(k in scene for k in ('design_intent', 'design_selection', 'materialized_design', 'architecture_contract')),
            'do not replace an occupied-building contract or mix independent planning contracts')
    require(scene.get('visual_plan', {}).get('view_intent') == 'exterior', 'exterior view required; interiors and cuts use their own gates')
    require(not scene.get('representation') and not scene.get('room_programs'), 'cutaways and occupied-room programs are outside this adapter')
    require(set(LIMITS).issubset(set(c.get('unverified', []))), 'declare hidden engineering scope as unverified')
    parts = {p['id']: p for p in scene.get('parts', [])}
    def ids(field):
        value = c.get(field, [])
        if not isinstance(value, list) or not value or any(not isinstance(x, str) or x not in parts for x in value):
            require(False, field + ' needs existing part IDs'); return []
        require(len(value) == len(set(value)), field + ' contains duplicate IDs')
        return value
    envelopes, roads, focal = ids('envelopes'), ids('roads'), ids('focal')
    require(len(envelopes) >= 2, 'district needs multiple registered exterior masses')
    require(all(parts[k]['kind'] == 'wall' and parts[k].get('semantic_role') == 'exterior building envelope' for k in envelopes),
            'envelopes must be explicit opaque exterior masses, not rooms')
    require(all(parts[k]['kind'] in ('slab', 'paving') for k in roads), 'roads require supported planar surfaces')
    require(not any(p['kind'] in ('stair', 'ramp') for p in parts.values()),
            'this bounded exterior adapter does not cover occupied vertical circulation')
    roles = c.get('roles', {})
    allowed = {'terrain', 'envelope', 'roof', 'roof_equipment', 'street', 'plaza', 'edge_protection', 'landscape'}
    require(isinstance(roles, dict) and set(roles) == set(parts) and all(v in allowed for v in roles.values()),
            'every part must have an explicit exterior role')
    if isinstance(roles, dict):
        require({k for k, v in roles.items() if v == 'envelope'} == set(envelopes), 'envelope inventory differs from roles')
        require({k for k, v in roles.items() if v == 'street'} == set(roads), 'road inventory differs from roles')
        kinds={'terrain':{'slab','paving'},'envelope':{'wall'},'roof':{'slab'},
               'roof_equipment':{'cabinet'},'street':{'slab','paving'},'plaza':{'slab','paving'},
               'edge_protection':{'wall','railing'},'landscape':{'slab','custom'}}
        require(all(k in parts and parts[k]['kind'] in kinds.get(role,set()) for k,role in roles.items()),
                'part kind is outside its exterior role; use a richer adapter for occupied rooms or mechanisms')
        require(all(p['kind']!='custom' or p.get('parameters',{}).get('adapter')=='natural_tree_mass_v1' for p in parts.values()),
                'custom exterior shapes need a tested extension, not a disguised interior')
    alternatives = c.get('alternatives', [])
    require(isinstance(alternatives, list) and len(alternatives) >= 3
            and all(isinstance(a, dict) and a.get('id') and a.get('organization') and a.get('reason') for a in alternatives),
            'record at least three spatial alternatives and their tradeoffs')
    if isinstance(alternatives, list) and all(isinstance(a, dict) for a in alternatives):
        require(len({a.get('id') for a in alternatives}) == len(alternatives), 'duplicate alternatives')
        require(c.get('selected') in {a.get('id') for a in alternatives}, 'selected organization missing')
    require(type(c.get('seed')) is int, 'record the design seed')
    # Realized street network: shared edge of positive length, same height.
    def box(k):
        p = parts[k]; return p['origin'], [a+b for a,b in zip(p['origin'], p['size'])]
    def touch(a, b):
        lo, hi = box(a); other, top = box(b)
        overlap = [min(hi[i],top[i])-max(lo[i],other[i]) for i in range(2)]
        return abs(hi[2]-top[2]) < 1e-6 and min(overlap) >= -1e-6 and max(overlap) > 1e-6
    seen = set(); pending = roads[:1]
    while pending:
        k = pending.pop()
        if k in seen: continue
        seen.add(k); pending.extend(r for r in roads if r not in seen and touch(k, r))
    require(seen == set(roads), 'street surfaces are disconnected or have incompatible levels')
    for e in envelopes:
        lo, hi = box(e)
        for r in roads:
            other, top = box(r)
            require(not all(min(hi[i],top[i])-max(lo[i],other[i]) > 1e-6 for i in range(2)),
                    'street crosses building footprint: ' + r + ' / ' + e)
    # Each envelope must sit fully within its declared bearing footprint.
    # Base validation separately verifies contact height and ground reachability.
    supports = {b['part']: b['on'] for b in scene.get('bearings', [])}
    for e in envelopes:
        lower = supports.get(e)
        require(lower in parts, 'envelope has no represented bearing: ' + e)
        if lower in parts:
            lo, hi = box(e); a, b = box(lower)
            require(all(a[i]-1e-6 <= lo[i] and hi[i] <= b[i]+1e-6 for i in range(2)),
                    'unsupported setback/overhang: ' + e)
    require(set(focal).issubset(set(scene.get('visual_plan', {}).get('readable', []))),
            'focal assemblies must pass actual guide readability')
    require({x['target'] for x in scene.get('callouts', [])}.issubset(set(focal)),
            'annotation destinations must be focal visible assemblies')
    return sorted(set(issues))


def errors(scene):
    try:
        return _errors(scene)
    except (TypeError,KeyError,ValueError,AttributeError,IndexError) as exc:
        return ['exterior environment: malformed contract ('+str(exc)+')']


def handoff(scene):
    c = scene['exterior_environment']
    return {'mode': c['mode'], 'organization': c['selected'], 'seed': c['seed'],
            'checks': 'Represented envelope contacts, setback footprints, separate connected street surfaces, visible focal assemblies; strict physical checks still apply to every part.',
            'unverified': c['unverified'],
            'refinement': 'Develop facade bays, mullions, aligned floor bands, roof assemblies and street life within the registered exterior envelopes. These are facade illustrations, not modeled interiors. Keep distinct tower silhouettes and the distant skyline; do not turn this into an isolated single-tower study.'}
