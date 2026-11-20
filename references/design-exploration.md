> Scope: this document describes the optional strict numerical workflow or its implementation patterns. For ordinary illustration requests, use [the current general workflow](../SKILL.md) and [walkthrough](walkthrough.md); missing checkers are disclosed coverage limits, not a global refusal. Actual numerical failures still require repair.

# Explore designs before freezing geometry

The brief owns counts, connections, exclusions and view requests. Planning choices
must remain separately recorded. A camera change, renaming or uniform scaling is
not a new physical design. Geometry, guide readability and final pixels have
independent gates.

## Domain contracts and real capabilities

`DesignIntent.from_data()` accepts `domain`, `subject`, `constraints`, `choices`,
`program_roles` and `features`. Intent version 2 serializes the domain explicitly.
Old inputs receive conservative subject-based domain inference; prefer an explicit
domain for new scenes. Unknown hard constraints and domains are rejected.

| Domain | Entities | Relationships | Minimum inventory |
|---|---|---|---|
| building | occupied spaces and circulation | circulation, vertical access | one space; no universal room count |
| process | process units | process flow with typed interfaces and maintenance access | one unit |
| mechanism | mechanical components | transmission with support | one or two components are allowed |
| vehicle | vehicle subsystems | service connection and mounting | one subsystem |
| environment | site regions | site access, walkable surfaces and terrain contact | one region |

`choices.component_count` or `zones_per_level` accepts 1–30. Defaults are specific
to the domain and program inventory. Building programs may be assigned by level
or zone. Other domains assign program by component, without inventing a room or
central staircase. Only building grammar currently supports multiple levels.

These are graph contracts, not domain solvers. Non-building candidates have
`capability.status: unsupported` until a complete materializer is registered.
For example, a curved airship enclosure is explicitly unsupported; a rendered
shell primitive alone does not provide a complete vehicle realization. An urban
site uses `site_access`, never fluid ports as streets.

`domain_grammar.capability()` distinguishes planning support, availability of a
physical adapter and its still-pending validation. The bunker adapter supports
`hub`, `spine` and `branched`, five allocated spaces per level, and 2–12 levels.
`ring` and `stepped` remain conceptual alternatives and explicitly unsupported by
that adapter. This limitation is local to the bunker builder, not a universal
building requirement. `require_materializable: true` excludes unsupported
candidates before scoring; it never replaces one topology with another.

## Comparable diversity and reproducible selection

Variant/selection policy version 3 evaluates the entire valid candidate set
before novelty is assigned. Distances are symmetric. Organization, program
inventory, program adjacency, silhouette and section have separate descriptors;
view changes are excluded. Translation, free XY rotation and uniform scale are
equivalent. Orientation-specific design constraints require a future explicit
adapter; they are not silently verified.

Semantic fingerprints include program allocation. `fingerprint(c, semantic=False)`
reports structural organization separately. Fingerprints are approximate graph
and quantized-distance filters, not graph-isomorphism proofs. Tiny metric edits
near quantization boundaries can change fingerprints. History currently provides
exact fingerprint exclusion only, not a claimed metric of distance to unavailable
historic geometry.

Duplicate classes choose a stable representative, independent of input order.
Novelty is the minimum distance to the other distinct valid candidates. Every
candidate in a duplicate class has the same `internal_diversity`; duplicate
representatives and exact historical repeats are reported separately. Invalid
candidates receive no quality score. Mean travel hops remain observable but do
not favor a hub unless `quality_objective: shortest_travel` explicitly requests
that preference. `constraints.closed_loop: true` rejects dangling routes.

Default selection retains all distinct feasible candidates with the best functional
quality, then hashes the common design seed and content fingerprint to choose one.
Internal diversity describes the candidate set; it does not automatically prefer
the most isolated outlier. The Pareto frontier remains reported evidence, separately
from `eligible_ids` and `selection_policy`. A default winner may lie outside that
frontier without violating any requirement. This avoids a hub winning every seed
merely because it is the most novel candidate in a fixed set.

`choices.quality_objective: shortest_travel` gives that explicit functional quality
priority before seeded selection. `choices.novelty_objective: maximize` explicitly
requests maximum novelty among the best-quality feasible candidates. No aesthetic
metric can compensate for failed hard requirements or unsupported capability.

Candidate position and input order do not determine the winner. Conflicting seed
streams are rejected. A root seed independently derives design, camera and detail
streams. Regression trials require multiple supported organizations across many
seeds, not equal family frequencies or a universal statistical guarantee.

`verify_selection()` recomputes policy-versioned evidence, candidate hashes,
reports, eligible pool and the selected result. Version 1 or 2 evidence must be
regenerated explicitly; never relabel a frozen selection without recomputing it.

## Complete realization

`materialized_design` maps every selected node and edge to actual allocated
parts, access volumes and topology-preserving locations. `requirements[edge_id]`
adds typed witnesses for every declared edge requirement: supported flight,
landing, aperture, headroom or clearance. Program contracts name actual component
kinds and assembly membership; names alone remain semantic declarations.

The reproducible bunker command is:

```text
python -B scripts/build_bunker.py --output <new-run-folder> --seed 27 --levels 6 --family branched
```

Omit `--family` for capability-aware exploration. `--levels` comes from the brief;
six is this example's value, not a domain rule. The three adapters realize a
radial hub, a longitudinal chain and a branch with a secondary junction. Every
one keeps its own selected geometry, actual doors, stacked floor supports,
stairwell openings and the same validated stair/access contracts. The mountain
cavity expands to the actual occupied footprint. Display removal never deletes
physical walls or geological enclosure from the validated scene.

`evaluate_designs.run_bunker_materialization_matrix()` exercises every declared
bunker adapter with the same strict physical and graph-realization checks. It
records distinct topology signatures and keeps guide/final-pixel status `not_run`.
The broader matrix in `evaluate_designs.py` remains a planning probe and reports
unsupported domain materialization honestly. It does not turn a graph pass into
a functional or artistic pass.

CLI planning: `python -B scripts/design_variants.py --intent <intent.json>
--out-dir <new-folder> --seed 42`. Evidence goes outside the installed skill and
existing destinations are refused. Use tests for all 120 candidate permutations,
small mechanism inventories, unsupported capabilities and all physical bunker
families. Final pixels still require direct inspection.
