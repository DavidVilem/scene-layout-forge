# Optional output: a real 3D explorer

Revision 33 interaction: fixed maquette with orbit, zoom, selection and isolation by visibility. No exploded movement or reassembly; no separation acceptance requirement. Old offset/phase fields are accepted for compatibility but normalized to zero displacement. Preserve visual fidelity and support/access checks.


Only when explicitly requested, the output order is ilustrada.png, coloreada.png, then explorador.html in the same numbered output folder. Ambient video is not part of this flow. Respect explicit requests for only an image or another scope. Preserve both PNGs and all previous outputs. The HTML contains actual mesh geometry and controls; rotating an image plane is not a 3D reconstruction.

## Shared scene, different representations

For a new scene, plan semantic assemblies and connections early. Reuse numerical geometry already saved by the image workflow where it exists. After coloring, compare the final pixels to that model; do not assume the artistic generator preserved every part. For an existing image, inspect its history before rebuilding. Record each assembly as modeled (geometry from a supplied/design model), observed (reconstructed from visible evidence), or inferred (a design assumption). Visible evidence does not determine hidden rooms or precise dimensions. Do not show invented interiors as recovered facts. Keep unknown regions unknown or mark their inferred design explicitly.

The 3D technical representation may be simpler than the artwork but must retain the subject's defining shapes, meaningful supports and connections. Do not substitute arbitrary boxes for essential curved or mechanical forms. Existing adapters export their actual faces; unsupported defining shapes need a tested indexed/custom adapter or explicit partial scope. An unavailable adapter does not invalidate the finished image pair. Continue building an appropriate representation within scope; if the requested model still cannot be completed, retain the pair/history and state that HTML is incomplete. Never disable numerical checks to obtain an export.

No automatic image-to-3D inference, surface reconstruction or physical dismantling solver is bundled. The executing agent builds the model from the brief/history/pixel evidence using the existing geometry APIs. Code checks model consistency, not truth about unseen geometry. Do not request load weights, pressure or engineering specifications merely to create a conceptual explorer.

## Build contract

Use scripts/explorer_workflow.py. Supply the existing scene format accepted by render_scene.build and a config with title, limitations, dimensions_verified (normally false), and assemblies. Every rendered owner must belong to exactly one assembly, including routes named connection[0], etc. The exporter rejects unowned faces, duplicate owners, nonexistent members and detected geometry failures.

Each assembly has:
- id, label, members (exact scene part IDs and route owners).
- All group offsets are normalized to zero; geometry always stays assembled.
- Legacy phase and offset fields are ignored for motion; no movement metadata is needed.
- provenance: modeled, observed or inferred, with evidence. Groups serve selection and visibility only.

Scene coordinates are X/Y on the ground and Z up. Measured dimensions require dimensions_evidence; conceptual proportions must not acquire measurement claims merely because the model uses meter units. Custom objects keep their real meshes and registered identities. Preserve typed interface, port, support and route checks whenever supplied. The viewer's camera and projection changes never mutate the physical scene.

## Execution and history

1. Inspect the final colored image and source model. Save original request, source lineage, scene and config. Identify important correspondence checks and limits.
2. prepare(project, scene, config, brief, pair=output_folder, parent_history=existing_run) retains source PNG copies/hashes, geometry, assembly config, coverage, code snapshots and exact runtime. It creates a new persistent output/history/explorer-* folder. Earlier failures remain available. Do not use example=True for a user's completed triple: that mode only makes explicitly identified independent technical prototypes without an image pair.
3. render(job) writes candidate.html with embedded model and runtime. No network/CDN, Node, server or plugin is needed to open the delivered HTML. The two optional reference-image buttons load the sibling original PNGs; keep the three files together when sharing a user result. The 3D model itself remains usable if the PNGs are absent.
4. Run scripts/check_explorer_browser.mjs against the candidate using a development workspace with Playwright and an installed Chromium-family browser. It opens the real file and tests WebGL, selection, fixed geometry/reset, orthographic views, clipping, visibility/isolation, keyboard, SVG export, offline requests and mobile layout. Capture screenshots and inspect them visually; the report alone does not prove visual quality.
5. Inspect the complete maquette and isolated groups. Isolation only changes visibility. Verify group coordinates stay at their assembled positions after selection, isolation, show-all and reset.
6. Review correspondence, assembled, section, views and interaction with concrete passed/failed/uncertain observations. accept(job, observations, browser_report) checks source/candidate identity, actual candidate-bound browser report, failures and overwrite protection before delivering explorador.html beside the source pair. Keep all corrections as new preparations linked to the previous history; do not erase screenshots or change frozen attempts. If a destination exists use a fresh numbered folder with byte-identical PNG copies and recorded lineage.

## Controls and technical limitations

- Drag rotates, wheel/pinch zooms, controls pan; keyboard arrows orbit and Escape resets. Selection is available both on geometry and in the assembly list. Hide/show and isolate operate on groups.
- Geometry remains fixed. No exploded animation, movement slider, disassembly sequence or reassembly control is generated.
- Three view buttons use the same mesh for top/front/side orthographic projections. Orbiting then explores true depth, not a different generated picture.
- Clipping uses an X/Y/Z plane and exposes modeled surfaces only. It does not create unseen internals or fill solid cut caps. This is a conceptual section, not a construction section drawing.
- SVG download exports an assembled, axis-aligned schematic projection using the same mesh and current visibility. In 3D mode it exports top view. It ignores clipping, states that limitation on the sheet, adds no unverified dimensions, and uses approximate painter sorting (not exact CAD hidden-line removal). Printed/exported details remain conceptual.
- Detailed triangles and component ownership are exported from the original adapters. Framing, shading and material palette are technical and will differ from the graphite/color artwork. Do not claim pixel-perfect 3D texturing.

## Distribution

assets/explorer contains source HTML/JS, the bundled Three.js runtime, development package versions and its MIT license. No user image, generated scene, browser profile or run history belongs in the skill ZIP. The package works offline; development dependencies are only needed when changing/rebuilding/testing the runtime. scripts/build_explorer_runtime.mjs builds it from a separate development workspace. Preserve third-party notices. Test and audit the release after changes.

For reconstruction v2, pass feature_review to accept; see [maquette fidelity](maquette-fidelity.md). Review source/model detail and access separately from browser operation.

## Revision 26: presence is not fidelity
For every image-based 3D delivery, follow [fidelity acceptance](fidelity-acceptance.md). Render a source-comparable view of the retained model with fidelity_review.render_comparison, inspect it, and supply comparison plus five fidelity aspects per feature to accept. A flat canopy replacing a pitched roof, incorrect vessel silhouette or uncertain critical yaw cannot pass just because the parts exist. Keep maquette materials. Record image reuse separately from the revision constructing the model.
