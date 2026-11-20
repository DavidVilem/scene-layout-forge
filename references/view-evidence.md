# Bind a guide to the design and annotation targets

After validating the physical scene and rendering the chosen display, call:

```python
from view_contract import create, errors
view = create(physical_scene, display_scene, renderer, guide_path)
assert not errors(physical_scene, view, guide_path)
from finish_contract import freeze, request
lock = freeze(physical_scene, view)
```

The guide must already have been saved as PNG and the renderer must still hold its depth-tested owner raster. `create` produces version 2 evidence and a typed `AnnotationPlan` for each callout: exact ID/text/target, interior surface tip, normalized text box, leader polyline and surface owner. A bounded route search avoids other text boxes, earlier leaders, people, protected context and required interface owners. If there is no clear route or usable target, it fails instead of fabricating visibility. Boxes use a scale-relative lettering estimate; final typography still needs review.

The record binds scene, display, camera, image dimensions, PNG bytes, ownership raster and annotation layout with hashes. It also embeds `projection_review` with a digest and the same raster dimensions: this is the normalized component/junction evidence consumed by the workflow 3 visual gate. Use `errors(..., renderer=renderer)` to check tips against the live owner raster as well. Changing a tip to an adjacent part invalidates both the annotation digest and ownership check. Version 1 evidence (including historical records without a version) remains an explicit legacy compatibility path; it lacks route evidence. Hashes detect stale artifacts; they are not a security boundary or geometric proof by themselves.

Strict finishing requires this evidence and the realized design-selection contract. `prepare_finish.py` accepts `--view <view.json> --guide <guide.png>` alongside its scene, brief and output arguments. A modified scene, camera or image requires rebuilding the evidence and lock. For cutaways, the display carries the original physical-scene hash and explicitly lists omitted geometry/routes.

The finishing handoff includes normalized target coordinates and named parts. Image generation can still shift a surface or a leader; review each actual arrow tip at native resolution. Do not paste guide coordinates blindly onto generated pixels. Preserve the two targeted-correction limit. A failed connection requiring a new route goes back to design and geometry; a visual ambiguity can receive a constrained clarity correction without changing endpoints.

Surface pixels and calculated guide routes do not prove recognizability, final leader routing, final type placement or mechanical correctness. Those remain visual checks. Guide evidence always records artistic pixel review as `not_run` until a separate reviewer inspects the generated PNG. A requested number of labels means that many mapped annotations; a title cannot replace one.
