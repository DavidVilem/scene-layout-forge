> Scope: this document describes the optional strict numerical workflow or its implementation patterns. For ordinary illustration requests, use [the current general workflow](../SKILL.md) and [walkthrough](walkthrough.md); missing checkers are disclosed coverage limits, not a global refusal. Actual numerical failures still require repair.

# Registered geometry, detail development and immutable corrections

Use this workflow for new scenes in every domain. Start persistent history and resolve optional annotations as described in [execution policy](execution-policy.md) before generation. Set `registered_geometry: true`, schema v2 and `validation_policy: strict`. Start with [design exploration](design-exploration.md) and check [coherence](coherence-validation.md). Legacy examples remain useful patterns with explicitly partial coverage.

## Register novel geometry before rendering

First select represented scope. A broad skyline may use [supported exterior composition](exterior-environments.md), even without a whole-city materializer. The `exterior_environment` contract replaces the room-graph realization requirement only for its bounded exterior scope; physical checks, actual guide visibility, history and independent pixel review remain required. Do not extend this exception to an occupied cutaway or an unmodeled mechanism.

Represent a new shape as a `custom` part with its ID, origin, bounds and `parameters` containing an adapter name, local vertices, indexed faces, optional indexed edges and explicit limitations. Store the procedural builder outside the installed package for a user-specific scene; contribute reusable source only after testing it. A generic box must not stand in for a defining shape.

The indexed adapter checks finite vertices, bounds, face indices and nondegenerate triangles. Rendered faces receive component ownership and participate in the existing visibility report. These checks do not prove watertightness, absence of self-intersections or engineering accuracy. The named adapter's limitations are included in coverage output.

`build()` seals the full registered mesh. `Renderer` rejects appended faces/edges or changed geometry after validation. Register deckhouses, secondary services and context assemblies as scene parts; do not draw a custom hull or crane directly onto a validated mesh and imply it was checked. This is workflow integrity, not a security boundary against arbitrary Python.

## Contact evidence

For a custom component on planar supports, declare `custom_contacts` with `part`, `on` and at least three non-collinear world points defining a contact patch. The validator checks support-top overlap and samples vertices, edge midpoints and centroid on the actual registered triangles. It establishes local surface contact evidence, not full contact integration, load capacity or lateral stability.

Side-mounted components can use `mounts` with part/support IDs, axis and side (-1 or +1). The supported planar adapters check face contact and footprint overlap; the support relation participates in the ground path. Arbitrary curved mountings still require another verified adapter. Declare unsupported coverage rather than treating a bounding box as physical proof.

## Secondary assemblies before finish

Define `detail_regions`: a name, registered primary IDs, distinct secondary IDs, and a subject-specific microdetail description. Intentional smooth/quiet regions may omit secondary IDs only with `quiet_reason`. This makes missing planned assemblies discoverable; counts of detail IDs do not establish rich composition. Inspect whether they form useful spatial layers and meaningful construction.

Reuse component APIs, not the complete layout/flow of another subject. The dry-dock example constructs its own intake-to-pump-to-discharge network; it does not rename a water-treatment module. Keep process scope conceptual where source data is absent.

## Camera selection

Read [camera selection](camera-selection.md) for projected junction witnesses and ranking. Required joints can veto a spacious but uninformative view; optional detail visibility is assessed across several regions. Neither pixel area nor an overall score proves that an assembly is understandable.

Use `projection_review.review()` to compare candidate views after a low-resolution guide render. It reports visible component extents, full framing, secondary visibility and floor occupancy. `choose()` can reject missing subjects or clipped critical access and favor readable focal assemblies. Supply subject-specific critical/focal IDs; no camera angle is a universal default. Inspect the chosen native guide: positive pixels are not recognizable figures or proof of joints. Move supported figures or revise a camera when cabinets hide them, then revalidate and rebuild.

## Freeze the handoff and corrections

`finish_contract.freeze(scene, view)` validates and snapshots the physical scene, realized selection evidence, routes, interface roles, camera and detail plan. Strict scenes require [bound view evidence](view-evidence.md); legacy `freeze(scene)` remains compatible but explicitly partial. `request(lock, brief, art_direction)` combines the short request with this handoff and written style. The planner must still design a subject-specific scene; this helper does not parse arbitrary natural language into geometry.

`prepare_finish.py --scene <scene.json> --view <view.json> --guide <guide.png> --brief "Dique seco" --run <history-run> --source <builder.py>` (add `--stage-records <ordered-approvals.json>` for v4) saves a lock and finishing prompt outside the package. Use the current guide and that written handoff with the available image tool. No old artwork or conversation is required.

Use `correction(lock, scene, edits)` for annotation, interface-clarity, paper-tone or contracted-count corrections. Edits accept kind and target. A count repair may additionally carry `extra_at: [x,y]`, a normalized image coordinate from actual pixel review identifying an invented extra. It must not authorize removal of a registered part or a new process interpretation. The helper rejects altered scene snapshots and carries every route plus external-boundary meaning into the request. If a correction needs a different destination or new component, revise geometry, validate and render a new guide, then create a new lock. Never combine an old lock with a new process interpretation.

External and connected nozzles use open bores; only `termination: cap` creates a blind end. Manifold axial ends with open interfaces remain open in the guide. This improves visual evidence but does not model the unknown continuation or prove that the artistic image preserved it.

This freezes instructions, not pixels. After generation independently trace the visible routes, count subjects and inspect contacts/labels. Mark contradictions and occluded/unverified segments. Do not add invented major scenery during finish; register it first. Preserve the existing two-correction limit for one scene. A new kernel/design iteration is a distinct recorded trial, not a way to hide endless correction loops.

Always retain contracts, guides, prompts, source scripts, variants and independent reviews in project history, including failures. Select one final PNG; do not automatically delete intermediates. Keep runtime files outside the distributable skill.
