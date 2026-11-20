"""Select original conditional drawing rules from explicit scene facts.

Evidence confidence is a bounded organization score, never a probability that a
scene is correct. Distinct tests/copies within one evidence family count once.
This selector neither validates physical geometry nor recognizes final pixels.
"""
from dataclasses import dataclass
from pathlib import Path
import copy
import json
import math

VERSION=1
ROOT=Path(__file__).resolve().parents[1]
FACTS={'domain','view_intent','projection','context_mode','value_policy',
       'material_families','has_material_frames','organic_types','has_support_contract'}
DOMAINS={'building','process','mechanism','vehicle','environment'}
VIEWS={'free','plan','elevation','exterior','interior','section','cutaway','detail'}
CONTEXTS={'isolated','situated','interior','landscape'}
POLICIES={'neutral','dark_interior','open_air','diagram'}
MATERIALS={'matte_metal','glass','concrete','wood','stone','cloth','rubber'}
MODES={'operational','comparison','negative_control','scope_limit'}

def _text(value,label):
    if not isinstance(value,str) or not value.strip():raise ValueError(label+' requires nonempty text')

def _number(value,label):
    if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=1:
        raise ValueError(label+' must be finite within 0..1')

def _condition(condition):
    if not isinstance(condition,dict) or not condition:raise ValueError('nonempty conditional expression required')
    for operator in ('all','any'):
        if operator in condition:
            if set(condition)!={operator} or not isinstance(condition[operator],list) or not condition[operator]:
                raise ValueError('conditional '+operator+' needs a nonempty list')
            for child in condition[operator]:_condition(child)
            return
    if condition.get('fact') not in FACTS:raise ValueError('unknown scene fact in condition')
    operators=set(condition)-{'fact'}
    if len(operators)!=1 or not operators<={'eq','in','intersects'}:raise ValueError('unsupported conditional operator')
    operator=next(iter(operators));value=condition[operator]
    if operator=='eq':
        if type(value) not in (str,bool):raise ValueError('eq expects a string or boolean')
    elif not isinstance(value,list) or not value or any(type(v) not in (str,bool) for v in value):
        raise ValueError(operator+' expects a nonempty list of strings/booleans')

def matches(condition,facts):
    """Unknown facts never satisfy an affirmative condition."""
    if 'all' in condition:return all(matches(c,facts) for c in condition['all'])
    if 'any' in condition:return any(matches(c,facts) for c in condition['any'])
    key=condition['fact']
    if key not in facts:return False
    value=facts[key]
    if 'eq' in condition:return type(value)==type(condition['eq']) and value==condition['eq']
    if 'in' in condition:return not isinstance(value,(list,tuple,set)) and value in condition['in']
    return isinstance(value,(list,tuple,set)) and bool(set(value)&set(condition['intersects']))

@dataclass(frozen=True)
class PatternRecord:
    id: str
    family: str
    principle: str
    applicability: dict
    exceptions: list
    confidence: dict
    mode: str
    evidence: list
    limits: list

    @classmethod
    def from_data(cls,data,known_evidence_families):
        if not isinstance(data,dict) or set(data)!=set(cls.__dataclass_fields__):raise ValueError('PatternRecord fields differ from version 1')
        for key in ('id','family','principle'):_text(data[key],key)
        if data['mode'] not in MODES:raise ValueError('unsupported pattern mode')
        _condition(data['applicability'])
        if not isinstance(data['exceptions'],list):raise ValueError('exceptions must be a list')
        for exception in data['exceptions']:
            if not isinstance(exception,dict) or set(exception)!={'when','reason'}:raise ValueError('exception needs when/reason')
            _condition(exception['when']);_text(exception['reason'],'exception reason')
        confidence=data['confidence']
        if not isinstance(confidence,dict) or set(confidence)!={'ceiling','basis','interpretation'}:raise ValueError('explicit confidence basis/ceiling/interpretation required')
        _number(confidence['ceiling'],'confidence ceiling');_text(confidence['basis'],'confidence basis');_text(confidence['interpretation'],'confidence interpretation')
        if not isinstance(data['evidence'],list) or not data['evidence']:raise ValueError('evidence records required')
        for evidence in data['evidence']:
            if not isinstance(evidence,dict) or set(evidence)!={'family','source','scope'}:raise ValueError('evidence needs independent family, source and scope')
            if evidence['family'] not in known_evidence_families:raise ValueError('unknown independent evidence family')
            _text(evidence['source'],'evidence source');_text(evidence['scope'],'evidence scope')
        if not isinstance(data['limits'],list) or not data['limits']:raise ValueError('explicit pattern limits required')
        for value in data['limits']:_text(value,'pattern limit')
        return cls(**copy.deepcopy(data))

def load_catalog(path=None):
    value=json.loads(Path(path or ROOT/'references/pattern-rules.json').read_text(encoding='utf-8-sig'))
    validate_catalog(value)
    return value

def validate_catalog(catalog):
    if not isinstance(catalog,dict) or catalog.get('version')!=VERSION:raise ValueError('unsupported pattern catalog version')
    policy=catalog.get('confidence_policy',{})
    if set(policy)!={'baseline','per_independent_family','ceiling','interpretation'}:raise ValueError('explicit confidence policy required')
    for key in ('baseline','per_independent_family','ceiling'):_number(policy[key],key)
    if policy['baseline']>policy['ceiling']:raise ValueError('confidence baseline exceeds ceiling')
    _text(policy['interpretation'],'confidence interpretation')
    families=catalog.get('evidence_families')
    if not isinstance(families,dict) or not families:raise ValueError('independent evidence family registry required')
    for key,value in families.items():
        _text(key,'evidence family ID')
        if not isinstance(value,dict) or set(value)!={'question','independence_basis'}:raise ValueError('evidence family needs question and independence basis')
        for text in value.values():_text(text,'evidence family explanation')
    records=catalog.get('patterns')
    if not isinstance(records,list) or not records:raise ValueError('pattern records required')
    ids=set()
    for raw in records:
        record=PatternRecord.from_data(raw,families)
        if record.id in ids:raise ValueError('duplicate pattern ID')
        ids.add(record.id)
    return []

