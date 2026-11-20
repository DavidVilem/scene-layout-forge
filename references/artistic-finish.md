> Scope: this document describes the optional strict numerical workflow or its implementation patterns. For ordinary illustration requests, use [the current general workflow](../SKILL.md) and [walkthrough](walkthrough.md); missing checkers are disclosed coverage limits, not a global refusal. Actual numerical failures still require repair.

# From verified geometry to architectural illustration

Use this path when a user wants a hand-drawn image rather than the calculated study. Keep the scene, references and review record in the current project run, never in this skill.

Read [art-direction.md](art-direction.md) before building the guide. The guide must already express the requested architectural density and depth.

## Separate input roles

- Layout guide: current calculated scene. Identify its counts, camera, circulation and connection topology explicitly.
- Optional style reference: user-provided runtime artwork. Borrow mark-making, paper, line hierarchy and tonal treatment only. Do not import its equipment, labels, people or composition unless requested.
- With no style reference, describe the medium directly. The package requires no private artwork to function.

For interior perspectives, separate total scene counts from what the selected frame can show. State which foreground objects are cropped and which repeated assemblies recede behind others. Tell the finisher to preserve that visibility instead of inserting hidden items into the aisle to satisfy a total count. A count in the scene data is not a visible count in the final image. If every item must be inspectable, change the guide's framing or layout before polishing.

Use the calculated `component_visibility` report to flag missing visible surfaces by component ID, then inspect those locations. A handful of visible pixels is not proof that a worker or valve can be recognized. Record the chosen framing's limitations in the run notes, not as universal exceptions in the skill. Recount the artistic result independently.

Do not send the entire conversation's image history. Include only the current guide and selected runtime references. Inspect local files first. Prefer the available built-in image tool; missing tools are a capability limit, not permission to silently use a paid API.

For registered scenes, use [the frozen handoff](registered-workflow.md). Derive corrections with `finish_contract.correction`; a topology change requires a rebuilt guide, not a free-form artistic patch.

## Build the finish prompt

