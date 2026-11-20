# Situated static actor poses

Use people only when requested or justified by the brief. Preserve exact counts
and physical stature when moving them through depth. A camera changes projected
size; it does not change body dimensions.

The original `worker` without `parameters.pose` remains the unchanged standing
adapter. `worker_pose.make_worker_pose` adds two explicitly supported static
templates: `seated` and `leaning`. The same specification generates primitive
solids, occupied bounds and contact anchors. A pose label alone cannot convert a
standing mesh into a seated figure. Unknown poses and versions fail.

```python
from worker_pose import make_worker_pose
from actor_plan import add_actor

person = make_worker_pose('operator', 'seated', position=[0, 0, 0],
                          stature=1.8, seat_height=.468, helmet=False)
add_actor(scene, person, task='review instruments while seated',
          support='floor', seat='seat')
```

`position` locates the local feet plane in world coordinates; `yaw` rotates the
actual solids and anchors together. `stature` is the nominal physical height,
while `part.size` is the posed bounding envelope. Translation and perspective
never modify stature. `seat_height` and `hand_height` are distances above that
feet plane. The seated template accepts a seat height of 0.18–0.45 times stature;
the leaning template accepts a palm plane of 0.4–0.75 times stature. These are
tested implementation limits of the schematic templates, not human standards.

`ActorPlan` version 1 remains standing-only. Version 2 accepts the new poses and
requires their actual renderer parameters to match the plan. A seated actor
names its `seat`; a leaning actor names `tool` and `hand` (`left` or `right`). A
worktop can be the contact target when the task is inspecting or bracing against
that surface; the term does not imply a particular tool mechanism.

`add_actor` registers one `worker`, its floor-bearing graph edge and typed
`actor_contacts`. Each contact has `id`, `type`, `actor`, `anchor`, `target`,
world `point` and world outward `normal`:

- `foot_support` requires both template sole patches on the actual upward floor.
- `seat_support` requires the rendered pelvis bottom point on the actual seat.
- `hand_tool` requires the declared glove/palm patch on the target surface.

Points are regenerated from current pose geometry before comparison. Stale
coordinates, a borrowed neighbor's seat, missing contacts, lower furniture,
floating hands or a floor on another level fail. The native seat adapter checks
its actual seat plane (0.52 of the seat part's height), not its overall box top.
Other supported planar and registered surfaces use their actual surface checks.
Unknown target surfaces remain unsupported.

`relation_contracts` exposes these contact IDs for camera witnesses. Correct
physics and visible explanation are separate: a hidden pelvis contact does not
become visible because a contact record passes. Select a useful side view or
report the occluded evidence.

Strict collision checking uses the pose's ellipsoids, boxes and bounded limb
segments against supported planar solids and the actual native seat solids.
It does not globally exempt the actor/furniture pair. Exact detected penetrations
fail. Potential intersections involving conservative limb end bounds, oblique
box bounds or unsupported targets remain `unsupported` and block strict
acceptance. Arbitrary-yaw geometry is generated correctly, but this is not a
promise of arbitrary-oriented furniture collision coverage.

The fixture [situated-workers](../examples/situated-workers/README.md) and
`test_worker_pose.py` cover seated/leaning geometry, actual rendered contact
points, distinct poses, stature variants, world transforms, missing seat,
floating palm/feet, stale witnesses and legacy standing counts. This is a static
illustration helper, not biomechanics, anatomy verification, balance, grip-force,
ergonomics or motion simulation. Generated pixels need independent review.
