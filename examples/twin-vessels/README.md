# Twin Vessels

Original procedural component example.

## Reproducible decision contract

Short prompt: Two vertical storage vessels, one circulation pump, one stair and maintenance platform, exactly two helmeted workers. Use a three-quarter architectural view with readable outlet/header/pump connections. Add three English leader callouts: STORAGE VESSELS, CIRCULATION PUMP and MAINTENANCE PLATFORM.

Intent: Follow the declared vessel/header/pump connections and supported maintenance access.

Discarded choice: Rejected extra vessels or workers and closing an external route merely to simplify the silhouette.

Physical schema: `1`; scope: partial adapter coverage; passing the fixture does not migrate it to complete strict workflow v3. Read `scene.py` for actual geometry and `recipe.json` for counts, camera and semantic targets. The schema number alone is not a coverage verdict. Adapters are those real part kinds and interfaces constructed by that scene; unknown functions remain unsupported.

Invariants: preserve the recipe counts (2 vessel, 1 pump, 2 worker, 1 stair, 1 landing), declared support/interface relationships and label target IDs. A display cut or style change cannot replace those obligations.

Run from the package root, with the documented Python dependencies:

```text
python -B scripts/run_example.py twin-vessels --validate-only
python -B scripts/check_examples.py --example twin-vessels
```

The first command checks the valid fixture. The second repeats it and deliberately mutates inventory, then worker height, route endpoints, attachment ports and shaft alignment where present; every applicable negative must fail. It does not generate images. For an original guide, add `--out-dir <new-folder-outside-package>` to `run_example.py` without `--validate-only`. Never overwrite an earlier run.

Limits: this example does not certify structural loads, process performance, machinery dynamics or human ergonomics. Geometry checks do not verify labels or functionality in a generated PNG. Rebuild current view/handoff evidence and independently review the actual final image. For balanced component and boundary cases use [the staged evaluator](../../evals/executable-cases.md).
