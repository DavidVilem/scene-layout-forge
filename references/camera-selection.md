# Camera selection from guide evidence

Use after physically validating the candidate scene and rendering several plausible cameras. The cameras may be oblique, lateral, aerial, interior or orthographic as the subject and user require. `camera_geometry.candidates(scene, intent='free')` proposes renderer kwargs with different heights, distances, directions and supported projections. `requested={...}` preserves a requested camera; a plan produces an orthographic top view. Sections and cutaways require an already registered display cut. Rendering these options is required before selection. A rotated view is not a new design.

`projection_review.review(renderer, scene)` retains the legacy component visibility fields and adds normalized owned surface area, height, raster size and local junction witnesses. `choose(reports, required, focus, full=())` remains compatible. `rank(...)` returns admissibility, rejection reasons, metrics and score for every supplied camera; retain that evidence in the execution directory when audit artifacts are requested.

## Critical visibility witnesses

Declare a few informative contacts in `scene['camera_junctions']` before comparing views. Derive their points from the physical connection or support geometry; do not invent screen locations to make a test pass.

```python
scene['camera_junctions'] = [{
    'id': 'shaft-bearing',
    'relation_id': 'shaft_bearing:shaft->bearing',
    'point': [x, y, z],              # world-space position at the visible joint
    'owners': ['shaft', 'bearing'],  # actual renderer surface ownership IDs
    'required': True,
    'radius_fraction': 0.012,        # fraction of shorter guide dimension
    'min_pixels': 2
}]
report = review(renderer, scene)     # after renderer.draw(...)
ranking = rank(reports, required=['shaft', 'bearing'], focus=['drum'],
               full=['stairs'], readable=['worker'])
chosen = choose(reports, ['shaft', 'bearing'], ['drum'], full=['stairs'],
                readable=['worker'])
```

Both owned surfaces must contribute pixels within the projected neighborhood. A whole component visible elsewhere does not satisfy this test. Strict scenes require `relation_id`: `relation_contracts.witness_errors` verifies its owners and point against the actual relation region before testing visibility. A witness outside that region, outside the frame, behind the camera or without one owner fails. Legacy scenes without a link are explicitly `legacy_unbound`. Radius is resolution-relative, bounded to 10% of the shorter image dimension, and should remain local to the joint; do not expand it to absorb unrelated surfaces.

All junctions marked `required` are hard gates by default. The union across camera reports prevents a missing record from bypassing a gate. A caller can explicitly supply `critical_junctions=['shaft-bearing']`. Every focal ID must have visible pixels, even when absent from `required`. Focal and `readable` IDs use equivalent visible area at a fixed `usage_size` (default 1024 square), plus a two-pixel minimum short span. Nine pixels is only a rejection floor, not proof of recognition. Increasing a render from 512 to 2048 does not itself improve this decision. Reports without raster dimensions retain the explicitly reported legacy raw-pixel mode.

## Ranking admissible views

Hard gates run before scoring: requested subjects visible, requested full objects inside frame, requested readability floor and critical junction witnesses. Failed views have no quality score.

Admissible views balance focal owned area (30%), average screen-area readability (30%), the weakest declared detail region (20%), the least readable focal object (10%) and optional junction visibility (10%). Empty floor occupancy contributes only a small penalty (at most 2%). Area readability saturates at 0.5% of the raster per component; focal coverage saturates at 30%. These are transparent guide heuristics, not engineering thresholds. They reward readable surfaces distributed across the requested assemblies instead of only the minimum bounding-box width. Legacy reports without area data retain a width-based fallback.

Inspect `metrics` and the native guide before accepting the winner. Large rock shells, walls or floor plates usually belong in context, not in `focus`. Define informative equipment, occupied spaces, access or detail assemblies as focal IDs. If all views fail, change the layout, physical opening/display cut or camera set, then rerender; do not silently drop a required witness.

Nearby projected surfaces can overlap despite a physical gap. This module does not check the joint's contact, support, opening, clearance, load path or functional role; the physical validators must do that. It does not inspect the final generated illustration, recognize workers, certify artistic detail or prove the arrow endpoints. Those remain independent visual review obligations. Exact score ties use names only as a deterministic tiebreak; there is no preferred angle.

## Typed visual intent and detail evidence

`visual_contract.compile_visual_contract(physical_scene, evidence=review_report)` compiles `visual_plan`, `context_plan`, `detail_budget`, `light_material_plan` and optional `actor_plan`. Its `errors`, `status` and `guide_status` are separate from physical validation. Missing plans return `not_run` with `legacy_no_visual_plans`; they never acquire a fabricated visual pass. Unknown fields, unknown physical IDs and unsupported versions are rejected.

`VisualPlan` declares an objective, primary/secondary IDs, critical witness IDs, readable/full IDs, quiet reasons, depth layers and usage dimensions. Centering or symmetry is allowed. `ContextPlan` declares each entity's role and reason, physical ownership, exact kind counts, exclusions, protected IDs and area/entity budgets. All supporting or traversable context must already be physical geometry. `DetailBudget` declares region primary/secondary/critical IDs, optional microdetail descriptions and minimum projected area/span. A list of invisible bolts cannot satisfy secondary detail.

An intentionally quiet region preserves `quietReason` exactly and must identify `quiet_kind`: clean glazing, unadorned surface, subpixel secondary detail or protected reading space. Clean glazing must actually reference glass; protected reading space must link protected IDs. Quietness does not excuse hidden critical or declared secondary parts. There is no uniform density requirement and no automatic dark-background rule.

## Occupied-subject framing

An optional typed `VisualPlan.subject_framing` identifies the subject IDs, a purpose, minimum normalized width/height/owned area and whether every subject bound must remain inside the frame. Context IDs are excluded explicitly. This prevents a huge geological enclosure from making a tiny occupied building appear adequately framed. Thresholds belong to the specific reading objective: the six-level bunker requires at least 58% width, 30% height and 4% owned area, while a deliberately sparse plan or an elongated component may need another contract. These are guide rejection floors, not universal composition rules.

`useful_camera.fit_camera(scene, subject_ids, ...)` fits a pinhole camera around occupied bounds with optical margins, independently of the size or world offset of its context. `camera_options` proposes four useful directions/heights for the supported hub, spine and branched bunker families, plus a wider hub option that reserves annotation space. That option must pass the same occupied-size gate. A straight-on view is permitted when it explains a long spine best; oblique views remain alternatives. No geometry, contacts or counts move during this search.

`select_useful_view` compares rendered previews, checks normalized occupied framing, required components/details, physically linked junctions and every annotation route, then rerenders and rechecks the selected camera at delivery size. A failed native check tries another already admissible candidate; it never downgrades a gate. `build_bunker.py` uses this path and writes `camera-selection.json` with all candidate scores/failures. If none passes, selection fails with retained diagnostics rather than emitting a successful handoff. The selected camera is rebound to a newly derived display and final view evidence before freezing.
