> Revision 17 default: [reviewed illustration with proportional checks](../references/walkthrough.md). Full registered geometry is optional when explicitly requested. Numerical fixtures below do not limit drawable subjects. History remains mandatory.

# Executable examples

All examples are original procedural code. No image files or machine-specific paths are required. Read the nearest recipe and scene before adapting it, rather than importing counts from an unrelated example.

For a short **rooftop skyline** request, use the current [urban exterior example](worked-cases/urban-exterior.md) and [composer](../scripts/urban_skyline.py). It has strict supported exterior geometry and real guide/history preparation. The older single-tower example and three-block evaluation fixture are not the limit of the skill's compositional scope. This bounded route does not model hidden interiors or certify construction.

| Example | Use | Files |
|---|---|---|
| Supported drive | External transmission continuity and shaft/bearing alignment | [scene](supported-drive/scene.py), [recipe](supported-drive/recipe.json), [prompt](supported-drive/prompt.txt), [builder](supported-drive/build.py), [limits](supported-drive/README.md) |
| Situated workers | Static seated/leaning tasks with actual foot, pelvis and palm contacts | [scene](situated-workers/scene.py), [recipe](situated-workers/recipe.json), [prompt](situated-workers/prompt.txt), [builder](situated-workers/build.py), [limits](situated-workers/README.md) |
| Space station | Curved modules, attachment ports, trusses and arrays | [scene](space-station/scene.py), [recipe](space-station/recipe.json), [prompt](space-station/prompt.txt), [builder](space-station/build.py) |
| Machine interior | Gears, rotor, cooler and control assembly study | [scene](machine-interior/scene.py), [recipe](machine-interior/recipe.json), [prompt](machine-interior/prompt.txt), [builder](machine-interior/build.py) |
| Technical plan | Orthographic room layout and real openings | [scene](technical-plan/scene.py), [recipe](technical-plan/recipe.json), [prompt](technical-plan/prompt.txt), [builder](technical-plan/build.py) |
| Twin vessels | Small connection and label study | [scene](twin-vessels/scene.py), [recipe](twin-vessels/recipe.json), [prompt](twin-vessels/prompt.txt), [builder](twin-vessels/build.py) |
| Process hall | Three modules, six vessels/workers, three pumps and overhead architecture | [scene](process-hall/scene.py), [recipe](process-hall/recipe.json), [prompt](process-hall/prompt.txt), [builder](process-hall/build.py) |
| Service building | Architecture without inherited process equipment | [scene](service-building/scene.py), [recipe](service-building/recipe.json), [prompt](service-building/prompt.txt), [builder](service-building/build.py) |

`python -B examples/<name>/build.py --validate-only` checks a scene without rendering. For a guide, supply `--out-dir` pointing outside the installed skill. Optional `--width`, `--height` and `--supersample` control guide resolution. Existing destinations and outputs inside the skill are rejected.

Recipes specify counts, camera and semantic label targets. These annotated fixtures do not enable annotations in a new user request: configure its annotation policy before its guide. See [optional-annotation and retention examples](worked-cases/optional-annotations.md). Labels are not automatically placed by these example builders: the agent must choose readable positions and validate arrows during the artistic stage. Each scene is a starting point, not a guarantee of visibility from every camera or a final image-quality benchmark. Example outputs must stay outside the package.

Worked reasoning cases (not executable fixtures): [elevation mount](worked-cases/elevation-mount.md), [annotation near an obstruction](worked-cases/annotation-junction.md). Read the common art direction before finishing any example; example prompts do not override it.

Short prompts for fresh-session checks: [behavior probes](short-requests/README.md). Additional worked cases: [contextual interior](worked-cases/contextual-interior.md) and [urban variety](worked-cases/urban-variety.md). These are text-only trials; they do not enlarge the executable geometry catalog.

Short-request development: [rigid airship](worked-cases/rigid-airship.md) and [cross-domain depth](worked-cases/short-request-depth.md).

[Typed water hall](typed-water-hall/README.md): [scene](typed-water-hall/scene.py), [recipe](typed-water-hall/recipe.json), [builder](typed-water-hall/build.py), [prompt](typed-water-hall/prompt.txt). This v2 example adds typed fluid interfaces, generated nozzles and mandatory support paths. Older fixtures remain legacy-partial.

[Registered dry dock](dry-dock/README.md): [scene](dry-dock/scene.py), [recipe](dry-dock/recipe.json), [builder](dry-dock/build.py), [short prompt](dry-dock/prompt.txt). Adds custom hull registration, sampled contacts, independent flow topology and pre-finish detail regions.

[Connected mountain bunker](connected-mountain-bunker/README.md): strict physical-model and display-cut example with six connected levels, program-specific assemblies, actual host openings, and realized design mapping. Its capability-aware materializer realizes hub, spine and branched graphs with separate floor arrangements and adjacency; ring and stepped remain explicitly unsupported. Reproducible alternatives: [longitudinal bunker](bunker-spine/README.md) and [branching bunker](bunker-branched/README.md). `scripts/build_bunker.py --output <new-run-folder>` writes the physical/display/guide evidence for finishing. `run_example.py` also honors the display cut while keeping physical validation separate.

For alternate spatial graphs across domains use the [design matrix](../evals/design-matrix.md); for reusable component placement use [assemblies](../references/assemblies.md). A new scene must realize its own selected graph instead of copying the bunker.

[Domain boundary decisions](worked-cases/domain-boundaries.md) give compact positive
and negative planning cases for building, process, mechanism, vehicle and environment
requests. They distinguish grammar support from a complete physical adapter.

The three bunker examples use the reusable [occupied-room programs](../references/room-programs.md):
six furniture programs, three reproducible secondary arrangements each, actual
floor/wall contacts and an empty central cross. They add planning/inspection
tables, lockers, carts, supply pallets and other program-specific assemblies.
The fixed six-level brief still requests five stair flights and no people;
physical part counts are recomputed from the complete scene.

Every recipe example now includes `decision-contract.json`: the actual schema,
adapter kinds, physical coverage, count/label invariants and positive/negative
commands. `check_examples.py --example <name>` verifies that documentation against
the scene before exercising its mutations. The current catalog contains thirteen
executable recipe examples, including [situated workers](situated-workers/README.md),
and [sixteen executable worked questions](../evals/executable-cases.md) with explicit
complete-subject capability boundaries. None of these counts imply finished artwork.


[Architectural station regression](../references/architectural-gates.md): workflow-v4 executable gates, contour approach, physical door apertures, supported roof frames and partial presentation cuts. Run `scripts/station_stage_example.py --project <project-directory>`; retained guides require artistic finishing and independent review. The example's fixed seed reproduces one bounded regression case; do not impose its floorplan, roof form, camera or station component set on other requests.

The older recipe examples above test their documented components. Their workflow-v2/v3 success is not evidence that a new building passes the eight architectural stages. New building designs must materialize a v4 contract, including their own environment, program, alternatives and visibility witnesses.

New default cases: [general illustrations](worked-cases/general-illustration.md).

Visual continuity: [a main, tee and capped branch](route-continuity/README.md).

Current delivery contract: [one design, two outputs](worked-cases/two-outputs.md).


Optional requested animation: see [motion walkthrough](worked-cases/subtle-animation.md). Preserve the illustrated/colored pair; retain animation evidence and inspect actual motion before delivery.

## Interactive 3D continuation

See [explorer worked case](worked-cases/explorer-3d.md) for an independent geometry demonstration and the separate real-image correspondence workflow.

See [new-subject reconstruction](worked-cases/reconstruction.md) for the separate optional 3D workflow.
