# Image pair and interactive 3D

## Short invocation

"Use $scene-layout-forge to illustrate a mountain service station. Deliver the graphite illustration, its colored edit and the 3D HTML explorer, preserving history."

When 3D is explicitly requested, the sequence produces ilustrada.png, coloreada.png and explorador.html. The model is designed from the station's operation and evidence, not copied from a factory template. Room access, cable route and supporting terrain remain meaningful. Hidden spaces are inferred only when intentionally designed and marked as such. No ambient video is produced.

## Executable independent prototype

scripts/explorer_example.py supplies two vessels, a pump, pipework, stairs and a platform, all from the existing connected geometry fixture. It is independent of any user's artwork and does not claim to reproduce the detailed artistic images. Its separation is explanatory rather than a certified dismantling procedure.

```python
from explorer_example import example
from explorer_workflow import prepare, render
scene, config = example()
job = prepare(project, scene, config, original_brief, example=True)
candidate = render(job)
```

For a user's real triple, use pair=the_selected_output_folder instead of example=True. Check the paired image against the geometry, then run browser tests and independent visual review before accept. A fixture is not a substitute for reconstructing the actual user's scene.

## Other subjects

- Urban panorama: assemblies may be terrain, street blocks, towers, podiums and roof services. Keep hidden floor plans unknown instead of inventing apartments. Top projection is conceptual urban organization.
- Machine: casing, frame, rotor and services; detach at explicit joints, keep rigid pipes rigid, show disconnections. Operating motion is a separate later scope.
- Building: ground/supports, storeys, enclosure and service groups; hiding a roof is not deleting structural evidence. Existing door/stair/landing checks still apply.
- Landscape: actual terrain mesh and meaningful vegetation groups; no building rooms or industrial pipe fixtures inherited from examples.

## Failure probes

Reject duplicate/missing component ownership, unknown assembly members, fixed groups with moving offsets, invalid stage ranges, geometry that already fails its validators, changed PNGs, changed HTML, missing browser review, and overwriting an existing explorer. Visually catch opaque wall occlusion of exploded groups, arrows that imply connected separated ports, clipping that invents internal detail, and model/image mismatches. Correct in a new retained attempt, not by weakening the source checks.
