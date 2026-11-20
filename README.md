> Revision 17 default: [reviewed illustration with proportional checks](references/walkthrough.md). Full registered geometry is optional when explicitly requested. Numerical fixtures below do not limit drawable subjects. History remains mandatory.

Revision 33 removes exploded motion and reassembly. The 3D model stays fixed, with orbit, zoom, selection, isolation by visibility and sections. Existing source-fidelity and support/access checks remain required.

Revision 2026-11-18.37 adds the [independent 3D core](references/independent-3d.md): pre-generation scene binding for new designs, single-image reconstruction sessions, landmark camera fitting, immutable geometry snapshots and real GLB export. It preserves existing support/contact checks and independent fidelity acceptance. This is an agent-assisted modeling workflow, not a pretrained automatic image-to-3D service.

# Scene Layout Forge

The stable command remains `$scene-layout-forge`; its display name is Scene Layout Forge.

Current revision: **2026-11-18.37**. See [exterior environment scope](references/exterior-environments.md) and [release scope and migration](references/revision-12.md).

Revision 2026-11-18.37 adds [reusable construction families and presentation workflow](references/presentation-maquette.md), a procedural botanical-pavilion example and studio lighting with contact shadows. It preserves the shared spatial plan, loft geometry, supported access networks and independent visual review.

Previous revisions added [architectural design and repair checks](references/architecture-repair.md): complete buildings unless a cut is requested, explicit roles/hosts/supports, and visual review of the whole design before coloring. The 3D explorer supports translucent enclosure and [actual-browser source comparisons](references/fidelity-acceptance.md). Examples and repair history remain separate from user images.

A portable skill for producing **a reviewed graphite PNG, its colored edit and an optional explicitly requested 3D HTML explorer** of technical structures, plans, buildings, vehicles and machine interiors. It develops a spatial plan, uses available numerical checks and an optional guide, then generates and independently reviews the hand-drawn finish. Ambient animation remains off by default. An explicit request derives animada.mp4 from the colored image while retaining both PNGs and history. See [animation](references/subtle-animation.md) for supported local effects, layers and optional encoder requirements. No external video service is bundled.

## Two images, with optional 3D

Default order: `ilustrada.png` → `coloreada.png`. An explicit 3D request activates [the separate reconstruction kernel](references/reconstruction-kernel.md) and adds `explorador.html`, in the same numbered output directory. The HTML uses bundled Three.js and opens offline with WebGL; it contains real geometry, selection, fixed-assembly visibility and isolation, clipping, plan/elevation views and schematic SVG export. No runtime installation is needed to view it. Development dependencies and rebuild instructions are in [3D explorer](references/explorer-3d.md). Artistic images remain unchanged. Inferred geometry is identified, not claimed as recovered hidden structure.

Read the [worked 3D example](examples/worked-cases/explorer-3d.md). Browser checks and independent visual review are required, and history is preserved. The HTML is a technical interpretation rather than a photorealistic reconstruction or construction drawing. Ordinary drawing requests never require reconstruction. The optional kernel can construct new subjects from agent-authored visual specifications, including single external images; it does not guarantee exact hidden geometry from arbitrary pictures.

## Install and invoke

Copy this entire folder as `scene-layout-forge` into your agent's skill directory. For a project-scoped Codex installation, use `.agents/skills/scene-layout-forge` beneath that project. Open a new conversation in the project and invoke `$scene-layout-forge`. No personal drive letter, old conversation or reference image is required.

Python 3.11+ and the packages in [requirements.txt](requirements.txt) are required for calculated geometry. Install dependencies into your chosen virtual environment with `python -m pip install -r requirements.txt` from this package, or use the resolved path to that file. An available image-generation tool is required for the artistic finish. If unavailable, the agent reports the limitation; the Python renderer does not replace it. This package requires no embedded artwork or API key for its local geometry utilities.

## Structure

- [SKILL.md](SKILL.md): agent workflow and resource routing.
- [kit](kit/__init__.py): public Python entry point for the shared geometry implementation.
- [examples](examples/README.md): original executable scenes, recipes and portable prompts, plus worked reasoning cases and short-request behavior probes. Legacy and strict validation scopes are distinguished.
- [references](references/art-direction.md): art direction, geometry contract, rendering and review guidance.
- [evals](evals/README.md): realistic agent prompts and visual acceptance rubric.
- [scripts](scripts/run_example.py): guide building, validation and distribution audit; existing implementation modules remain here for backward compatibility.
- [tests](tests/test_portability.py): relocated-installation and distribution checks. Geometry regression tests remain in `scripts/test_*.py`.
- [.github/workflows/ci.yml](.github/workflows/ci.yml): automated numerical and portability checks when hosted as a repository.

## Quick test without references

Ask: `Use $scene-layout-forge to draw a fictional orbital research station with detailed habitats, trusses and solar arrays. Choose a useful technical view, use the built-in graphite style and meaningful English arrow labels without reference images, and save ilustrada.png, its reviewed color edit coloreada.png and explorador.html in the same new numbered output folder.`

For a local calculated-guide smoke test, run from this package (choose an output location outside it):

```sh
python -B examples/twin-vessels/build.py --out-dir ../layout-review/twin-vessels
python -B scripts/check_examples.py
python -B scripts/check_package.py
python -B -m unittest discover -s scripts -p "test_*.py"
python -B -m unittest discover -s tests -p "test_*.py"
```

