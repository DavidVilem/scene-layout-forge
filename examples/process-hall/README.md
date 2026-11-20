# Process Hall

Original procedural component example.

## Reproducible decision contract

Short prompt: Complex industrial service hall: six vessels in three modules, three pumps and exactly six helmeted workers. Supported beams, braces, ducts, cable trays and cabinets supply architecture at several heights. Use this as a connectivity starting point, not a mandatory frontal composition. Inspect camera occlusions and develop a project-specific interior with depth before final art. Four English leader callouts identify storage vessels, a circulation pump, a maintenance platform and a cable tray.

Intent: Read three process modules, supported overhead architecture and maintenance access.

Discarded choice: Rejected copying the frontal composition into every plant or adding background workers beyond the exact six.

Physical schema: `1`; scope: partial adapter coverage; passing the fixture does not migrate it to complete strict workflow v3. Read `scene.py` for actual geometry and `recipe.json` for counts, camera and semantic targets. The schema number alone is not a coverage verdict. Adapters are those real part kinds and interfaces constructed by that scene; unknown functions remain unsupported.

Invariants: preserve the recipe counts (6 vessel, 3 pump, 6 worker, 3 stair, 3 landing), declared support/interface relationships and label target IDs. A display cut or style change cannot replace those obligations.

Run from the package root, with the documented Python dependencies:

```text
python -B scripts/run_example.py process-hall --validate-only
python -B scripts/check_examples.py --example process-hall
```

The first command checks the valid fixture. The second repeats it and deliberately mutates inventory, then worker height, route endpoints, attachment ports and shaft alignment where present; every applicable negative must fail. It does not generate images. For an original guide, add `--out-dir <new-folder-outside-package>` to `run_example.py` without `--validate-only`. Never overwrite an earlier run.

Limits: this example does not certify structural loads, process performance, machinery dynamics or human ergonomics. Geometry checks do not verify labels or functionality in a generated PNG. Rebuild current view/handoff evidence and independently review the actual final image. For balanced component and boundary cases use [the staged evaluator](../../evals/executable-cases.md).
