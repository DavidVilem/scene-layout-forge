# Typed water hall

Run the builder as for other examples. This v2 example has four vessels, two transfer pumps, two platforms/stairs and five workers. All fluid ports generate nozzles from analytic component surfaces. Diameter, medium, flow role and route tangent are checked. Header and outlet boundary tubes have explicit feet. The external boundary means connection beyond the scene is unverified, not a drain or a simulated treatment cycle.

Supported parts require a bearing path to the ground slab. Two supports are required by the current beam/landing adapter. Wall panels and secondary services remain outside full support coverage; inspect coverage output. Contact checks use bounding boxes, not load analysis. Endpoint bodies are excluded from automatic route/obstacle checks; local nozzle checks do not prove an entire route never re-enters its own equipment. Check that visually and do not claim complete collision coverage.

This module is a reusable assembly example, not a mandatory arrangement for all plants. Legacy examples remain partial and require explicit migration for v2 claims. No images are included.

## Reproducible decision contract

Short prompt: A detailed two-module water-treatment hall with four vessels, two pumps, five workers and explicit supported piping. No hydraulic performance claim.

Intent: Read two typed process modules and the independent maintenance/support paths.

Discarded choice: Rejected adjacency without compatible fluid interfaces and any claim of hydraulic capacity.

Physical schema: `2`; scope: partial adapter coverage; passing the fixture does not migrate it to complete strict workflow v3. Read `scene.py` for actual geometry and `recipe.json` for counts, camera and semantic targets. The schema number alone is not a coverage verdict. Adapters are those real part kinds and interfaces constructed by that scene; unknown functions remain unsupported.

Invariants: preserve the recipe counts (4 vessel, 2 pump, 5 worker, 2 stair, 2 landing), declared support/interface relationships and label target IDs. A display cut or style change cannot replace those obligations.

Run from the package root, with the documented Python dependencies:

```text
python -B scripts/run_example.py typed-water-hall --validate-only
python -B scripts/check_examples.py --example typed-water-hall
```

The first command checks the valid fixture. The second repeats it and deliberately mutates inventory, then worker height, route endpoints, attachment ports and shaft alignment where present; every applicable negative must fail. It does not generate images. For an original guide, add `--out-dir <new-folder-outside-package>` to `run_example.py` without `--validate-only`. Never overwrite an earlier run.

Limits: this example does not certify structural loads, process performance, machinery dynamics or human ergonomics. Geometry checks do not verify labels or functionality in a generated PNG. Rebuild current view/handoff evidence and independently review the actual final image. For balanced component and boundary cases use [the staged evaluator](../../evals/executable-cases.md).
