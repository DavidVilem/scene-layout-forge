# Component and drawing contracts

Keep a scene specification in project source, not in the skill. Record component IDs, dimensions, support/parent IDs, ports and intended connections. Do not infer engineering certification from conceptual dimensions.

## Visual contract

Before fixing the camera and geometry, read [art-direction.md](art-direction.md). Record architectural density, spatial layers, paper/ink tone, reference roles and exact labels with targets. Validate the technical guide against this visual brief too; mandatory equipment counts alone do not define the whole environment.

## Components

- Stair: positive height/run/width, integer count, uniform rise and tread, top matches landing. A projected tread may look smaller with perspective; uniform pixels are not the criterion.
- Platform: slab with support points, protected edges and a deliberate stair opening. Rail posts stand on slab edges; rails never close the access opening.
  The bundled validator checks explicit railing bars and posts at each declared stair/ramp-to-landing entrance. It uses the renderer's world-space endpoints and post spacing, including reversed access. Keep the central entrance clear; this local test does not prove that the entire walking route is unobstructed.
  When a platform passes beside tall equipment, declare and check their clearances at the platform height. Correct footing and an aligned stair do not rule out the slab cutting into a vessel. Use explicit cutout geometry if the design intentionally wraps around equipment; do not hide an intersecting solid slab behind the vessel in the camera view.
- Vessel: consistent radius, supported legs/base, named inlet/outlet; flange orientation follows port axis.
- Pump: motor and housing supported on the same base, clear inlet/outlet and coupling; separate it visually from the worker.
- Pipe: centerline route and radius, tangent curved elbows for final-quality geometry, real junctions only at declared tee/manifold nodes. A capped end is legitimate if explicitly designed. Do not misdiagnose every occlusion as a broken pipe.
  A crossing is not an implied junction: revise its geometry or model the intended branch as explicit connections. Connection validation checks local bend radius, conservative self-clearance and interference between routes outside bounded declared junction zones. Inspect those zones and wider fittings separately; a permitted connection zone does not prove that its fitting geometry is correct.
- Architecture: beams terminate on columns/corbels; columns meet foundations; cabinets and conduits anchor to a wall; drains sit flush to floor. Repeated joints derive from spacing parameters.
- Workers: feet on a walkable surface, context-appropriate headwear and readable limbs; clothing follows the requested art direction. Two workers means exactly two figures, not two plus silhouettes in the distance.
  If a figure is hidden, first adjust the camera or, when the brief permits, move the figure within a supported walking surface. Changing from a platform to the floor requires updating both elevation and support ID. Declare clearance pairs against nearby equipment, columns and other figures; include the figure in `route_obstacles` when checking pipe interference. These checks use the body envelope and do not establish a complete walking route. Compare non-worker parts and connection routes before/after a people-only layout correction so visibility fixes do not silently redesign the plant. Re-render at delivery resolution; do not equate a positive pixel count with a readable person.
- Labels: derive wording from the actual object, with leader endpoint on its visible surface. Use only a few useful English callouts; avoid fake specifications and decorative foreign text.

## Review passes

1. Count and silhouette: all requested components, none hidden by decorative architecture.
2. Connectivity: follow each major route, check endpoints and obvious intersections.
3. Access and support: stairs, landing, handrails, worker footing, beam supports.
4. Projection and marks: consistent depth, no mesh facet outlines on smooth tanks, no paper noise covering lines, correct label targets.
5. Artistic finish: reference-like graphite/tone and line hierarchy; no unrequested glossy rendering.

Record what was actually inspected and unresolved faults. See `geometry.md` for implemented adapters, validation coverage and known limits. Neither a valid scene contract nor a polished raster image establishes physical correctness.