The example builder creates a **calculated guide**, even though the shared renderer names its PNG `ilustrada.png`. It does not call an image model. Agent workflow must still finish and inspect the artistic image. Run commands with absolute resolved script paths from other working directories; examples resolve their imports from their own location.

Numerical tests do not certify engineering accuracy or artistic quality. Generative outputs are not byte-reproducible and can change counts, connections or labels. Follow [verification](references/verify.md) and [eval instructions](evals/README.md).

## Distribution

Only source, instructions and procedural examples belong in the package. Runtime references, outputs, credentials, caches and vendored dependencies do not. No assets folder is needed because there are no bundled image assets. See [contribution guidance](CONTRIBUTING.md) and [structure rationale](references/structure.md). This local package has not been published; a distribution license must be selected by its owner before public release.

Revision 2026-11-13.9 adds a typed water-hall example and [coverage documentation](references/typed-interfaces.md). Schema v1 remains compatible but partial; v2 is not a dynamics or process simulator.

Revision 2026-11-13.10 adds [registered geometry, camera evidence and frozen correction contracts](references/registered-workflow.md). The new dry-dock example includes short-request probes; images remain outside the distributable package.

Revision **2026-11-13.11** adds [design exploration](references/design-exploration.md), [local assemblies and real openings](references/assemblies.md), [strict coherence gates](references/coherence-validation.md) and [bound visible annotation targets](references/view-evidence.md). The graph planner exposes alternative spatial organizations before detail geometry; it is not a universal natural-language CAD compiler. Reusing the same seed reproduces the calculated design, not stochastic finishing pixels. With no seed, new exploration is allowed and meaningful differences are measured independently of camera, translation and scale.

Use the [cross-domain matrix](evals/design-matrix.md) to test selection and reproducibility. Its 24 runs test graphs, not 24 finished images. Unsupported geometry stays explicit rather than inheriting a pass from another example. The [walkthrough](references/walkthrough.md) covers the new physical-model-to-cutaway path.

Revision **2026-11-13.13** adds three physically materialized bunker organizations,
domain-specific planning, requirement-level evidence, conditional visual/context/detail
and material plans, normalized focal visibility, and PNG-bound independent review.
The [pattern library](references/pattern-library.md) is written knowledge, with no
reference artwork or private paths. [Run manifests](references/visual-planning.md)
compare actual inputs between clients; they do not promise identical image outputs.

The same revision includes [functional room kits](references/room-programs.md),
[seated and leaning actor contacts](references/actor-poses.md), registered surface
material transport and [sixteen executable evaluation cases](evals/executable-cases.md).
Each of the thirteen recipe examples has a verified decision contract with its
actual coverage and positive/negative commands. Manifests bind reviewed PNGs and
distinguish native pixels from transformed exports; unknown client facts stay unknown.

Revision .13: [eight-stage workflow and retained execution history](references/eight-stage-workflow.md). One selected PNG, with all attempts preserved outside the package.

Revision .14 adds [executable architectural gates](references/architectural-gates.md), sequential scene-bound approvals, protected arrival/entry/envelope witnesses and a portable station regression example. Stage 8 checks an independently reviewed PNG; it is not automated visual recognition. Old fixtures retain their explicitly limited legacy scope.

Revision **2026-11-13.15** makes annotations request-driven and history automatic across all domains. Current delivery requires a retained checked guide, source, exact prompt and review; direct image generation is incomplete. See [execution policy](references/execution-policy.md). Historical fixtures remain readable but cannot bypass current delivery acceptance.

Default outputs: `ilustrada.png` and `coloreada.png` in the same numbered output folder. Color is an image-to-image edit of the reviewed illustration. Read [color editing](references/color-editing.md). Earlier results and history are retained.

Forward-time animation: clouds/traffic advance, foliage sways, rotors turn, and walking uses prepared poses. A visually assessed motion inventory selects meaningful actions; clips no longer default to ping-pong loops. See [temporal motion](references/subtle-animation.md).

Revision 24 preserves the matte maquette style and adds [feature fidelity and access checks](references/maquette-fidelity.md): declared detail tiers, protected entry/passages, conservative overlap review and an initial-view direction. Visual feature review remains required; these are not automatic image recognition or exhaustive collision tests.

Revision 25 adds a lightweight camera/group perspective contract, named pixel evidence, pre-color rejection of known perspective errors, and source-like 3D correspondence guidance. Existing histories remain readable. Numerical and evidence checks do not automatically recognize perspective in generated pixels.

Revision 26: byte-bound source/model comparison renders, five-aspect fidelity acceptance, image reuse lineage and rejection of separated intended contacts. No images or histories bundled.

Revision 28 separates fresh creation from authorized editing/reconstruction, retains rejected duplicate images, and binds new 3D builds to the current reviewed colored delivery. Repeating a prompt requests a new design; changing only the folder is not a new design.

Revision 34 uses illustration -> colored edit -> explicitly requested fixed 3D reconstruction. The accepted colored image is the reconstruction source; no pre-generation snapshot is required. The progress audit distinguishes setup-only histories from actual production evidence.

Revision 35 adds the persistent delivery coordinator and a shorter execution entrypoint. It prepares the next color request and distinguishes requested 3D work from accepted delivery; inventory alone is never completion.

Runtime discovery: see [runtime startup](references/runtime-startup.md) before executing Python examples.

## License

Project source is available under the [MIT License](LICENSE). The bundled Three.js runtime retains its [separate MIT license and copyright notice](assets/explorer/THREE-LICENSE.txt).
