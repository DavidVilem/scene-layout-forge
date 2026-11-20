"""Check every procedural example and deliberate invalid controls, without generating art."""
import argparse,copy,json
from collections import Counter
from run_example import load_example,names,ROOT
from scene_model import validate,validation_report
from typed_interfaces import coverage

def decision_errors(data,recipe,record):
    issues=[]
    if record.get('version')!=1:issues.append('unsupported example decision contract')
    for key in ('short_prompt','intent','decision_reference','positive_command','negative_command','negative_controls'):
        if not isinstance(record.get(key),str) or not record[key].strip():issues.append('missing example decision field: '+key)
    if record.get('schema_version')!=data.get('schema_version',1):issues.append('example contract schema differs from actual scene')
    if record.get('adapter_kinds')!=sorted({p['kind'] for p in data['parts']}):issues.append('example adapter inventory differs from actual scene')
    if record.get('coverage_status')!=validation_report(data)['status']:issues.append('example contract cannot promote actual physical coverage')
    invariants=record.get('invariants',{})
    if invariants.get('recipe_counts')!=recipe['counts'] or invariants.get('semantic_label_targets')!=recipe['labels']:issues.append('example contract lost recipe invariants')
    if not record.get('limits'):issues.append('example contract needs explicit limits')
    return issues

def check(example_names=None):
    results=[]
    selected=names() if example_names is None else list(example_names)
    if not selected or any(name not in names() for name in selected):raise ValueError('choose known nonempty example names')
    for name in selected:
        data,recipe=load_example(name)
        record=json.loads((ROOT/'examples'/name/'decision-contract.json').read_text(encoding='utf-8'))
        problems=decision_errors(data,recipe,record)
        if problems:raise AssertionError(name+': '+'; '.join(problems))
        bad=copy.deepcopy(data)
        bad['expected_counts']['vessel']=Counter(p['kind'] for p in data['parts'])['vessel']+1
        if not validate(bad):raise AssertionError('Invalid count accepted: '+name)
        workers=[p for p in data['parts'] if p['kind']=='worker']
        if workers:
            bad=copy.deepcopy(data)
            next(p for p in bad['parts'] if p['kind']=='worker')['origin'][2]+=.2
            if not validate(bad):raise AssertionError('Floating worker accepted: '+name)
        if data.get('connections'):
            bad=copy.deepcopy(data);bad['connections'][0]['route'][0][0]+=.5
            if not validate(bad):raise AssertionError('Disconnected route accepted: '+name)
        if data.get('attachments'):
            bad=copy.deepcopy(data)
            target,port=bad['attachments'][0]['to'].split(':',1)
            next(p for p in bad['parts'] if p['id']==target)['ports'][port][0]+=.25
            if not validate(bad):raise AssertionError('Disconnected attachment accepted: '+name)
        if data.get('shaft_bearings'):
            bad=copy.deepcopy(data)
            target=bad['shaft_bearings'][0]['bearing']
            next(p for p in bad['parts'] if p['id']==target)['origin'][0]+=.03
            if not validate(bad):raise AssertionError('Misaligned bearing accepted: '+name)
        results.append({'example':name,'geometry':'passed','coverage':coverage(data),'decision_contract':'verified','negative_controls':'passed','artistic_review':'not_run'})
    return results

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--example',action='append',choices=names())
    args=parser.parse_args();print(json.dumps(check(args.example),indent=2))
