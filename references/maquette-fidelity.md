# Maquette fidelity and clear access — reconstruction v2

Preserve the architectural model style: real three-dimensional solids, matte restrained colors, readable edges, orthographic navigation and removable groups. Do not replace it with a photo plane or force realistic textures. The same direction applies to cities, buildings, landscape models and mechanical assemblies. Scale the detail to the visible subject: a city needs blocks, podiums, setbacks, entrances and roof/service variation, not identical towers with arbitrary noise.

The previous v1 compiler could accept a few generic volumes with labels. A source bounding rectangle only proved that an observation was recorded, not that an entrance or its details existed. New reconstructions use schema_version=2 with quality_contract. Old specifications remain readable with quality marked not_run; do not present them as passing fidelity checks.

## Protect recognizability

Before modeling, inventory the source's important features. Use primary forms, secondary assemblies and fine construction details in each visible detail zone. Feature records have id, level (`primary`, `secondary`, `fine`), parts, evidence, status (`modeled`, `simplified`, `omitted`), critical and reason when simplified/omitted. Critical features cannot be omitted or simplified away. Explicitly include the entrance/access for a building where visible; include openings and mechanism identity for machines. A few nested boxes named after detailed equipment are insufficient visual evidence.

quality_contract contains features, detail_zones (id and feature IDs), landmarks (feature IDs to make readable in the opening camera), access_scope, protected_spaces and overlap_review. Do not force the same room count, building type, angle or detail count onto all subjects. The compiler verifies inventory consistency; it does not recognize objects in source pixels. Compare actual source and rendered views to verify the feature truly appears. The final HTML acceptance requires feature_review keyed by every feature ID, with status visible/simplified/unverified and concrete notes. Critical features must be visually confirmed as visible. An uncertain hidden back is acceptable; an absent visible main door is not.

## Check actual free spaces

Each protected space has id, purpose, min and max in world XYZ. Model a volume through a door, over a stair tread or along a passage. Set its bottom above the real walking surface, including the actual threshold. The mesh/box separating-axis check rejects intersecting surfaces and checks containment in closed meshes. Touching a volume boundary is allowed within tolerance. These checks cover supplied volumes, not construction codes, human egress certification or every unmodeled path.

If necessary, exceptions maps component IDs to specific reasons. Do not exempt a wall, handrail or cabinet merely to pass a blocked entrance. Model the opening or move the obstruction. A deliberately closed movable door may need a separate open-state model; document that state rather than claiming the closed leaf is passable. Broken or open meshes may not support containment checks; surface intersections are still tested.

For overlap_review, name component pairs, classification (`intended_contact`, `nested`, `separate`) and reason. Separate parts with intersecting bounds fail conservatively. Nested cases such as telescope inside dome are expected bounds overlaps and still require visual inspection from multiple angles. This is not a universal mesh-collision solver. Inspect the entry, source-facing facade, source-like view, opposite side, plan and isolated important assemblies. Verify isolation changes only visibility and leaves all component coordinates unchanged. No dismantling or reassembly is required.

## Camera and detail decisions

Optional presentation contains direction=[x,y,z] and zoom (0.3..3). It sets only the opening 3D view; orbit and orthographic views remain free. Choose a view where critical features are readable. The source-like camera is a review aid, not a mandatory global angle. If a roof hides control equipment, retain it and use hide/isolate or a section rather than permanently removing the architecture. Do not let landscape bounds make the subject illegibly tiny.

Build distinct geometry for details that change recognition: door jambs/lintels and real gaps, window frames, rail posts and contacts, reachable stairs, facade joints, roof units, instrument screens or shell ribs. Keep decorative microdetail subordinate and share host assembly motion with attached details. Fine detail is not a substitute for correct masses, supports or access. Preserve image pairs unchanged. When a prior result is improved, create a new numbered output folder with identical source PNG copies and linked history; never overwrite the earlier HTML silently.

Compare relative object rotations and roof/cabin/deck silhouettes from a source-like camera before acceptance; a simplified hull box does not establish vessel correspondence. The interactive opening camera can remain orthographic. See perspective-review.md for the difference between image projection and maquette display.

## Revision 26: presence is not fidelity
For every image-based 3D delivery, follow [fidelity acceptance](fidelity-acceptance.md). Render a source-comparable view of the retained model with fidelity_review.render_comparison, inspect it, and supply comparison plus five fidelity aspects per feature to accept. A flat canopy replacing a pitched roof, incorrect vessel silhouette or uncertain critical yaw cannot pass just because the parts exist. Keep maquette materials. Record image reuse separately from the revision constructing the model.
