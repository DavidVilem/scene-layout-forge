# Occupied room programs

`scripts/room_programs.py` supplies six original local furniture kits. It adds
recognizable secondary assemblies in the front and corner areas instead of
counting more legs or small marks as a richer room. Each program has three
deterministic arrangements. The room index cycles those arrangements so adjacent
rooms on one level differ; the independent detail seed changes the starting
variant without changing stair or topology requirements.

| Program | Actual compound objects beyond its primary furniture |
|---|---|
| Control | Communications rack, document cupboard, planning table and document tray, bracketed shelf |
| Dormitory | Bedside units, personal locker bank, footlocker, writing desk and seat, separate bedding layers |
| Storage | Varied open racks and bins, pallet deck on sleepers, supply containers, packing table and sorting bins |
| Workshop | Under-bench drawers, supported vise jaws, wall-mounted toolboard, tool cupboard and inspection table/case |
| Utilities | Wall-mounted distribution cupboards, maintenance cupboard, service table/case, rectangular duct return and filter on separate brackets |
| Medical | Bedside units, supply cupboard, supported treatment cart with two trays, treatment case and bracketed supply shelf |

These are approximately five to eight functional assembly groups per room, with
multiple solid members and explicit contacts. A part count is an implementation
inventory, not a quality score. Program-specific `semantic_role`, `design_program`,
assembly descriptions and `detail_recipe` explain the purpose of the geometry.
The scene also stores one compact `room_programs[zone]` recipe with selected
secondary targets. Final appearance still requires inspection of the actual PNG.

## Caller-owned placement and support

`program_assembly(program, width=7.4, depth=7.4, seed=52, variant_index=0)`
returns local geometry around a room center. `place_program(...)` namespaces it
and binds `@floor` and `@north` to the actual floor and wall fragments supplied
by the caller. Wall mounts must geometrically meet those fragments; a remote
wall, absent floor or unsupported program raises an error. The caller then adds
the returned parts, bearings, mounts and assemblies to its physical scene.

```python
kit = place_program(
    'workshop', 'workshop-a', floor_id='floor-a',
    wall_parts={'north': ['north-left', 'north-right', 'north-lintel']},
    scene_parts=scene['parts'], transform=RigidTransform((cx, cy, floor_z)),
    width=7.4, depth=7.4, seed=52, variant_index=1,
)
for field in ('parts', 'bearings', 'mounts', 'assemblies'):
    scene.setdefault(field, []).extend(kit.get(field, []))
scene['assemblies'].append(kit['assembly'])
```

The central 1.8 m cross stays empty below the service height in the supported
footprint. The scene still supplies real openings and walking envelopes and
validates them after composition. Wall fragments therefore represent actual
apertures, not assumed doors. The bunker integration retains its six original
callout targets and all five physical stair flights while choosing larger,
visible secondary objects for each region.

Current kit limits are explicit: at least 7.4 by 7.4 m clear interior, translation
frames only, and conceptual furniture. Smaller rooms or rotated fixture mounts
need a separate layout/contact adapter; they are rejected rather than squeezed
into this arrangement. The utilities extension meets the bunker caller's
standard rectangular trunk at local x=2.8; another caller must supply its own
matching trunk if it claims that connection. Airflow, electrical operation,
clinical performance, capacity and human ergonomics are not validated.

`test_room_programs.py` checks every declared program variant, room-to-room and
seed variation, central clearance, explicit unsupported limits and negative
missing-contact/blocked-route cases. `test_bunker_families.py` exercises all three
declared physical organizations. Guide ownership checks can establish that the
new pieces are visible; they do not approve the artistic result.
