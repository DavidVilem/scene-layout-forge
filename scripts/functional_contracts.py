"""Explicit coverage of declared functions; geometry contracts, not performance."""


def functional_checks(scene):
    parts={p['id']:p for p in scene.get('parts',[])};checks=[];seen=set();covered=set()
    contracts=scene.get('functional_contracts',[])
    for index,contract in enumerate(contracts):
        key=contract['part'];role=contract['role'];cid=contract.get('id',f'functional[{index}]:{key}')
        status='unsupported';message='No functional adapter for this component and role'
        if cid in seen:status='failed';message='Duplicate functional contract ID'
        elif key not in parts:status='failed';message='Unknown functional component'
        elif parts[key]['kind']=='pump':
            if role=='stored':
                linked=any(key in (r['from'].split(':')[0],r['to'].split(':')[0]) for r in scene.get('connections',[]))
                status='failed' if linked else 'passed';message='Stored pump must not participate in process routes'
            elif role=='installed_pump':
                roles=[s.get('role') for s in parts[key].get('interfaces',{}).values()]
                status='passed' if 'inlet' in roles and 'outlet' in roles else 'failed'
                message='Installed pump requires inlet and outlet interfaces; flow capacity is unverified'
        elif role=='component_set':
            required=contract.get('required_kinds',[]);members=contract.get('members',[])
            if not required or not members or key not in members or any(k not in parts for k in members):
                status='failed';message='Component-set contract requires known members including its owner and required kinds'
            else:
                kinds={parts[k]['kind'] for k in members}
                missing=set(required)-kinds
                status='failed' if missing else 'passed'
                message='Missing required component kinds: '+', '.join(sorted(missing)) if missing else 'Declared component kinds exist; function and recognition remain unverified'
        seen.add(cid);covered.add(key)
        checks.append(dict(check='functional',contract_id=cid,part=key,role=role,status=status,
                           message=message,parts=[key],critical=contract.get('critical',True)))
    for key,p in parts.items():
        if p['kind']=='pump' and key not in covered:
            checks.append(dict(check='functional',contract_id=None,part=key,role=None,status='failed',
                message='Pump requires installed_pump or stored role',parts=[key],critical=True))
    if not checks:
        checks.append(dict(check='functional',contract_id=None,status='not_applicable',
            message='No functional contracts or mandatory pump role declared',parts=[],critical=True))
    return checks
