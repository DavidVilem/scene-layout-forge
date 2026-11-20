# Situated workers

An original, strict physical fixture with one seated operator and one leaning
inspector. These are explicit example counts, not default people for other briefs.

`worker_pose_examples.seated_scene()`, `leaning_scene()` and
`contact_atlas_scene()` are reusable constructors. Each uses the native `worker`
kind, so count and owner registration stay intact. The pose's nominal stature is
separate from its occupied envelope. `ActorPlan` version 2 and typed
`actor_contacts` bind real feet, pelvis and palm surfaces to existing floor,
seat and bench geometry. Missing furniture or a moved surface fails validation.

Run `python -B examples/situated-workers/build.py --validate-only` from the package.
For a calculated guide, pass a new `--out-dir` outside the package. Then use the
normal artistic-finish workflow and inspect the generated pixels independently.

The seated template fits a declared seat height; the leaning template fits a
declared worktop height. Their reach limits are adapter limits, not universal
human proportions or accessibility rules. No dynamic posture, anatomy,
balance, grip force or structural safety is simulated. See
[actor poses](../../references/actor-poses.md).

## Reproducible decision contract

Short prompt: draw one seated operator and one leaning inspector at a workbench.

Intent: explain seated pelvis/feet and leaning hand/feet contacts with visible supported furniture. Discarded choice: relabeling a standing mesh as seated or moving the seat without rebuilding contacts. Schema2, strict ActorPlan2, worker/seat/column/slab adapters. Preserve exactly two actors, fitted stature and declared contact surfaces; no default workers are inferred in another brief.

```text
python -B scripts/run_example.py situated-workers --validate-only
python -B scripts/check_examples.py --example situated-workers
```

The positive loads the real contact atlas; the negative inventory and floating-worker mutations must fail. See [the staged evaluator](../../evals/executable-cases.md) for an additional moved-seat failure. Neither result certifies anatomy, balance or final generated pixels.