def evidence_confidence(record,catalog):
    """One contribution per registered family, regardless of copies/sources."""
    record=PatternRecord.from_data(record,catalog['evidence_families']) if isinstance(record,dict) else record
    families=sorted({e['family'] for e in record.evidence});policy=catalog['confidence_policy']
    score=min(policy['ceiling'],record.confidence['ceiling'],policy['baseline']+len(families)*policy['per_independent_family'])
    return {'score':round(score,6),'independent_families':families,
            'basis':record.confidence['basis'],'interpretation':policy['interpretation'],
            'execution_status':'Source evidence families only; no scene, test execution or final-pixel pass is inferred.'}

def scene_facts(scene):
    if not isinstance(scene,dict):raise ValueError('scene must be an object')
    facts={};unknown=[];conflicts=[]
    def explicit(key,raw,allowed):
        if isinstance(raw,str) and raw in allowed:facts[key]=raw
        elif raw is not None:unknown.append(key+': unsupported explicit value')
        else:unknown.append(key+': not supplied')
    def block(name):
        value=scene.get(name,{})
        if not isinstance(value,dict):unknown.append(name+': object not supplied');return {}
        return value
    explicit('domain',block('design_intent').get('domain'),DOMAINS)
    explicit('view_intent',block('visual_plan').get('view_intent'),VIEWS)
    explicit('projection',block('camera').get('projection'),{'orthographic','perspective'})
    explicit('context_mode',block('context_plan').get('mode'),CONTEXTS)
    light=block('light_material_plan');explicit('value_policy',light.get('value_policy'),POLICIES)
    parts={p['id']:p for p in scene.get('parts',[]) if isinstance(p,dict) and isinstance(p.get('id'),str)} if isinstance(scene.get('parts',[]),list) else {}
    material_families=set();framed=False
    materials=light.get('materials',{})
    for owner,spec in materials.items() if isinstance(materials,dict) else ():
        if owner not in parts:unknown.append('material owner: absent from scene');continue
        if not isinstance(spec,dict) or spec.get('family') not in MATERIALS:unknown.append('material family: unsupported');continue
        material_families.add(spec['family'])
        def vec(value):return isinstance(value,(list,tuple)) and len(value)==3 and all(type(v) in (int,float) and math.isfinite(v) for v in value)
        if all(vec(spec.get(k)) for k in ('origin','axis','tangent')):
            aa=sum(v*v for v in spec['axis']);tt=sum(v*v for v in spec['tangent']);dot=sum(a*b for a,b in zip(spec['axis'],spec['tangent']))
            if aa>1e-12 and tt>1e-12 and abs(dot)<=1e-6*math.sqrt(aa*tt):framed=True
            else:unknown.append('material frame: invalid axes')
        else:unknown.append('material frame: not supplied')
    if material_families:facts['material_families']=sorted(material_families)
    if framed:facts['has_material_frames']=True
    organic=set()
    for part in parts.values():
        if part.get('kind')=='worker':organic.add('standing_actor')
        params=part.get('parameters',{})
        if isinstance(params,dict) and params.get('adapter')=='natural_tree_mass_v1':organic.add('tree_mass')
    if organic:facts['organic_types']=sorted(organic)
    if any(isinstance(scene.get(k),list) and scene[k] for k in ('bearings','mounts','surface_contacts','custom_contacts','ground_contacts')):facts['has_support_contract']=True
    if facts.get('view_intent')=='plan' and facts.get('projection')=='perspective':conflicts.append('Requested plan and perspective camera conflict; no projection pattern can authorize this mismatch.')
    if facts.get('context_mode')=='isolated' and block('context_plan').get('entities'):conflicts.append('Isolated context contains entities; pattern selection does not authorize adding them.')
    return facts,sorted(set(unknown)),conflicts

def select_patterns(scene,catalog=None):
    """Return only relevant conditional rules, plus honest omissions/conflicts.

    The optional catalog is useful for portable tests and original extensions.
    Selection is deterministic and leaves both scene and catalog unchanged.
    """
    catalog=load_catalog() if catalog is None else catalog;validate_catalog(catalog)
    facts,unknown,conflicts=scene_facts(scene);selected=[];excluded=[]
    for raw in sorted(catalog['patterns'],key=lambda r:r['id']):
        record=PatternRecord.from_data(raw,catalog['evidence_families'])
        if not matches(record.applicability,facts):continue
        exceptions=[e['reason'] for e in record.exceptions if matches(e['when'],facts)]
        if exceptions:excluded.append({'id':record.id,'reason':'; '.join(exceptions)});continue
        selected.append({'id':record.id,'family':record.family,'mode':record.mode,'principle':record.principle,
            'applicability':copy.deepcopy(record.applicability),'exceptions':copy.deepcopy(record.exceptions),
            'confidence':evidence_confidence(record,catalog),'limits':list(record.limits)})
    return {'version':VERSION,'facts':facts,'rules':selected,'excluded_by_exception':excluded,
            'unknown_facts':unknown,'conflicts':conflicts,
            'scope':'Conditional original guidance only. Geometry, guide readability and inspected final pixels retain their independent gates.'}
