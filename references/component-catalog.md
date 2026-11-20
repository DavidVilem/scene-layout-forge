# Component vocabulary and coverage

The catalog contains 43 supported kinds grouped by purpose, not by allowed subject. Select them according to the brief. Existing industrial examples remain compatible.

| Family | Components |
|---|---|
| Structure | column, beam, slab, footing, brace, corbel |
| Envelope | wall, window, door, curtain_panel, mullion, parapet |
| Circulation | stair, landing, railing, ramp |
| Equipment and routes | vessel, pump, pipe, valve, manifold, flange |
| Services | cabinet, conduit, cable_tray, drain, duct |
| Site and people | paving, planter, bollard, worker |
| General technical assemblies | shell, ring_frame, bulkhead, truss, panel_array, console, seat, gear, rotor, heat_exchanger, luminaire, instrument_panel |

## New technical adapters

All use the declared origin/size envelope. `parameters.orientation` is `y` by default (local longitudinal axis), or `x`/`z`. It permutes local geometry into the specified axis; arbitrary oblique rotation is not implemented. Segment resolution defaults to 48 (12–128).

- `shell`: elliptical cylindrical surface, open ends by default. `capped: true` adds ends for a full circle. `arc_degrees` (30–360) allows a partial curved shell, centered over the local +Z side. No wall thickness or pressure calculation is implied.
- `ring_frame`: annular frame with an actual aperture; `inner_ratio` (0.1–0.95) controls opening size.
- `bulkhead`: rectangular panel with a true elliptical opening and inner side surfaces. It does not include a hinged leaf; design that separately when required.
- `truss`: longitudinal chords, cross frames and diagonal members; `bays` (1–40). Contact checks do not certify structural loads.
- `panel_array`: a thin panel with a surface cell grid; `rows`/`columns` (1–100). Suitable for conceptual solar arrays or modular paneling; not an electrical model.
- `console`: a supported cabinet base with a sloping control face; no populated software UI is implied.
- `seat`: four legs, seat and back. The versioned seated worker template fits its actual seat plane; use [actor poses](actor-poses.md) to declare pelvis and foot contacts.
- `gear`: radial tooth profile (`teeth` 6–80), not an involute engineering gear or a meshing solver.
- `rotor`: central shaft with radial schematic blades (`blades` 2–20), not an aerodynamic blade profile.
- `heat_exchanger`: two end blocks and a regular tube bundle, not a thermal simulation.
- `luminaire`: mounted base and diffuser geometry.
- `instrument_panel`: plate with round instrument bezels; dial markings belong to the finish or an explicit surface detail adapter.

The existing `worker` accepts `helmet: false` for non-construction contexts. Count and footing rules remain active. Do not infer pose support from this switch.

The default worker remains standing. Registered `seated` and `leaning` templates
use `ActorPlan` v2, independently recorded stature, actual renderer geometry and
typed foot/seat/palm contacts. Other poses remain unsupported.

`attachments` records `from` and `to` as `part:port` pairs for coincident structural interfaces, separately from fluid `connections`. Validation checks named port existence and coordinate agreement; it does not prove the ports lie on the intended physical surface. Verify those against the actual mesh and do not use coincident center points to disguise a gap.

See [geometry](geometry.md) for the earlier adapters, [subject planning](subject-planning.md) for unsupported shapes, and [verification](verify.md) for visual acceptance.

## Registered geometry and service details

`custom` indexed components and their sampled surface contacts are described in
[registered workflow](registered-workflow.md). They are useful for new silhouettes,
not a claim that arbitrary geometry is physically valid.

`cable_tray` and `duct` accept `orientation: x|y|z` (default y); the complete
cross section and repeated crossbars rotate with the declared axis. Invalid
orientations are rejected. A `corbel` can use `top_flat: true` for a horizontal
upper bearing face and sloping underside. Register its wall mounting and the
supported tray separately; these do not establish load capacity.
