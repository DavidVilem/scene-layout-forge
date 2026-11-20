# Connected mountain bunker

The materializer supports three different organizations: hub, spine and branched.
The explorer compares five graph families, records unsupported ring/stepped
capabilities and selects only a realizable candidate. The bundled hub fixture
requests `family=hub` explicitly. Default policy version 3 keeps all equally valid
supported organizations eligible for reproducible seed-based selection. `--family spine` or `--family branched` explicitly
selects another implemented topology; no graph is silently replaced with a hub.
Every selected zone and adjacency is bound to its own constructed geometry and
walk volumes. Seed controls reproducible exploration and detail.

Run `build.py --output <new-project-run-directory> --seed 1 --count 5` with the
skill's dependencies. It saves the complete physical scene and structured strict
validation, a separate cutaway display scene and a calculated guide. It does not
call an image model. `--no-render` checks the physical scene only. `--levels` preserves the requested
count; the current stair adapter accepts 2–12 levels.

Six occupied levels contain control, sleeping, storage, workshop, utility and
medical programs; radial rooms connect to one continuous stair core. Doorways and
floor holes are actual subdivided openings. Roofs/front walls are removed only in
the representation. Furniture uses supported beds, workbenches, open storage racks, operator
seats, consoles and distribution cupboards. The
physical terrain includes an empty cavity, four surrounding rock regions, crown
bands, sampled outer slopes and a lower geological band. Near-side rock and front crown bands are removed
only from the display scene. Contact samples and geometric noninterference do
not establish a geotechnical calculation or validate the rock span. Eight
continuous footing solids connect the lowest rooms and corridors to the lower
geological band; the deeper core foundation contacts it directly. The contact
geometry is checked, while bearing capacity and settlement remain unverified.

Use the runtime guide with the written artistic finish and independently review
the final PNG. Neither numerical validation nor a display cut verifies generated
pixels, stability, ventilation capacity, fire egress or building-code compliance.

Occupied-room revision: six reusable programs now add real secondary assemblies
with three deterministic variants per program, including planning and inspection
tables, personal lockers, tool cupboards, supply pallets and treatment carts.
Fixtures bind to the actual floor/wall fragments; the central circulation cross
and original callout target IDs remain stable. Read [room programs](../../references/room-programs.md)
for the footprint, placement and performance limits. The complete physical
inventory is computed from the scene; visible requested counts stay six levels
and five stair flights for this example. Rebuild guide and pixel-review evidence
after any furniture change.

## Reproducible decision contract

Short prompt: Six connected occupied levels with explicit supported stairs, real apertures, program assemblies and a sectioned mountain. This bundled fixture explicitly selects hub; spine and branched have their own examples. Default exploration uses selection policy 3 to choose reproducibly among equally qualified supported candidates. Ring and stepped remain unsupported.

Intent: Realize an explicitly selected hub with connected occupied levels and real section openings.

Discarded choice: Rejected silently substituting hub for an unsupported family, inheriting workers, or removing physical supports with the display cut.

Physical schema: `2`; scope: strict registered physical geometry; final artistic pixels are separate. Read `scene.py` for actual geometry and `recipe.json` for counts, camera and semantic targets. The schema number alone is not a coverage verdict. Adapters are those real part kinds and interfaces constructed by that scene; unknown functions remain unsupported.

Invariants: preserve the recipe counts (5 stair, 16 console), declared support/interface relationships and label target IDs. A display cut or style change cannot replace those obligations.

Run from the package root, with the documented Python dependencies:

```text
python -B scripts/run_example.py connected-mountain-bunker --validate-only
python -B scripts/check_examples.py --example connected-mountain-bunker
```

The first command checks the valid fixture. The second repeats it and deliberately mutates inventory, then worker height, route endpoints, attachment ports and shaft alignment where present; every applicable negative must fail. It does not generate images. For an original guide, add `--out-dir <new-folder-outside-package>` to `run_example.py` without `--validate-only`. Never overwrite an earlier run.

Limits: this example does not certify structural loads, process performance, machinery dynamics or human ergonomics. Geometry checks do not verify labels or functionality in a generated PNG. Rebuild current view/handoff evidence and independently review the actual final image. For balanced component and boundary cases use [the staged evaluator](../../evals/executable-cases.md).
