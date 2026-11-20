# Independent spatial core: two routes

Revision 33 interaction: fixed maquette with orbit, zoom, selection and isolation by visibility. No exploded movement or reassembly; no separation acceptance requirement. Old offset/phase fields are accepted for compatibility but normalized to zero displacement. Preserve visual fidelity and support/access checks.


Activate only for an explicit 3D request. Resolve the selected project; no private sources or earlier conversation are required. `scripts/kernel3d` owns sessions, camera fitting, frozen geometry and GLB interchange. It reuses geometry validators and the HTML viewer as adapters. An image-only request still follows the normal illustration workflow.

This is agent-assisted reconstruction: inspect the image and author actual meshes. It is not a learned image-to-3D service. A single image cannot determine hidden geometry uniquely. Any subject can be attempted using general meshes; do not guarantee exact reconstruction of arbitrary pixels. Do not request engineering loads to establish visual continuity.

## New images and optional model: image first

1. Complete the ordinary illustration workflow, then color-edit the accepted illustration. Retain both reviewed deliveries and their attempt history. Do not create a 3D snapshot as a prerequisite.
2. Stop here if the current prompt does not request 3D. If it does, inspect the accepted colored image and author the reconstruction from its visible geometry, following the observation and modeling steps below. Keep hidden regions identified as inference. Fit camera and silhouettes before microdetail.
3. Call `reconstruction_kernel.build(project, spec, colored_source, original_brief, pair=delivery_folder, illustration_attempt=attempt, parent_history=run)`. The current-pair identity is checked; no pre-generation spatial snapshot is required. This compiles actual meshes, runs applicable connection/support/access checks and renders a fixed HTML candidate.
4. Inspect the browser and compare the candidate with the source. Repair meaningful differences while retaining earlier attempts. Accept with the usual fidelity and browser evidence; save `explorador.html` beside the unchanged PNGs. A working viewer is not a fidelity pass.

The lower-level `design_first` snapshot/binding APIs remain supported for explicit legacy workflows and tests, but are not the default route and must not block ordinary illustration/color creation. If such a snapshot is supplied, its immutable binding remains validated.

## Existing single image

1. `start(project, 'single_image', brief, source)` preserves the original pixels and identity without generating either PNG again.
2. Inspect source at native resolution. Record major silhouettes, edge families, depth order, openings, object orientation, contact endpoints and focal detail. Distinguish visible evidence from inferred backs, thicknesses and ground below occlusions.
3. Author a mesh specification from those observations, not from an unrelated example. Prioritize global shape and camera before secondary detail. Reuse components only when their form fits the source.
4. For measurable correspondences, call `calibrate(run, world, image, initial)`: at least six matched 3D points and normalized 2D locations with depth variation. The fitter records residuals and rejects planar-only input. It does not detect landmarks or prove silhouette accuracy. If depth/camera is ambiguous, retain the chosen estimate and reason; do not fabricate a numerical fit.
5. `snapshot(run, spec, camera, evidence)` builds checked geometry, guide and GLB. `reconstruct(run, snapshot)` creates the actual HTML candidate using the retained source. This route requires no paired illustration, history from an earlier run, or image generation backend.
6. Compare with the source camera, then orbit to inspect inferred sides and contacts. Correct the largest mismatch in a new snapshot linked through `previous`; retain every candidate. Apply normal fidelity acceptance and `deliver_glb` only after review. An unaccepted GLB remains available in history as a clearly labeled draft.

## Review and completion

Separate software execution, visual fidelity and inferred geometry. A successful viewer, camera fit or export is not a fidelity pass. Review silhouette, proportion, orientation, placement, openings, connections and route coverage per defining component. Do not stop after an arbitrary two model repairs: continue targeted corrections within the authorized task while meaningful progress is possible. Preserve actual unresolved limitations rather than renaming a failed candidate as finished. The two-correction limit for local raster edits remains separate.

The CLI `python -B scripts/spatial_3d.py --help` exposes start, snapshot, calibrate, reconstruct and deliver-glb. JSON specifications follow the existing reconstruction schema. Portable examples are in [independent core examples](../examples/worked-cases/independent-3d.md).
