# Detailed technical-anime style contract

This written style works without a reference image. Use [context and composition](context-composition.md) to choose setting and variety independently of this drawing medium. It is shared across technical subjects; object selection and view are separate. Preserve explicit user overrides, including color, language, detail level or a request for no annotations.

Read [short-request planning](short-request-planning.md) when the brief leaves the design open. Prioritize secondary assemblies and spatial richness before adding surface marks.

Apply [drawing construction](drawing-construction.md): perspective and proportion precede finish. Keep a coherent light direction, contact shadows and a few meaningful tonal groups. Darker marks describe contact, section edges and focal structure; do not turn all background detail equally dark. Scale figures in world space and project them with their surroundings. Never bend straight architecture arbitrarily to imitate a lens or force all verticals upright under a tilted camera.

## Readability at two scales

At normal viewing size, the subject, spatial arrangement and primary functional connections must be clear. When inspecting the image at native pixel scale (without changing its camera), each focal region should contain plausible construction detail: fasteners at joints, seams at panel boundaries, brackets under supported parts, clamps on conduits, hinges on access covers and frames around openings. Select details that belong to the subject. A solar array has cell grids, spars and harnesses; a machine has shafts, bearings and casing joints; a building has slabs, frames, cladding and circulation. Do not paste industrial pipes onto every subject.

Plan large forms, secondary assemblies and fine construction marks separately. Detail should explain assembly, function or scale. Avoid repetitive texture wallpaper, empty slabs, disconnected decoration and microscopic noise. Do not force equal density everywhere: retain necessary circulation and quiet areas for labels while ensuring focal assemblies are developed. Zooming into hatch noise is not evidence of detailed design.

## Drawing language and tone

- Precise hand-drawn animation production layout, fine graphite gray and thin charcoal ink. Slight natural pressure variation, restrained pale construction strokes, selective crosshatching and gentle pencil shading.
- A clear contour hierarchy: strongest for foreground/outer silhouettes and significant section edges; medium for structures and functional connections; finest for bolts, seams, hidden-depth suggestions and annotation leaders. Do not draw hidden geometry through opaque surfaces.
- Paper near white with a barely perceptible ivory tint. Neutral gray ink and shadows. No yellow wash, sepia, ochre or aged parchment. Grain must not obscure linework. No glossy 3D rendering or photographic metal.
- For perspective scenes, choose depth cues according to the lighting and reading objective. Atmospheric distance may reduce contrast outdoors; a critical connection at the back of a room may need stronger local contrast. For plans/elevations, preserve orthographic alignment instead of inventing atmospheric perspective. A space subject can remain a clean technical drawing on paper without adding a black space background or colored planets.
- People are optional, never automatic. When requested, use appropriate clothing and poses for their context. No compulsory helmets, standing-only poses or unsupported feet. In a microgravity scene, use handholds/restraints when relevant rather than inventing a floor gravity direction.

## Optional annotations, enabled by the request

Without an annotation request, use no explanatory labels or arrows. When annotations are requested without a number, choose roughly 3-5 concise English callouts based on actual named assemblies. Scale label count to the composition; do not add a fixed list of factory terms. The intent is to help identify unfamiliar components, not fill margins.

Before finishing, map each exact label to a component ID and a visible surface. Ask for thin leader lines with small arrowheads, modest readable hand-lettered sans-serif uppercase lettering and calm placement in available space. Arrowheads must end on the named part, not on empty space, another pipe or a person's body. Avoid leaders crossing text, faces and important junctions. Group related labels where helpful but do not duplicate arrows unnecessarily.

No Japanese, decorative pseudo-writing, invented measurements or standards claims. An instruction to avoid decorative text does not remove meaningful callouts. User-supplied terminology/language overrides the English default. Inspect wording and target position independently after generation.

## Finishing handoff

Include this condensed contract explicitly when constructing the image prompt: **richly detailed technical-anime production drawing, purposeful small construction parts, neutral graphite and fine ink on near-white paper, readable hierarchy, optional requested semantic arrow callouts, requested view and counts preserved**. Expand with the actual subject-specific details and label-target map. Never rely on the mode name `graphite` or on a past image in another chat.

The guide controls geometry, pose and view, not final tint, uniform hatch patterns or crude schematic figures. Optional references affect mark-making only unless the user says otherwise. Do not send unrelated image history. Inspect the final at whole-image and junction scales; compare against this written contract even when there is no reference. Similar styling is an aim, not a guarantee of identical stochastic output across clients.


## Detail map and explicit finishing handoff

