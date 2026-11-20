"""General illustration delivery with persistent evidence, not CAD certification.

The strict registered workflow remains available separately. Unsupported numerical
checks are disclosed here; actual failures never become permission to generate.
"""
import argparse
import json
import shutil
import uuid
from pathlib import Path
from history_run import new_run, STAGES
from run_manifest import digest, sha, source_identity
from pixel_review import image_identity
from route_continuity import inspect as continuity_report, review_keys, finish_rules

import perspective_contract as perspective
import architecture_continuity as architecture
from creation_identity import check_attempt

ROOT = Path(__file__).resolve().parents[1]
STATES = {'visible_correct', 'visible_error', 'uncertain', 'occluded'}
BASE_REVIEW = ('subject', 'perspective', 'detail', 'paper_tone', 'connections',
               'supports', 'circulation', 'annotations')

def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        if isinstance(value, str): stream.write(value)
        else: json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def assess(scene=None):
    """Recompute evidence; no caller-supplied 'passed' report is accepted."""
    if scene is None:
        return {'status': 'limited', 'checks': [{'check': 'numerical_geometry',
                'status': 'not_run', 'message': 'No full schema-v2 model supplied. Separate guide/continuity checks retain their own scope.'}]}
    if scene.get('schema_version') != 2 or scene.get('validation_policy') != 'strict':
        raise ValueError('Numerical models must retain schema-v2 strict checks; do not downgrade.')
    from scene_model import validation_report
    report = validation_report(scene)
    checks = report.get('checks', [])
    failures = [c for c in checks if c['status'] == 'failed']
    unknown = [c for c in checks if c['status'] not in ('passed', 'not_applicable')]
    return {'status': 'failed' if failures else 'limited' if unknown else 'passed',
            'checks': checks, 'scope': 'Applicable represented geometry only; no loads or hidden engineering.'}

def validate_plan(plan):
    perspective.validate(plan.get("perspective_contract"))
    for key in ('subject', 'view', 'setting', 'composition', 'detail', 'relationships'):
        if not plan.get(key): raise ValueError('Plan requires ' + key)
    if not isinstance(plan['relationships'], dict): raise ValueError('Named relationships required')
    if any(not isinstance(v, str) or not v.strip() for v in plan['relationships'].values()):
        raise ValueError('Describe each support, connection or spatial relationship')
    stages = plan.get('stages', [])
    if len(stages) != 8: raise ValueError('Eight proportional stage decisions required')
    for stage in stages:
        if stage.get('status') not in ('planned', 'not_applicable') or not stage.get('reason'):
            raise ValueError('Stage needs a decision and scope reason, not an invented approval')
    if not isinstance(plan.get('annotations'), list): raise ValueError('Explicit annotation list required; [] means none')
    if plan.get('route_scope') not in (None, 'present', 'absent'):
        raise ValueError('route_scope must be present or absent when supplied')
    if plan.get('route_scope') == 'present' and plan.get('continuity') is None:
        raise ValueError('Describe route starts and ends in continuity; no numerical adapter is required')
    if plan.get('route_scope') == 'absent' and plan.get('continuity') is not None:
        raise ValueError('Route scope contradicts the continuity inventory')
    continuity = continuity_report(plan.get('continuity'))
    if continuity['status'] == 'failed': raise ValueError('; '.join(continuity['errors']))

def compile_prompt(plan, brief):
    validate_plan(plan)
    architecture.validate(plan, brief)
    style = (ROOT / 'references/art-direction.md').read_text(encoding='utf-8')
    return ('PHASE 1: Create ONLY the graphite/ink illustrated PNG of the scene. Color editing is a separate subsequent operation; do not produce two panels or a colored version now. Original user brief:\n' + brief +
            '\n\nResolved scene and represented scope:\n' + json.dumps(plan, ensure_ascii=False, indent=2) +
            '\n\nWritten art direction:\n' + style +
            '\n\nThe guide, if supplied, constrains major spatial routes and proportions, not rendering quality. '
            'Develop all planned secondary assemblies and fine construction detail; do not copy sparse guide shading. '
            'Preserve connections, contacts and a usable passage. Unsupported numerical checks are not proof of correctness. '
            'Render only requested annotations from the list; an empty list means NO labels, arrows or other explanatory text. '
            'No panels, tutorial steps, report, guide overlay or extra views in the final image.' + finish_rules(plan) + perspective.rules(plan) + architecture.rules(plan))

