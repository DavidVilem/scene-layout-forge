# Optional image-derived 3D kernel

Revision 33 interaction: fixed maquette with orbit, zoom, selection and isolation by visibility. No exploded movement or reassembly; no separation acceptance requirement. Old offset/phase fields are accepted for compatibility but normalized to zero displacement. Preserve visual fidelity and support/access checks.


## Activation and scope

Use this module only when the user requests a 3D model, interactive explorer, 3D decomposition or spatial reconstruction. An ordinary illustration request keeps the two-image workflow. A requested 2D plan alone does not require 3D. Ambient animation is separate. Do not edit or reduce the artistic image to fit this kernel.

Accept a single raster source or the existing illustrated/colored pair. For a new illustration plus requested 3D, follow [the independent image-first route](independent-3d.md): generate and review the illustration, edit and review its color, then reconstruct the accepted colored image. For an existing image inspect available history first; unavailable history does not prevent reconstructing visible features. The agent performs visual analysis and writes a specification. The bundled Python is a compiler and validator, not an automatic visual detector, learned image-to-3D model or hidden-geometry oracle. Any subject can be attempted through composed or custom meshes, but exact complete reconstruction of every image is not guaranteed. Abstract images, severe occlusion and contradictory perspectives may support only a limited conceptual interpretation.

## Independent workflow

1. **Read the image.** Inspect at actual resolution. Identify the silhouette, defining surfaces, functional groups, occlusion, ground and source camera. Record important evidence as normalized image rectangles and semantic targets. Do not use an unrelated demo scene.
2. **Author a spatial hypothesis.** Choose a coordinate frame and relative proportions. Mark observed, inferred and modeled components. Record hidden assumptions even for an observed shell: its back is not observed. Use source/history dimensions only when available; do not ask for weights or hydraulic specifications.
3. **Build defining geometry.** Use `reconstruction_geometry.py` for composed boxes, ellipsoids, revolved profiles, tube sweeps, triangulated grids and arbitrary indexed meshes. Transforms apply scale, then X/Y/Z Euler rotation in degrees, then translation. Rotational profiles use radius/height, Z axis; partial angles create openings. These are geometry building blocks, not domain-specific templates. Doors/openings must be actual gaps or shaped mesh, not labels on solid walls. Arbitrary concave forms require explicitly triangulated input. Do not replace a dome, hull, organism or optical tube with an arbitrary box because an adapter is absent.
4. **Connect what is modeled.** Author named world-space anchors and contacts on actual surfaces. The compiler checks anchor coincidence and surface membership. Routes use existing scene connections and retain endpoint/curvature/clearance validation. A shared point is local contact evidence, not proof of stability, contact area, circulation or load capacity. Record support scope for every component; inspect untested joints visually. Keep supported strict checks when reusing existing models; do not downgrade them into a new unchecked reconstruction to pass.
5. **Generate a real candidate.** `reconstruction_kernel.build` saves source identity, specification, model, checks and linked explorer history, then produces candidate.html. A missing subject adapter is not an external blocker: use the general shapes or author a mesh. Planning alone is not a completed requested reconstruction. Retain a failure report if construction fails and repair it within the current task.
6. **Compare and correct.** In a source-like view, compare the main silhouette, relative heights, proportions, openings, entry and connections. Then orbit and inspect depth, backs and contact points. Correct major contradictions in a new linked attempt; continue targeted reconstruction corrections while meaningful progress is possible, preserving unresolved limits honestly. Do not claim pixel-exact correspondence or transfer model checks to the artistic image. A simpler technical representation is acceptable only if it preserves defining shapes and distribution.
7. **Check and deliver.** Run the actual browser checker, inspect assembled/intermediate/separated/section/plan/mobile views and use explorer_workflow.accept with specific observations. For a pair deliver explorador.html beside the unchanged PNGs. For an external single image use a new output directory containing explorador.html and the byte-identical source reference. Retain complete history. Separate conceptual parts without portraying that animation as a physically valid dismantling sequence.

