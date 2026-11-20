"""Versioned visual intent. Never changes geometry or replaces physical gates.

Plans are opt-in; absent plans remain ``not_run`` rather than gaining invented
intent. All quantitative observations concern the calculated guide, not final art.
"""
from dataclasses import asdict, dataclass, field, fields
import math


def _number(value, lo, hi, name):
    if type(value) not in (int, float) or not math.isfinite(value) or not lo <= value <= hi:
        raise ValueError(name + ': finite number outside allowed range')


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(name + ': nonempty text required')


def _ids(value, name):
    if not isinstance(value, (list, tuple)) or any(not isinstance(v, str) or not v.strip() for v in value) or len(set(value)) != len(value):
        raise ValueError(name + ': unique nonempty IDs required')


def _size(value):
    if not isinstance(value, (list, tuple)) or len(value) != 2 or any(type(v) != int or not 64 <= v <= 8192 for v in value):
        raise ValueError('usage_size: two integer dimensions 64..8192 required')


def _parse(cls, raw):
    if not isinstance(raw, dict):
        raise ValueError(cls.__name__ + ': object required')
    unknown = set(raw) - {f.name for f in fields(cls)}
    if unknown:
        raise ValueError(cls.__name__ + ': unknown fields ' + ', '.join(sorted(unknown)))
    try:
        return cls(**raw)
    except TypeError as exc:
        raise ValueError(cls.__name__ + ': ' + str(exc)) from exc


@dataclass(frozen=True)
class QuietRegion:
    id: str
    reason: str

    def __post_init__(self):
        _text(self.id, 'quiet ID'); _text(self.reason, 'quiet reason')


@dataclass(frozen=True)
class VisualLayer:
    name: str
    ids: list
    role: str

    def __post_init__(self):
        _text(self.name, 'layer name'); _text(self.role, 'layer role'); _ids(self.ids, 'layer IDs')


@dataclass(frozen=True)
class SubjectFraming:
    ids: list
    purpose: str
    min_width_fraction: float = .5
    min_height_fraction: float = .3
    min_owned_area_fraction: float = .03
    require_in_frame: bool = True

    def __post_init__(self):
        _ids(self.ids, 'framing subject IDs'); _text(self.purpose, 'framing purpose')
        if not self.ids: raise ValueError('subject framing needs physical IDs')
        for name in ('min_width_fraction', 'min_height_fraction', 'min_owned_area_fraction'):
            _number(getattr(self, name), 0, 1, name)
        if type(self.require_in_frame) != bool: raise ValueError('require_in_frame must be boolean')


@dataclass(frozen=True)
class VisualPlan:
    objective: str
    primary: list
    secondary: list = field(default_factory=list)
    critical_witnesses: list = field(default_factory=list)
    readable: list = field(default_factory=list)
    full: list = field(default_factory=list)
    quiet: list = field(default_factory=list)
    layers: list = field(default_factory=list)
    usage_size: list = field(default_factory=lambda: [1024, 1024])
    min_readable_pixels: float = 9
    min_readable_span: float = 2
    view_intent: str = 'free'
    subject_framing: dict | None = None
    version: int = 1

    def __post_init__(self):
        _text(self.objective, 'reading objective')
        for name in ('primary', 'secondary', 'critical_witnesses', 'readable', 'full'):
            _ids(getattr(self, name), name)
        if not self.primary:
            raise ValueError('VisualPlan needs a primary subject')
        if set(self.primary) & set(self.secondary):
            raise ValueError('primary and secondary roles overlap')
        if self.view_intent not in {'free', 'plan', 'elevation', 'exterior', 'interior', 'section', 'cutaway', 'detail'}:
            raise ValueError('unsupported view intent')
        _size(self.usage_size)
        _number(self.min_readable_pixels, 1, 65536, 'min_readable_pixels')
        _number(self.min_readable_span, 1, 1024, 'min_readable_span')
        if type(self.version) != int or self.version != 1: raise ValueError('unsupported VisualPlan version')
        object.__setattr__(self, 'quiet', [asdict(_parse(QuietRegion, raw)) for raw in self.quiet])
        object.__setattr__(self, 'layers', [asdict(_parse(VisualLayer, raw)) for raw in self.layers])
        if self.subject_framing is not None:
            object.__setattr__(self, 'subject_framing', asdict(_parse(SubjectFraming, self.subject_framing)))


