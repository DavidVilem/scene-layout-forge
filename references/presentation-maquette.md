# Presentation maquettes: construct, render, compare, deliver

Revision 33 interaction: fixed maquette with orbit, zoom, selection and isolation by visibility. No exploded movement or reassembly; no separation acceptance requirement. Old offset/phase fields are accepted for compatibility but normalized to zero displacement. Preserve visual fidelity and support/access checks.


Use this workflow when an interactive 3D maquette is requested. A short prompt should not require the user to enumerate mullions, joints or roof framing. The target is a presentation model: recognizable massing, purposeful secondary construction, clear entrances, a coherent base, restrained materials, readable glazing, grounded contact shadows and usable inspection controls.

## Why a working viewer can still fail

The reconstruction compiler converts authored shapes; it does not add missing construction automatically. A tower box, flat canopy and rectangular train can pass topology checks while remaining a poor model. A feature called `fine` is not proof of detail. In each spatial zone, the primary form, secondary assemblies and fine features must belong to that actual zone. Lobby benches cannot satisfy roof detailing. Do not make every decorative element critical or mistake subpixel brick texture for the identity of a building.

## Build useful construction families

Read the function signatures in [maquette_parts.py](../scripts/maquette_parts.py). These helpers return ordinary shape dictionaries, not images or an alternate renderer. They retain the normal mesh, contact, protected-space, source-comparison and browser checks:

- `wall_openings(width,height,depth,openings)` partitions a wall around actual rectangular holes. Each opening is `(x,z,width,height)`. Never place an uncut opaque wall behind a window or door.
- `window(width,height,cols,rows,frame)` returns separate `frame` and `glass` shapes. Give glass its own transparent component; keep both in the same host assembly. Do not place opaque duplicate surfaces in its plane.
- `pitched_roof(width,length,eave,rise,bays)` returns skin, ribs and seams. Adapt the actual silhouette to the source; a pitched family is inappropriate for a curved dome.
- `canopy(width,length,height,bays)` includes a pitched skin, ribs, seams, posts, baseplates, braces and lights. Align column positions with platform routes; the family does not know the scene's access constraints.
- `vehicle_shell(width,length,height,base)` supplies a continuous rounded longitudinal loft, separate windows, trims, bogies and lights. This is a starting construction family, not a historically accurate or universal train. Adapt its sections to visible source contours before acceptance.
- `translated(shapes,offset)` returns an independent transformed copy. Local axes are X width, Y length/depth, Z height. Use normal shape rotation for other orientations.

Use these where appropriate, and author surfaces/indexed meshes for other forms. Do not force every subject into these families. [Executable pavilion example](../examples/presentation-maquette/build.py) demonstrates reusable geometry across a different subject, with no embedded artwork. It emits a specification; it is not a visual-fidelity certificate.

## Completion sequence

1. Establish shared semantic parts and proportions for new image+3D requests; for existing images, observe the actual source. Reserve construction work for the model rather than spending the entire execution on illustration planning.
2. Block primary forms and openings, then finish the defining secondary assemblies before source comparison: glazing, roof systems, support arrangements and curved shells. A blockout is an internal milestone, not a delivery candidate.
3. Add source-visible fine families in each zone, with host contact and appropriate repetition. Re-run actual passage and connection checks. Avoid giant unoccupied slabs and coarse decorative lines that overwhelm the miniature.
4. Render the actual HTML from a comparable camera and inspect the complete composition plus close views of the dominant facade, vehicle/mechanism and roof. Fix geometry and material occlusion separately. A glass shader cannot repair a missing opening.
5. For each observed defect, record component IDs, a concrete intended change and a view that will verify it. Rebuild and recheck. Keep earlier attempts. Do not treat a list of readily correctable omissions as a completed response, and do not reuse a previous design for a new prompt.
6. Accept only after normal correspondence and browser review. Deliver beside the image pair; keep construction scripts, screenshots, comparisons and any simplified/inferred scope in history. If actual tools fail, distinguish that from an unfinished modeling task.

## Display and simplification

The bundled viewer uses Z-up studio lighting, matte materials, soft contact shadows and subdued edge lines. Transparent panels do not cast opaque shadows. Clipping disables the main shadow caster to avoid an uncut roof shadow hiding the revealed interior. The technical world grid is hidden in the presentation view. All meshes remain real, selectable and orbitable.

Inspect geometry even with better lighting: visual polish is not fidelity. Simplify leaf shapes, brick texture and tiny hardware at miniature scale; retain recognizable openings, roof profiles, structural rhythm and visible equipment. Hidden backs remain labeled inference. A single image does not prove exact dimensions or unseen structure.
