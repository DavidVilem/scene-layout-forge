# Repair geometry before declaring an incomplete explorer

Use this continuation only for repairing an explicitly requested current model. Fresh requests still start new designs. A failed fidelity comparison is a work item. Browser success only validates controls. Do not stop merely because a draft has correctable missing glazing, an inaccurate nose or a disconnected floor.

## Order of work

1. Fit a source-comparable camera and inventory visible primary silhouettes, enclosure, openings and walking surfaces. Distinguish perspective mismatch from geometry mismatch before remodeling.
2. Resolve massing and levels first. Establish walking-surface elevations and a continuous route through entrance, hall and platform. If the source does not show a level change, do not invent a step; if it does, represent its visible stair/ramp/landing. Record hidden transitions as inferred. No engineering weights or code certification are required.
3. Build recognizable profiles as surfaces, sweeps or indexed meshes. For a vehicle nose, design the continuous body-to-front silhouette, then fit windshield and lights to that surface. Adding a rounded object onto a box is not enough when their joining cross-sections disagree.
4. Build glazing as actual panels with appropriate transparency, frames, jambs and host relationships; frames alone are not a glazed enclosure. Keep actual entrance openings passable. Inspect transparency in the real HTML renderer.
5. Only after these pass, add fine detail. Compare repaired components and their neighbors, rerun connection/support/clearance checks, and test the new candidate in the browser.

These are subject-dependent decisions, not mandatory trains, glass or ramps in unrelated models. Preserve the source image, miniature materials and free viewing angle.

## Executable continuation

Use `reconstruction_repair.revise(project, parent_reconstruction_history, revised_specification, issues, authorization, pair=None)`.
Each issue contains `id`, `components` (actual semantic component IDs), `observed`, `target`, `action` and `verification` (required view/junction). The helper saves the proposal before checking it, recompiles both specifications, rejects unchanged target geometry, reruns existing validators and builds a new retained candidate. It uses the parent's retained source, verifies its hash and preserves previous attempts. It never generates replacement source images or claims automatic visual recognition.

The return is `(audit, reconstruction_run, explorer_job, candidate_html)`. Inspect the candidate, render a fresh source comparison, and repeat for unresolved findings. Do not use the two image-edit corrections as a limit on mesh revisions. If repeated revisions do not improve the same component, change its modeling approach or revisit the camera instead of adding cosmetic details. Stop only for an actual tool/access limitation, explicit user stop, or after documenting unsuccessful distinct approaches and the remaining mismatch; a finding alone is not a stopping condition.

Before `explorer_workflow.accept`, supply `repair_review` with `candidate_sha256` and `issues` keyed by every issue ID. Each item requires status `resolved`, source_evidence, model_evidence and neighbor_checks. Unresolved targets cannot pass. The normal browser, source-comparison and feature-fidelity gates still apply; this repair record does not replace them. No helper can establish semantic fidelity from a changed hash or a JSON assertion alone.

## Example: terminal continuation

Repair three independent defects in dependency order: hall-to-platform walking levels; missing facade glazing and actual doorway; vehicle body/nose junction and windshield. Preserve the successful hall roof, columns and source PNGs. Each needs its own semantic IDs and visual check. Do not change every element or regenerate the whole station merely because the train nose is wrong. Retain all intermediate candidates with pending repairs until independently reviewed.

Use [shared design, general lofts and supported access networks](shared-design-3d.md) when planning a new reconstruction or repairing shape and circulation. Do not drop existing access destinations during repairs.

Use the [retained repair cycle](repair-cycle.md) to track every comparison and carry unresolved defects across candidates. A first mismatch schedules repair, not task termination.
