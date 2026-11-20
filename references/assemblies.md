# Assemblies, real openings and display cutaways

Use `scripts/assembly_model.py` when a component is an arrangement of real pieces,
when a wall or floor needs an opening, or when the illustration reveals a closed
building. These helpers do not simulate loads, motion, process performance or
hidden image connections.

## Keep three representations separate

1. **Component assembly:** defining local geometry, ports, supporting contacts and
   member IDs. A bed has a frame, legs, mattress and headboard; a workbench has a
   supported top. Neither is an arbitrarily renamed cabinet.
2. **Complete physical scene:** placed components, hosts and openings, routes,
   bearings, access constraints and the full enclosure. Validate this scene.
3. **Display scene:** a derived camera presentation that can hide or clip selected
   surfaces. Never transfer a display check to the physical scene or the final
   raster. Keep all three scopes explicit in the temporary run report.

## Place reusable assemblies

```python
from assembly_model import RigidTransform, compose_assembly, workbench

local = workbench('bench', width=2, depth=.8, height=.9)
placed = compose_assembly(local, RigidTransform((4, 2, .25), yaw=90),
                          prefix='workshop/')
scene['parts'].extend(placed['parts'])
scene['bearings'].extend(placed['bearings'])
for leg in placed['assembly']['ground_contacts']:
    scene['bearings'].append({'part': leg, 'on': 'workshop-floor'})
```

`RigidTransform` rotates about Z in degrees and then translates. Its `point`,
`vector`, `inverse`, `compose` and `bounds` methods distinguish points from
directions. `parent.compose(child)` applies the child first. Compose transforms
before compiling a nested assembly; do not repeatedly bake intermediate meshes.
Use stable semantic IDs and a namespace prefix for each instance.

`compose_assembly` transforms local ports into their new part-relative positions,
world-coordinate connection routes and explicit contact patches. It prefixes
part parents, connection endpoints, bearing/access references, member IDs, ground
contacts, logical host IDs and opening records. No placement modifies its input.
External references not included in the assembly remain unchanged.

Versioned `relations` also move with the assembly: endpoint anchors are recomputed
relative to the placed part origin, normals and axes rotate, world contact patches
move, and relation IDs receive the namespace prefix. The same placement transforms
surface/ground-contact records, bounded ground planes, access nodes and walking
paths, and relation-bound camera witnesses. Their physical validation scope does
not increase merely because the records were transformed.

Translation preserves native component adapters. Plain rectangular solids at
quarter turns remain rectangular. Other rotated components are compiled from
their **actual adapter mesh**, preserving stairs, shells and other defining
shapes; they are never replaced by their bounding boxes. The result records the
source kind, source part and compilation limitations.

**Current validation boundary:** the native stair-access and typed-fluid checks
are axis-specific. A baked rotated shape is renderable geometry, not proof that
these checks support its orientation. Validate the physical source and provide an
oriented validator/contact adapter before using such a shape as a fully verified
physical component. Unsupported orientation must remain unverified or fail the
applicable strict gate. Do not lower the validation policy to make it pass.
Non-orthogonal placement of host/opening records is rejected because they need an
oriented aperture adapter. Native quarter-turn box support remains applicable;
arbitrary rotated AABB contact is conservative and insufficient.

## Subtract an opening from a host

```python
from assembly_model import cut_host, opening_errors

host = {'id': 'partition', 'kind': 'wall',
        'origin': [0, 0, .25], 'size': [6, .3, 3]}
aperture = {'id': 'passage', 'origin': [2, 0, .25],
            'size': [1.2, .3, 2.2]}
cut = cut_host(host, [aperture], normal_axis='y')
assert opening_errors(cut) == []
scene['parts'].extend(cut['parts'])
scene.setdefault('hosts', []).extend(cut['hosts'])
scene.setdefault('openings', []).extend(cut['openings'])
```

The opening uses world coordinates and must span the complete host thickness. A
wall can use `x` or `y`; a floor uses `z`. The hole must remain within the host face.
The helper partitions a plain rectangular host into disjoint closed solids,
subtracting the union of openings. Its solid volume equals host volume minus
opening volume, including overlaps. A complete removal, unsupported adapter,
partial recess, invalid dimensions or excessive partition is rejected.

Logical host records retain `id`, `origin`, `size` and `fragments`; opening records
retain `id`, `host`, `origin`, `size` and `normal_axis`. Optional `filled_by` names a
separate part whose bounds must fit the opening. A door-like drawing on an intact
wall is not an opening. A stairwell's hole must be present in every floor it
passes; a shaft requires a continuous declared clear volume.

