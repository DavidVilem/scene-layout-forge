# Supported inline drive

This fixture demonstrates external continuity and supported bearing axes, not gearbox internals or a safe operating machine. The rotor is stopped for inspection; an operational installation needs a designed guard. The enclosing gearbox is a plausible coaxial unit, not proof of a particular ratio or gear design.

Run `build.py --validate-only`, or `build.py --out-dir <new external folder>` for a calculated guide. The shared schema checks attachments, counts and declared bearings. `shaft_bearings` checks both actual shaft/bearing interfaces. Deliberately shifting a bearing sideways, undersizing its aperture or shortening the shaft must fail. The numerical checks do not prove the generated finish preserves these interfaces.

Detail map: motor cooling fins/end-cover fasteners and foot mounts; reducer enclosure seams, coupling guard attachment points and input/output connections; bearing housings, pedestal feet and rotor hub. Do not add gears beside the unit just to imply transmission. Label arrows terminate on exposed housing surfaces away from the shaft silhouette. Use camera freedom; no reference art or fixed perspective is required.

The shaft and hub are coaxial in this fixture; keyed/clamped torque transfer and enclosed gearing are conceptual and must not be presented as analytically verified. For a new load or axis arrangement create its own contract instead of stretching this fixture.

## Reproducible decision contract

Short prompt: Conceptual inline motor, coupling, enclosed coaxial reducer, output shaft and rotor between two bearing supports. Stopped for maintenance; no internal gear or dynamic verification claim.

Intent: Trace the visible shaft, coupling and bearing alignment in a stopped transmission.

Discarded choice: Rejected inventing internal gearbox meshes or treating shaft alignment as a dynamic or load calculation.

Physical schema: `1`; scope: partial adapter coverage; passing the fixture does not migrate it to complete strict workflow v3. Read `scene.py` for actual geometry and `recipe.json` for counts, camera and semantic targets. The schema number alone is not a coverage verdict. Adapters are those real part kinds and interfaces constructed by that scene; unknown functions remain unsupported.

Invariants: preserve the recipe counts (1 rotor, 2 ring_frame, 0 worker), declared support/interface relationships and label target IDs. A display cut or style change cannot replace those obligations.

Run from the package root, with the documented Python dependencies:

```text
python -B scripts/run_example.py supported-drive --validate-only
python -B scripts/check_examples.py --example supported-drive
```

The first command checks the valid fixture. The second repeats it and deliberately mutates inventory, then worker height, route endpoints, attachment ports and shaft alignment where present; every applicable negative must fail. It does not generate images. For an original guide, add `--out-dir <new-folder-outside-package>` to `run_example.py` without `--validate-only`. Never overwrite an earlier run.

Limits: this example does not certify structural loads, process performance, machinery dynamics or human ergonomics. Geometry checks do not verify labels or functionality in a generated PNG. Rebuild current view/handoff evidence and independently review the actual final image. For balanced component and boundary cases use [the staged evaluator](../../evals/executable-cases.md).
