# Architectural decisions and continued repair

Use this contract for buildings. It records design intent and evidence completeness, not automatic aesthetic judgment or structural calculation. A short illustration request permits a coherent design; it does not authorize a display cut. User-requested sections and naturally open shelters remain valid.

Before detailing, distinguish the primary structural system, enclosure, entrance, and subordinate canopies or ornament. Describe where each begins and ends, what carries it and how its edges join neighboring construction. An arched portal may be subordinate when it clearly belongs to a complete vestibule or facade bay. It need not span every building. Conversely, a small arch pasted onto an unrelated glass screen is not repaired simply by extending the glazing. Decide whether to integrate, resize or remove it before preserving details.

For a conflict, compare two feasible massing/entry solutions, choose one for the current brief and record the discarded alternative. Preserve user requirements and successful scene qualities, not an accidental defect in a previous generation. Do not impose symmetry, arches, glass, an exterior view or a common floor count on unrelated subjects.

## Plan contract

`architecture` includes representation (`complete` or `section`), enclosure, roof_wall_junctions, openings and routes. Each opening names kind (`door`, `window`, `permanent_open_bay`, `display_cut`), boundary and reason. A section requires user_cut_request quoted from the brief plus cut_boundary. Validate the actual meaning of the request; substring presence alone cannot prove permission.

New building designs also include `design`: primary element ID, selected_reason, rejected_alternative, and elements. Each element has id, role (`ground`, `structure`, `enclosure`, `opening`, `canopy`, `ornament`), extent, junction and hosts (known element IDs). For a spanning element, set spanning=true and supports to at least two other element IDs. The graph must reach a ground element. This is a topology check, not load analysis; do not ask the user for engineering data.

## Independent review

The generated image needs observations for enclosure, junctions, openings, routes and design. For design, compare the actual span hierarchy, visible support locations, entrance scale and transitions with the selected concept. A glass-filled hole, component count or valid JSON is insufficient evidence. Review at scene scale before close details. If the image changes the primary design, repair that before coloring or reconstructing 3D.

## Repair as work

Use `repair_cycle.record(folder, artifact, issues, parent=None)` for concrete discrepancies; each issue has id, component, observed, target and action. Correct the artifact, inspect it, then `resolve(record_path, new_artifact, observations)` with issue IDs mapped to status resolved/unresolved plus evidence. The ledger binds hashes and requires actual changed artifacts, but cannot judge whether the evidence is truthful. Unresolved issues remain work. Do not label an artifact complete solely because its controls function or a failure report exists.

Keep two local corrections per image stage. A necessary change of architectural concept is a new preparation with the previous rejection linked, not an undisclosed replacement or an endless retry. For explicitly requested 3D, repair missing critical geometry, compare again, and test the new candidate. Use the existing fidelity acceptance gates without weakening them. If the budget or an external tool genuinely prevents completion, retain all attempts and report the exact remaining defect.

HTML cuts and separation controls are reversible inspection tools, not a request to remove walls from the source images. The explorer opens assembled and uncut.