@dataclass(frozen=True)
class ContextEntity:
    id: str
    role: str
    reason: str
    physical: bool = True
    family: str = ''

    def __post_init__(self):
        _text(self.id, 'context ID'); _text(self.reason, 'context reason')
        if self.role not in {'scale', 'support', 'access', 'use', 'location', 'atmosphere'}:
            raise ValueError('unsupported context role')
        if type(self.physical) != bool: raise ValueError('physical must be boolean')
        if not isinstance(self.family, str): raise ValueError('context family must be text')
        if not self.physical and self.role in {'support', 'access', 'use', 'scale'}:
            raise ValueError('support, access, use and scale context must be physical')


@dataclass(frozen=True)
class ContextPlan:
    mode: str
    entities: list = field(default_factory=list)
    exclusions: list = field(default_factory=list)
    protected_ids: list = field(default_factory=list)
    max_entities: int = 20
    max_area_fraction: float = .35
    exact_counts: dict = field(default_factory=dict)
    version: int = 1

    def __post_init__(self):
        if self.mode not in {'isolated', 'situated', 'interior', 'landscape'}:
            raise ValueError('unsupported setting mode')
        if type(self.version) != int or self.version != 1: raise ValueError('unsupported ContextPlan version')
        if type(self.max_entities) != int or not 0 <= self.max_entities <= 1000:
            raise ValueError('max_entities must be integer 0..1000')
        _number(self.max_area_fraction, 0, 1, 'max_area_fraction')
        _ids(self.exclusions, 'context exclusions'); _ids(self.protected_ids, 'protected IDs')
        if not isinstance(self.exact_counts, dict) or any(not isinstance(k, str) or type(v) != int or v < 0 for k, v in self.exact_counts.items()):
            raise ValueError('exact_counts must map kind to nonnegative integer')
        entities = [_parse(ContextEntity, raw) for raw in self.entities]
        object.__setattr__(self, 'entities', [asdict(e) for e in entities])
        _ids([e.id for e in entities], 'context IDs')
        if len(entities) > self.max_entities: raise ValueError('context entity budget exceeded')
        if self.mode == 'isolated' and entities: raise ValueError('isolated context cannot add entities')


@dataclass(frozen=True)
class DetailRegion:
    name: str
    primary: list
    secondary: list = field(default_factory=list)
    critical: list = field(default_factory=list)
    microdetails: list = field(default_factory=list)
    quietReason: str = ''
    quiet_kind: str = ''
    min_area_pixels: float = 9
    min_span_pixels: float = 2

    def __post_init__(self):
        _text(self.name, 'detail region name')
        for name in ('primary', 'secondary', 'critical'): _ids(getattr(self, name), name)
        if not self.primary: raise ValueError('detail region needs primary IDs')
        if not isinstance(self.microdetails, list) or any(not isinstance(v, str) or not v.strip() for v in self.microdetails):
            raise ValueError('microdetails must be descriptions')
        if self.quietReason:
            _text(self.quietReason, 'quietReason')
            if self.quiet_kind not in {'clean_glazing', 'unadorned_surface', 'subpixel_secondary', 'protected_reading_space'}:
                raise ValueError('quiet region requires a supported contextual quiet_kind')
        elif self.quiet_kind or not self.secondary:
            raise ValueError('region without secondary detail requires contextual quietReason')
        _number(self.min_area_pixels, 1, 65536, 'detail pixel area')
        _number(self.min_span_pixels, 1, 1024, 'detail span')


