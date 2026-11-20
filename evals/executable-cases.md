# Sixteen executable worked questions

`evaluate_registered.py` executes physical positives, deliberate negatives and
calculated-guide observations across six domain groups. Complete subject scope
is stated separately from the bounded fixture. Legacy adapters remain partial;
a validated seat/contact example is not a complete train generator. No image
model or final-art approval is invoked.

Run all cases and six controlled ablations from any current directory:

```text
python -B <skill-root>/scripts/evaluate_registered.py --output <new-external-report.json>
```

Use `--case E05 --no-ablations` for one positive/negative question. `--no-guides`
is available for a physical-only pass and reports guide evidence as `not_run`.
The output refuses overwriting or writing inside the package.

The report separates rule contracts, physical coverage, rejected mutations,
guide ownership and final pixels. Critical failure rate, missed mutations and
partial-coverage count are reported independently of `visual_preference`, which
stays `not_observed`. All claimed comparisons hold the physical model fixed;
context/detail removal is a declared display-only omission. Material, light and
style-seed changes must preserve depth and ownership. A real pump fixture is
also compared under two value policies. ID renaming and admissible rigid
translation are property controls, not different designs.

| Case | Actual fixture / scope | Deliberate negative |
|---|---|---|
| E01 Connected mountain bunker | `bunker`: complete registered pilot | `stair_support` |
| E02 Water-treatment chain | `example:typed-water-hall`: existing typed process fixture; partial coverage retained | `route_endpoint` |
| E03 Instrumentation workshop | `room:workshop`: registered occupied-room component kit; active facility not inferred | `wall_mount` |
| E04 Drawbridge transmission study | `example:supported-drive`: legacy shaft/bearing component study; complete drawbridge unsupported | `shaft_alignment` |
| E05 Vehicle cabin seated contact | `seated`: registered seated task/contact fixture; complete train cabin unsupported | `seat_gap` |
| E06 Sloped access/landing study | `ramp`: registered ramp/landing access; stepped residence materializer unsupported | `blocked_access` |
| E07 Observatory mount transmission | `example:supported-drive`: legacy mounted transmission study; complete observatory unsupported | `attachment` |
| E08 Station module attachment | `example:space-station`: legacy curved-module attachment fixture; occupied microgravity interior unsupported | `attachment` |
| E09 Site blocks and access | `site`: registered three-block site component study; full district generator unsupported | `roof_gap` |
| E10 Curved hull support study | `example:dry-dock`: registered dry-dock hull/contact fixture with partial coverage; airship/mooring unsupported | `hull_gap` |
| E11 Occupied control room | `room:control`: registered occupied-room kit; activity poses require separate actor plan | `furniture_support` |
| E12 Controlled material chart | `materials`: registered fixed-geometry value/material/context fixture | `label_target` |
| E13 Situated contact atlas | `contacts`: registered seated/leaning contact examples, not biomechanics | `seat_gap` |
| E14 Narrow process service study | `plant`: existing typed plant routes/access with partial coverage; full gallery generator unsupported | `route_endpoint` |
| E15 Isolated valve assembly | `valve`: legacy valve primitive; strict support and functional valve adapter unsupported | `extra_context` |
| E16 Same pump plant at night | `plant`: existing plant geometry held fixed for value comparison; partial coverage retained | `route_endpoint` |

## E01 — Connected mountain bunker

Short prompt: Draw a mountain bunker with connected occupied levels.

Intent/decision: Preserve the requested level count; compare hub, spine and branched materializers with real apertures and stairs. Actors require an explicit actor brief/plan.

Discarded choice: Removing a physical support cannot be excused by hiding the facade in the display cut.

Adapter/schema scope: complete registered pilot. Inspect the source constructor in `evaluation_fixtures.py`; each returned scene declares its actual schema and support/interface data.

Invariants: preserve actual fixture part identities, contacts, count and intended target `core-stair-0`. The negative changes `stair_support`; its rejection is required while the baseline remains unchanged.

```text
python -B scripts/evaluate_registered.py --case E01 --no-ablations
```

Limits: The originally proposed stepped comparison is unsupported; branched is the implemented third organization. The new complete fixture does not add workers implicitly. Geotechnical and structural performance are unverified. Room-kit footprint/translation limits are explicit; program furniture does not certify process or human performance.

Finished pixels: not run by this fixture. A production subject needs its own complete current view/handoff and actual PNG review.

## E02 — Water-treatment chain

Short prompt: Draw a small water-treatment installation with safe maintenance access.

Intent/decision: Trace typed pump/header/vessel endpoints and preserve open external boundaries; treat actors as a separately declared inventory.

Discarded choice: A tube ending near a nozzle without the declared connection must fail.

