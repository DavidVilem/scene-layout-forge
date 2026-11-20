# Domain decisions with falsifiable limits

These original planning cases describe tested grammar behavior. They are not
claims that complete physical scenes or final artwork have been generated for
every domain. See [domain tests](../../scripts/test_domain_diversity.py) and the
[materialization matrix](../../scripts/evaluate_designs.py).

| Short brief | Contract and permitted decision | Negative case and required outcome |
|---|---|---|
| Two-piece winch transmission | `mechanism`, two mechanical components, a transmission edge with typed interface and support obligations. No circulation room is introduced. | Naming two blocks `drive` and `brake` does not create transmission. No complete mechanism materializer is registered: capability stays unsupported. |
| A small water-treatment chain | `process`, process units, process-flow edges and independent maintenance-access requirements. Program inventory defines the units. | A street-style adjacency cannot witness fluid continuity. A missing typed interface must fail the eventual physical adapter even when the graph is connected. |
| A scientific airship interior | `vehicle`, subsystem inventory and service/mount relationships; curved enclosure remains an explicit feature. | The shell primitive does not establish wall thickness, structural attachment or a complete vehicle. `curved_enclosure` reports an unsupported materialization reason. |
| An urban district around a square | `environment`, site regions and `site_access` with walkable-surface and clearance obligations. | Reusing process-flow ports as streets violates the domain contract. Terrain and street realization remain unsupported until a tested site adapter exists. |
| Six connected bunker floors in a mountain | `building`, exact six levels, connected graph, occupied programs, real apertures and supported vertical access. Hub, spine and branched adapters are available. | Ring and stepped cannot silently reuse a hub. An unsupported requested family fails selection; a missing landing, blocked door or floating footing fails physical/realization checks. |
| A small building room | `building`, one space is an allowed inventory; general planning does not require five rooms. | The bunker adapter's five-space-per-level limit is local to that adapter. It cannot claim to materialize this room by expanding the request without authorization. |

The same seed in different domains produces different entity and relationship
types, not just renamed rooms. Capability reports are recomputed against the
registry: changing a flag from unsupported to supported is rejected.

Free rotation, renaming, camera changes and texture seeds do not establish a new
layout. A program reassignment changes the semantic fingerprint while preserving
the structural fingerprint. Requested closed-loop circulation rejects dangling
nodes before quality or novelty is considered; compactness cannot compensate for
failing that requirement.

For three materialized building alternatives, use the
[hub example](../connected-mountain-bunker/README.md),
[spine example](../bunker-spine/README.md) and
[branched example](../bunker-branched/README.md). Each retains strict geometry
validation, typed witnesses, materialization maps and explicit artistic status.