@dataclass(frozen=True)
class DetailBudget:
    regions: list
    usage_size: list = field(default_factory=lambda: [1024, 1024])
    version: int = 1

    def __post_init__(self):
        if type(self.version) != int or self.version != 1: raise ValueError('unsupported DetailBudget version')
        _size(self.usage_size)
        regions = [_parse(DetailRegion, raw) for raw in self.regions]
        object.__setattr__(self, 'regions', [asdict(r) for r in regions])
        _ids([r.name for r in regions], 'detail region names')
        if not regions: raise ValueError('DetailBudget needs regions')


@dataclass(frozen=True)
class MaterialSpec:
    family: str
    origin: list = field(default_factory=lambda: [0, 0, 0])
    axis: list = field(default_factory=lambda: [0, 0, 1])
    tangent: list = field(default_factory=lambda: [1, 0, 0])
    mapping: str = 'planar'
    spacing: float = .12
    density: float = .12
    base_value: float = 232
    mark: str = 'auto'
    vertex_uv: list = field(default_factory=list)

    def __post_init__(self):
        if self.family not in {'matte_metal', 'glass', 'concrete', 'wood', 'stone', 'cloth', 'rubber'}:
            raise ValueError('unsupported material family')
        if self.mapping not in {'planar', 'cylindrical', 'registered'}: raise ValueError('unsupported surface mapping')
        if self.mapping == 'registered':
            from surface_mapping import uv_array
            uv_array(self.vertex_uv)
        elif self.vertex_uv: raise ValueError('vertex_uv requires registered mapping')
        if self.mark not in {'auto', 'none', 'cross', 'axial', 'grain', 'endgrain', 'stipple'}: raise ValueError('unsupported mark grammar')
        for name in ('origin', 'axis', 'tangent'):
            v = getattr(self, name)
            if not isinstance(v, (list, tuple)) or len(v) != 3: raise ValueError(name + ': XYZ required')
            for x in v: _number(x, -1e9, 1e9, name)
        aa = sum(v*v for v in self.axis); tt = sum(v*v for v in self.tangent)
        dot = sum(a*b for a,b in zip(self.axis, self.tangent))
        if aa <= 1e-12 or tt <= 1e-12 or abs(dot) > 1e-6 * math.sqrt(aa*tt):
            raise ValueError('material axis and tangent must be nonzero perpendicular vectors')
        _number(self.spacing, .00001, 1e5, 'material spacing')
        _number(self.density, 0, .8, 'material density')
        _number(self.base_value, 24, 250, 'material value')


@dataclass(frozen=True)
class LightMaterialPlan:
    key_direction: list = field(default_factory=lambda: [-.6, .8, 1.5])
    ambient: float = .7
    key_strength: float = .3
    shadow_strength: float = .12
    materials: dict = field(default_factory=dict)
    value_policy: str = 'neutral'
    line_weights: list = field(default_factory=lambda: [1.8, 1, .55])
    version: int = 1

    def __post_init__(self):
        if type(self.version) != int or self.version != 1: raise ValueError('unsupported LightMaterialPlan version')
        if not isinstance(self.key_direction, (list, tuple)) or len(self.key_direction) != 3:
            raise ValueError('key_direction needs XYZ')
        for v in self.key_direction: _number(v, -1e6, 1e6, 'key_direction')
        if sum(v*v for v in self.key_direction) <= 1e-12: raise ValueError('key_direction is zero')
        for name in ('ambient', 'key_strength', 'shadow_strength'): _number(getattr(self, name), 0, 1, name)
        if self.ambient + self.key_strength > 1.000001: raise ValueError('ambient + key_strength exceeds 1')
        if self.value_policy not in {'neutral', 'dark_interior', 'open_air', 'diagram'}: raise ValueError('unsupported value policy')
        if not isinstance(self.line_weights, (list, tuple)) or len(self.line_weights) != 3:
            raise ValueError('three relative line weights required')
        for weight in self.line_weights: _number(weight, .1, 4, 'line weight')
        if not self.line_weights[0] > self.line_weights[1] > self.line_weights[2]: raise ValueError('line weights must descend: silhouette, construction, detail')
        if not isinstance(self.materials, dict): raise ValueError('materials must map existing IDs to materials')
        for key in self.materials: _text(key, 'material owner')
        object.__setattr__(self, 'materials', {key: asdict(_parse(MaterialSpec, spec)) for key, spec in self.materials.items()})


