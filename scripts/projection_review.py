"""Compare projected guide evidence; never certify geometry or artistic pixels.

Call review after drawing each candidate. No camera angle is prescribed here.
"""
import math

import numpy as np
from visual_contract import usage_metrics


def _junctions(renderer, scene):
    records = {}
    for spec in scene.get('camera_junctions', []):
        key = spec['id']
        if key in records:
            raise ValueError('duplicate camera junction: ' + key)
        owners = list(spec['owners'])
        if len(set(owners)) < 2:
            raise ValueError('camera junction needs at least two distinct owners')
        point = np.asarray(spec['point'], dtype=float)
        radius = float(spec.get('radius_fraction', .012)) * min(renderer.w, renderer.h)
        minimum = int(spec.get('min_pixels', 2))
        if point.shape != (3,) or not np.isfinite(point).all() or not 0 < radius <= .1 * min(renderer.w, renderer.h) or minimum < 1:
            raise ValueError('invalid camera junction witness: ' + key)
        counts = {owner: 0 for owner in owners}
        projected = []
        try:
            projected = [float(v) for v in renderer.project(point)[:2]]
            x, y = projected
            inside = bool(0 <= x < renderer.w and 0 <= y < renderer.h)
            if inside:
                x0, x1 = max(0, math.floor(x-radius)), min(renderer.w, math.ceil(x+radius)+1)
                y0, y1 = max(0, math.floor(y-radius)), min(renderer.h, math.ceil(y+radius)+1)
                yy, xx = np.mgrid[y0:y1, x0:x1]
                near = (xx + .5-x)**2 + (yy + .5-y)**2 <= radius**2
                patch = renderer.owner[y0:y1, x0:x1]
                for owner in owners:
                    owner_id = renderer.part_ids.get(owner)
                    if owner_id is not None:
                        counts[owner] = int(np.count_nonzero(near & (patch == owner_id)))
        except ValueError:
            inside = False
        relation_errors = []
        if spec.get('relation_id') or scene.get('validation_policy') == 'strict':
            from relation_contracts import witness_errors
            relation_errors = witness_errors(scene, spec)
        scaled = {owner: count * 1024**2/(renderer.w*renderer.h) for owner, count in counts.items()}
        records[key] = {'point_xy': projected, 'owners': owners, 'owner_pixels': counts,
                        'required': bool(spec.get('required', True)), 'in_frame': inside,
                        'visible': inside and all(value >= minimum for value in scaled.values()) and not relation_errors,
                        'radius_pixels': radius, 'min_pixels': minimum,
                        'usage_owner_pixels': scaled, 'usage_size': [1024, 1024],
                        'relation_id': spec.get('relation_id'), 'relation_errors': relation_errors,
                        'physical_binding': 'failed' if relation_errors else 'linked' if spec.get('relation_id') else 'legacy_unbound'}
    return records


def review(renderer, scene):
    result = {}; ids = renderer.part_ids
    total = renderer.w * renderer.h
    for part in scene['parts']:
        mask = renderer.owner == ids.get(part['id'], -1); yy, xx = np.where(mask)
        try:
            o = np.asarray(part['origin']); size = np.asarray(part['size'])
            projected = np.array([renderer.project(o+size*[x,y,z]) for x in (0,1) for y in (0,1) for z in (0,1)])
            fully = bool(np.isfinite(projected).all() and np.all(projected[:,0] >= 0) and np.all(projected[:,0] < renderer.w)
                         and np.all(projected[:,1] >= 0) and np.all(projected[:,1] < renderer.h))
        except ValueError:
            fully = False
        result[part['id']] = {'visible_pixels': int(len(xx)), 'fully_in_frame': fully,
            'bbox': [] if not len(xx) else [int(xx.min()), int(yy.min()), int(xx.max()), int(yy.max())],
            'width_fraction': 0 if not len(xx) else float((xx.max()-xx.min()+1)/renderer.w),
            'height_fraction': 0 if not len(xx) else float((yy.max()-yy.min()+1)/renderer.h),
            'area_fraction': float(len(xx)/total)}
    regions = []
    for region in scene.get('detail_regions', []):
        visible = [key for key in region['secondary'] if result.get(key, {}).get('visible_pixels', 0) > 0]
        regions.append({'name': region['name'], 'visible_secondary': visible,
                        'hidden_secondary': [key for key in region['secondary'] if key not in visible]})
    kinds = {part['id']: part['kind'] for part in scene['parts']}
    floor = sum(value['visible_pixels'] for key, value in result.items() if kinds[key] in {'slab', 'paving'})
    return {'components': result, 'regions': regions, 'floor_fraction': floor/total,
            'image_size': [renderer.w, renderer.h], 'junctions': _junctions(renderer, scene),
            'limits': 'guide visibility and scale only; nearby owned surfaces do not prove contact, accessibility or artistic correctness'}