def prepare(project, stem, brief, plan, scene=None, guide=None, sources=(), run=None, client=None):
    run = Path(run) if run else new_run(project, stem, brief)
    if (run/'01-site/brief.txt').read_text(encoding='utf-8') != brief:
        raise ValueError('Original brief differs from run history')
    attempt = run/'08-finish'/('illustration-' + uuid.uuid4().hex[:12])
    attempt.mkdir()
    save(attempt/'plan.json', plan)
    try:
        if (run/'operation.json').exists(): shutil.copyfile(run/'operation.json',attempt/'operation.json')
        validate_plan(plan)
        coverage = assess(scene)
        continuity = continuity_report(plan.get('continuity'))
        save(attempt/'continuity.json', continuity)
        if plan.get('continuity') is not None:
            coverage['route_continuity'] = continuity
            coverage['checks'].append({'check':'route_continuity', 'status':continuity['status'],
                'message':'Declared route destinations checked; see continuity.json for scope and pixel-review limits.'})
        save(attempt/'coverage.json', coverage)
        if scene is not None: save(attempt/'scene.json', scene)
        if coverage['status'] == 'failed': raise ValueError('Detected geometry failure; repair before generation')
        for stage, decision in zip(STAGES, plan['stages']):
            save(run/stage/(attempt.name + '.json'), decision)
        if guide:
            check_attempt(attempt,guide)
            image_identity(guide)
            shutil.copyfile(guide, attempt/'guide.png')
        for index, source in enumerate(sources):
            dest = attempt/'sources'; dest.mkdir(exist_ok=True)
            shutil.copyfile(source, dest/(str(index) + '-' + Path(source).name))
        prompt = compile_prompt(plan, brief)
        save(attempt/'prompt.txt', prompt)
        request = {'prompt': prompt, 'transparent_background': False}
        if guide: request['referenced_image_paths'] = [str((attempt/'guide.png').resolve())]
        save(attempt/'request.json', request)
        save(attempt/'source.json', {'skill': source_identity(ROOT), 'client': client or {},
             'image_model': 'unknown unless the tool exposes it', 'mode': 'reviewed_illustration', 'perspective_coverage': 'group_review' if plan.get('perspective_contract') else 'legacy_unstructured'})
        hashes = {p.relative_to(attempt).as_posix(): sha(p) for p in attempt.rglob('*') if p.is_file()}
        save(attempt/'receipt.json', {'files': hashes, 'brief_sha256': sha(run/'01-site/brief.txt')})
    except Exception as exc:
        save(attempt/'failure.json', {'error': str(exc)})
        raise
    return attempt

def verify(attempt):
    attempt = Path(attempt)
    receipt = read(attempt/'receipt.json')
    for name, expected in receipt['files'].items():
        p = (attempt/name).resolve()
        if attempt.resolve() not in p.parents or not p.is_file() or sha(p) != expected:
            raise ValueError('Prepared evidence changed: ' + name)
    run = attempt.parent.parent
    if sha(run/'01-site/brief.txt') != receipt['brief_sha256']: raise ValueError('Original brief changed')
    return read(attempt/'plan.json')

def retain(attempt, image, actual_request):
    """Bind actual request and actual generated bytes; preserve every result."""
    attempt = Path(attempt); verify(attempt)
    if actual_request != read(attempt/'request.json'): raise ValueError('Tool request differs from prepared request')
    identity = image_identity(image)
    result = attempt/('result-' + uuid.uuid4().hex[:12]); result.mkdir()
    shutil.copyfile(image, result/'original.png')
    save(result/'generation.json', {'request': actual_request, 'image': identity})
    try: check_attempt(attempt,result/'original.png')
    except ValueError as exc:
        save(result/'rejected.json',{'error':str(exc)}); raise
    return result/'original.png'

def review(attempt, image, observations):
    plan = verify(attempt)
    required = set(BASE_REVIEW) | set(plan['relationships']) | review_keys(plan) | perspective.keys(plan) | architecture.keys(plan)
    if set(observations) != required: raise ValueError('Review must cover ' + ', '.join(sorted(required)))
    for item in observations.values():
        if item.get('status') not in STATES or not item.get('notes', '').strip():
            raise ValueError('Actual pixel observations and uncertainty required')
    perspective.review(plan, observations)
    states = {item['status'] for item in observations.values()}
    result = {'image': image_identity(image), 'plan_sha256': digest(plan), 'observations': observations,
              'status': 'needs_correction' if 'visible_error' in states else 'limited' if states != {'visible_correct'} else 'reviewed'}
    path = Path(image).parent/('review-' + uuid.uuid4().hex[:12] + '.json')
    save(path, result)
    return path

