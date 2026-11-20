"""Bind a physical design, display cut, raster and visible annotation targets.

Surface ownership is calculated-guide evidence, never artistic pixel evidence.
Coordinates are normalized so output resolution is not confused with camera.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def create(scene, display, renderer, guide):
    """Call AFTER renderer.draw and saving the guide; does not change the image."""
    path = Path(guide)
    with Image.open(path) as im:
        im.load()
        if im.format != 'PNG':
            raise ValueError('guide must be a decodable PNG')
        size = list(im.size)
    if display is not scene and display.get('representation', {}).get('type') == 'cutaway':
        if display['representation'].get('physical_sha256') != digest(scene):
            raise ValueError('display cut belongs to a different physical scene')
    from annotation_plan import create as annotation_create, signature
    from projection_review import review
    anchors = annotation_create(scene, renderer)
    projection = review(renderer, scene)
    return {'version': 2, 'scene_sha256': digest(scene), 'display_sha256': digest(display),
            'guide_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'image_size': size,
            'raster_size': [renderer.w, renderer.h], 'camera': scene.get('camera', {}),
            'annotations': anchors, 'annotations_sha256': signature(anchors),
            'ownership_sha256': hashlib.sha256(renderer.owner.astype('<i4').tobytes()).hexdigest(),
            'projection_review': projection, 'projection_review_sha256': digest(projection),
            'pixel_review': 'not_run',
            'scope': 'depth-tested guide surface ownership; artistic image requires independent review'}


def errors(scene, evidence, guide=None, *, renderer=None):
    if not isinstance(evidence, dict):
        return ['view evidence required']
    issues = []
    if evidence.get('scene_sha256') != digest(scene):
        issues.append('view evidence stale: physical scene changed')
    if evidence.get('camera') != scene.get('camera', {}):
        issues.append('view evidence camera changed')
    expected = {c['id']: c for c in scene.get('callouts', [])}
    records = evidence.get('annotations', [])
    if not isinstance(records, list):
        return issues + ['annotation evidence must be a list']
    if evidence.get('version') == 2:
        from annotation_plan import errors as annotation_errors, signature
        issues.extend(annotation_errors(records, renderer))
        if evidence.get('annotations_sha256') != signature(records): issues.append('annotation routes or tips changed after binding')
        if renderer is not None and evidence.get('ownership_sha256') != hashlib.sha256(renderer.owner.astype('<i4').tobytes()).hexdigest():
            issues.append('annotation ownership raster changed')
        projection = evidence.get('projection_review')
        if not isinstance(projection, dict) or evidence.get('projection_review_sha256') != digest(projection):
            issues.append('projection review changed or missing from guide evidence')
        elif projection.get('image_size') != evidence.get('raster_size'):
            issues.append('projection review raster differs from guide evidence')
    elif evidence.get('version', 1) != 1:
        issues.append('unsupported view evidence version')
    found = set()
    for item in records:
        if not isinstance(item, dict):
            issues.append('invalid annotation evidence'); continue
        label = expected.get(item.get('id'))
        if label is None or any(item.get(k) != label[k] for k in ('target', 'text')):
            issues.append('annotation evidence differs from label contract')
        if item.get('id') in found:
            issues.append('duplicate annotation evidence')
        found.add(item.get('id'))
        point = item.get('tip_xy')
        if not isinstance(point, list) or len(point) != 2 or any(type(v) not in (int, float) or not 0 < v < 1 for v in point):
            issues.append('annotation anchor must be inside the raster')
        if type(item.get('visible_guide_pixels')) != int or item['visible_guide_pixels'] < 9:
            issues.append('annotation target visibility missing')
    if found != set(expected):
        issues.append('annotation evidence incomplete')
    if guide is not None:
        path = Path(guide)
        if hashlib.sha256(path.read_bytes()).hexdigest() != evidence.get('guide_sha256'):
            issues.append('guide pixels differ from bound evidence')
        with Image.open(path) as im:
            im.load()
            if list(im.size) != evidence.get('image_size'):
                issues.append('guide size differs from bound evidence')
    return issues
