# Registered dry dock

The example constructs a new scene using component APIs, not a scaled copy of another plant. One registered hull, six sampled support patches, two pump units, a common discharge header, distinct intake boundaries, deck structures and wall services are defined before finishing.

Use the portable build command from the examples index. Freeze the resulting scene with `finish_contract` or `prepare_finish.py` before artwork. This example loads the recipe camera into its scene contract; retain the actual chosen camera when adapting it. Corrections must include that same camera.

The developed scene includes oriented wall trays, flat-top corbels, a grated walkway and a quay workshop with declared roof supports. These are registered before artistic finishing. Their presence is not a reason to add a workshop to unrelated subjects.

Short trial: "Illustrate a dry dock with a pumping station, five workers and English annotations."
Very short trial: "Dique seco."
These are planning probes, not proof that arbitrary text is parsed automatically. The minimal request permits a contextual scene; explicit counts/angle/style override example choices.

Inspect primary silhouette, secondary assembly depth, useful line hierarchy, five people, six keel contacts and the route meanings independently. The hull model is conceptual; contacts are sampled, not load-tested. Off-scene intake/outfall continuation and hidden interfaces remain unverified. No historical ship, docking procedure or engineering certification is implied.

No reference artwork is needed or included. Preserve diagnostics outside this package when requested.

## Reproducible decision contract

Short prompt: A conceptual dry dock with one supported ship, two pumps, five workers and a common discharge header.

Intent: Read actual hull/block contacts and the dewatering network separately from the display view.

Discarded choice: Rejected counting hidden supports as visible evidence or closing the external discharge with a blind cap.

Physical schema: `2`; scope: partial adapter coverage; passing the fixture does not migrate it to complete strict workflow v3. Read `scene.py` for actual geometry and `recipe.json` for counts, camera and semantic targets. The schema number alone is not a coverage verdict. Adapters are those real part kinds and interfaces constructed by that scene; unknown functions remain unsupported.

Invariants: preserve the recipe counts (1 custom, 2 pump, 5 worker, 1 stair, 6 footing), declared support/interface relationships and label target IDs. A display cut or style change cannot replace those obligations.

Run from the package root, with the documented Python dependencies:

```text
python -B scripts/run_example.py dry-dock --validate-only
python -B scripts/check_examples.py --example dry-dock
```

The first command checks the valid fixture. The second repeats it and deliberately mutates inventory, then worker height, route endpoints, attachment ports and shaft alignment where present; every applicable negative must fail. It does not generate images. For an original guide, add `--out-dir <new-folder-outside-package>` to `run_example.py` without `--validate-only`. Never overwrite an earlier run.

Limits: this example does not certify structural loads, process performance, machinery dynamics or human ergonomics. Geometry checks do not verify labels or functionality in a generated PNG. Rebuild current view/handoff evidence and independently review the actual final image. For balanced component and boundary cases use [the staged evaluator](../../evals/executable-cases.md).
