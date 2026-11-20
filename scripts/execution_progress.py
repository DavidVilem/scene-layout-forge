"""Read-only progress audit. Artifact presence is not visual acceptance.

Pass the illustration history and any explicitly linked kernel/color/explorer
histories. Never scan unrelated runs to make the current request look complete.
"""
import argparse
import json
from pathlib import Path


def inspect(roots):
    files = set()
    for root in roots:
        root = Path(root).resolve()
        if not root.is_dir():
            raise ValueError('History directory missing: ' + str(root))
        # Propagate access errors; unreadable evidence is not an empty run.
        def visit(folder):
            for path in folder.iterdir():
                if path.is_symlink():
                    continue
                if path.is_dir():
                    visit(path)
                elif path.is_file():
                    files.add(path)
        visit(root)
    categories = {
        'plans': {'plan.json', 'specification.json'},
        'geometry': {'scene.json', 'geometry-guide.png', 'model.glb'},
        'requests': {'request.json'},
        'generation_records': {'generation.json'},
        'candidates': {'candidate.html'},
        'delivery_records': {'delivered.json'},
        'failures': {'failure.json', 'rejected.json'},
    }
    evidence = {key: sorted(str(p) for p in files if p.name in names)
                for key, names in categories.items()}
    evidence['selection_records'] = sorted(str(p) for p in files if p.name.startswith('selected-') and p.suffix == '.json')
    started_only = not any(evidence.values())
    return {
        'state': 'initialized_only' if started_only else 'artifacts_present',
        'evidence': evidence,
        'next_action': ('Continue planning and execute the requested workflow; no production attempt is recorded.'
                        if started_only else 'Inspect evidence and execute the next unfinished stage.'),
        'limitation': 'Presence does not establish completion, fidelity or tool execution outside these histories.',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('histories', nargs='+', type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.histories), indent=2))
