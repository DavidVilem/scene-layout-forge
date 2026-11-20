# A shared spatial design for requested images and 3D

Activate only when 3D is requested. Ordinary illustration remains unrestricted and does not require a complete numerical model. An existing image can also be reconstructed; do not regenerate it to fit a simpler model.

For a new combined request, decide the common design before artistic generation: semantic component IDs, relative extents, floor levels, entrances and destinations, primary profiles, host relationships, and camera edge families. Retain these decisions with the illustration plan and carry them into the reconstruction specification. The generated pixels still require independent review: if the generator changes the plan, reconcile the actual accepted image with the specification before adding detail. Do not present the planning model as verified image correspondence.

For an existing image, recover those decisions from visible evidence; mark unseen extents and connections as inferred. No single image uniquely specifies its hidden 3D geometry. Never promise automatic faithful conversion of every possible image, including contradictory drawings. Build a recognizable conceptual reconstruction using appropriate surface/solid geometry and report ambiguity. Do not replace difficult subjects with a flat billboard or relief and call that a complete orbitable reconstruction.

## General forms instead of whole-subject adapters

The kernel accepts boxes, ellipsoids, sweeps, revolved profiles, gridded surfaces, indexed triangle meshes and `loft`.

A loft uses `rings`: at least two planar convex polygon cross sections of equal point count and consistent ordering. Caps are optional (default true). Vertices correspond between rings; the author must prevent twisting and self-intersection. The helper checks finite geometry, planar/convex rings and degenerate faces, not all self-collisions. Use indexed meshes for concave or branching forms. This works for tapered hulls, cab/body continuity, ducts, sculpted roofs and many other subjects without a dedicated vehicle/building adapter.

Design the primary outline before attaching panels. Window and body surfaces must not occupy the same plane: overlapping opaque placeholders can hide correct glazing. Move glazing with its host assembly unless explicitly showing an independently detachable part. A transparent roof skin and opaque ribs need separate materials but can share one assembly.

## Supported circulation

For occupied models, supply `access_network` where circulation matters. Nodes have unique id and world XYZ point on the actual walking surface. Set entry and targets. Each link has from, to, supports (mesh component IDs), and optional points (a continuous polyline with matching endpoints).

The validator intersects each line segment with coplanar supporting triangles and merges coverage intervals; it rejects unsupported gaps, wrong endpoints and unreachable destinations. This is not sparse point sampling. It handles planar slopes when segments follow them. For stairs, model tread/transition segments with an explicit suitable method; do not claim unsupported vertical segments as walking surfaces.

Use protected_spaces for width/headroom and obstruction checks separately. A supported centerline alone does not prove a passage is wide or clear. Do not request loads or certification data. Hidden circulation may be modeled as an inferred plausible route; the source image need not show every doorway, but the actual model must connect its declared destinations.

## Detail and acceptance

Build primary forms, openings and access first; then secondary construction (ribs, mullions, glazing, roof joints, bogies, mounted equipment); then fine detail visible at the intended model scale. Preserve richness with repeated constructive families, not disconnected decorative dots. Match the source-facing camera before deciding that proportions differ. Inspect material/occlusion problems in the actual browser.

Review recognizable silhouette, relative proportions, orientation, placement and connections. Distinguish acceptable material/texture simplification from missing visible structure. Validate geometric checks and browser controls independently. Hidden inferred geometry is not an observed fidelity failure, but must remain coherent. Known visible errors stay repair tasks, not exceptions waived to obtain a final filename.