Assign physical support relations to the resulting `host/cell-N` solids. A lintel
must have real supports; the subtraction helper does not invent them. Do not
carry a deleted host ID into bearings, routes or parents. Add stricter host/fill
interfaces when the scene needs them. A fit check alone is not proof that a door
can swing or that a stair can be traversed.

`opening_errors` verifies the host's own subtraction fragments and an explicitly
declared fill. It does not search every unrelated component for obstruction.
The full scene's circulation volumes and collision gate detect a cabinet placed
in a doorway or an additional slab blocking a stairwell. Run both checks.

## Derive a cutaway without deleting the real enclosure

```python
from assembly_model import compile_cutaway

# Validate and retain the complete physical scene first.
display = compile_cutaway(
    physical_scene,
    hide_ids=['roof'],
    cuts=[{'host': 'front-wall', 'axis': 'z', 'value': 1.2,
           'keep': 'lower'}],
)
```

Cuts are axis-aligned clipping planes inside plain rectangular components.
Unsupported custom mesh clipping is rejected. Hidden pieces and connections to
hidden or clipped endpoints are omitted **only** from the display scene. Its
`representation` records the physical SHA-256, hidden IDs, cut specifications,
omitted connections and limited validation scope. The input remains unchanged.
Show a plausible section boundary and distinguish intentional cuts from broken
mechanical or structural connections in the artistic brief.

## Semantic prototype scope

- `bed(...)`: four legs, frame, fitted mattress and headboard, with bearings and
  external ground-contact IDs.
- `workbench(...)`: four legs and supported top, with bearings and ground IDs.
- `storage_rack(...)`: four uprights, physically joined shelves and optional
  independently supported supply crates. Local mounts and bearings transform
  together; a rack is not a cabinet with a renamed role. Capacity and anchorage
  remain unverified.
- `elevator_shaft(...)`: continuous guide rails and **one** cabin at a chosen
  height, plus a clear-volume descriptor. It deliberately does not claim working
  suspension, guides, drive, landing doors or physical floor penetrations. Supply
  those separate assemblies and validate their interfaces for a complete design.

These are reusable component prototypes, not a fixed room or building layout.
Choose dimensions and arrangement from the brief. Do not turn the collection into
a single mandatory scene recipe.

## Geological section context

`mountain_section.build_mountain_section(...)` supplies closed heightfield solids
around a genuinely empty cavity, a sampled crown and outer slopes. The physical
model retains the front enclosure and full crown; `display_hidden` lists pieces
removed only from its section view. Its terrain cells have disjoint bounding
regions outside the occupied building and sampled planar base contacts. The
`terrain_contract` records dimensions, omissions and scope.

This is environmental form, not a geotechnical model. A geometric support path
does not demonstrate rock stability or certify the crown span. Contextual
subsurface bands end at z=-.4 and contact the outside ring; foundations ending
higher do not acquire an inferred bearing relation. The bunker builder fills
that interval with explicit footing solids and validates both contacts; another
builder must likewise provide its own contact geometry. Inspect the composed guide for occlusion before finishing
the illustration.

## Verification

Run `python -B -m unittest test_assembly_model -v` from the skill's `scripts`
directory. Tests cover transformed ports and attachment coincidence, preservation
of stair geometry under arbitrary yaw, stable namespaced contacts, aperture union
volume and empty space, rejected invalid hosts/cuts, fill obstruction and fit,
source immutability, display-only route removal and semantic prototype structure.
The image must still be inspected independently after finishing.


## Materialized family scope

The bunker builder supports three different selected organizations: `hub`,
`spine` and `branched`. It subtracts apertures from every traversed room wall,
constructs a supported slab for every graph edge and records typed opening and
clearance witnesses. Its stair core remains a tested adapter shared by these
organizations, rather than claiming that the floors all use the same topology.
Two through twelve levels are supported by this core. Ring and stepped building
realization is explicitly unavailable until separately implemented and tested.

Occupied programs use control consoles and seats, supported berths, open racks,
workbenches, and distribution cabinets with separate service consoles. These are
recognizable conceptual component sets, not proof of electrical, medical or
human-factors performance. The scene records assembly membership and component
kind contracts. Removing an actual defining component can therefore fail the
contract even if its program label is unchanged.

A display cut inherits the material/light intention for surviving components,
while preserving the original physical hash. It does not inherit a physical or
final-pixel pass flag.

For occupied interiors, [room-programs.md](room-programs.md) documents the six
local-frame kits and their floor/wall binding adapter. Each room receives several
functional assemblies, deterministic secondary variation and program-specific
detail recipes. All variants preserve the central access cross and require
explicit contacts; unsupported sizes and rotations are reported. These kits
can furnish another caller's room and do not prescribe its building topology.
