# Typed interfaces and support coverage (schema v2)

Use `schema_version: 2` for the supported assembly workflow. Version 1 remains renderable but its `coverage` is `legacy-partial`; missing contracts are not proof of correctness. Fluid ports support vessels, manifolds and pump casings. The versioned relation adapters below add bounded geometric checks; electrical mating, arbitrary reducers and dynamic joint behavior remain unsupported.

Use `typed_interfaces.add_interface(part, name, anchor, normal, diameter, role, medium='water', extension=.12, termination=None)`. Anchor and normal are component-local, normal unit-length and outward. Roles are inlet, outlet or bidirectional. An unused port needs an explicit cap or external boundary. `external` means unverified continuation, not a known process destination. The helper derives the legacy-compatible port tip; the renderer uses the same interface to create its nozzle and flange. Do not maintain unrelated hand-written ports and drawn nozzles.

The validator checks analytic surface attachment, outward normal, positive finite size, port-tip agreement, compatible medium/flow roles/diameters and tangent route endpoints. One route per port; use separate manifold branch ports rather than a crossing or multiple routes assigned to one point. A diameter change requires an implemented transition, not a validator exemption. Unmodeled reducers are currently rejected.

Heavy supported component kinds require explicit support paths. Legacy v2 `grounded` means a slab/footing with its top at the conceptual z=0 boundary. New `support_contract_version: 1` instead requires explicit `ground_surfaces` and `ground_contacts` for every root. Workers use their supported parent. Beam/landing adapters require two distinct supports; cantilevers need another verified adapter. Consult `coverage.unsupported_support_kinds`; registered walls, services and native ramps have support adapters. Contact geometry is not bearing capacity or structural stability.

V2 tests all non-endpoint parts as route obstacles using conservative expanded bounding boxes. Strict mode also checks endpoint-body reentry outside the local nozzle region. Pipe-to-pipe clearance, endpoint continuity, actual split host openings and declared component clearance tests remain active. Do not claim exact arbitrary-mesh collision or complete connection certification.

## Relation contract version 1

`relations` is an optional list of `{id, type, ...}` records. Use `relation_contract_version: 1` when adopting this contract. IDs are unique. Tolerance is positive and at most 0.0001 m; a large tolerance cannot conceal a gap. Unknown critical relation types produce `unsupported` and block strict acceptance.

- `rigid_mount`: `a` and `b` contain `part`, component-local `anchor` and unit outward `normal`; `points` supplies a world-space positive-area contact patch. Both frames must coincide, normals oppose, and sampled points touch both actual surfaces.
- `sliding_support`: the same contact evidence plus unit `axis` on both endpoints, equal and tangent to the contact plane. This verifies the declared current contact, not travel range or friction.
- `shaft_bearing` and `hinge`: `a` is the straight conduit shaft and `b` the annular ring-frame bearing. Their component-local anchors coincide; both `axis` vectors match actual bearing orientation. Shaft alignment, span and aperture are checked. Hinge motion is not simulated.
- `wall_opening`: `opening` references an existing through-opening and its actual host fragments.
- `stair_landing`: `flight` and `landing` reference an existing verified stair/ramp landing relation.
- `fluid_port`: `from` and `to` identify an existing typed connection; `endpoint` selects `from` or `to` for its local witness region.
- `flexible_anchor`: `a` references a routed pipe/conduit endpoint and `b` its actual host surface; coincident local anchors must touch it. This does not provide cable sag or cloth simulation.

Existing records expose deterministic IDs without changing their compatibility scope: `bearing:part->on`, `mount:part->on:axis:side`, `stair_landing:flight->landing` and `shaft_bearing:shaft->bearing`. `relation_contracts.relation_report` reports each relation independently. A camera junction supplies `relation_id`, exact `owners`, and a world `point` in that verified relation region. `witness_errors(scene, witness)` rejects stale IDs, different owners, detached surfaces and points moved elsewhere on the same objects. Camera visibility remains a separate check.

With relation version 1, an intentional collision exception also needs `relation_id`; its overlap region cannot exceed the verified local relation region. Earlier scenes retain their explicitly bounded v2 exception semantics. They do not acquire a new mechanical claim automatically.

## Logical routes and boundaries

`route_contract_version: 1` requires each spatial connection to name one `contract_id` in `route_contracts`. Each logical record supplies `id`, exact `from`/`to`, and `medium`. Optional `min_bend_radius`, `min_separation`, `max_unsupported_length`, `supports: [{part, point, normal}]` and `maintenance_volumes` add geometric obligations. A support point must touch its real support surface and the tube exterior; arc length between actual supports is checked. Unsupported geometry blocks a critical contract. Shared-junction separation needs its own local adapter; it is not globally exempted.

External interfaces under version 1 include `boundary: {service, destination}`. This records the intended continuation; it does not establish the unseen system's performance. The external nozzle remains open geometry. Freeze these meanings with the physical scene before finishing.

## Workflow and failure tests

1. Describe intended system relationships without inventing performance. Establish component IDs, interfaces, terminations, support contacts and circulation.
2. Generate the geometry from those contracts. Use `examples/typed-water-hall` as a pattern, not a universal composition. Inspect the guide at junction scale; correct missing or obscured connections before finishing.
3. Run `python -B -m unittest discover -s scripts -p test_typed_interfaces.py`. Tests include internal ports, reversed roles, diameter/medium mismatch, missing supports/terminations, floating beams, blocked stair openings, route obstacles and unsupported versions.
4. Hand off the current guide plus per-route and support relationships, explicit detail map and label targets. Preserve secondary architectural richness; do not cover errors with extra texture.
5. Independently classify final-image junctions as visible-consistent, contradicted or occluded/unverified. Review labels separately. Limit corrections as in the entrypoint; return residual limitations honestly.

Always retain contracts, guides, prompts, source scripts, variants and independent reviews in project history, including failures. Select one final PNG; do not automatically delete intermediates. Keep runtime files outside the distributable skill.
