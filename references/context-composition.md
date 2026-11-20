# Context and composition from short requests

This written policy works without pictures, earlier conversations or personal paths. Keep the requested subject dominant, the deliverable one PNG and the existing correction limit. Context is a design decision, not a mandatory collection of props.

## Choose a setting mode

| Mode | When to use | What to design |
|---|---|---|
| Isolated study | Explicit isolated object, white background, catalog/component study, or a diagram whose purpose needs isolation | Clear silhouette, contact/support if relevant, usable label space; no unsolicited scenery |
| Contextual scene | Default for a subject-only illustrative request | Coherent setting that explains location, scale and use; develop relevant secondary assemblies and spatial layers before choosing fine detail |
| Environmental scene | Explicit urban district, landscape, site, broad workplace or requested environment | Connected space, context layers and varied subordinate surroundings |

Plans, elevations and sections retain their requested projection. Add only relevant site/access information, not an unsolicited perspective background. Explicit transparent/empty background, counts, historical context and object isolation override automatic context.

For a short request, state one brief assumption and continue when it is low-consequence. Choose a generic concept when no real make/model is specified. If a term could refer to substantially different subjects and the request itself does not disambiguate it, ask one concise question before designing; do not rely on unavailable chat history. A generic vehicle interior is not automatically a named historical aircraft. If real identity or historical fidelity is requested, use suitable primary documentation and disclose gaps.

## Add context with a purpose

Every added element should explain contact, scale, access, setting or use. A machine can sit on an anchored workshop floor with restrained walls/services; a vehicle can occupy a neutral maintenance or display area; an interior can show a subdued apron, landscape or adjacent room through its glazing. Do not silently imply flight, combat, damage, a particular institution or hazardous activity. People are optional, never a requirement of automatic context. Avoid adding a crowd, tools, trees and buildings to every subject.

Match enclosure and external light directions. Transparent openings should reveal plausible surroundings where the chosen setting calls for them, without turning every window into an equally detailed picture. Opaque, frosted or overexposed glazing may be appropriate when intentional. For grounded subjects, show consistent contact and shadows. For urban scenes, continue streets and site logic to the frame edge instead of automatically putting the district on an isolated floating rectangular plinth.

Plan primary subject, immediate setting and distant context separately. In an open-air scene, reduced distant contrast may explain atmosphere; in a dark interior, a distant opening may instead be the strongest contrast. Choose the cue by light and function. Subordinate emphasis does not mean omitting meaningful secondary architecture. Neutral paper is a medium, not a requirement for an empty background. Leave calm areas for labels without erasing context solely to create white margins. In count-sensitive scenes, exclude extra objects of the counted type from the background unless explicitly permitted; scenery must not invalidate the count.

## Meaningful variation, not random decoration

Identify what should repeat (floor heights within one building, matched bearings, structural bays) and what can vary (building proportions, roof programs, block size, setback pattern, equipment placement). Preserve standardized or symmetric assemblies when function requires them. Do not randomize bolts, supports, scales or axes to look organic.

For districts, vary several design dimensions together: footprint, aspect ratio, height group, podium/roof treatment, terrace distribution, spacing and block use. Provide a few related families rather than one tower scaled repeatedly or unrelated shapes everywhere. Locate plazas and access by circulation and available space; do not paste the same park into every block. Keep street continuity and realistic scale. Distinguish a floor band from a window grid and carry each around corners coherently.

For interiors, use functional zones and different secondary assemblies rather than mirrored rows of identical props. For vehicles or machinery, vary the context and view without modifying identity-defining geometry or necessary symmetry. Detail density does not compensate for a weak composition or missing context.

## Camera and guide handoff

Choose direction, height, distance and crop according to the subject, setting and important visible interfaces. Consider sensible alternatives briefly; deliver only one view. Do not force frontal symmetry, eye-level corridors, isometric catalog framing or close crops. Respect explicit projection/angle requests, and use close-up only when requested. A straightforward front view remains valid when it explains the requested subject best.

Add major contextual geometry and variation to the guide before finishing. State which low-detail guide surfaces represent streets, walls or ground rather than literal display plinths. The finisher may enrich planned seams, props and distant uncounted context within scope; it must not invent additional major assemblies, buildings subject to a count, or change access/camera to fill blank areas. Include chosen mode, allowed context, prohibited inferences and the variation plan in its prompt, alongside the common art and annotation contract.

Review the actual PNG for grounding, scale, setting readability, purposeful variation, subject dominance and label space. Mark context/style failures separately from geometry failures and apply only justified corrections. Do not claim that one successful setting proves broad stylistic reliability.

## Executable context with bounded scope

Use `ContextPlan` to list entity IDs with `scale`, `support`, `access`, `use`, `location` or `atmosphere` roles and a concrete reason. Supporting, used, scale or traversed elements must be registered physical parts. `mode='isolated'` rejects added context. `exact_counts` checks physical kinds; the separate final-pixel gate must still catch background copies and reflections. `protected_ids` reject hidden required reading surfaces, while entity and visible-area budgets restrain context rather than forcing equal blank space everywhere.

`context_geometry.add_tree(scene, id, ground_id, xy, size, family=..., seed=...)` adds an original registered trunk/crown mass and explicit root contact on an existing flat slab, footing or landing. Broadleaf, columnar and pyramidal families vary silhouette and crown radii; the seed changes the natural mass without moving the ground interface. An off-ground root patch is rejected. This is a conceptual context adapter, not a botanical species library or a slope/soil simulation. Uneven terrain requires a tested terrain contact adapter; do not use a shadow or `grounded` label as a substitute. Protect access and focal surfaces when placing vegetation and evaluate it through the same camera.

Architecture and interiors should expose program differences through actual secondary assemblies before selecting windows, panels or mark density. Landscape layers may use overlap, scale or selective values only when the projection and lighting support that cue. Orthographic plans retain scale with distance. Repeated construction stays regular where required; organic silhouettes may vary where they communicate growth and setting. These are conditional design principles, not compulsory scene templates.
