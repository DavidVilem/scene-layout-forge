# Space Station

Original procedural component example.

## Reproducible decision contract

Short prompt: Fictional orbital research station exterior with two cylindrical modules, two lateral trusses, four solar panel wings and a docking collar. No people, factories, tanks or invented engineering measurements. Three-quarter technical perspective on near-white paper with detailed joints, thermal seams and panel cells.

Intent: Read curved module identity, truss attachments, arrays and docking interface.

Discarded choice: Rejected arbitrary people on an exterior floor, process tanks and a claim of an occupied microgravity interior.

Physical schema: `1`; scope: partial adapter coverage; passing the fixture does not migrate it to complete strict workflow v3. Read `scene.py` for actual geometry and `recipe.json` for counts, camera and semantic targets. The schema number alone is not a coverage verdict. Adapters are those real part kinds and interfaces constructed by that scene; unknown functions remain unsupported.

Invariants: preserve the recipe counts (2 shell, 2 truss, 4 panel_array, 0 worker, 0 vessel, 0 pump), declared support/interface relationships and label target IDs. A display cut or style change cannot replace those obligations.

Run from the package root, with the documented Python dependencies:

```text
python -B scripts/run_example.py space-station --validate-only
python -B scripts/check_examples.py --example space-station
```

The first command checks the valid fixture. The second repeats it and deliberately mutates inventory, then worker height, route endpoints, attachment ports and shaft alignment where present; every applicable negative must fail. It does not generate images. For an original guide, add `--out-dir <new-folder-outside-package>` to `run_example.py` without `--validate-only`. Never overwrite an earlier run.

Limits: this example does not certify structural loads, process performance, machinery dynamics or human ergonomics. Geometry checks do not verify labels or functionality in a generated PNG. Rebuild current view/handoff evidence and independently review the actual final image. For balanced component and boundary cases use [the staged evaluator](../../evals/executable-cases.md).
