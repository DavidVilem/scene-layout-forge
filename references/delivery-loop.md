# Persistent requested-output loop

The pipeline starts after illustration preparation and lives inside that attempt.
It does not replace generation, visual inspection or the existing acceptance
functions. Resolve helpers from the installed skill, not a personal directory.

```python
from delivery_pipeline import start, advance, attach_explorer

# attempt was returned by illustration_workflow.prepare(...).
# Decide from the current user request, not from subject complexity.
pipeline = start(attempt, requested_3d=user_requested_3d)
pending = advance(pipeline)
```

When a pipeline is active, illustration/color `accept` automatically checkpoints the next action and returns it as `next_action`; illustration acceptance also prepares the color job. Execute that returned action, then call `advance` again. Keep the returned pipeline
path in the run and in any continuation notes. Do not create another run just
because another image-tool call is required.

- `generate_illustration`: read `request`, invoke the available image generator,
  retain its actual output with `illustration_workflow.retain`, and advance.
- `review_illustration`: inspect the retained original, use `review` with real
  observations and `accept` into the chosen fresh directory. For errors use the
  existing local correction functions and review the new result before accepting.
- `edit_color`: `advance` has created or resumed a real `color_workflow` job.
  Read `request`, inspect its source image, call the image tool in edit mode, and
  `color_workflow.retain(job, actual_result, actual_request)`. Advance again.
- `review_color`: compare both images, `color_workflow.review` and `accept`.
  When correcting, use `color_workflow.prepare(..., previous=job,
  correction=observed_defect)` and keep the same pipeline. Advance selects the
  newest current-source color job; it does not create duplicate jobs on resume.
- `build_3d`: inspect `source` and author actual geometry. Use
  `reconstruction_kernel.build` with `illustration_attempt`, `pair` and the
  original brief. `attach_explorer(pipeline, returned_job)` binds the current
  candidate. Its source must be the current accepted colored image.
- `review_or_repair_3d`: inspect source/model correspondence and actual browser
  behavior. Correct geometry in a linked candidate and attach that job. Call
  `explorer_workflow.accept` with genuine evidence after it passes. Do not
  manually create `delivered.json` to bypass acceptance.
- `deliver`: only `complete: true` means the requested outputs have acceptance
  records and unchanged files. It does not prove that the human/agent's visual
  observations were true; those reviews remain an independent responsibility.

CLI:

```text
python -B scripts/delivery_pipeline.py start <attempt> --3d
python -B scripts/delivery_pipeline.py next <attempt>/delivery-pipeline.json
python -B scripts/delivery_pipeline.py attach-explorer <pipeline> <explorer-job>
```

Omit `--3d` unless requested. `--illustration-only` is solely for an explicit
single grayscale output. `next` exits 2 while work remains and 0 on accepted
delivery. An exception is a concrete problem to diagnose and repair, not an
accepted partial outcome. Tool waits must be resumed using the runtime's actual
wait mechanism; elapsed waiting without a tool result is not success or a
fabricated failure. Preserve actual errors and useful progress when blocked.

The coordinator cannot prevent a host from interrupting a turn or force an agent
to keep running after it stops. It supplies explicit durable pending work so the
agent can continue the same request instead of guessing from a history folder.
