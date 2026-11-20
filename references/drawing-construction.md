# Constructing a drawing from a coherent scene

Use these written principles when moving from design intent to a guide and then to the hand-drawn finish. They do not depend on reference images or conversation history. A diagram from a drawing tutorial is an illustration of a limited setup, not a universal geometric rule.

## 1. Volumes before surface detail

Establish the main masses, voids, structural spans, occupied zones and access routes. Build essential forms with the appropriate adapter: a curved shell is not an arbitrary box, an opening is a real opening, and a stair needs its run, rise, landings and surrounding clearance. Use bounding volumes for planning only; do not mistake them for final object geometry. Keep the physical scene separate from any display cut so removing a front wall for explanation does not remove its structural role.

Choose the important visible relationships before adding bolts: shaft to bearing, pipe to nozzle, flight to landing, wall to opening, figure to support. Validate those relationships with the applicable physical adapters. Geometry validation and drawing composition answer different questions.

## 2. Perspective comes from camera and object orientation

Keep camera choice free within the user's request. In linear perspective, parallel world lines in each direction share a vanishing direction. Depending on orientation, a family may meet at a finite vanishing point or remain parallel on the image:

- A level camera aligned with a rectangular space commonly gives one finite vanishing point for its depth axis.
- A level oblique view commonly gives two finite points for horizontal axes; verticals remain parallel.
- A generally oblique, tilted view can give three finite points, including vertical convergence. Do not force vertical edges upright after projecting it.
- Different rotated objects may have different vanishing points. Curved shells do not acquire arbitrary straight-line vanishing families.
- Orthographic plans, sections and axonometric views retain parallel families and do not use finite vanishing points. Their equal-size objects do not shrink merely because they are farther from the camera.

These are consequences of the camera, not selectable decoration. Do not impose one-point perspective on every interior or an isometric view on every mechanism. Fit the field of view and framing to the assembly; do not curve straight physical members to make them fit. Fish-eye is a different projection, and a Droste effect is recursive composition rather than an additional vanishing-point mode. Use either only when explicitly requested and after implementing and validating an appropriate adapter. Neither is currently supported by `Renderer`.

### Existing renderer API

```python
from render_scene import build, Renderer
from projection_review import review, rank

mesh = build(display_scene)  # validated physical scene or its registered display cut
renderer = Renderer(
    mesh, width=1200, height=900,
    projection='perspective', camera_eye=[8, -10, 7],
    camera_target=[0, 0, 1.6], fov=55, near=.1,
    finish='graphite', shadows=True,
)
image = renderer.draw(mesh)
report = review(renderer, display_scene)
screen_xyz = renderer.project([x, y, z])
world_xyz = renderer.unproject(*screen_xyz)
```

The numbers above demonstrate arguments, not a required composition or scale. Explicit `camera_eye` and `camera_target` must be finite world-coordinate triples and supplied together with `projection='perspective'`. `fov` accepts 10–120 degrees and `near` must be positive; the near plane clips geometry and must not be used to conceal invalid joints. For an orthographic view use `projection='orthographic', azimuth=..., elevation=...` without explicit eye/target. The legacy angle adapter retains 5–90 degrees; explicit elevation views may set `allow_level=True` for -90–90 degrees. A level perspective view is possible with equal eye and target heights. Current explicit eye/target framing has no camera-roll argument.

Render candidate cameras, compare `projection_review.rank(...)`, and inspect the selected guide. Use the focal assemblies and critical junction witnesses described in [camera-selection.md](camera-selection.md), not only a large floor or enclosing shell. `Renderer.project()` returns screen x/y and depth; this depth is a projection coordinate, not a physical distance. Use `unproject()` for reconstruction rather than treating depth values as meters.

## 3. Scale and figure contact in world coordinates

Give people plausible world dimensions and poses, with variation where useful. Keep those dimensions when moving a figure to the background; perspective supplies the change in screen size. Do not lengthen distant people to compensate for a smaller projection or make every head occupy the same image row. Shared head height on the horizon is only a special case involving level camera, equal head elevation and matching eye height. Tilted cameras, crouched or seated poses and different floors invalidate that shortcut.

Place feet on the actual floor, tread or platform surface. For seated figures align the pelvis with the seat and feet with the intended support; do not use a silhouette that only looks nearby. Then inspect the projected overlap and native guide: a real contact can be hidden by a rail or cabinet. Screen coincidence alone does not prove physical contact. Reposition the figure or camera without changing human scale to obtain legible contacts. Numerical support checks, visible pixel witnesses and final image inspection remain separate evidence.

The default worker remains standing. `ActorPlan` records task, physical stature, support and exact count. Version 2 adds [registered seated and leaning templates](actor-poses.md) with actual rendered pelvis/sole/palm contacts and a separate posed envelope. Changing the pose label without changing geometry fails. A lower or absent seat, hovering palm or feet on another level also fails. Unknown poses remain unsupported. These static templates do not certify anatomy, grip strength, balance or biomechanics.

