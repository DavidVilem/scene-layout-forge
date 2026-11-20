---
name: scene-layout-forge
description: Create a detailed graphite PNG and its faithful colored edit; only when explicitly requested, reconstruct the colored image as a fixed interactive 3D maquette. Preserve scene identity, connections, supports and execution history.
metadata:
  revision: "2026-11-18.37"
---

# Scene Layout Forge

Deliver `ilustrada.png`, then `coloreada.png`. Only an explicit request for 3D adds `explorador.html` after the accepted color image. A plan, technical subject or complex building does not imply 3D. A user asking for only one image overrides the default pair. Keep the requested detail and style; no private images, personal paths or prior conversation are required.

## Execute the whole requested chain

The order is **illustration -> colored edit -> optional image-derived 3D**. Do not model the 3D first. A generated base image is an intermediate, not the final response to a pair/3D request. Continue without asking the user to say "continue". The tools below save evidence and enforce transitions; the agent still invokes the image tool, models geometry and performs visual reviews.

1. Resolve the project and loaded revision. Before generation, follow [runtime startup](references/runtime-startup.md): on Windows execute `scripts/resolve_python.ps1`, retain its JSON in history and use its verified absolute interpreter for all helpers. Do not equate missing `python` on PATH with missing Python. Start `history_run.new_run(project, stem, brief=original_request)` and preserve the original brief.
2. Make the proportional design plan below and call `illustration_workflow.prepare(..., run=run)`. This produces an `attempt` containing the exact image request.
3. Start `delivery_pipeline.start(attempt, requested_3d=True|False)` with `True` only if the current prompt requests 3D. Use `color=False` only for an explicitly grayscale-only request. This persists the requested outputs. Resume this same pipeline within the current task.
4. Execute the `next_action` returned by image acceptance. When the pipeline is active, illustration/color acceptance automatically records this transition and illustration acceptance prepares the color job. Call `delivery_pipeline.advance(pipeline)` to resume or inspect pending work. The CLI equivalent is `python -B scripts/delivery_pipeline.py next <pipeline>`; exit 2 means work remains, not a tool failure. See [delivery loop](references/delivery-loop.md) for executable calls.

| Next action | Execute now |
|---|---|
| `generate_illustration` | Invoke the available image tool with the saved request; retain its actual output. |
| `review_illustration` | Inspect pixels, correct observed errors when needed, review and accept into `ilustrada.png`. |
| `edit_color` | The coordinator has prepared the color edit request. Inspect its source, invoke the image tool again as an edit, and retain that result. |
| `review_color` | Compare source and color pixels, correct changes when needed, review and accept `coloreada.png`. |
| `build_3d` | Only for requested 3D: inspect the accepted color image, author the reconstruction, build the candidate and attach its job to the pipeline. |
| `review_or_repair_3d` | Execute `repair_step` using the [retained repair cycle](references/repair-cycle.md). Record defects, revise geometry, attach the new candidate, compare again and continue in this task until the existing acceptance gates pass. |
| `deliver` with `complete: true` | Report the verified output paths, actual PNG dimensions, revision, history and remaining limitations. |

The coordinator prepares requests but cannot execute the image tool on the agent's behalf. A successful image-tool return does not finish a multi-output task. Copy/retain the actual returned local output before continuing; saving a request is not invoking it. Do not silently switch providers or require API credentials when the built-in tool is available.

Do not end merely because an image or draft exists, a review is pending or another tool call is needed. If an actual external failure, unavailable capability, user cancellation or exhausted applicable image correction budget prevents completion, retain the exact evidence and clearly identify the incomplete stage. Never fabricate success or a tool error. Do not label a correctable first model mismatch an external blocker. `execution_progress.py` is a low-level inventory only, not the completion decision.

## Design and artistic quality

Read [art direction](references/art-direction.md), [context and composition](references/context-composition.md) and [drawing construction](references/drawing-construction.md) for the current illustration. Consult [pattern library](references/pattern-library.md) only for relevant patterns. Use the [general walkthrough](references/walkthrough.md) and [general examples](examples/worked-cases/general-illustration.md) for plan schemas. Do not load every specialist reference before generating.

Use eight proportional decisions in the plan, with scope and reasons; they are not eight certificates:

1. **Site and activity:** choose a subject-specific setting and meaningful arrival/exit or continuation.
2. **Program:** design useful rooms/equipment and their relationships, not a fixed quota of boxes.
3. **Massing and composition:** consider two plausible arrangements; choose the view freely to explain this subject. No mandatory front view, corridor, close-up, symmetry or floor count. Cutaways only when requested.
4. **Structure and contacts:** show plausible supported forms, mounted equipment and terrain contacts. Run available validators on supplied numerical geometry without claiming load simulation.
5. **Levels and openings:** provide actual entrances, passages, stairs/landings and clearance in the represented scope. Inapplicable stages get a reason, not invented architecture.
6. **Systems and detail:** distribute primary forms, secondary assemblies and fine joints across visible zones and depth bands. Expand short briefs with purposeful construction; avoid empty rooms, repeated generic equipment or texture noise.
7. **Representation:** choose coherent camera/edge families. Use a numerical guide if helpful; otherwise a written spatial plan is sufficient for illustration. A full 3D model is not required. A schematic guide does not limit artistic detail.
8. **Pixels and finish:** transfer the complete art direction, relationships and detail plan to the image request, then inspect the actual output independently.

