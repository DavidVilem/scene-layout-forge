# Mechanical coherence before rendering

Use when a subject transmits motion, force or flow. This reference checks the represented static design. Optional subtle animation follows the separate animation workflow; it does not establish mechanical dynamics or engineering certification. No dismantling UI is promised.

## Two separate paths

State the function and trace (1) the transmission path from source to load and (2) the load path from moving assembly through bearings, frame and foundation. Name stationary and moving parts, joint type and rotation/translation axis. A motor housing must react torque through a mounting; a bearing housing belongs to the stationary support while its shaft may rotate. Do not join moving parts to fixed frames with a cable, brace or guard that would prevent the intended motion.

For rotation, use coherent motor output, coupling, reducer input/output, supported shaft and driven member. Inline and right-angle reducers are both legitimate; do not force all axes parallel. A changed axis needs an explicit transmission mechanism. Do not invent a gearbox ratio or visible internal teeth when no design supports them. For translation, name the actuator, joints and guides, and check how the moving end attaches to the load. For fluid systems, trace inlet, device and outlet separately from structural support.

## Geometry checks

- Coaxial direct shafts/couplings share an axis and contact; nonparallel shafts need the intended gearbox, belt, linkage or other coupling.
- Shafts pass through bearing apertures; the housings are mounted, not attached decoratively beside the shaft. Do not draw the full structure hanging from the motor shaft unless an explicit load-rated arrangement is justified.
- Show the driven connection: reducer output to trunnion, pulley to shaft, or actuator pin to lever. Proximity alone does not establish contact or torque transfer.
- Keep practical access for inspection. Check the current pose for clashes; do not claim a full movement envelope was checked unless sampled geometry actually establishes it. A future movable model requires additional range, collision, restraint and joint data.
- Guards, cable loops and flexible services follow moving/fixed relationships. An exploded assembly would need different validation, and is not part of this workflow.

The optional scene field `shaft_bearings` accepts `{ "shaft": "part-id", "bearing": "part-id" }` entries for a straight `conduit` shaft and a `ring_frame` bearing. Validation uses the actual shaft endpoints/radius and bearing envelope/orientation/aperture to check alignment, coverage and clearance. It does not check load capacity, internal bearing races, gearing, friction, stability or whole-scene collisions. Other mechanisms require project-specific geometric checks, not fake declarations in this field.

The [typed relation contract](typed-interfaces.md#relation-contract-version-1) adds explicit local frames for this same narrow shaft/bearing geometry and for a static hinge declaration. A valid axis flag cannot override misaligned physical shaft endpoints. Rigid mounts need opposing surface normals and a contact patch; sliding supports additionally require a shared tangent axis. Flexible anchors must meet a registered routed component endpoint and its host surface. Unknown mechanisms remain unsupported. These checks establish a specific current geometric relationship, not motion, torque transmission, clearance over a full cycle or mechanical safety.

Bind any visible joint witness to its `relation_id` and verified local region before testing camera visibility. The same two parts seen near a displaced point do not prove their joint. Preserve local anchors, axes, contact patches, support destinations and route boundary meanings together when transforming an assembly or correcting a finish.

## Review the finished image

Trace both paths again on generated pixels. Classify visible interfaces as consistent, contradicted or hidden/unverified. If a housing was disconnected, an axle moved off its bearing or an impossible extra brace appeared, correct that region while preserving view and counts, within the existing two-correction limit. Never report "functional" solely from appearance. For concealed internals report external arrangement plausibility only.

See the [supported drive example](../examples/supported-drive/README.md) and [elevation case](../examples/worked-cases/elevation-mount.md). These describe alternatives, not universal templates.