def usage_metrics(component, report, size=(1024, 1024)):
    """Equivalent visible area/span at a fixed use size; never raw supersamples."""
    image = report.get('image_size')
    if image and len(image) == 2 and min(image) > 0:
        area = component.get('visible_pixels', 0) * size[0]*size[1]/(image[0]*image[1])
        box = component.get('bbox', [])
        span = min((box[2]-box[0]+1)*size[0]/image[0], (box[3]-box[1]+1)*size[1]/image[1]) if len(box) == 4 else min(component.get('width_fraction', 0)*size[0], component.get('height_fraction', 0)*size[1])
        return area, span
    # Historical reports can rank by raw pixels, but have no normalized span evidence.
    return component.get('visible_pixels', 0), None


def subject_metrics(report, identifiers):
    """Union of owned subject pixels, excluding context by explicit ID contract."""
    components=report.get('components',{});size=report.get('image_size',[0,0])
    boxes=[components.get(key,{}).get('bbox',[]) for key in identifiers]
    boxes=[box for box in boxes if len(box)==4]
    box=[min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)] if boxes else []
    return {'width_fraction':(box[2]-box[0]+1)/size[0] if box and size[0] else 0,
            'height_fraction':(box[3]-box[1]+1)/size[1] if box and size[1] else 0,
            'owned_area_fraction':sum(components.get(key,{}).get('area_fraction',0) for key in identifiers),
            'bbox':box,'visible_components':sum(components.get(key,{}).get('visible_pixels',0)>0 for key in identifiers)}


