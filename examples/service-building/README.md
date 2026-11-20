# Service Building

Original procedural component example.

## Reproducible decision contract

Short prompt: Four-storey technical service building, two structural bays per side, an entrance ramp and canopy, rooftop service cabinets and planted forecourt. No process vessels, pumps or workers. Draw a three-quarter exterior in neutral graphite and fine ink. Label the entrance canopy and rooftop equipment in English. This tests architectural variety without inheriting industrial fixture objects.

Intent: Explain an architectural entrance, repeated structure and rooftop service equipment.

Discarded choice: Rejected inheriting vessels, pumps or workers from the industrial examples; the brief asks for none.

Physical schema: `1`; scope: partial adapter coverage; passing the fixture does not migrate it to complete strict workflow v3. Read `scene.py` for actual geometry and `recipe.json` for counts, camera and semantic targets. The schema number alone is not a coverage verdict. Adapters are those real part kinds and interfaces constructed by that scene; unknown functions remain unsupported.

Invariants: preserve the recipe counts (1 door, 1 ramp, 2 cabinet, 0 worker, 0 vessel, 0 pump), declared support/interface relationships and label target IDs. A display cut or style change cannot replace those obligations.

Run from the package root, with the documented Python dependencies:

```text
python -B scripts/run_example.py service-building --validate-only
python -B scripts/check_examples.py --example service-building
```

The first command checks the valid fixture. The second repeats it and deliberately mutates inventory, then worker height, route endpoints, attachment ports and shaft alignment where present; every applicable negative must fail. It does not generate images. For an original guide, add `--out-dir <new-folder-outside-package>` to `run_example.py` without `--validate-only`. Never overwrite an earlier run.

Limits: this example does not certify structural loads, process performance, machinery dynamics or human ergonomics. Geometry checks do not verify labels or functionality in a generated PNG. Rebuild current view/handoff evidence and independently review the actual final image. For balanced component and boundary cases use [the staged evaluator](../../evals/executable-cases.md).