def correction(attempt, image, review_path, instructions):
    """At most two local corrections; changed design requires a new preparation."""
    attempt = Path(attempt).resolve(); image = Path(image).resolve(); verify(attempt)
    if attempt not in image.parents: raise ValueError('Correct a retained original from this attempt')
    record = read(review_path)
    if record['image'] != image_identity(image): raise ValueError('Review is not for these pixels')
    if read(image.parent/'generation.json')['image'] != record['image']: raise ValueError('Generated original changed')
    number = len(list(attempt.glob('correction-*.json'))) + 1
    if number > 2: raise ValueError('Two-correction budget exhausted; report remaining defects')
    if number > 1:
        previous = read(attempt/('correction-' + str(number-1) + '.json'))['request']
        if read(image.parent/'generation.json')['request'] != previous:
            raise ValueError('Inspect the preceding correction result before another correction')
    request = {'prompt': instructions + finish_rules(verify(attempt)), 'referenced_image_paths': [str(Path(image).resolve())], 'transparent_background': False}
    save(attempt/('correction-' + str(number) + '.json'), {'request': request, 'source_image': image_identity(image), 'review': record})
    return request

def retain_correction(attempt, image, actual_request):
    attempt = Path(attempt); verify(attempt)
    requests = [read(p)['request'] for p in attempt.glob('correction-*.json')]
    if actual_request not in requests: raise ValueError('Unprepared correction request')
    result = attempt/('result-' + uuid.uuid4().hex[:12]); result.mkdir()
    identity = image_identity(image); shutil.copyfile(image, result/'original.png')
    save(result/'generation.json', {'request': actual_request, 'image': identity})
    try: check_attempt(attempt,result/'original.png')
    except ValueError as exc:
        save(result/'rejected.json',{'error':str(exc)}); raise
    return result/'original.png'

def accept(attempt, image, review_path, destination):
    attempt = Path(attempt).resolve(); image = Path(image).resolve(); destination = Path(destination)
    plan = verify(attempt); record = read(review_path)
    check_attempt(attempt,image)
    if attempt not in image.parents: raise ValueError('Select a retained original from this attempt')
    identity = image_identity(image)
    generation = read(image.parent/'generation.json')
    allowed = [read(attempt/'request.json')] + [read(p)['request'] for p in attempt.glob('correction-*.json')]
    if generation['request'] not in allowed: raise ValueError('Generated request has no prepared history')
    if generation['image'] != identity or record['image'] != identity or record['plan_sha256'] != digest(plan):
        raise ValueError('Review or generated pixels changed')
    # Recheck review shape rather than trusting a forged summary status.
    required = set(BASE_REVIEW) | set(plan['relationships']) | review_keys(plan) | perspective.keys(plan) | architecture.keys(plan)
    if set(record['observations']) != required: raise ValueError('Incomplete review')
    values = list(record['observations'].values())
    if any(v.get('status') not in STATES or not v.get('notes','').strip() for v in values): raise ValueError('Invalid review')
    perspective.review(plan, record['observations'])
    known_errors = [k for k,v in record['observations'].items() if v['status']=='visible_error']
    completed = {digest(read(p)['request']) for p in attempt.glob('result-*/generation.json')}
    correction_count = sum(digest(read(p)['request']) in completed for p in attempt.glob('correction-*.json'))
    if known_errors and correction_count < 2:
        raise ValueError('Correct observed errors before accepting; budget remains')
    if destination.exists(): raise FileExistsError('Do not overwrite a previous result')
    limits = [c['message'] for c in read(attempt/'coverage.json')['checks'] if c['status'] not in ('passed','not_applicable')]
    limits += [k + ': ' + v['notes'] for k,v in record['observations'].items() if v['status'] != 'visible_correct']
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as stream: stream.write(image.read_bytes())
    outcome = {'mode': 'reviewed_illustration', 'final': str(destination.resolve()), 'image': image_identity(destination),
               'limitations': limits, 'known_visual_errors': known_errors, 'review': str(Path(review_path).resolve()),
               'claim': 'Visual illustration; no load, manufacturing or hidden-system certification.'}
    save(attempt/('selected-' + uuid.uuid4().hex[:12] + '.json'), outcome)
    if (attempt/'delivery-pipeline.json').is_file():
        from delivery_pipeline import checkpoint
        outcome['next_action'] = checkpoint(attempt/'delivery-pipeline.json')
    return outcome

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--stem', required=True)
    parser.add_argument('--brief-file', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--scene', type=Path)
    parser.add_argument('--guide', type=Path)
    args = parser.parse_args()
    print(prepare(args.project, args.stem, args.brief_file.read_text(encoding='utf-8-sig'), read(args.plan),
                  read(args.scene) if args.scene else None, args.guide))
