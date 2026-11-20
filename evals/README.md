> Revision 17 default: [reviewed illustration with proportional checks](../references/walkthrough.md). Full registered geometry is optional when explicitly requested. Numerical fixtures below do not limit drawable subjects. History remains mandatory.

# Evaluations

Revision .16 adds [urban exterior regression](../examples/worked-cases/urban-exterior.md). The same short rooftop-city request must reach a real guide and recorded finishing request without demanding unshown rooms. Positive and mutated-negative checks run in `test_exterior_environment.py`; artistic evaluation remains independent. Test both annotated and unannotated requests, a second seed/organization and a camera change. A prepared guide is not a generated final PNG.

[evals.json](evals.json) contains realistic agent requests with prompt, expected-output and input-file fields. [rubric.json](rubric.json) separates objective constraints from visual review. These are evaluation specifications, not claims that the agent has passed them.

There are two independent layers:

1. **Automated local checks:** `scripts/check_examples.py`, geometry regressions and `tests/test_portability.py`. They validate counts, invalid-control rejection, PNG decoding, working-directory independence and non-overwrite. They use no image-generation service.
2. **Agent and visual evaluations:** give one prompt to a fresh session with the installed skill and a new project. Supply only files explicitly needed by that case; start the first three without any references. Inspect the generated PNG at full composition and at critical joints. Record each rubric criterion as pass, fail, not_run or occluded_unverified, with concrete evidence. Do not mark an unread image passed.

For the occupied-output case, create a sentinel result and compare its hash afterward. For unavailable-tool evaluation, really use an environment without that capability; do not pretend a hidden tool is absent. For local correction, supply a runtime image containing the stated defects, outside the package. If no suitable input exists, mark that case not_run.

Keep evaluation records outside the installed skill. Record skill revision, model/tool when exposed, prompt, reference roles, image dimensions, observed counts, label correctness, unresolved junctions and final outcome. Always retain intermediate evidence in project history, even when selecting only one final image. A sample pass is not a universal quality guarantee.

Revision 11 adds a third independent layer, [design exploration matrix](design-matrix.md), before geometry. Test a fixed intent across seeds and different domains: variation must preserve required functions and explicit constraints. Record selected graph fingerprints and family, but do not count novel camera orientation as novel layout. An alternate graph is only usable when its actual realization passes geometric checks.

Physical regression tests deliberately inject missing fluid interfaces, wrong-size nozzles, unattached services, overlapping cabinets, blocked circulation, stale selection-to-geometry mappings and altered view evidence. A positive control must still pass. Independent forward tests should receive only the realistic brief, skill and raw needed files, without the author's expected solution.

Revision 12 adds a [balanced matrix of 16 evaluation cases](revision-12-matrix.md)
and its [machine-readable specifications](revision-12-matrix.json). These are not
16 completed artistic trials. Use the actual per-layer status and adapter limits.
Compare light, surface marks and context with unchanged geometry. Include a short
prompt across several seeds: order-independent scores alone are insufficient if
selection still always chooses one outlier family. Preserve hard requirements first.

Run the [executable case registry](executable-cases.md) with
`python -B scripts/evaluate_registered.py --output <new-external-report.json>`.
It executes sixteen actual bounded fixtures, typed negatives, guide ownership
observations and six fixed-model ablations. Strict and partial coverage remain
separate; final pixels and visual preference are not invented. The thirteen recipe
examples also provide `decision-contract.json`, verified by `check_examples.py`
against their actual schema, adapters, coverage and count/label invariants.

The [pattern registry](../references/pattern-rules.json) encodes applicability and
exceptions; duplicate evidence families cannot inflate its confidence bookkeeping.
It cannot turn a heuristic into physical truth or a generated-image pass.


Color-stage evaluation: source illustration retained byte-for-byte; actual edit uses its pixels; both names are correct; dimensions and comparative review checked; moved connections/text or lost detail require correction. Synthetic workflow tests do not establish image quality.


Optional requested animation: see [motion workflow](../references/subtle-animation.md). Preserve the illustrated/colored pair; retain animation evidence and inspect actual motion before delivery.

## Interactive 3D evaluation

Evaluate image correspondence separately from browser operation. Run the real browser checker documented in [3D explorer](../references/explorer-3d.md), then inspect assembled, intermediate, separated, clipped, plan and mobile captures. Test ownership, source tampering, detected geometry failures, restoration and unverified dimensions using test_explorer_workflow.py. Synthetic browser receipts in unit tests test acceptance logic only; they do not count as visual evidence.

Revision 23 adds a separate opt-in reconstruction kernel. Test ordinary illustration without HTML, explicit reconstruction of an external image, curved/custom mesh subjects and contact-surface failures. A browser demo alone is not evidence of image correspondence.