def compile_visual_contract(scene, *, evidence=None):
    """Compile supplied plans and validate ID links. Returns errors, never mutates.

    ``evidence`` is projection_review.review output; absent evidence leaves the
    guide gate not_run. Even a passed result says nothing about physical validity.
    """
    plans = {}; issues = []
    classes = {'visual_plan': VisualPlan, 'context_plan': ContextPlan,
               'detail_budget': DetailBudget, 'light_material_plan': LightMaterialPlan}
    from actor_plan import ActorPlan
    classes['actor_plan'] = ActorPlan
    by_id = {p['id']: p for p in scene.get('parts', [])}
    known = set(by_id)
    for name, cls in classes.items():
        if name not in scene: continue
        try: plans[name] = asdict(_parse(cls, scene[name]))
        except (ValueError, TypeError) as exc: issues.append(name + ': ' + str(exc))
    def references(ids, path):
        for key in ids:
            if key not in known: issues.append(path + ': unknown physical ID ' + key)
    visual = plans.get('visual_plan', {})
    for name in ('primary', 'secondary', 'readable', 'full'): references(visual.get(name, []), name)
    for region in visual.get('quiet', []): references([region['id']], 'quiet')
    for layer in visual.get('layers', []): references(layer['ids'], 'layer')
    framing=visual.get('subject_framing')
    if framing: references(framing['ids'], 'framing subject')
    junctions = {j['id'] for j in scene.get('camera_junctions', [])}
    for key in visual.get('critical_witnesses', []):
        if key not in junctions: issues.append('unknown critical witness: ' + key)
    if visual.get('view_intent') == 'plan' and scene.get('camera', {}).get('projection', 'orthographic') != 'orthographic':
        issues.append('plan view requires orthographic projection')
    context = plans.get('context_plan', {})
    physical_context = []
    for entity in context.get('entities', []):
        if entity['physical']:
            references([entity['id']], 'context'); physical_context.append(entity['id'])
        elif entity['id'] in known: issues.append('physical scene entity cannot be declared atmosphere: ' + entity['id'])
    references(context.get('protected_ids', []), 'protected context')
    for key in context.get('exclusions', []):
        if key in known or any(p.get('kind') == key for p in by_id.values()): issues.append('excluded entity present: ' + key)
    for kind, count in context.get('exact_counts', {}).items():
        if sum(p.get('kind') == kind for p in by_id.values()) != count: issues.append('context exact count mismatch: ' + kind)
    materials = plans.get('light_material_plan', {}).get('materials', {})
    references(materials, 'material')
    from surface_mapping import material_errors
    for key, spec in materials.items():
        if key in by_id: issues.extend(material_errors(by_id[key], spec))
    if 'actor_plan' in plans:
        from actor_plan import errors as actor_errors
        issues.extend(actor_errors(scene, plans['actor_plan']))
    budget = plans.get('detail_budget', {})
    for region in budget.get('regions', []):
        for name in ('primary', 'secondary', 'critical'): references(region[name], 'detail ' + region['name'])
        if not set(region['critical']) <= set(region['primary'] + region['secondary']): issues.append('critical detail outside region: ' + region['name'])
        if region['quiet_kind'] == 'clean_glazing' and not all(materials.get(k, {}).get('family') == 'glass' or by_id.get(k, {}).get('kind') in {'window', 'curtain_panel'} for k in region['primary']):
            issues.append('clean_glazing quiet region must identify glass')
        if region['quiet_kind'] == 'protected_reading_space' and not set(region['primary']) <= set(context.get('protected_ids', [])):
            issues.append('quiet region lacks protected context IDs')
    guide_issues = []
    if evidence is not None:
        components = evidence.get('components', {})
        if framing:
            metrics=subject_metrics(evidence,framing['ids'])
            for name in ('width_fraction','height_fraction','owned_area_fraction'):
                if metrics[name]<framing['min_'+name]:guide_issues.append('occupied subject framing too small: '+name)
            if framing['require_in_frame']:
                for key in framing['ids']:
                    if not components.get(key,{}).get('fully_in_frame'):guide_issues.append('occupied subject clipped: '+key)
        for key in set(visual.get('primary', []) + visual.get('readable', []) + context.get('protected_ids', [])):
            comp = components.get(key, {}); area, span = usage_metrics(comp, evidence, visual.get('usage_size', [1024, 1024]))
            if comp.get('visible_pixels', 0) <= 0 or area < visual.get('min_readable_pixels', 9) or span is not None and span < visual.get('min_readable_span', 2):
                guide_issues.append('subject lacks usable guide surface: ' + key)
        for key in visual.get('full', []):
            if not components.get(key, {}).get('fully_in_frame'): guide_issues.append('clipped required subject: ' + key)
        for key in visual.get('critical_witnesses', []):
            witness = evidence.get('junctions', {}).get(key, {})
            if not witness.get('visible') or witness.get('relation_errors'): guide_issues.append('critical witness not demonstrated: ' + key)
        used = sum(components.get(key, {}).get('area_fraction', 0) for key in physical_context)
        if context and used > context['max_area_fraction']: guide_issues.append('context exceeds visible area budget')
        for region in budget.get('regions', []):
            for key in set(region['secondary'] + region['critical']):
                area, span = usage_metrics(components.get(key, {}), evidence, budget['usage_size'])
                if area < region['min_area_pixels'] or span is not None and span < region['min_span_pixels']:
                    guide_issues.append('detail lacks usable guide pixels: ' + region['name'] + '/' + key)
    return {'version': 1, 'status': 'failed' if issues or guide_issues else 'passed' if plans else 'not_run',
            'compatibility': 'explicit_plans' if plans else 'legacy_no_visual_plans',
            'plans': plans, 'errors': issues + guide_issues,
            'guide_status': 'failed' if guide_issues else 'passed' if evidence is not None and plans else 'not_run',
            'limits': 'intent and guide evidence only; physical validation and final-pixel review are independent gates'}


def errors(scene, contract=None, *, evidence=None):
    result = compile_visual_contract(scene, evidence=evidence)
    issues = list(result['errors'])
    if contract is not None and contract.get('plans') != result['plans']:
        issues.append('visual contract changed since compilation')
    return issues
