"""Portable design intent: user requirements remain distinct from planner choices."""
from dataclasses import dataclass, field
import hashlib, json, secrets
from domain_grammar import domain_name,infer_domain

VERSION = 'design-intent-2'
CONSTRAINT_KEYS = {'levels', 'connected', 'required_roles', 'forbidden_roles',
                   'required_features', 'forbidden_features', 'layout_family', 'closed_loop'}

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)

def content_hash(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()

@dataclass(frozen=True)
class DesignIntent:
    subject: str
    constraints: dict = field(default_factory=dict)
    choices: dict = field(default_factory=dict)
    program_roles: tuple = ('primary',)
    features: tuple = ()
    domain: str = 'building'

    @classmethod
    def from_data(cls, data):
        if not isinstance(data, dict): raise ValueError('intent must be an object')
        subject=data.get('subject')
        if not isinstance(subject,str) or not subject.strip(): raise ValueError('subject required')
        constraints=data.get('constraints',data.get('user_constraints',{}))
        choices=data.get('choices',{})
        if not isinstance(constraints,dict) or not isinstance(choices,dict): raise ValueError('constraints and choices must be objects')
        if set(constraints)-CONSTRAINT_KEYS: raise ValueError('unsupported hard constraints: '+', '.join(sorted(set(constraints)-CONSTRAINT_KEYS)))
        if 'levels' in constraints and (type(constraints['levels']) is not int or not 1<=constraints['levels']<=30): raise ValueError('levels must be integer 1..30')
        if 'connected' in constraints and type(constraints['connected']) is not bool: raise ValueError('connected must be boolean')
        if 'closed_loop' in constraints and type(constraints['closed_loop']) is not bool: raise ValueError('closed_loop must be boolean')
        if 'layout_family' in constraints and (not isinstance(constraints['layout_family'],str) or not constraints['layout_family']): raise ValueError('layout_family must be a nonempty name')
        for key in ('required_roles','forbidden_roles','required_features','forbidden_features'):
            if key in constraints and (not isinstance(constraints[key],list) or any(not isinstance(v,str) or not v for v in constraints[key])): raise ValueError(key+' must be a list of names')
        roles=data.get('program_roles',['primary']);features=data.get('features',[])
        for values in (roles,features):
            if not isinstance(values,(list,tuple)) or any(not isinstance(v,str) or not v for v in values): raise ValueError('roles/features must contain names')
        if not roles: raise ValueError('at least one program role required')
        # Round-trip forbids mutable aliases and non-JSON/nonfinite inputs.
        return cls(subject,json.loads(canonical(constraints)),json.loads(canonical(choices)),tuple(roles),tuple(features),domain_name(data.get('domain',infer_domain(subject))))

    def to_data(self):
        return {'version':VERSION,'subject':self.subject,'constraints':self.constraints,
                'choices':self.choices,'program_roles':list(self.program_roles),'features':list(self.features),'domain':self.domain}

    @property
    def fingerprint(self): return content_hash(self.to_data())

def seed_streams(seed=None):
    """Fresh entropy by default; one recorded root gives independent stable streams."""
    if seed is None: seed=secrets.randbits(64)
    if type(seed) is not int or seed<0: raise ValueError('seed must be a nonnegative integer')
    def derive(name): return int.from_bytes(hashlib.sha256(f'{seed}:{name}'.encode()).digest()[:8],'big')
    return {'root':seed,**{name:derive(name) for name in ('design','camera','detail')}}
