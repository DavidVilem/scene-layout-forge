# New subjects through the optional reconstruction kernel

Revision 33 interaction: fixed maquette with orbit, zoom, selection and isolation by visibility. No exploded movement or reassembly; no separation acceptance requirement. Old offset/phase fields are accepted for compatibility but normalized to zero displacement. Preserve visual fidelity and support/access checks.


Use [the reconstruction contract](../../references/reconstruction-kernel.md) only when 3D is requested. Preserve the image pair, history and original connection checks.

- **Observatory:** reconstruct the circular base, actual slotted dome, optical tube/mount, control wing and usable entrance separately. A dome can use partial revolved profiles and visible ribs. Keep back wall thickness and internal optics inferred or absent. Compare dome/wing proportions to the source, not an old industrial fixture.
- **Organic subject:** ellipsoids establish masses, but defining silhouettes need custom triangulated surfaces, variable profiles or detailed meshes. Limbs must meet the body; buried topology is inferred. Do not deliver a few generic spheres as a faithful detailed animal. Rigging and articulated walking are separate capabilities.
- **Landscape:** build a triangulated terrain grid, banks, visible paths and contextual vegetation. A single image does not establish distant terrain elevations; label those estimates. Preserve horizon composition through camera choice rather than inserting a fake depth claim.
- **Machine:** combine revolved surfaces, shells, shafts and custom brackets. Use real named contacts and pipe ports where visible. Unknown internals remain unknown, rather than adding invented functional gears.
- **Urban exterior:** compose real towers, podiums, setbacks and roofs from the visible layout; do not invent detailed floor plans for unseen interiors. Plan/top and section expose only modeled content.

Short request: "Use $scene-layout-forge to reconstruct this image as an interactive 3D explorer. Preserve the original, model the defining forms and connections, identify inferred regions and keep history."

Default regression request: "Use $scene-layout-forge to illustrate a coastal lighthouse." Expected: illustrated and colored PNGs only, with no reconstruction imposed.

Failure probes: malformed mesh indices, degenerate triangles, missing source evidence, observed part without an image region, a contact anchor inside rather than on a surface, separated joint anchors, contradictory route endpoints, unchanged images on delivery, partial model falsely presented as a complete conversion. None may be excused as an absent adapter.

## Maquette fidelity regression

A mountain visitor center with an entrance canopy, open door, steps, glass gallery and rooftop equipment must retain those features in 3D. Declare the entry, stairs and gallery as critical; split their primary/secondary/fine details into visible zones. Protect door and approach volumes, then deliberately add a wall across the door: compilation must fail. Removing decorative rail joints must be disclosed as simplification, not silently counted as complete detail. For an urban miniature, retain varied podiums, ground-level access and roof silhouettes while simplifying subpixel window fittings. Choose a useful free camera rather than forcing the previous observatory angle.

## Revision 26: presence is not fidelity
For every image-based 3D delivery, follow [fidelity acceptance](../../references/fidelity-acceptance.md). Render a source-comparable view of the retained model with fidelity_review.render_comparison, inspect it, and supply comparison plus five fidelity aspects per feature to accept. A flat canopy replacing a pitched roof, incorrect vessel silhouette or uncertain critical yaw cannot pass just because the parts exist. Keep maquette materials. Record image reuse separately from the revision constructing the model.

For rejected candidates, use [targeted geometry repairs](../../references/reconstruction-repairs.md). Preserve source identity and repair actual semantic components before repeating independent fidelity acceptance.


## Unfamiliar subjects with shared design

- Curved research vessel: use closed cross-section lofts for hull/cabin, separate glass from framing, connect the visible boarding route; hidden aft geometry remains inferred. No generic box hull accepted merely because an object named hull exists.
- Mountain observatory: use a revolved dome and explicit slit opening, nested instrument assemblies, floor-to-entrance route and shared source/model orientation. Keep the telescope visible through actual openings or viewer isolation.
- Transit hall: use a ruled or lofted roof skin and separate ribs, continuous glazing rather than opaque window placeholders, and declared supported access to each platform. If a common concourse is hidden in the image, model and label it as inferred instead of claiming it was observed.

These are construction approaches, not fixed compositions. Use [the shared-design contract](../../references/shared-design-3d.md); all visual comparisons and connection checks still apply.

See [presentation construction families](../../references/presentation-maquette.md) for executable openings, glazing, roofs, canopies and continuous shells.