## Specification versions 1 and 2

Components may specify `opacity` in (0,1], default 1. Use it for actual glazing surfaces in the HTML instead of deleting enclosure to reveal rooms. Meshes still participate in passage/contact checks. Source-like browser comparison shows the actual material; the legacy software raster may render that surface opaque. Keep geometry and inspection claims separate from material appearance.

New models use schema_version=2 and quality_contract from [maquette fidelity](maquette-fidelity.md). Version 1 remains readable with its quality checks explicitly not run.

Top fields: schema_version, title, camera_notes, limitations, components, assemblies, correspondence, optional contacts and connections.

Each component has id, shapes, provenance (`observed`, `inferred`, `modeled`), evidence, hidden_assumptions, support_note and optional anchors mapping names to world XYZ. Each observed component must appear in correspondence, whose entries have parts, evidence and image_bbox=[left,top,right,bottom] normalized to 0..1. These boxes are documented agent observations, not automatic image matching scores.

Shapes:

| type | Required geometry |
|---|---|
| box | size=[x,y,z], positive |
| ellipsoid | radii=[x,y,z], optional segments/rows |
| revolve | profile=[[radius,height],...], positive radii; optional start/end degrees, segments |
| sweep | points=[[x,y,z],...], radius; optional segments/caps |
| surface | rectangular points[row][column]=XYZ; compiler triangulates cells |
| mesh | vertices=XYZ list, faces=explicit triangle index triples |

Optional at, rotation and scale apply to each shape. Compose several shapes under one component where they belong to one semantic part. Assemblies use the explorer contract: exact members, offsets, optional phase, provenance, evidence and separation_note. Include route owners if using connections. Do not group observed and speculative subsystems together when it conceals important provenance differences. Contacts use `from: component:anchor` and `to: component:anchor`; both anchors must lie on actual mesh triangles. Every pipe connection needs valid endpoint anchors and a continuous route; the inherited validators remain active.

```python
from reconstruction_kernel import build
run, job, candidate = build(
    project, specification, colored_image, original_brief,
    pair=selected_output_folder, parent_history=current_history,
    illustration_attempt=current_illustration_attempt)
# For explicitly requested existing-image reconstruction, omit pair and
# use operation="reconstruct", reuse_reason=the_explicit_user_request.
# Inspect candidate and actual source; perform browser checks before accept.
```

CLI: `python -B scripts/reconstruction_kernel.py --project <project> --source <image> --spec <specification.json> --brief <request> [--pair <folder>] [--history <current-run>] --illustration-attempt <current-attempt>
For an explicitly requested existing-image reconstruction use --operation reconstruct --reuse-reason <user-authorization> instead of --illustration-attempt.`.

No user image or generated scene belongs in the distributable skill. Keep reconstruction specifications derived from a user's image in that project's history. Original generic examples may be shared. Runtime uses bundled Three.js; building the specification and numerical validation use the existing Python dependencies. Browser testing uses the separate development runtime documented in explorer-3d.md.

## Revision 26: presence is not fidelity
For every image-based 3D delivery, follow [fidelity acceptance](fidelity-acceptance.md). Render a source-comparable view of the retained model with fidelity_review.render_comparison, inspect it, and supply comparison plus five fidelity aspects per feature to accept. A flat canopy replacing a pitched roof, incorrect vessel silhouette or uncertain critical yaw cannot pass just because the parts exist. Keep maquette materials. Record image reuse separately from the revision constructing the model.

For rejected candidates, use [targeted geometry repairs](reconstruction-repairs.md). Preserve source identity and repair actual semantic components before repeating independent fidelity acceptance.

Use [shared design, general lofts and supported access networks](shared-design-3d.md) when planning a new reconstruction or repairing shape and circulation. Do not drop existing access destinations during repairs.

See [presentation construction families](presentation-maquette.md) for executable openings, glazing, roofs, canopies and continuous shells.