def _readability(component):
    """Saturating screen-space proxy, not a recognizable-detail classifier."""
    if component.get('visible_pixels', 0) <= 0:
        return 0.0
    if 'area_fraction' in component:
        # A thin silhouette spanning the frame must not count as a readable mass.
        return min(1.0, math.sqrt(max(0, component['area_fraction'])/.005))
    # Old reports did not include raster dimensions/areas. Retain useful ordering.
    return min(1.0, max(0, component.get('width_fraction', 0))/.2)


def rank(reports, required, focus, full=(), *, critical_junctions=None, readable=(), min_readable_pixels=9,
         usage_size=(1024, 1024), min_readable_span=2):
    """Return auditable admissibility and scores without inventing a camera.

    Focal IDs must have visible pixels. Readability uses a fixed usage_size when
    raster dimensions exist; legacy reports retain explicit raw-pixel behavior.
    Required junction IDs default to the union declared
    in reports, so omission from one report cannot silently bypass that gate.
    """
    if not focus:
        raise ValueError('at least one focal component required')
    if min_readable_pixels < 1:
        raise ValueError('min_readable_pixels must be positive')
    critical = set(critical_junctions) if critical_junctions is not None else {
        key for report in reports.values() for key, item in report.get('junctions', {}).items() if item.get('required', True)}
    records = []
    for name, report in reports.items():
        components = report['components']; failures = []
        for key in required:
            if components.get(key, {}).get('visible_pixels', 0) <= 0:
                failures.append('missing required component: ' + key)
        for key in full:
            if not components.get(key, {}).get('fully_in_frame', False):
                failures.append('clipped required component: ' + key)
        for key in focus:
            if key not in components:
                failures.append('unknown focal component: ' + key)
            elif components[key].get('visible_pixels', 0) <= 0:
                failures.append('hidden focal component: ' + key)
        for key in set(readable) | (set(focus) if report.get('image_size') else set()):
            area, span = usage_metrics(components.get(key, {}), report, usage_size)
            if area < min_readable_pixels or span is not None and span < min_readable_span:
                failures.append('insufficient readable pixels: ' + key)
        junctions = report.get('junctions', {})
        for key in sorted(critical):
            if not junctions.get(key, {}).get('visible', False) or junctions.get(key, {}).get('relation_errors'):
                failures.append('hidden or unmeasured critical junction: ' + key)
        if failures:
            records.append({'name': name, 'admissible': False, 'failures': failures, 'metrics': {}, 'score': None})
            continue
        focal = [components[key] for key in focus]
        if all('area_fraction' in c for c in focal):
            coverage = min(1.0, sum(c['area_fraction'] for c in focal)/.3)
        else:
            coverage = sum(_readability(c) for c in focal)/len(focal)
        detail_ids = set(readable)
        balances = []
        for region in report.get('regions', []):
            keys = set(region.get('visible_secondary', [])) | set(region.get('hidden_secondary', []))
            detail_ids.update(keys)
            if keys:
                balances.append(sum(_readability(components.get(key, {})) for key in keys)/len(keys))
        detail_ids.update(focus)
        amount = sum(_readability(components.get(key, {})) for key in detail_ids)/len(detail_ids)
        balance = min(balances) if balances else amount
        metrics = {'focal_coverage': coverage, 'readable_amount': amount, 'detail_balance': balance,
                   'focal_balance': min(_readability(c) for c in focal),
                   'junction_visibility': sum(bool(v.get('visible')) for v in junctions.values())/len(junctions) if junctions else 1.0,
                   'floor_fraction': min(1.0, max(0.0, report.get('floor_fraction', 0)))}
        score = (.30*coverage + .30*amount + .20*balance + .10*metrics['focal_balance']
                 + .10*metrics['junction_visibility'] - .02*metrics['floor_fraction'])
        records.append({'name': name, 'admissible': True, 'failures': [], 'metrics': metrics, 'score': score,
                        'readability_basis': 'normalized_usage_size' if report.get('image_size') else 'legacy_raw_pixels',
                        'usage_size': list(usage_size)})
    # Names break exact ties; no angle, view type or insertion order is preferred.
    return sorted(records, key=lambda item: (item['admissible'], item['score'] if item['score'] is not None else -1, item['name']), reverse=True)


def choose(reports, required, focus, full=(), **options):
    """Legacy entry point; use rank() as well when selection evidence is needed."""
    ranked = rank(reports, required, focus, full, **options)
    if not ranked or not ranked[0]['admissible']:
        raise ValueError('no candidate shows required subjects, framing and junctions; revise layout or cameras')
    return ranked[0]['name']
