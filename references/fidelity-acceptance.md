# Source fidelity acceptance, revision 26

This is an optional 3D continuation of the reviewed image pair, not a replacement for drawing. Keep matte maquette materials and free orbit. Simplify textures without changing recognizable shape, levels, openings, relative rotations and connections. No whole-subject adapter is required; build missing forms with registered meshes, sweeps and surfaces.

## Distinguish source identity from current revision

`prepare` writes `image-lineage.json`: source hashes, identical PNGs found in sibling output directories, and an explicit existing-pixels action. This scan is limited to output/*/*.png, not a universal provenance search. Unknown generation revision stays unknown. Copying pixels into a new numbered directory does not apply the current image/perspective workflow retroactively. Link original generation/review history when known. If the task requests image correction, actually edit/generate and review those pixels before treating it as completed. If only 3D is requested, preserve the unchanged pair and disclose reuse.

## Compare the retained model itself

After rendering the HTML candidate:

```python
from fidelity_review import render_comparison
comparison = render_comparison(job, {
    'projection': 'perspective',
    'eye': [12, -18, 10], 'target': [0, 0, 2], 'fov': 50,
    'rationale': 'Explain matching visible facade, roof slope and boarding side.'
})
```

These numbers are illustrative, never a required view. Fit eye/target/FOV to the source; orthographic sources use orthographic comparison with azimuth/elevation. The renderer uses the same retained scene that compiled the HTML. It saves model.png, source.png, side-by-side.png and hashes binding them to scene, HTML and source. Inspect those images; render another retained comparison when camera fitting is poor. The helper does not solve camera calibration or compare semantic shapes automatically. The viewer's default maquette view can remain orthographic.

Review all critical visible features, including forms that the model currently omits. Inventory cannot consist only of parts that happened to be easy to build. For a vessel include visible hull silhouette, cabin/bridge levels, roof profiles and boarding interface; for architecture include visible roof slopes, facade rhythm, openings and route geometry. Use subject-specific features, not a universal room quota.

Each feature_review item still has presence `status` and `notes`, and now also `fidelity` with five keys: shape, proportions, orientation, placement, connections. Each key contains status (`matched`, `mismatch`, `uncertain`, `not_applicable`), source_evidence, model_evidence. Only genuinely inapplicable connections may use not_applicable, with reason. Record uncertainty for hidden noncritical surfaces separately from visible critical identity. A known mismatch anywhere blocks final HTML acceptance; uncertain critical visible features remain a draft to repair, not an excuse to drop details.

Example:

```python
feature_review['entry_canopy']['fidelity']['shape'] = {
    'status': 'mismatch',
    'source_evidence': 'Two sloping roof planes meet above timber trusses.',
    'model_evidence': 'Single flat slab with no pitched profile.'
}
```

That is a defect even when the canopy exists. Fix its mesh before acceptance. Conversely a matte untextured model with the correct pitched silhouette may match shape while omitting unimportant wood grain.

Call `accept(..., feature_review=feature_review, comparison=comparison)`. For image-based delivery the overall correspondence review must be passed after critical features are established. Remaining noncritical/hidden simplifications must be listed in model limitations and individual observations. All connection/support/clearance checks remain active. An intended_contact pair whose bounds are separated now fails; bounds touching/overlap alone still does not prove contact. Use actual anchor checks where applicable and inspect junctions.

Never satisfy fidelity by changing review words alone. Revise geometry, retain a new candidate, render comparison, inspect and repeat. Persist rejected reviews in history. Functional browser success establishes controls, not fidelity. Tests use synthetic images and explicitly do not establish artistic matching.

## Actual browser comparison

If the software raster makes transparent enclosures opaque or cannot show fine registered meshes legibly, compare the actual HTML renderer. Run `scripts/capture_explorer_comparison.mjs <runtime-workspace> <candidate.html> <job/comparison-folder> <browser-executable> <camera.json>`. The camera file uses projection=perspective, eye, target, fov and rationale. The capture resets assembly, visibility and clipping, then uses a perspective review camera on the same scene; normal navigation remains orthographic. It records candidate and screenshot hashes and browser errors.

Then call `fidelity_review.record_browser_comparison(job, comparison_folder)` and inspect its source/model images. It binds the source and actual candidate capture to the same acceptance contract. Camera fitting and semantic fidelity still require visual judgment; an image hash is not a similarity score. Do not use an unrelated rendered model, invisible assemblies or an illegible screenshot as evidence.
