# Technical Plan

Original procedural component example.

## Reproducible decision contract

Short prompt: A top-down orthographic layout of a technical control room and storage space. Preserve entrance and internal passage openings. Draw walls, furniture and meaningful English labels. No perspective, people, invented dimensions or implied building-code certification.

Intent: Keep a genuine top-down orthographic room arrangement with open entrance and passage.

Discarded choice: Rejected perspective camera, invented dimensions and extra people; the plan remains a conceptual layout.

Physical schema: `1`; scope: partial adapter coverage; passing the fixture does not migrate it to complete strict workflow v3. Read `scene.py` for actual geometry and `recipe.json` for counts, camera and semantic targets. The schema number alone is not a coverage verdict. Adapters are those real part kinds and interfaces constructed by that scene; unknown functions remain unsupported.

Invariants: preserve the recipe counts (1 console, 1 cabinet, 2 seat, 0 worker), declared support/interface relationships and label target IDs. A display cut or style change cannot replace those obligations.

Run from the package root, with the documented Python dependencies:

```text
python -B scripts/run_example.py technical-plan --validate-only
python -B scripts/check_examples.py --example technical-plan
```

The first command checks the valid fixture. The second repeats it and deliberately mutates inventory, then worker height, route endpoints, attachment ports and shaft alignment where present; every applicable negative must fail. It does not generate images. For an original guide, add `--out-dir <new-folder-outside-package>` to `run_example.py` without `--validate-only`. Never overwrite an earlier run.

Limits: this example does not certify structural loads, process performance, machinery dynamics or human ergonomics. Geometry checks do not verify labels or functionality in a generated PNG. Rebuild current view/handoff evidence and independently review the actual final image. For balanced component and boundary cases use [the staged evaluator](../../evals/executable-cases.md).
