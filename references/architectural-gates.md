> Scope: this document describes the optional strict numerical workflow or its implementation patterns. For ordinary illustration requests, use [the current general workflow](../SKILL.md) and [walkthrough](walkthrough.md); missing checkers are disclosed coverage limits, not a global refusal. Actual numerical failures still require repair.

# Executable architectural stages, revision .14

Use `workflow_version: 4`, `schema_version: 2`, `validation_policy: strict` for new
occupied buildings, interiors and architectural cuts. Exterior district landscapes
use the separate current [exterior environment contract](exterior-environments.md).
Versions 2/3 remain readable for historical component tests, not as a
way to avoid building gates. A declared architecture contract cannot be downgraded.
Non-building subjects keep their applicable physical workflow; do not fabricate
an architectural envelope for an isolated mechanism.

The new gates are in [architecture_stages.py](../scripts/architecture_stages.py).
They add semantic geometry requirements to existing collision, real-opening,
typed-interface and support checks. They do not calculate forces, spans, soil
capacity, fire safety, rope dynamics, regulations or final-image correctness.

## Contract

`architecture_contract` has version 1 and mode `building`:

- `site`: registered terrain IDs, placement reason, operating direction and an
  `approach` with an exterior access root, entry node, traversable surface IDs and
  optional eye height (default 1 m). The root must be outside occupied spaces and
  building floor footprints, above a real approach surface, and connected to entry.
- `occupied_floors`: actual building slab IDs, separate from exterior approach.
- `spaces`: each ID, activity, area reason, bounds `{min,max}`, interior access node,
  registered fixtures and real door opening IDs. An intentionally open space uses
  `enclosed: false`; do not use this to disguise a sealed room.
- `alternatives`: at least three distinct numeric envelope/height/roof proposals,
  arrival and tradeoff. Camera or room translation alone does not count. The
  selected proposal additionally binds `realized_by`, `geometry_sha256`, and each
  volume's `parts` and actual bounding size. Shapes beyond bounding extents still
  require visual/domain review; a roof name is not a shape proof.
- `envelope.roofs` and `roof_supports`: every roof lists actual distributed support
  contacts. Current gate supports multiple-contact arrangements; a cantilever needs
  a dedicated adapter, not an invented second support. Existing validators verify
  contact surfaces and ground paths separately. Distribution is not strength.
- `required_systems` and `systems`: subject-defining assemblies with actual members,
  connected links bound to typed routes/contact records, and coverage limits.
  A collection of nearby cabinets or missing contracts cannot substitute for a system.
- `witnesses`: required roles `arrival`, `entrance`, `envelope`, `operation`, `context`.
  Each has ID, actual part IDs and optional `min_area_fraction` (default .0003,
  minimum .0001). Actual guide ownership must show those surfaces. Add door and
  connection witnesses where subject identity depends on them. Visible pixel area
  is only a screening measure: inspect recognizability and relationships manually.

See [the station adapter](../scripts/station_architecture.py) and
[negative tests](../scripts/test_architecture_stages.py) for executable structures.

## Ordered evidence and dependency invalidation

```python
from architecture_stages import report, record_stage, save_record
from finish_contract import freeze

# Build the site/program first; then materialize and verify the complete scene.
# Inspect the guide independently before approving stage 7.
records = []
for stage in range(1, 8):
    record = record_stage(scene, stage, records, view,
                          note=stage_decisions[stage])
    save_record(run, record)
    records.append(record)
lock = freeze(scene, view, stage_records=records)
```

Every record binds the exact scene and preceding record; stages 7/8 also bind the
view. Changing any physical/architectural decision invalidates the entire chain
conservatively. Retain the earlier scene and approvals, rebuild, then approve a new
chain. Do not merely edit a `passed` field or reuse a hash from an old guide.
Stages 4-6 run the strict physical validator again. The finish preflight reruns the
architectural gates and checks the seven records rather than trusting a summary.
The chain establishes reproducible checks, not independent human testimony.

For stage 8, inspect the actual generated PNG. Supply all pixel-review observations,
including `architecture:<witness-id>` with normalized image `region` and a concrete
explanation. Essential architecture must be `visible_correct`; `uncertain`, hidden
or wrong architecture cannot be approved. Other unresolved nonessential details
may be disclosed using the existing limited status.

```python
from accept_delivery import accept
selected = accept(lock, generated_png, png_bound_review, run, new_final_path)
```

This verifies PNG identity, evidence coverage and architectural observations, writes
stage-8 evidence and copies the selected PNG exclusively. No variants are deleted.
The observations are supplied by a visual reviewer; Python is not recognizing a
building from the pixels. Failure after the correction limit remains a failed or
limited study, not certified success. Do not endlessly re-freeze the same design
to reset artistic retries.

## Portable regression

From the installed package run:

```sh
python -B scripts/station_stage_example.py --project <project-directory>
python -B -m unittest discover -s scripts -p test_architecture_stages.py
```

The CLI saves source, geometry, failed reports and multiple partial-section views
in a unique project history directory. Every view attempt gets a fresh subdirectory;
revisions never overwrite an earlier guide. Select and inspect one view before
freezing. This example's fixed seed is for regression only; ordinary requests retain
free composition and fresh design exploration. It models a conceptual single-level
terminal, not every cableway type. Older fixtures test their stated narrower scope.

## Cross-domain architectural probes

Use short requests without reference pictures or conversation history:

1. Mountain cable-car terminal: arrival reaches boarding; cabin departure and
   supported canopy remain legible; local cuts retain doors and structural piers.
2. Hillside library: separate public arrival, reading areas and service rooms;
   terrain affects levels; stairs must reach actual landings and openings.
3. Coastal lighthouse maintenance building: entry from the coastal path, supported
   envelope and equipment access; no factory floorplan or arbitrary extra levels.

For each, remove the real approach, move the access root inside, seal a door, detach
a support, remove a required system, erase roof/entry visibility and stale the
selected envelope. These must fail the relevant gates. A new subject may require
an adapter; prose examples do not claim those adapters are already implemented.