Before finishing, identify a few visible focal regions appropriate to the selected view (usually three, fewer for a small object). For each, name the primary assembly, secondary attached parts and small construction details that will be visible at the output size. For example, a structural joint may need a gusset, fasteners and a seam; a service route may need a tray, cable bundles, clamps and end connectors; a maintenance assembly may need a hinge, latch, mounted instruments and supported wiring. Select by subject, not a mandatory list of pipes or rivets. Include enough secondary assemblies to avoid large undecided blank regions, while retaining glazing, access and label space.

The spatial plan and optional geometry establish the supports, openings, routes, silhouette and visible assemblies. The finish may resolve planned surface joints, controls and small fasteners beyond the guide's schematic detail without adding major equipment, changing connections or moving people. Explicitly tell the finisher that a low-detail guide is not a ceiling on artistic construction detail. Do not demand pixel-identical reproduction of sparse guide linework. Major structure must be decided in the plan before finishing; if represented by a guide, update that guide too.

Compose the finishing prompt with these concrete fields, filled for the current subject:
- Chosen setting mode, purposeful contextual elements and variation plan; user overrides and count limits remain binding.
- Chosen camera, distance, view type and required visible counts; do not insert eye-level/foreground rules unless the brief calls for them.
- Detail map: named focal regions with their planned secondary assemblies and close-scale joints. Preserve readable depth and quiet space.
- Mark-making: rich technical-anime production drawing; three contour weights, fine pressure variation, selective graphite shading and pale construction strokes; near-white paper and neutral gray ink, no yellow or sepia.
- Exact label-to-part mapping: modest, neatly hand-lettered sans-serif uppercase English callouts and thin leader arrows, no typeset serif report headings. User terminology, language and typography requests take precedence.
- Guide invariants versus allowed fine-detail enrichment, followed by a reminder of all required counts and arrow targets.

Do not bake a fixed scene, image, filename, camera or actor layout into this handoff. The same written style must work for a wide exterior, a plan or a mechanical section. The instruction is a repeatable input specification, not a guarantee of identical generated pixels or equal detail at arbitrary resolutions.



## Annotation execution (only when enabled)

Use small, slightly irregular hand-lettered sans-serif capitals: subtle natural variation of stroke and spacing, no artificial wobble, no typeset headings or underlined titles. Legibility takes precedence over irregularity. A leader is a separate thin stroke, not an underline attached to the whole caption.

Map each label to a visible surface before finishing. Prefer an exposed face away from silhouettes and intersections. If an arrow would end beside a person, rail, cable crossing or adjacent housing, move its target within the same part or reposition the label. Use a short elbow leader when useful. Do not route across a person's body to reach a component behind it. At native size inspect the arrow tip and its immediate neighbours: a line that merely reaches the general assembly is insufficient. If the named part is hidden, revise the guide/view or report it unverified; never invent its visibility. Keep language/count overrides and camera freedom.

## Executable art direction and evidence boundaries

In strict mode, use the typed plans in `visual_contract.py` before freezing. In default illustration mode, preserve the same artistic decisions in the general plan without requiring a numerical freeze. They separate reading objective, contextual purpose, construction detail and light/material intent without moving geometry. A plan may choose a centered hero, an off-center machine, a dark interior or a sparse glazed plane. None receives automatic approval from its composition label. Guide evidence rejects hidden focus, unreadable required secondary IDs, context that occludes protected parts and unlinked critical junctions.

Plan marks in a local surface frame. Compare material changes on the same geometry and camera; compare lighting with materials fixed. Spacing, density and tone are separate controls. A fine local pattern should average away at small usage sizes while the secondary construction remains legible. A denser hatch field or a larger render is not additional assembly detail. `quietReason` records why a region is calm and survives handoff unchanged; it cannot waive critical detail visibility.

Three relative line weights distinguish selected silhouettes, construction and surface details. The procedural guide implements that hierarchy where edge ownership is known; final expressive line quality still belongs to pixel review. Surface hatching never changes depth, component ownership, openings, routes or supports. Local material/annotation corrections remain subject to those physical invariants and require review of the new PNG.


## Continuous construction without sacrificing richness

Every pipe, duct or cable should have a meaningful start and end. Plan them using the visual-continuity contract. A route joins a real fitting, enters equipment, ends with a deliberate closure/outlet, passes through a framed/sleeved opening, or continues outside the view. Never let it fade into empty space or merge accidentally with a neighboring contour. Occlusion hides a continuing path; it is not an endpoint. Keep trajectory and diameter consistent on reappearance. Crossing routes remain separate unless an explicit tee joins them.

Keep abundant organized detail. New secondary pipes must also attach to a real destination and have a meaningful termination. Preserve silhouettes, camera, contrast and detail density during local connection fixes. Do not solve continuity by emptying the scene, replacing it with a schematic, or exposing every hidden connection.
