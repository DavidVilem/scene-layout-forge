> Scope: this document describes the optional strict numerical workflow or its implementation patterns. For ordinary illustration requests, use [the current general workflow](../SKILL.md) and [walkthrough](walkthrough.md); missing checkers are disclosed coverage limits, not a global refusal. Actual numerical failures still require repair.

# Exterior environments: representation before adapter selection

Revision 2026-11-13.16 corrects a scope error: a rooftop skyline was rejected because no complete urban building materializer existed. A distant facade does not require a habitable model of all its floors. Conversely, a cutaway station cannot be relabeled a skyline to avoid doors or machinery checks.

## Routing

1. Preserve the original short request in history before any tool generation.
2. Identify the visible representation: exterior landscape, occupied interior, cutaway, mechanism or process. Keep explicit user detail, view, counts and annotation intent.
3. For a skyline, compose supported exterior envelopes, stacked roof/setback slabs, roof equipment, landscape masses and street surfaces. A rectangular tower envelope is appropriate geometry at this scale; using a box for a cable mechanism is not.
4. Write `exterior_environment` version 1, mode `urban_exterior`, with alternatives, chosen organization, seed, full part-role inventory, envelopes, roads, focal IDs and unverified scope. Use strict registered schema-v2 and workflow v3. Do not also attach a fictional `materialized_design` or occupied-building contract.
5. Run ordinary scene validation **and** `exterior_environment.errors`. It checks represented support/overlap, fully supported tier footprints, separate connected coplanar road surfaces, allowed component roles and mandatory focal readability. These checks do not establish full building structure, hidden services, foundation capacity or real pedestrian connectivity through unmodeled doors.
6. Render and inspect an actual guide. Change camera, occluders or the focal design if an important surface cannot be read; do not mark missing pixels visible. Preserve every attempted guide. Camera overrides remain free and are validated with the actual view.
7. Freeze the exact scene/view, prepare history with `execution_history.preserve`, then invoke the image tool with the recorded request and guide. Use the written graphite style. Facade modules, roof details and atmospheric depth remain essential even though unseen interiors are out of scope.
8. Review the generated pixels independently. Requirements include envelopes, setbacks, streets, roof equipment, scope, visual detail and each requested callout. Retain limitations and every attempt. Select only one final PNG through `accept_delivery.accept`.

## Executable starting point

`scripts/urban_skyline.py` is a **bounded exterior example**, not a mandatory layout. It supplies several parcel occupancy organizations, varied heights and setbacks, a roof observation point, grounded exterior masses, supported equipment, street/plaza surfaces, planted beds and distant skyline masses. Facade surface grids continue around corners. Different seeds alter parcel occupancy/volumes; a camera change alone is not a new design. All tower envelopes remain rectilinear; curved/twisted towers need tested geometry extensions.

From a project, resolve the installed script path and use:

```sh
python -B <skill>/scripts/urban_skyline.py --project <project> --brief <request.txt> --annotations
```

The helper creates history automatically, preserves the guide, model, projection review, source, scope, exact finish prompt and manifest. It stops at `prepared_not_generated`: the agent must inspect the guide, call the image tool, retain its result, review pixels and accept the final. Do not present the procedural guide as finished art. `--annotations` is for an explicitly annotated request; omit it otherwise. `--seed` reproduces a guide for a regression test; omit it for fresh exploration. `--camera <camera.json>` accepts an explicit supported camera without waiving visibility. `--family` can select avenue, staggered or courtyard organization.

Read the original request and adapt the example's parts, camera, streets, focus and density. Do not force this district onto other subjects. The general `domain_grammar.capability` reports packaged materializer coverage; an unsupported whole materializer is **not** a ban on composing supported shapes. An essential unsupported visible connection still blocks the affected scope until implemented/tested. No geometry or history bypass was added.

## Annotation leaders

Protect people, required interfaces, text boxes, existing leaders and destination neighborhoods. Do not protect an entire annotated tower/roof from all other leaders: that can make a planted area on the same roof unreachable. A thin leader may cross an unprotected surface, but its tip must belong to the correct visible component. Inspect actual generated arrows separately.

## Scope limits

The exterior adapter deliberately rejects interior/cutaway contracts, occupied stairs/ramps, arbitrary custom shapes and components outside its roles. It checks geometric plausibility of represented masses and contacts, not actual load paths through hidden structural framing. A request for entrances, occupied vertical circulation or mechanism operation requires the appropriate richer adapter. Preserve the successful current scene when expanding scope; never claim missing engineering evidence has been validated.
