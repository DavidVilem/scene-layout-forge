# Visual continuity: a path must go somewhere

This is a lightweight drawing contract, not hydraulics, structural analysis or a demand for CAD. Keep the current rich graphite/ink direction and freedom of view. Never ask for load or pressure data to draw an ordinary scene.

## Record before finishing

Set plan.route_scope to present. Add plan.continuity with version 1, an inventory of route IDs, nodes and routes. See [executable example](../examples/route-continuity/example.json). Every route has id, from, to and trace. Nodes have kind and description:

- equipment_port: actual connection on equipment, with a readable interface cue.
- connector: two routes meet, such as an inline joint or modeled diameter transition.
- junction: at least three routes meet at an explicit tee or branch fitting.
- cap: one route ends in a visible closed plate/cap, not an unexplained open cylinder.
- outlet: one route ends in a deliberately designed outlet, with a cue describing its purpose.
- wall_passage: route crosses an opening/sleeve; continues_to describes its continuation beyond the wall.
- frame_exit: route naturally leaves the view; continues_to describes the off-frame continuation. Do not invent a visible end in the middle of the image.

The four physical terminal types equipment_port/cap/outlet/wall_passage require cue. Wall passage and frame exit require continues_to. Each terminal meets exactly one route; create separate ports for different routes. A closed loop can use two or more connector nodes with explicit paths, not a start/end at the same arbitrary point.

Optional node position and route points use one consistent coordinate system. When both are supplied, route ends must meet their nodes. No dimensions or coordinates are required for a purely descriptive design. Coordinate checks do not measure joints in generated pixels.

Use crossings entries {routes: [a,b], kind: separate, cue: front/behind relationship} or {routes:[a,b], kind:joined, node:tee_id}. A joined crossing must refer to the shared junction. Use occlusions entries {route:id, behind:object, continuation:trajectory explanation}. Occlusion does not create a terminal. These records describe intended geometry; the finisher must still depict it coherently.

## Preserve detail and evaluate the actual image

Keep long mains, short branches and depth-rich repetitions. Splitting a main at a tee adds route IDs, not another disconnected pipe. Generate inventories programmatically for repeated families. The tunnel builder demonstrates 35 principal runs and four capped branches, represented as 43 connected graph edges; these counts are an example, not a required style.

After finishing, follow visible pipes across flanges and elbows. Inspect every apparent free end. Verify that short stubs are attached at one end and closed or intentionally open at the other. Compare direction/width before and after occlusion when both portions are visible. A line crossing another line is not evidence of a tee. Check foreground, middle distance and distant rhythm without asking for every bolt to remain legible at vanishing-point scale.

The general review includes ends, crossings, occlusion and newly added routes. Mark a visible break visible_error and request a local correction. Use uncertain/occluded only when sightlines genuinely prevent inspection, not to excuse a plainly disconnected stub. Preserve all generated versions and exact corrections. A passed connectivity graph is design evidence; it does not prove the picture follows it.

## Other architectural encounters

Stairs must lead between accessible surfaces; a landing cannot dissolve into a wall. Platforms must meet supports and a plausible access. Walls need coherent corners, floor/roof edges and openings. Brackets should contact their host and the supported object. Reuse their existing geometric validators where available; do not require a new universal engineering model before illustration.
