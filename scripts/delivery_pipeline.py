"""Resume the requested artifact chain without treating an intermediate as done.

The agent executes image tools, modeling and visual reviews. This coordinator
prepares the color request and returns concrete pending work; it never invents
tool results or lowers the individual acceptance checks.
"""
import argparse
import json
import uuid
from pathlib import Path
from illustration_workflow import read, save, verify
from pixel_review import image_identity
from run_manifest import sha


def start(attempt, *, requested_3d=False, color=True):
    if type(requested_3d) is not bool or type(color) is not bool:
        raise ValueError('Explicit boolean output choices required')
    if requested_3d and not color:
        raise ValueError('Use standalone reconstruction for an existing single image')
    attempt = Path(attempt).resolve()
    verify(attempt)
    path = attempt/'delivery-pipeline.json'
    record = {'attempt': str(attempt), 'color': color, 'requested_3d': requested_3d}
    if path.exists():
        if read(path) != record:
            raise ValueError('Existing requested deliverables differ; do not silently change scope')
    else:
        save(path, record)
    return path


def attach_explorer(pipeline, job):
    record = read(pipeline)
    if not record['requested_3d']:
        raise ValueError('3D was not requested')
    job = Path(job).resolve()
    # Check actual source binding, not a nearby candidate from another run.
    pending = advance(pipeline)
    if pending['action'] not in ('build_3d', 'review_or_repair_3d'):
        raise ValueError('Finish the accepted colored image before attaching 3D')
    source = read(job/'source.json')
    colored = source['images'].get('coloreada.png')
    if not colored or Path(colored['path']).resolve() != Path(pending['source']).resolve() or colored['sha256'] != sha(pending['source']):
        raise ValueError('Explorer belongs to a different colored image')
    # Each repair is a new immutable link. The latest link selects the candidate.
    folder = Path(pipeline).parent
    from explorer_repair_cycle import latest
    existing = sorted(folder.glob('pipeline-explorer-*.json'))
    if existing:
        parent = Path(read(existing[-1])['job'])
        if parent.resolve() != job and latest(parent):
            inherited = job/'repair-parent.json'
            if inherited.exists() and Path(read(inherited)['job']).resolve() != parent.resolve():
                raise ValueError('Repair parent already bound')
            if not inherited.exists():
                save(inherited, {'job': str(parent.resolve())})
    index = len(list(folder.glob('pipeline-explorer-*.json')))+1
    save(folder/('pipeline-explorer-%06d.json' % index), {'job': str(job)})


def advance(pipeline):
    record = read(pipeline)
    attempt = Path(record['attempt'])
    verify(attempt)
    def pending(action, **data):
        return {'complete': False, 'action': action, **data}
    selected = sorted(attempt.glob('selected-*.json'), key=lambda p:p.stat().st_mtime_ns)
    if not selected:
        results = sorted(attempt.glob('result-*/original.png'))
        if results:
            return pending('review_illustration', attempt=str(attempt), originals=[str(p) for p in results])
        return pending('generate_illustration', request=str(attempt/'request.json'))
    choice = read(selected[-1]); illustrated = Path(choice['final'])
    if image_identity(illustrated) != choice['image']:
        raise ValueError('Accepted illustration changed')
    outputs = {'ilustrada': str(illustrated)}
    if not record['color']:
        return {'complete': True, 'action': 'deliver', 'outputs': outputs}
    import color_workflow as color
    deliveries = sorted(attempt.glob('color-*/delivered.json'), key=lambda p:p.stat().st_mtime_ns)
    valid = [p for p in deliveries if read(p)['source'] == choice['image'] and Path(read(p)['ilustrada']).resolve() == illustrated.resolve()]
    if not valid:
        jobs = sorted(attempt.glob('color-*/source.json'), key=lambda p:p.stat().st_mtime_ns)
        jobs = [p.parent for p in jobs if read(p)['identity'] == choice['image'] and Path(read(p)['illustrated']).resolve() == illustrated.resolve()]
        job = jobs[-1] if jobs else color.prepare(attempt, illustrated)
        color._verify(job)
        if (job/'generation.json').exists():
            return pending('review_color', job=str(job), original=str(job/'original.png'), source=str(illustrated))
        return pending('edit_color', job=str(job), request=str(job/'request.json'), source=str(illustrated))
    delivered = read(valid[-1]); colored = Path(delivered['coloreada'])
    if image_identity(colored) != delivered['colored']:
        raise ValueError('Accepted colored image changed')
    outputs['coloreada'] = str(colored)
    if not record['requested_3d']:
        return {'complete': True, 'action': 'deliver', 'outputs': outputs}
    links = sorted(attempt.glob('pipeline-explorer-*.json'))
    if not links:
        return pending('build_3d', source=str(colored), pair=str(colored.parent), illustration_attempt=str(attempt))
    job = Path(read(links[-1])['job'])
    bound = read(job/'source.json')['images']['coloreada.png']
    if Path(bound['path']).resolve() != colored.resolve() or bound['sha256'] != sha(colored):
        raise ValueError('Explorer source changed')
    if not (job/'delivered.json').exists():
        from explorer_repair_cycle import next_step
        return pending('review_or_repair_3d', job=str(job), candidate=str(job/'candidate.html'), source=str(colored), repair_step=next_step(job))
    delivery = read(job/'delivered.json'); html = Path(delivery['path'])
    if html.resolve() != colored.with_name('explorador.html').resolve() or sha(html) != delivery['sha256']:
        raise ValueError('Accepted explorer missing, changed or in a different delivery folder')
    outputs['explorador'] = str(html)
    return {'complete': True, 'action': 'deliver', 'outputs': outputs}


def checkpoint(pipeline):
    """Persist the real next action after an accepted image, including failures."""
    path = Path(pipeline)
    target = path.parent/('pipeline-step-' + uuid.uuid4().hex[:12] + '.json')
    try:
        result = advance(path)
    except Exception as error:
        save(target, {'complete': False, 'action': 'repair_transition',
                      'error': type(error).__name__ + ': ' + str(error)})
        raise
    save(target, result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('start'); init.add_argument('attempt'); init.add_argument('--3d', dest='three', action='store_true'); init.add_argument('--illustration-only', action='store_true')
    step = sub.add_parser('next'); step.add_argument('pipeline')
    link = sub.add_parser('attach-explorer'); link.add_argument('pipeline'); link.add_argument('job')
    args = parser.parse_args()
    if args.command == 'start':
        print(start(args.attempt, requested_3d=args.three, color=not args.illustration_only))
    elif args.command == 'attach-explorer':
        attach_explorer(args.pipeline, args.job)
    else:
        result = advance(args.pipeline)
        print(json.dumps(result, indent=2))
        # Nonzero means required work remains, not that the tool has failed.
        raise SystemExit(0 if result['complete'] else 2)
