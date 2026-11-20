# Revision-12 planning and evidence

Use `workflow_version: 3` for non-building runs and v4 with architectural gates for new buildings. This adds visual planning to the
existing schema-v2 registered physical scene; it does not replace strict validation.
Older fixtures remain explicitly partial unless migrated and rechecked.

The maintained field definitions and examples are in `scripts/visual_contract.py`.
Create `visual_plan`, `context_plan`, `detail_budget` and `light_material_plan`, plus
`actor_plan` when people have specified tasks. Compile them with
`compile_visual_contract(scene, evidence=view["projection_review"])`. Unknown or incomplete required
plans must be corrected rather than converted to an apparent pass.

The order is physical model -> useful views -> explicit visual plan -> inspected
guide -> frozen finish contract -> image generation -> independent pixel review.
Context or decoration cannot introduce new load paths or block previously checked
openings. Keep a justified quiet region when it improves focus. Preserve freedom
of view and a scene-specific background; do not enforce a central corridor.

## Finishing and review

`prepare_finish.py --scene <scene.json> --view <view.json> --guide <guide.png>
--brief "<short user request>" --run <history-run> --source <builder.py>` (plus `--stage-records <ordered-records.json>` for v4) writes:

- `finish-lock.json`: immutable scene, geometric results, visual plan and view hashes.
- `handoff.json`: prioritized invariants, view, identity, detail, materials and notes.
- `finishing-prompt.txt`: the written request and art direction for the image tool.
- `run-manifest.json`: installed revision/source hash, input hashes and observed tools.

The generator receives the compact original `finish-style.txt` direction plus
structured scene priorities. The complete per-part material frames and physical
contact samples remain in the lock; its prompt uses focal material specifications,
semantic groups and the current guide. The default 30,000-character budget is checked
before writing outputs. Oversized requests fail explicitly; never truncate endpoints,
critical supports or user constraints to fit a service limit.

Optional `--client`, `--reasoning-model`, `--image-tool`, `--image-model` record only
facts actually exposed by the environment. The reasoning model is not necessarily
the image model. Unknown stays `unreported`. A matching short prompt alone is not
a controlled comparison between clients.

After visually inspecting the **generated PNG**, create observations for
`pixel_review.requirements(lock)`. Use `visible_correct`, `visible_error`, `occluded`
or `uncertain`, with a specific note and normalized region where useful. The
`pixel_review.py` command binds these observations to file and decoded-pixel hashes,
dimensions, scene and view. It checks evidence coverage and identity; it does not
perform image recognition or certify the truth of supplied observations.

`finish_contract.correction` requires this current record for v3 and coordinate-based
repairs. It accepts at most correction indices 1 and 2. Count, label, tone, material
and regional detail edits preserve the same scene. Moving supports, changing an
opening or redirecting a route requires rebuilding and a new freeze. Every edit
requires inspecting all critical pixels again for regressions.

## Persistent execution history

Use history_run.new_run(project, stem) for the eight stage folders. Keep failures and all intermediate evidence. No automatic cleanup. One selected PNG remains in its delivery folder; report both locations. See [eight stages](eight-stage-workflow.md). The legacy cleanup_plan helper is only for a later explicit deletion request.

For a client comparison run `scripts/run_manifest.py <desktop.json> <vscode.json>`.
Compare inputs first, then the independent pixel reports and real native dimensions.
Equal manifests cannot promise deterministic output or parity of service behavior.

The manifest records the actually loaded skill directory and working directory only
in the external runtime record. Never ship that record in the source package. Empty
or malformed records fail comparison; unknown client facts cannot establish model
equivalence. `same_recorded_inputs` and `complete_input_evidence` are separate:
legacy runs without a guide/view may share recorded inputs but lack full evidence.

Bind a reviewed final result before closing the retained run:

```sh
python -B scripts/run_manifest.py --finalize <run-manifest.json> --lock <finish-lock.json> --image <ilustrada.png> --review <pixel-review.json> --native-image <tool-output.png> --generation <observed-facts.json> --out <new-outcome.json>
```

`observed-facts.json` may contain `tool`, `model`, `requested_size`, `quality`, `seed`,
`reference_use`, `reference_sha256`, the actual `prompt_sha256` and `correction_index`
(0 for initial generation, 1 or 2 for a bounded repair). Record only exposed facts; unknown values
stay `unreported`. The native image argument must identify the actual tool output,
not an upscaled export. The checker decodes both PNGs and reports preserved native
pixels, a transformation, or unverified native resolution when no original is given.
It verifies the frozen scene, guide identity and independent pixel review before
binding dimensions and hashes. A limited review remains limited in the result.
