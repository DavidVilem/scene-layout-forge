# Perspective: camera, groups and visible evidence

For new spatial illustrations include `perspective_contract` in the plan. This is a lightweight design/evidence contract, not a demand for a complete numerical model. Never ask users for vanishing-point coordinates. Infer a useful arrangement from their brief. Preserve free camera selection and organized construction detail.

Example (original fictional river terminal):

```python
perspective_contract = {
    'projection': 'perspective',
    'camera': 'Single elevated oblique camera, no fisheye; frame both boarding and entrance.',
    'horizon': 'Common camera horizon; distant shoreline is not automatically the horizon.',
    'groups': [
        {'id': 'terminal', 'orientation': 'Long facade along riverbank',
         'families': {'longitudinal': 'Straight facade heads and sills',
                      'vertical': 'Column and mullion axes'},
         'exceptions': 'Sloping canopy braces and roof slopes are separate directions'},
        {'id': 'ferry', 'orientation': 'Moored at a slight angle to the terminal',
         'families': {'longitudinal': 'Straight cabin roof side edges and window sill runs',
                      'vertical': 'Upright cabin posts'},
         'exceptions': 'Hull sheer, rounded roof front and raked windscreen are not parallel horizontal edges'}],
    'relationships': [{'groups': ['terminal', 'ferry'], 'alignment': 'rotated',
                       'reason': 'Vessel yaw differs from building; horizontal families still share a camera horizon'}]
}
```

Add dock and gangway groups when their directions matter. Do not copy this arrangement to unrelated scenes. For orthographic views record parallel families rather than finite vanishing points. For nonspatial subjects use `projection: not_applicable`, empty groups and an explicit reason in camera/horizon. Existing plans without the contract remain legacy-unstructured, not geometrically certified.

## Before image generation

Identify parallel straight families within each rigid group, relative yaw and sloping/curved exceptions. A roof edge is not necessarily level. A vessel may pitch or roll; declare such a choice instead of forcing all its directions onto a level-world horizon. Avoid claiming exact orientation for a cropped object.

For risky connected assemblies, prepare a small common-camera guide with axes and masses, using existing renderer projection. Inspect it and save the script/model/camera in history. This does not require a whole-subject adapter. Guide sparsity must not reduce artistic detail. Never claim a written plan or rendered guide validates ImageGen pixels.

## After generation, before color

Use `perspective_contract.keys(plan)` in addition to the existing review keys. Each added observation has status, notes, and a nonempty `evidence` list naming actual visible edges/regions. A visible_correct group needs at least two edge observations. This enforces evidence completeness, not its truth.

Example observation: `{'status':'uncertain', 'notes':'Vessel is cropped; longitudinal agreement cannot be established.', 'evidence':['Cabin roof side edge is short at right border.', 'Lower window sill partially hidden by boarding railing.']}`.

Compare multiple long straight edges from distinct parts of the same family. On a diagnostic copy, extend them toward their estimated intersection; compare horizontal-family intersections against a common horizon. Save overlays in history only. Do not estimate a reliable vanishing point from nearly parallel or very short pixel lines. Record approximate endpoints, selection rationale and uncertainty when using overlays. Curves, slopes and hand-drawn line variation require separate interpretation; do not declare a defect solely from unlike screen angles.

`perspective:camera` reviews projection consistency and horizon evidence. `perspective:relationships` reviews declared rotations and junctions between groups. Group keys review internal coherence (roof/cabin/deck, facade/corners/floor bands, etc.). Merely saying 'oblique view' or 'clear depth' is insufficient.

If a visible contradiction is found, correct that region before coloring, retaining camera, silhouettes, detail, people and scene layout. Keep the two-correction limit. If unresolved, preserve the illustration and clearly report coloring/3D as incomplete; do not spend a color edit propagating a known perspective error. Uncertain hidden geometry is not a reason to force a cutaway or block the entire image.

## Color and optional 3D

In the color composition/linework comparison explicitly inspect the same roof, sill, deck and corner witnesses for new drift. A retained error does not become correct because color preserved it.

For 3D, compare projected model silhouettes and relative group orientations from a source-like perspective camera. The opening display may remain an orthographic matte maquette. Do not compare orthographic screen slopes directly to a perspective image or force the image to match a generic box model. Missing hull/cabin shape and incorrect relative yaw are correspondence defects, not merely texture simplification. Preserve optional 3D and existing connection/access checks.
