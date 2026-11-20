# Public geometry API

Add the resolved installed skill root to the Python import path, then use `from kit import ...`. The facade imports the existing implementation from the sibling scripts directory; it contains no duplicate renderer. Old script entry points remain compatible.

| Export | Purpose |
|---|---|
| `make_part(id, kind, origin, size, **kwargs)` | Component declaration in metres, z-up |
| `validate(scene)` | List of declared constraint errors; empty means those checks passed |
| `twin_vessels()` | Original small assembly fixture |
| `factory(bays=3, enclosed=False)` | Repeated modules and explicit crossovers |
| `highrise(floors=24, bays=3)` | Original architectural assembly |
| `rounded_route(points, bend_radius, steps_per_quarter=12)` | Tangent route construction |
| `build(scene)` | Construct the depth-rendered mesh after validation |
| `Renderer(mesh, width, height, ...)` | Calculated projection and ownership/visibility analysis |
| `generate(scene_path, out_dir, ...)` | Validated PNG guide in a new destination |

Read [geometry.md](geometry.md) for parameters, component orientations and limitations. Read [walkthrough.md](walkthrough.md) for the end-to-end handoff. All geometry implementations are local to this package.

General technical parts and structural `attachments` use the same scene API; see [component catalog](component-catalog.md). A top-down guide uses `projection="orthographic", elevation=90`.