## 4. Overlap and visibility before detail

Use depth-tested ownership to distinguish a hidden part from a missing part. Preserve intentional overlaps that explain depth, while avoiding accidental tangencies between rails, pipe edges, worker limbs and arrow tips. Leave enough separation for the important junctions to be read. If a junction is essential but hidden, alter the permitted camera or registered display cut; do not draw its edges through an opaque foreground surface.

Test continuous routes and door/stair clearance in the physical scene, then test their visibility in the guide. A white gap on the drawing is not proof of a usable opening. A crossing in screen space is not automatically a pipe junction or collision.

## 5. Construction detail and the hand-drawn finish

After the camera and relationships work, distribute useful secondary parts across the focal regions: seams at panel boundaries, fasteners at joints, collars on actual pipe ends, brackets at supports, hinges beside removable covers, and grips on accessible equipment. Retain the chosen masses, openings, contacts, counts and camera. Add fine detail without inventing a different load path or moving a critical interface.

Use three relative line weights: strongest for selected silhouettes and nearby dominant edges, medium for construction boundaries, finest for secondary detail and restrained construction marks. Pressure variation is stylistic; it must not break straight members, misalign couplings, warp a common perspective family or erase the inside edge of an opening. Reduce distant detail and contrast selectively without turning every distant component into a blank box. Do not interpret orthographic drawing as a demand for atmospheric fading.

Pass the camera, geometry invariants, subject-specific detail map and annotation-target map explicitly to the finishing tool. Review its actual output independently, including neutral paper tone, readable joints, figure contacts and arrow endpoints. Fine graphite texture cannot repair an impossible connection.

## 6. Light and selective shadow support form

Use a coherent light direction and restrained contact/cast shadow to clarify grounded parts, recesses and overlapping volumes. Keep highlights as paper and avoid equal-value hatching on every surface. Distinguish cast shadow from material darkening; neither should camouflage joints that need inspection. `LightMaterialPlan` provides key direction, ambient/key strengths, cast-shadow strength, value policy and three descending relative line weights. `build(scene)` carries the validated plan into the mesh, and `Renderer` uses the same light for face values and its optional shadow pass. No plan retains the explicitly legacy fixed appearance. Neither mode simulates global illumination or proves physical contact.

Material records reference existing component IDs and local frames (`origin`, perpendicular `axis`/`tangent`), spacing, density, base value and mark grammar. Planar and cylindrical mappings retain the rigid-frame adapter. Cylindrical angular marks use a periodic integer phase across the seam; rigidly transform the frame with the owner. Wood end faces receive transverse rings while side faces carry longitudinal grain. Matte metal, glass, concrete, wood, stone, cloth and rubber have distinct restrained defaults. Glass is a quiet fill specification, not a ray-traced transparency claim.

For a prescribed bend or deformation, use `mapping='registered'` with `vertex_uv=[[u,v], ...]` in the material record for a `custom` part. The UV list must correspond exactly to that part's indexed `parameters.vertices`, and its faces must be explicit nondegenerate triangles. `surface_mapping.TriangleMap` interpolates these coordinates on the actual registered 3-D triangles, including perspective clipping. Shared edge vertices retain matching UVs so grain can continue around a corner. To deform the surface, change its registered vertices, update bounds and physical contacts as necessary, revalidate, and rebuild; retain the UV labels to carry the pattern with those material points. A changed shape never inherits approval of its old supports. The material adapter does not move vertices or create a second rendering mesh.

There is no automatic UV unwrap, deformation solver, cloth dynamics or optical reflection/refraction. Degenerate UVs, mismatched vertex counts, nontriangular mapped faces and registered mappings on unsupported primitive adapters are rejected explicitly. Use a deliberate UV chart/seam when the surface needs one; arbitrary seam stitching is not inferred. Style ablations keep the same registered geometry, contacts, depth and ownership. `Renderer(..., style_seed=0)` optionally changes paper grain/noise only; zero preserves the prior deterministic appearance and a nonnegative seed gives reproducible alternatives.

## Executable checks and limits

Run `python -B -m unittest test_drawing_projection -v` from the skill's `scripts` directory. The tests use the real renderer to check common vanishing directions, orthographic parallelism, depth-dependent scale, tilted verticals, constant human world height and special-projection rejection. They establish camera mathematics and a few construction invariants. They do not verify that a generated illustration follows the guide, that human forms are correct, or that physical joints, supports or loads are valid.

Run `python -B -m unittest test_surface_mapping -v` for corner grain continuity, registered deformation transport, cylinder facet/seam continuity, perspective clipping, invalid-map rejection and material/style-seed ablations. These tests include an actual supported registered surface and require geometry signatures, depth and ownership to remain unchanged when only style changes.
