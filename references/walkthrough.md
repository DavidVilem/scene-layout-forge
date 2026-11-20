# General illustration walkthrough

Always generate and review the illustration first, then the colored edit. Only an explicit 3D request continues into the independent reconstruction core using the accepted colored image. A guide is optional; a full 3D model is not a prerequisite.

1. Resolve this package's scripts directory and the user's project. Add the former to Python's import path; do not use a personal hardcoded path. Create `run = history_run.new_run(project, stem, brief)` before any generation.
2. Build a small `plan` with subject, view, setting, composition, detail, named relationships, annotations (empty unless requested), and eight stage decisions `{status: "planned", reason: "..."}` or not_applicable with a reason. This is a design record, not a certificate. For route-bearing scenes add route_scope: present and a continuity contract; for unrelated scenes use absent. See visual-continuity.md. No engineering data is needed.
3. Build/inspect an optional guide. Save original builder and model in history. Available typed support/connection checks still run on supplied numerical models. A failed check must be fixed; unsupported and unmodeled properties remain visible in coverage.
4. `attempt = illustration_workflow.prepare(project, stem, brief, plan, scene=scene_or_none, guide=guide_or_none, sources=[builder], run=run)`. Send the returned folder's `request.json` exactly to the image tool. Its prompt includes the current written style, not an old conversation.
After preparation, call `delivery_pipeline.start(attempt, requested_3d=user_requested_3d)` and follow [the persistent delivery loop](delivery-loop.md). The following steps are its image-stage operations, not independent completion points.

5. Save the returned original using `retain(attempt, generated_png, actual_request)`. Inspect it. Record all BASE_REVIEW keys plus each relationship ID and, when a continuity contract is present, its four continuity review keys with `{status: "visible_correct" | "visible_error" | "uncertain" | "occluded", notes: "actual observation"}`. Call `review(attempt, original, observations)`.
6. For a visible defect, prepare `correction(attempt, original, review_path, concrete_edit_request)`, call the image tool, retain with `retain_correction`, and inspect/review the new bytes. At most two local corrections. Do not produce fake passed records to exhaust a budget.
7. Choose an unused numbered output folder and call `accept(attempt, selected_original, selected_review, final_path)`. Preserve the selected PNG and coverage limits, then advance the pipeline into coloring. This selection is not final completion of a pair/3D request. Preserve the full history even when a stage or tool fails.

The agent must actually view the guide and final PNG. Code binds evidence and checks completeness; it cannot verify that an agent's written visual observation is true. The strict route and its existing examples are separate: read registered-workflow only for that requested mode.

8. After accepting ilustrada.png, execute the [color edit workflow](color-editing.md). The task is complete only when both ilustrada.png and coloreada.png are reviewed and retained, unless the user explicitly requests a single version.


Optional requested animation: see [motion workflow](../references/subtle-animation.md). Preserve the illustrated/colored pair; retain animation evidence and inspect actual motion before delivery.

## Requested 3D: continue the same design

After the reviewed pair, reconstruct the visible design from the accepted colored image. Preserve its camera, forms, openings and relationships; mark hidden geometry as inferred. Follow [independent spatial core](independent-3d.md) and [3D explorer](explorer-3d.md), compare the actual images with the model, and review a real browser before delivery. Existing supplied images instead use the single-image route. An image-only request does not activate either 3D route.

For new spatial plans, add the perspective_contract from perspective-review.md. Review all perspective_contract.keys(plan), including named evidence lists, before color. Preserve the diagnostic overlays in history.

For buildings, add the [architectural decision contract](architecture-repair.md) before image generation. Distinguish a complete enclosure from a user-requested display section. Validate the roles/host graph, then review the actual design hierarchy in the generated pixels. An existing arch is not automatically a requirement to preserve. See the [facade repair example](../examples/worked-cases/architecture-repair.md).

When a comparison fails, record concrete repair tasks with repair_cycle, correct the geometry or image, and inspect the new artifact before resolving each task. Use the browser capture comparison when the software raster obscures glazing or fine meshes; never accept an illegible diagnostic image as fidelity evidence.


## Repeated short requests: independent creation

Request: “Illustrate a railway terminal and create its 3D explorer.” Repeating this request starts another create run. First concept might be a transverse hall with a steel portal; another could use longitudinal sawtooth bays and a recessed entrance. These are possibilities, not fixed templates. Select from the site and circulation needs; retain complete entrances and support continuity in either case. Do not load yesterday's image as an edit reference or copy yesterday's reconstruction specification. Generate fresh graphite pixels, review, color-edit and review, then build the explicitly requested explorer with `illustration_attempt=attempt` and the current colored image.

Contrast: “Repair the entrance of the previous terminal” authorizes an edit run with `reuse_reason` quoting that request and explicitly identified source. “Reconstruct this existing image in 3D” authorizes standalone reconstruction. Never select those modes merely to bypass a failed create guard.

Retain rejected candidates and failure records. A decoded-pixel duplicate check does not prove that two different images depict distinct architectural designs; review massing, layout, entrances and circulation separately. A new camera alone is not a new building.
