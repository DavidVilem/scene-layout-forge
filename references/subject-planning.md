# Plan an unfamiliar technical subject

Convert a plain-language request into a brief functional description, major assemblies, connecting or supporting relationships, required visible counts, view and annotation targets. Select details from those assemblies rather than from whichever example is shortest. For a named real machine or structure requiring fidelity, consult available user documentation and appropriate primary sources. For a fictional concept, use plausible arrangements and identify conceptual rather than measured detail.

| Request | Useful default view | Assemblies to consider |
|---|---|---|
| Room/building plan | Top-down orthographic | Wall thickness, real openings, circulation, furniture/equipment footprints |
| Building exterior | Three-quarter perspective or requested elevation | Structure, floors, envelope, entrances, roof services |
| Machine interior | Open housing or a clearly chosen section | Shafts, bearings, gears/rotors, casing, mounts, power/service paths |
| Vessel/vehicle interior | Interior angle and distance chosen for access and visible assemblies | Curved shell/ribs, bulkheads, doors, equipment, access and context-specific crew |
| Orbital station | Three-quarter exterior or requested interior | Habitats, docking nodes, trusses, power arrays, thermal/control services |
| Unknown technical structure | The view that reveals its function | Derive structural and functional assemblies, then choose or implement geometry |

Examples are vocabulary, not a whitelist. A request outside this table should still be decomposed from its purpose. Do not force a factory, human figures, tanks, a particular panel layout or a fixed camera into an unrelated design. Do not promise any arbitrary object can be represented accurately by the existing catalog.

## Short requests and context

Apply [context and composition](context-composition.md) before fixing the camera. Choose setting, useful variation and view as separate decisions. A terse subject request does not imply a white-background catalog image or a historically specific model. User requests for isolation or exact projection remain authoritative.

## View contract

Plans are parallel projections with true openings and no perspective convergence. If dimensional accuracy matters, use supplied dimensions and keep labels tied to model measurements; otherwise omit invented dimensions. A plan is still a PNG illustration, not editable CAD or a construction permit drawing.

For sections/cutaways, decide which shell pieces are omitted and model the visible section edges; merely using translucent walls creates false geometry. For interiors, use an actual interior camera and inspect the open circulation route. Eye level is an option, not a default. An elevated oblique or wide lateral view may reveal more assemblies. Unless explicitly requested, avoid close-ups, oversized foreground figures and automatic centered corridor compositions. For an unspecified view, consider at least two sensible camera directions/distances in planning and choose one that makes structure and required objects readable; this does not require rendering or delivering multiple images. Respect explicit eye-level, close-up, plan or section requests. Detail density is independent of camera proximity: a wide view should convey secondary assemblies at its scale, not be cropped tighter to manufacture detail. For exteriors, retain clear silhouette and assembly hierarchy, with enough obliqueness to distinguish depth.

## Extending beyond the catalog

Compose existing primitives only when they express the real shape. For unsupported geometry, implement a project-local mesh adapter with explicit local coordinates, bounds, shape parameters, ports/contacts and material marks. Test finite nondegenerate faces, bounds, openings and invalid inputs; render a small isolated guide and inspect it before adding it to the scene. Curved hulls are curved surfaces, gears have teeth, open doors have apertures, seats support the intended pose. A generic box is not an acceptable silent replacement.

Validate new contacts and connections explicitly. AABB bounds are conservative envelopes: they cannot prove an opening is clear inside a hollow shell or that two gears mesh. Use geometry-specific checks where the relationship matters. If an essential feature cannot be represented or inspected, report the limit rather than claiming a generic substitute is correct. Reusable adapters should enter the package only after tests and cross-domain review.