State setting mode, subject/context hierarchy and permitted variation from [context and composition](context-composition.md). Do not mistake neutral paper for an empty setting or add background towers to a counted district. Use the explicit handoff fields in [art direction](art-direction.md#detail-map-and-explicit-finishing-handoff). Preserve the chosen camera rather than importing an eye-level or close-view example. Carry the focal-region detail map into the prompt, with three contour weights and hand-lettered callouts only when requested.

1. State the layout guide's role and the exact mandatory counts from the scene specification. Name the camera and the required connections and walking route. Preserve these invariants after every correction.
   For repeated connected equipment, translate the actual port graph into a short per-module route description plus inter-module links. Describe where each shared header sits and which branch enters/exits the pump; naming the equipment alone does not preserve its connections. Count those routes against the scene data. State that the same planned scene is being finished, preserving its geometry while developing its approved architectural details and visual depth. Do not use a sparse guide and then forbid the detail requested in the brief. Do not reuse fixture-specific counts for a different design.
2. Describe neutral fine graphite and ink on near-neutral off-white paper with a faint ivory tint; explicitly avoid yellow, sepia, ochre and aged parchment, confident continuous edges, selective construction strokes, restrained crosshatching and slight line-weight variation. Avoid repeating a digital hatch pattern on every surface. Specify darker foreground outlines and lighter distant detail when the composition has depth.
3. Limit enrichment to planned architecture: panel joints, anchored baseplates, stair stringers, platform grating, cabinet seams, short attached conduits. New equipment, branches or people must come from the scene contract developed from the brief, not from ornamental filling during finishing. A short brief permits planning relevant secondary assemblies before the guide; it does not restrict the design to nouns explicitly listed by the user.
4. If people are requested, specify context-appropriate clothing, headwear and poses; do not add workers or helmets by default. Check seated support, standing feet or relevant restraints and adult proportions. Their scale comes from nearby doors/rails/stairs, not a larger cartoon head. Pose changes must preserve footing and clearance.
5. Preserve the label policy in the visual contract. Annotations are off unless the current request asks for them. When enabled, include only the requested callouts with fine leader arrows. Never translate "no Japanese/decorative text" into "no text anywhere". Supply exact English label text and its intended object. Use few labels; omit decorative numbers and fabricated specifications. Leaders should terminate on visible surfaces, not empty space or an unrelated nearby fitting. Explicitly remove guide titles if they are not part of the deliverable.

The sample counts are not defaults: an unrelated building illustration must not inherit vessels or workers just because the regression fixture contains them.

## Compare after generation

Inspect the image, not just a tool success message. Trace the principal pipe route; count equipment and humans; follow the stair to the landing; check rails at the opening and supports under platforms. Check text verbatim, leaders, repeated step direction, cylinder silhouettes and limb contacts. A hidden segment is not automatically a disconnected one.

In an interior view, compare the frame itself before judging detail: near-wall crop, beam intersections, successive column footings, stair opening and the clear aisle. Added surface shadows can clarify separation without adding equipment. Preserve intentionally quiet wall/ceiling regions; filling them with new services changes the design. Then compare the nearest complete assembly endpoint by endpoint, and mark distant occluded connections separately. Natural clothing and selective graphite are style evidence, not evidence of topology preservation.

Record discrepancies separately from aesthetic preference. For a local defect, request a targeted correction with all invariants repeated. Follow the entrypoint's retry limit. If exact geometry is essential and generative polishing changes it, retain a calculated final or disclose the unresolved discrepancy rather than calling the result validated.

For repeated industrial assemblies, check topology per bay, not just whole-image equipment counts. Enumerate each vessel outlet, shared header, pump branch and inter-bay crossover from the scene data. A correct count of tanks does not prove a connected plant. For each connection record `visible-consistent`, `occluded-unverified` or `contradicted` in the project review notes. Only the first status supplies positive visual evidence. An apparently hidden junction must not be silently marked correct.

Before sending a calculated factory guide, inspect its connection visibility report (see [geometry.md](geometry.md)). Whole-route surface visibility can coexist with an obscured pump inlet. Review endpoints with zero nearby route pixels and select a clearer camera where needed. Positive pixel counts are an inspection aid, not an attachment certificate. These measurements are from the calculated guide; never transfer their status to the generated finish without reinspection.

When the brief allows layout changes and a camera change does not expose critical junctions, revise the source layout instead of asking the finishing model to invent hidden connections. Preserve required components and the port graph; reroute pipes or relocate supports with their supported members. A relocated port must lie on the actual equipment surface. Revalidate contacts, clearance and circulation, then inspect all figures and equipment again: moving a post away from a pipe can hide a worker elsewhere. Generate a fresh guide from the revised scene before editing the artistic result.

Targeted edits can introduce new defects: restoring a missing header may duplicate shell outlets; removing an extra branch may disconnect a crossover. After every edit retrace the entire affected route, including both endpoints and junctions retained from the previous image. When the correction limit is reached, keep the verified calculated result for geometry-critical delivery; if providing the artistic study, explicitly identify its remaining uncertain or incorrect connections. Never describe such a study as validated.

A successful small-scene finish demonstrates that workflow only. It does not prove dense factories, arbitrary skyscrapers, every label or all line junctions will remain correct. Validate those compositions independently.

## Repetitive building facades

For towers, derive occupied story count, structural bay count, roof configuration and entry components from the scene contract before finishing. Distinguish structural bays from glass subdivisions. Count story intervals between slab bands from the ground floor through the top occupied floor; the roof parapet is not an additional story. Follow each band around the visible corner and check that it meets the same level on both faces. Inspect aligned mullions, canopy supports, ramp-to-landing contact and small site elements separately from the overall silhouette.

Treat glass reflections and hatching as surface-only changes confined within existing panes. Do not ask for generic facade enrichment when exact repetitions matter: it can introduce extra windows or floors. A full-height image can hide roof equipment and compress entrance details. Record those features as unverified if the delivered view cannot show them; change the calculated camera first when their visibility is required. Do not invent visibility by asking the finish model to unfold or distort the roof. A numerical scan of dark bands can corroborate a manual floor count, but shadows, mullions and reflections also create peaks; it is not a general automated floor validator.

After selecting a result, retain the original generated file, all variants, exact prompts and independent review notes in persistent project history. Verify the selected PNG and report both its location and the history location. One final deliverable does not request cleanup. Never embed runtime images into the shareable skill.
