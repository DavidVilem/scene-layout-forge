# Cross-domain design-graph regression matrix

This matrix exercises planning diversity and reproducibility without ImageGen.
It does **not** evaluate technical drawings, mechanical function, piping,
architectural support, headroom, artwork quality or real-world compliance.

Run from any working directory using the resolved installation script path:

```text
python -B scripts/evaluate_designs.py --out-dir <new-project-evaluation-folder>
```

The default has six domains, four root seeds (0, 1, 2, 3), and four candidates per
run: 24 planning runs and 96 candidate graphs. All evidence is written outside
the installed package. An existing output directory is rejected. `--seeds` and
`--count` allow another explicit experiment; record changes before comparing it
with the baseline.

| Domain | Design strata | Program inventory |
|---|---:|---|
| Sectioned mountain bunker | 6 levels | Utilities, storage, workshops, quarters, medical, command |
| Urban district | 1 site stratum | Building blocks, public space, street network, services |
| Scientific airship gondola | 1 level | Navigation, atmospheric lab, maintenance, life support |
| Water-treatment installation | 1 level | Treatment, pumping, service access, controls |
| Winch maintenance assembly | 1 level | Drive, drum support, brake, controls |
| Mountain observatory | 1 site stratum | Instrument, mount, maintenance, control room |

These domains share the generic spatial graph grammar, but their declared
programs differ. A graph that puts a drive and drum in reachable zones does not
establish a shaft connection. A declared curved enclosure does not construct a
hull. Every candidate starts with geometry and artistic validation `not_run`.
Specialized geometry builders and their validators remain necessary.

## Acceptance gates

- Every candidate satisfies the **supported intent checks**, including requested
  levels, required program inventory and declared graph reachability.
- Replay with the same seed reproduces candidates, selection and decision
  evidence exactly for the recorded source revision.
- Each domain's four selected graphs contain at least two distinct topologies;
  each individual run offers at least two distinct candidate designs. A topology
  signature removes metric positions, so shifting a stack or changing its camera
  cannot satisfy this gate on its own.
- Changing camera/detail seeds, translation or a small global rotation is
  detected as the same design by the full normalized fingerprint.
- Passing the selected fingerprint as a prior excludes that exact repeat and
  selects another feasible candidate. Passing all available fingerprints fails
  explicitly and requires new design choices; it does not weaken constraints.

This deliberately small regression target is not a universal novelty guarantee.
Do not describe four outputs as four unique organizations when only two topology
signatures are observed. A larger distribution study should inspect family
frequencies and rejection reasons, and include domain-specific feasibility.

## Initial recorded result

The baseline source run passed the listed graph gates for all six domains. Each
domain produced **two distinct selected topologies across four seeds**. The
pipeline reproduced selections and excluded prior exact fingerprints. No image
generation or geometry-validation run was made for this matrix. Program names and
features were checked as declared inventory, not as realized parts.

`design-matrix.json` contains all candidate snapshots and selection reports;
`summary.json` contains gates, observed topology counts and source hashes. Keep
these run files with project diagnostics when requested, not in the skill archive.

## Connect graph evidence to real geometry

`materialization_requirements(selected)` provides zone IDs and required graph
links as a checklist. A separate realized-scene contract should map each zone ID
to actual spaces/components and each edge ID/pair to an opening, passage or access
assembly. Check that mapped IDs exist, that the realized graph is reachable, and
that associated clearances/supports are verified by the matching geometry adapter.
Reject a mapping that lists a cabinet as an elevator without a shaft and openings.

A matching ID or hash proves data lineage only. It cannot prove the layout was
built, nor that a generative finish preserved it. Require geometry and pixel
evidence as separate downstream gates.

## Future matrix extensions

Add adversarial intents for forbidden rooms, fixed projection, one inaccessible
level, a pipe graph mislabeled as circulation, incompatible user requirements,
and insufficient program capacity. Run visual evaluations separately with fixed
output size and tool configuration. Compare whole composition and critical
junctions; never infer them from these graph-only results.