Adapter/schema scope: existing typed process fixture; partial coverage retained. Inspect the source constructor in `evaluation_fixtures.py`; each returned scene declares its actual schema and support/interface data.

Invariants: preserve actual fixture part identities, contacts, count and intended target `m0-pump`. The negative changes `route_endpoint`; its rejection is required while the baseline remains unchanged.

```text
python -B scripts/evaluate_registered.py --case E02 --no-ablations
```

Limits: No hydraulic/process capacity or new complete treatment-facility v3 materializer is claimed.

Finished pixels: not run by this fixture. A production subject needs its own complete current view/handoff and actual PNG review.

## E03 — Instrumentation workshop

Short prompt: Draw a scientific instrumentation workshop with clear working space.

Intent/decision: Use supported workbenches, consoles, storage racks and access; attach any tool/person interaction explicitly.

Discarded choice: Renaming detailed cabinets as instrumentation cannot replace missing required component kinds.

Adapter/schema scope: registered occupied-room component kit; active facility not inferred. Inspect the source constructor in `evaluation_fixtures.py`; each returned scene declares its actual schema and support/interface data.

Invariants: preserve actual fixture part identities, contacts, count and intended target `room/toolboard`. The negative changes `wall_mount`; its rejection is required while the baseline remains unchanged.

```text
python -B scripts/evaluate_registered.py --case E03 --no-ablations
```

Limits: Complete active-workshop layout generation and arbitrary seated/tool-working poses remain unsupported. Room-kit footprint/translation limits are explicit; program furniture does not certify process or human performance.

Finished pixels: not run by this fixture. A production subject needs its own complete current view/handoff and actual PNG review.

## E04 — Drawbridge transmission study

Short prompt: Draw a drawbridge during maintenance above a canal.

Intent/decision: Separate pivot/load/transmission relations, service clearance and water context before a complete scene is attempted.

Discarded choice: A cable through a roller or a detached pivot cannot pass merely because its endpoints are close in screen space.

Adapter/schema scope: legacy shaft/bearing component study; complete drawbridge unsupported. Inspect the source constructor in `evaluation_fixtures.py`; each returned scene declares its actual schema and support/interface data.

Invariants: preserve actual fixture part identities, contacts, count and intended target `input-shaft`. The negative changes `shaft_alignment`; its rejection is required while the baseline remains unchanged.

```text
python -B scripts/evaluate_registered.py --case E04 --no-ablations
```

Limits: Cable/roller kinematics, full drawbridge realization, water dynamics and load analysis remain unsupported.

Finished pixels: not run by this fixture. A production subject needs its own complete current view/handoff and actual PNG review.

## E05 — Vehicle cabin seated contact

Short prompt: Draw a train control cabin with an operator and a view outside.

Intent/decision: Keep camera/world scale consistent; require a real seat and operator pose contacts before claiming seated activity.

Discarded choice: A floating seated operator or incompatible outside perspective must remain unsupported/failed.

Adapter/schema scope: registered seated task/contact fixture; complete train cabin unsupported. Inspect the source constructor in `evaluation_fixtures.py`; each returned scene declares its actual schema and support/interface data.

Invariants: preserve actual fixture part identities, contacts, count and intended target `seated-operator`. The negative changes `seat_gap`; its rejection is required while the baseline remains unchanged.

```text
python -B scripts/evaluate_registered.py --case E05 --no-ablations
```

Limits: Registered seated/leaning task templates are supported; complete vehicle interiors, arbitrary rigging, dynamics and biomechanics are not inferred.

Finished pixels: not run by this fixture. A production subject needs its own complete current view/handoff and actual PNG review.

## E06 — Sloped access/landing study

Short prompt: Draw a stepped technical residence on a hillside.

Intent/decision: Require real terrain contact, level-to-level access and openings; preserve selected stepped organization only when an adapter exists.

Discarded choice: A stair ending against an intact slab must fail even if a graph edge connects the floors.

Adapter/schema scope: registered ramp/landing access; stepped residence materializer unsupported. Inspect the source constructor in `evaluation_fixtures.py`; each returned scene declares its actual schema and support/interface data.

Invariants: preserve actual fixture part identities, contacts, count and intended target `ramp`. The negative changes `blocked_access`; its rejection is required while the baseline remains unchanged.

```text
python -B scripts/evaluate_registered.py --case E06 --no-ablations
```

Limits: Do not reinterpret a stepped house as the hub bunker. Cantilever capacity, terrain stability and full stepped architecture remain unsupported.

Finished pixels: not run by this fixture. A production subject needs its own complete current view/handoff and actual PNG review.

## E07 — Observatory mount transmission

Short prompt: Draw a scientific observatory with a visible instrument mount.

Intent/decision: Distinguish instrument, support, transmission and access; terrain context must remain subordinate to readable mount relationships.

