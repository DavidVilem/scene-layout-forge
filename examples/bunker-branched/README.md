# Branching bunker

Original procedural example of the `branched` adapter. It realizes the selected
graph as six physically connected levels. Floors, corridor slabs, door apertures
and support locations differ from the hub family; the tested stair core is shared.

Run `python -B examples/bunker-branched/build.py --validate-only` for the
physical checks. Use `--out-dir <new-folder>` for a calculated guide outside the
skill. A guide is not a finished illustration and is not visually approved by
these checks. For another count use `scripts/build_bunker.py --family branched
--levels <count> --seed 27 --output <new-folder>`.

The mountain is a geometric enclosure with a separate display cut. Structural
capacity, geology, fire egress, service performance and final pixels remain
unverified by the geometry checks. No people or unrelated industrial process
equipment are added by this brief.

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

Short prompt: Branching conceptual underground fortress, six connected levels and a physically empty mountain cavity. The selected branched graph is realized with its own walls, apertures, supported corridors and furnishing assemblies.

Intent: Realize a branch and secondary junction with physically mapped corridors and diverse occupied rooms.

Discarded choice: Rejected renaming the hub graph or filling the stairwell to make the elevation simpler.

Physical schema: `2`; scope: strict registered physical geometry; final artistic pixels are separate. Read `scene.py` for actual geometry and `recipe.json` for counts, camera and semantic targets. The schema number alone is not a coverage verdict. Adapters are those real part kinds and interfaces constructed by that scene; unknown functions remain unsupported.

Invariants: preserve the recipe counts (5 stair, 16 console), declared support/interface relationships and label target IDs. A display cut or style change cannot replace those obligations.

Run from the package root, with the documented Python dependencies:

```text
python -B scripts/run_example.py bunker-branched --validate-only
python -B scripts/check_examples.py --example bunker-branched
```

The first command checks the valid fixture. The second repeats it and deliberately mutates inventory, then worker height, route endpoints, attachment ports and shaft alignment where present; every applicable negative must fail. It does not generate images. For an original guide, add `--out-dir <new-folder-outside-package>` to `run_example.py` without `--validate-only`. Never overwrite an earlier run.

Limits: this example does not certify structural loads, process performance, machinery dynamics or human ergonomics. Geometry checks do not verify labels or functionality in a generated PNG. Rebuild current view/handoff evidence and independently review the actual final image. For balanced component and boundary cases use [the staged evaluator](../../evals/executable-cases.md).
