# Conceptual coherence gates

Use `validation_policy: strict` for new physical scenes. `scene_model.validation_report(scene)` reports the base checks and coherence checks together. A legacy example remains `partial`; schema v2 alone is not full validation. Critical `failed` or `unsupported` evidence blocks strict acceptance. `not_applicable` is legitimate only when the feature is absent; `not_run` is never a pass.

## Components, interfaces and support

An installed pump declares `functional_contracts: [{part: "pump", role: "installed_pump"}]` and requires both inlet and outlet with valid connections or explicit external boundaries. A stored spare instead declares `role: stored` and has no inferred process function. Typed interfaces continue to carry medium, flow role, orientation, size and termination. A flange that merely appears near another does not connect it. Nozzle footprints must fit the supported host adapter; paths may enter their terminal only within the declared nozzle neighbourhood.

Every declared functional contract produces exactly one result carrying `contract_id` (explicit `id`, or a stable index/part fallback), part and role. A non-pump contract is not silently ignored: an unknown adapter produces `unsupported`. The modest `component_set` role verifies `members` and `required_kinds`; it does not prove operation or recognize a picture. Missing mandatory pump contracts remain separate failures. `not_applicable` means there are no declared contracts or mandatory pump functions.

Support paths cover equipment, structure, furniture and services. Use bearings for planar contact and mounts for planar side attachment. Curved contacts need their own adapter; moving an unsupported object into a bounding box is not support proof. Collision broad phase considers all registered parts, not only manually listed pairs. Opaque-box overlap fails; curved or hollow overlap may be conservatively `unsupported`. A local `contact_exceptions` record needs the exact shared region, relation and reason, rather than a global pair exclusion. It records intended assembly overlap and does not certify its mechanics. Never auto-whitelist every collision to obtain a pass.

`grounded` declares a boundary of the support graph; it does not detect actual earth or fix a visible gap. When ground or a geological layer is modeled, connect the foundations to that actual surface through explicit contacts. Keep only the outer modeled site boundary as the declared root. The bunker example includes continuous foundation pads and a regression that rejects a raised footing. This establishes contact, not soil bearing capacity or rock stability.

For a new explicit ground contract, set `support_contract_version: 1`. Register `ground_surfaces: [{id, type: "plane", point, normal, bounds: {min, max}}]` and `ground_contacts: [{part, surface, points}]`. Each root requires a positive-area patch on the bounded plane and its actual opposing surface. The plane can be inclined and translated. Legacy v2 roots explicitly retain their old z=0 boundary semantics. `surface_contacts: [{part, on, points, normals?}]` supports planar boxes, native ramps/stair treads, registered mesh triangles and the supported analytic cylinder surfaces. Every supplied normal is checked. Flat patch interiors are sampled so corners cannot bridge a hole. Curved patches are sampled evidence, not a continuous surface-intersection proof. Degenerate point/line contact is `unsupported`; unknown surface adapters remain `unsupported`.

Support graphs reject undeclared cycles. `support_cycles: [{members, reason}]` may explain an intended cycle, but each member still needs a verified route to a physical root. A cycle cannot support itself. Bearing samples on registered terrain must meet the actual triangles, rather than just the top of its bounding box.

## Access and openings

`access_nodes` have IDs and positions; `access_roots` declare real entries. Each `access_volumes` item names `from`, `to`, `min`, `max` and whether it is critical. Nodes must lie inside their volumes and connect to an entry. Use multiple adjacent volumes for turning paths rather than one enormous diagonal AABB. A volume may list `traversable_parts` only for stairs, ramps, slabs and landings actually forming its walkable support; it cannot hide walls or cabinets.

Check head clearance and landing approaches in the physical model. A stair reaching the correct elevation is insufficient if the slab over it is solid. Use `assembly_model.cut_host` to form real disjoint pieces around the opening and validate the opening records. Openings and structural supports must survive every rigid placement. Validate geometry before deriving a separate display cut.

`traversable_parts` never skips the solid stair or ramp. A rectangular volume is tested against native stair tread boxes/rails and the actual ramp wedge. For an inclined journey, supply `walking_path` world points, `body_below`, `body_above` and `half_width`. The path endpoints must match its access nodes; the swept body must fit the declared bounds. A selected `supported_flight` requirement also needs `walking_offset`, the vertical distance from the path's body reference to its real walking surface. Samples must follow actual treads/ramp heights and cover both ends, so a nearby floating path cannot claim that flight. All obstacles, including the named walking support, participate in collision checks. Stair rails retain conservative envelopes. These dimensions are conceptual clearance choices, not building-code approval.

## Selected graph requirement coverage

Keep `materialized_design.edges[edge_id]` as its access-volume list. Add `materialized_design.requirements[edge_id][requirement]` for every selected `edge.requires`:

- `supported_flight: {parts: [...]}` references real supported stairs/ramps spanning this edge's levels.
- `landing: {parts: [...]}` binds real supported landing/slab parts to those flights' landing relations.
- `headroom` or `clearance: {access_volumes: [...], min_height: 1.8}` covers exactly the edge's mapped volumes and checks their profiles and solids. A larger declared minimum is allowed; 1.8 m is the adapter's conceptual lower bound, not a legal standard.
- `opening: {openings: [...]}` references actual clear host openings intersected by this edge.

Missing evidence fails. Another floor's flight or opening does not substitute for this edge. Unknown requirements are `unsupported`. `design_realization.realization_report` separates each requirement and its validators from graph identity and program declarations. Old non-strict graph fixtures explicitly report requirement `not_run`; strict scenes cannot use this compatibility path. A zone may add `program_contract: {adapter: "component_set", required_kinds: [...], assemblies: [...]}` to verify real members of the allocated zone. Semantic labels alone retain their declared-only scope.

## Failure controls and limits

`scripts/test_coherence.py`, `scripts/test_physical_contracts.py` and `scripts/test_requirement_contracts.py` include overlapping cabinets, blocked landings, floating ramp/duct, ground gaps, sloped contact frames, displaced relation witnesses, unrelated requirement evidence, missing openings, insufficient headroom, unknown functional contracts and changed route destinations. Positive controls and bounded intended contacts prevent a validator that rejects everything from appearing successful.

These checks establish conceptual spatial consistency within supported adapters. They do not calculate stress, stability, fluid performance, code compliance or dynamic motion. Self-intersections of arbitrary meshes, curved collision narrow phase, arbitrary-axis support integration and actual equipment operation may remain unsupported. Keep those limitations in the report; do not lower severity merely to finish an image. The final raster has its own independent review.