Discarded choice: A nearby casing cannot substitute for a verified transmission axis.

Adapter/schema scope: legacy mounted transmission study; complete observatory unsupported. Inspect the source constructor in `evaluation_fixtures.py`; each returned scene declares its actual schema and support/interface data.

Invariants: preserve actual fixture part identities, contacts, count and intended target `coupling`. The negative changes `attachment`; its rejection is required while the baseline remains unchanged.

```text
python -B scripts/evaluate_registered.py --case E07 --no-ablations
```

Limits: No telescope pointing, dome kinematics, optical behavior or complete observatory materializer.

Finished pixels: not run by this fixture. A production subject needs its own complete current view/handoff and actual PNG review.

## E08 — Station module attachment

Short prompt: Draw a scientific space-station interior with clearly declared crew support conditions.

Intent/decision: Declare gravity/support assumptions and equipment anchors; curved primitive geometry alone does not establish full functional interior validity.

Discarded choice: Arbitrary floor-standing crew cannot stand in for microgravity restraints.

Adapter/schema scope: legacy curved-module attachment fixture; occupied microgravity interior unsupported. Inspect the source constructor in `evaluation_fixtures.py`; each returned scene declares its actual schema and support/interface data.

Invariants: preserve actual fixture part identities, contacts, count and intended target `habitat`. The negative changes `attachment`; its rejection is required while the baseline remains unchanged.

```text
python -B scripts/evaluate_registered.py --case E08 --no-ablations
```

Limits: No microgravity actor rig, restraint simulation or complete strict v3 station interior is claimed.

Finished pixels: not run by this fixture. A production subject needs its own complete current view/handoff and actual PNG review.

## E09 — Site blocks and access

Short prompt: Draw an urban district from above with readable streets and varied building programs.

Intent/decision: Use site regions and site-access relations; preserve orthographic intent if requested and vary program before facade decoration.

Discarded choice: Random window changes that conflict with floor structure do not constitute functional urban diversity.

Adapter/schema scope: registered three-block site component study; full district generator unsupported. Inspect the source constructor in `evaluation_fixtures.py`; each returned scene declares its actual schema and support/interface data.

Invariants: preserve actual fixture part identities, contacts, count and intended target `block-1`. The negative changes `roof_gap`; its rejection is required while the baseline remains unchanged.

```text
python -B scripts/evaluate_registered.py --case E09 --no-ablations
```

Limits: No city-scale parcel/road geometry solver, traffic model or full site support/access realization.

Finished pixels: not run by this fixture. A production subject needs its own complete current view/handoff and actual PNG review.

## E10 — Curved hull support study

Short prompt: Draw a scientific airship moored at a service site.

Intent/decision: Retain hull identity and declared anchoring; reject a missing curved-enclosure/materialization adapter before finishing.

Discarded choice: Adding bolts to a smooth hull cannot compensate for missing mooring or wrong major proportions.

Adapter/schema scope: registered dry-dock hull/contact fixture with partial coverage; airship/mooring unsupported. Inspect the source constructor in `evaluation_fixtures.py`; each returned scene declares its actual schema and support/interface data.

Invariants: preserve actual fixture part identities, contacts, count and intended target `ship`. The negative changes `hull_gap`; its rejection is required while the baseline remains unchanged.

```text
python -B scripts/evaluate_registered.py --case E10 --no-ablations
```

Limits: No researched real-model identity, aerodynamic/structural performance or complete mooring simulation is inferred.

Finished pixels: not run by this fixture. A production subject needs its own complete current view/handoff and actual PNG review.

## E11 — Occupied control room

Short prompt: Draw a control room with purposeful furniture and clear circulation.

Intent/decision: Use actual consoles, operator seats and supported room programs; reserve contrast for meaningful instruments instead of filling all monitors black.

Discarded choice: Unusable circulation or a competing black screen mass cannot be excused by more ornamental detail.

Adapter/schema scope: registered occupied-room kit; activity poses require separate actor plan. Inspect the source constructor in `evaluation_fixtures.py`; each returned scene declares its actual schema and support/interface data.

Invariants: preserve actual fixture part identities, contacts, count and intended target `room/communications-rack`. The negative changes `furniture_support`; its rejection is required while the baseline remains unchanged.

```text
python -B scripts/evaluate_registered.py --case E11 --no-ablations
```

Limits: Operator seating interaction remains unsupported without a new pose adapter; screen software and facility operations are not modeled. Room-kit footprint/translation limits are explicit; program furniture does not certify process or human performance.

Finished pixels: not run by this fixture. A production subject needs its own complete current view/handoff and actual PNG review.

## E12 — Controlled material chart

Short prompt: Internal fixture: show identical geometry and light with different material marks.

