"""Evidence-bound repair queue. Agent performs geometry edits and visual review."""
import argparse
import json
from pathlib import Path
from run_manifest import sha


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def latest(job):
    records = sorted(Path(job).glob('repair-cycle-*.json'))
    if not records:
        return None
    result = read(records[-1])
    if result['candidate_sha256'] != sha(Path(job)/'candidate.html'):
        raise ValueError('Repair queue refers to changed candidate; rebuild and review')
    for evidence in result['evidence']:
        if sha(evidence['path']) != evidence['sha256']:
            raise ValueError('Repair comparison evidence changed')
    return result


def record(job, issues, approach, evidence, previous_job=None):
    job = Path(job).resolve()
    inherited = job/'repair-parent.json'
    if inherited.exists():
        required = read(inherited)['job']
        if previous_job and Path(previous_job).resolve() != Path(required).resolve():
            raise ValueError('Repair parent cannot be replaced')
        previous_job = required
    if not isinstance(approach, str) or not approach.strip():
        raise ValueError('Describe the actual modeling/camera approach')
    if not isinstance(issues, list) or len({i['id'] for i in issues}) != len(issues):
        raise ValueError('Unique issue IDs required')
    if not evidence:
        raise ValueError('Retained source/model comparison evidence required')
    files = [{'path': str(Path(p).resolve()), 'sha256': sha(p)} for p in evidence]
    previous = latest(job) or (latest(previous_job) if previous_job else None)
    old = {i['id']: i for i in previous['issues']} if previous else {}
    if previous_job and previous and previous['approach'].strip() == approach.strip():
        if any(i['status'] == 'open' and i.get('stalled', 0) >= 2 for i in previous['issues']):
            raise ValueError('Repeated stalled approach; change camera fit or geometry construction and document it')
    if set(old) - {i['id'] for i in issues}:
        raise ValueError('Carry every tracked issue forward, including resolved issues')
    if previous_job:
        # Each retained explorer source contains the full colored-image binding.
        before = read(Path(previous_job)/'source.json')['images']['coloreada.png']['sha256']
        after = read(job/'source.json')['images']['coloreada.png']['sha256']
        if before != after:
            raise ValueError('Repair cannot change source image')
    observations = []
    for issue in issues:
        item = dict(issue)
        for key in ('id', 'components', 'observed', 'target', 'action', 'verification'):
            if not item.get(key):
                raise ValueError('Concrete repair field required: '+key)
        if item.get('status') not in ('open', 'resolved'):
            raise ValueError('Issue status must be open or resolved')
        if item.get('priority') not in ('critical', 'major', 'detail'):
            raise ValueError('Issue priority required')
        if item.get('progress') not in ('new', 'improved', 'unchanged', 'regressed', 'resolved'):
            raise ValueError('Observed progress required')
        if item['status'] == 'resolved' and (item['progress'] != 'resolved' or not item.get('neighbor_checks')):
            raise ValueError('Resolution needs neighbor checks and comparison evidence')
        parent = old.get(item['id'])
        same_candidate = previous and previous['candidate_sha256'] == sha(job/'candidate.html')
        if parent and same_candidate and parent['status'] == 'open' and item['status'] == 'resolved':
            raise ValueError('Cannot resolve a defect by changing review text on unchanged candidate')
        stalled = parent.get('stalled', 0) if parent else 0
        item['stalled'] = (stalled + (0 if same_candidate else 1)) if item['progress'] in ('unchanged', 'regressed') else 0
        observations.append(item)
    result = dict(candidate_sha256=sha(job/'candidate.html'), approach=approach,
                  previous_job=str(Path(previous_job).resolve()) if previous_job else None,
                  evidence=files, issues=observations)
    path = job/('repair-cycle-%06d.json' % (len(list(job.glob('repair-cycle-*.json')))+1))
    with path.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
    return next_step(job)


def next_step(job):
    review = latest(job)
    if review is None:
        parent = Path(job)/'repair-parent.json'
        return {'action': 'capture_and_review', 'previous_job': read(parent)['job'] if parent.exists() else None, 'instruction': 'Render source-matched camera, inspect silhouettes, roof axes, openings, access and context; carry all previous issues into the new review.'}
    issues = sorted((i for i in review['issues'] if i['status'] == 'open'),
                    key=lambda i: ('critical', 'major', 'detail').index(i['priority']))
    if not issues:
        return {'action': 'validate_and_accept', 'instruction': 'Run unchanged browser, connection and fidelity gates; this queue alone is not acceptance.'}
    return {'action': 'change_modeling_approach' if any(i['stalled'] >= 2 for i in issues) else 'revise_geometry',
            'issues': issues,
            'instruction': 'Correct prioritized components, preserve source/accepted neighbors, rebuild using reconstruction_repair.revise, attach new candidate, render and inspect again in this task. Stagnation requires a new camera fit or geometry construction, not ending the task.'}


def validate_acceptance(job):
    review = latest(job)
    if not review and (Path(job)/'repair-parent.json').exists():
        raise ValueError('Rebuilt candidate requires review of inherited defects')
    if review and any(i['status'] != 'resolved' for i in review['issues']):
        raise ValueError('Repair cycle still has open defects; revise geometry and compare again')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('job')
    parser.add_argument('--review', help='JSON with issues, approach, evidence and optional previous_job')
    args = parser.parse_args()
    result = record(args.job, **read(args.review)) if args.review else next_step(args.job)
    print(json.dumps(result, indent=2))