Style: hand-drawn technical anime background, neutral gray graphite and fine ink on near-white paper, three line weights, natural pressure variation, selective shading and atmospheric depth. Detail comes from recognizable construction and material joins. No global yellow/sepia, aged parchment or glossy render. Color uses restrained subject-appropriate materials and light beneath readable linework, preserving the same composition.

Annotations are optional: `annotations: []` unless requested. Requested labels use thin precise arrows to visible components; English unless overridden. People follow the brief and scene activity; never inherit fixed counts from examples.

For spatial scenes use [perspective review](references/perspective-review.md): camera, edge families and relative orientations. Distinctly rotated objects can have distinct vanishing directions. For buildings use [architectural continuity](references/architecture-repair.md): purposeful massing, complete enclosure unless a cutaway is requested, real openings and coherent roof junctions. Review these in the pixels before color.

## Continuous connections and supports

For pipes, cables or ducts, use `route_scope: "present"` and the lightweight [continuity contract](references/visual-continuity.md); otherwise use `absent`. Every route has meaningful start/end destinations: equipment port, joint, cap, outlet, wall passage with continuation or frame exit. Occlusion is continuing geometry, never a terminal. Tees are shared junctions, not nearby crossings. Maintain density using route families when appropriate.

Run applicable typed interface, contact, clearance and support checks on supplied geometry. Fix detected failures; record unsupported/not-run checks honestly. Trace the generated pixels independently, including foreground ends and representative distant runs. Stairs connect accessible levels, platforms have supports and access, walls have coherent corners/openings, and brackets touch their host and supported part. Do not ask for loads or hydraulic specifications to establish visual continuity.

## Image stages and history

Use `illustration_workflow.retain`, `review`, and `accept` for the actual generated PNG. Inspect the whole image and important junctions at native resolution. Include required plan relationships, perspective and architecture review keys. Never transfer a guide's validation to pixels. Use up to two local illustration corrections; preserve all originals.

After illustration acceptance, the pipeline prepares `color_workflow.prepare` automatically. Follow [color editing](references/color-editing.md): inspect the reference, send the exact edit request, retain, compare and review composition, linework, connections, annotations, detail and palette. Accept only with the same framing/dimensions and no known changed geometry. Use up to two local color corrections. Never rename grayscale pixels to simulate color or independently generate a different scene.

Preserve history: plans, source scripts, exact tool requests, original outputs, corrections, failures, reviews and linked model/browser evidence. Never delete history automatically. Deliver only the requested accepted files into one new numbered output directory; do not overwrite older results or use `final.png`.

A fresh illustration request, even with identical wording, creates a fresh design and pixels. Follow [creation identity](references/walkthrough.md) for original-operation records. Within that same run, coloring the newly accepted illustration and reconstructing its colored image are authorized continuation, not forbidden reuse. Explicit edits/continuations of an older artifact use `operation` and `reuse_reason`; do not substitute old images for a new creation.

## Optional fixed 3D reconstruction

Read [independent core](references/independent-3d.md) and [reconstruction kernel](references/reconstruction-kernel.md) only after the accepted pair when 3D is requested. Inspect the colored image; fit visible camera, silhouettes, proportions, entrances and relationships, and mark hidden geometry as inferred. Use general meshes and [construction families](references/presentation-maquette.md) where helpful; do not replace defining shapes with arbitrary boxes.

Call `reconstruction_kernel.build(..., pair=output_folder, illustration_attempt=attempt)` using the current accepted color source and original brief. No pre-generation snapshot is required. Attach the returned explorer job with `delivery_pipeline.attach_explorer(pipeline, job)`. For an explicitly supplied existing-image reconstruction, the standalone route uses `operation='reconstruct'` with its authorization; do not regenerate the source.

The viewer is a fixed maquette: orbit, zoom, selection, visibility/isolation, optional sections, standard views. No piece displacement, exploded view, removal/reassembly sequence or separation acceptance requirement. Groups exist for visibility; fusing everything into one mesh is unnecessary.

Review through [explorer workflow](references/explorer-3d.md), [maquette fidelity](references/maquette-fidelity.md) and [source comparison](references/fidelity-acceptance.md). Browser controls passing is not fidelity approval. Preserve critical visible geometry, real entrances and connected routes; correct meaningful mismatches through [geometry repair](references/reconstruction-repairs.md). Keep previous candidates and unchanged PNGs. Use `explorer_workflow.accept` only with genuine browser and visual evidence. The coordinator recognizes that accepted HTML; a candidate alone remains pending. No exact reconstruction guarantee for arbitrary images or unobserved geometry.

## Other explicit modes

Strict exhaustive geometry is opt-in: [registered workflow](references/registered-workflow.md), [typed interfaces](references/typed-interfaces.md), [coherence checks](references/coherence-validation.md) and [architectural gates](references/architectural-gates.md). Keep their existing checks; do not apply every strict gate to ordinary illustration.

Ambient animation is off unless requested. Follow [subtle animation](references/subtle-animation.md) after the accepted pair; preserve both PNGs. Do not add animation to this default delivery chain.

## Maintenance

Run both unittest suites (`scripts` and `tests`, `test_*.py`), `scripts/check_examples.py` and `scripts/check_package.py`. Build the source-only ZIP with `scripts/build_package.py` outside the skill. Never embed user images, histories, generated media, private paths or credentials. Preserve prior releases. Synthetic control-flow tests do not prove image quality or that another agent will execute every instruction; report actual test scope.