Intent/decision: Change only material family/local mark treatment while preserving component ownership, silhouette and physical contacts.

Discarded choice: A shape change or moving contact cannot be presented as a material-only improvement.

Adapter/schema scope: registered fixed-geometry value/material/context fixture. Inspect the source constructor in `evaluation_fixtures.py`; each returned scene declares its actual schema and support/interface data.

Invariants: preserve actual fixture part identities, contacts, count and intended target `body`. The negative changes `label_target`; its rejection is required while the baseline remains unchanged.

```text
python -B scripts/evaluate_registered.py --case E12 --no-ablations
```

Limits: No physical optical transport, arbitrary deforming UVs or empirical final-image material-recognition study.

Finished pixels: not run by this fixture. A production subject needs its own complete current view/handoff and actual PNG review.

## E13 — Situated contact atlas

Short prompt: Internal fixture: inspect foot support, seat requirement, hand-tool contact and shaft-bearing alignment.

Intent/decision: Bind each claimed contact to actual surfaces and a localized relation witness; label unsupported pose contacts honestly.

Discarded choice: Painting a dark contact shadow over a separation cannot repair the missing relation.

Adapter/schema scope: registered seated/leaning contact examples, not biomechanics. Inspect the source constructor in `evaluation_fixtures.py`; each returned scene declares its actual schema and support/interface data.

Invariants: preserve actual fixture part identities, contacts, count and intended target `seated-operator`. The negative changes `seat_gap`; its rejection is required while the baseline remains unchanged.

```text
python -B scripts/evaluate_registered.py --case E13 --no-ablations
```

Limits: Registered seated/leaning task templates are supported; complete vehicle interiors, arbitrary rigging, dynamics and biomechanics are not inferred.

Finished pixels: not run by this fixture. A production subject needs its own complete current view/handoff and actual PNG review.

## E14 — Narrow process service study

Short prompt: Draw a narrow service gallery with pipes and an unobstructed maintenance route.

Intent/decision: Preserve access envelope, typed penetrations, route separation and optional explicit technician count before adding detail.

Discarded choice: Secondary equipment that blocks the corridor must fail physical validation even if it increases visual density.

Adapter/schema scope: existing typed plant routes/access with partial coverage; full gallery generator unsupported. Inspect the source constructor in `evaluation_fixtures.py`; each returned scene declares its actual schema and support/interface data.

Invariants: preserve actual fixture part identities, contacts, count and intended target `pump`. The negative changes `route_endpoint`; its rejection is required while the baseline remains unchanged.

```text
python -B scripts/evaluate_registered.py --case E14 --no-ablations
```

Limits: No automatic industrial maintenance-layout solver or unseen generated-pixel access verification.

Finished pixels: not run by this fixture. A production subject needs its own complete current view/handoff and actual PNG review.

## E15 — Isolated valve assembly

Short prompt: Draw an isolated valve assembly without background or people.

Intent/decision: Honor explicit isolation; provide registered component/port detail at useful scale and exact surface-bound annotations.

Discarded choice: Automatic factory scenery or unrequested people violate the isolation contract.

Adapter/schema scope: legacy valve primitive; strict support and functional valve adapter unsupported. Inspect the source constructor in `evaluation_fixtures.py`; each returned scene declares its actual schema and support/interface data.

Invariants: preserve actual fixture part identities, contacts, count and intended target `valve`. The negative changes `extra_context`; its rejection is required while the baseline remains unchanged.

```text
python -B scripts/evaluate_registered.py --case E15 --no-ablations
```

Limits: No valve capacity/pressure/leak model or claim that all arbitrary valve shapes have complete support adapters.

Finished pixels: not run by this fixture. A production subject needs its own complete current view/handoff and actual PNG review.

## E16 — Same pump plant at night

Short prompt: Draw the same pumping installation on a night shift with neutral paper and readable critical joints.

Intent/decision: Freeze geometry/view and change explicit tonal/light policy only; retain the intended dark interior/context without washing out the task.

Discarded choice: Forcing pale surroundings or hiding a broken route in black shadow fails the intended comparison.

Adapter/schema scope: existing plant geometry held fixed for value comparison; partial coverage retained. Inspect the source constructor in `evaluation_fixtures.py`; each returned scene declares its actual schema and support/interface data.

Invariants: preserve actual fixture part identities, contacts, count and intended target `pump`. The negative changes `route_endpoint`; its rejection is required while the baseline remains unchanged.

```text
python -B scripts/evaluate_registered.py --case E16 --no-ablations
```

Limits: No paired final-image night/day artistic evaluation, calibrated nocturnal illumination or service operation evidence is claimed.

Finished pixels: not run by this fixture. A production subject needs its own complete current view/handoff and actual PNG review.
