# Conditional drawing principles

These original rules are written implementation knowledge. No local collection,
image, OCR result, external skill or earlier conversation is a runtime dependency.
Illustrations can suggest a principle; their captions do not prove it. Repeated
copies of a diagram do not increase its evidential value. Confirm a rule with a
geometric test or controlled visual comparison before calling it verified.

The machine-readable [pattern catalog](pattern-rules.json) implements nine original
records in six priority families: projection, contact, light, context, material and
organic scope. `scripts/pattern_rules.py` validates explicit applicability, exceptions,
mode, limits and evidence confidence. `select_patterns(scene)` selects only from
the actual declared domain, camera/view, setting, light policy, owned material
frames and supported organic components. Missing facts stay unknown. Conflicting
plan/perspective or isolated/context declarations are reported, not resolved by
inventing new geometry or intent.

Evidence is grouped by independent question families. Copies, repeated tests and
extra source names in the same family contribute once. The bounded confidence
score describes evidence organization, not an empirical probability, executed-test
result, scene approval or final-image recognition. A new independence label needs
an explicit registry rationale; it is not inferred from a different filename.
Conditional exceptions preserve dark interiors and orthographic plans. Organic
guidance is limited to scale, silhouette and supported contact, with no medical,
anatomical-canon or biological-validation claim. The catalog has no image assets,
private reference identifiers or dependency on a local study collection.

## Perspective and geometry

- Build masses and their relations, then refine the **same** model. Freeze model,
  camera and display cut; a new opening requires rebuilding, not a texture edit.
- Derive vanishing directions from camera and each object's axes. Rotated objects
  need not share all vanishing points. Sloping stairs do not share horizontal axes.
- Plan views remain orthographic. Fish-eye and recursive views are unsupported
  until a real projection adapter and tests exist; never approximate them silently.
- Contact needs a surface, normal, contact patch and route to support. A dark
  shadow, adjacency in the image or a `grounded` name alone is not evidence.
- Preserve purposeful gaps: physical clearance and visible separation are different
  constraints. Neither requires a universal percentage of empty paper.
- Project people, vehicles and furniture from the same world. Do not enlarge
  distant figures or align all heads to create artificial legibility.

## Light, shadow and values

- Select a light direction or a documented soft-light treatment. Shape, local
  material tone, illumination and atmospheric separation are different variables.
- Reserve useful local contrast for the subject and its crucial junctions. The
  nearest object need not be darkest; a distant control assembly can be the focus.
- Lightening distant layers is conditional on atmosphere and scene lighting.
  A dark interior behind a bright opening is valid. Plans need no atmospheric blur.
- Quiet areas need a compositional reason, not arbitrary blankness. Darkness or
  noise must not conceal failed supports, missing stairs or interrupted pipes.
- Compare light changes with geometry/materials fixed; judge shape readability,
  not just whether the second result looks more dramatic. Guide shading is a
  graphical aid, not a physically certified lighting or shadow simulation.

## Line, texture and materials

- Use three relative line roles: silhouette/section, assembly edges, fine detail.
  Scale widths to delivery resolution. Vary pressure without breaking alignment.
- Texture follows local surfaces and changes with their projected orientation.
  Seams, wood grain, metal hatching and rock strata do not share a screen stencil.
- Allocate detail at three scales: main masses, secondary construction and fine
  marks. A small projected part cannot carry an arbitrarily detailed label or face.
- Fine marks belong to identifiable pieces. More dots, scratches or equal-density
  hatching across all surfaces do not improve construction or depth.
- Cables and flexible routes need endpoints, clearance and bend limits. Catenary,
  parabola and an artistic loose curve are not interchangeable physical models.

## Architecture and interiors

- Program and circulation precede supports, envelope, services and furniture.
  A workshop, dormitory and control room need different usable arrangements.
- Repetition follows construction; variation follows function. Do not randomize
  bolts, floor heights or window positions in ways that break continuity.
- Derive plan, section and inspection views from the same registered model.
  A display cut removes occlusion for explanation, not physical obligations.
- Add context to explain support, size, use or location. A subject-only prompt
  does not always imply a factory hall, centered corridor or foreground person.
- Choose a useful view freely. Good symmetry is allowed; choose another layout
  because it fits the program, not because asymmetry is compulsory.

## Landscape, nature and environmental context

- Terrain supporting a building is physical geometry and needs contact evidence.
  Distant landscape used only for context must not be misreported as validated support.
- Use vegetation families, branch direction and masses before leaf marks. Adapt
  density to scale and protect openings, annotation leaders and mechanism visibility.
- Water, mist and clouds need an identified phenomenon and directional treatment.
  Generic grain is not a simulation of fluid behavior.
- Organic references teach mass, contour, overlap, rhythm and local surface marks.
  They do not authorize universal anatomy, medical claims or biological accuracy.
  Animal species-specific geometry requires an implemented adapter or an explicit
  limited artistic scope; do not manufacture a technical validation for it.

## Focus, actors and annotations

- An actor starts with task, pose, foot/seat/tool contacts and clearance. A silhouette
  library does not establish a hand grasp or supported pelvis by itself.
- Every semantic annotation has exact text, a component ID, visible anchor,
  text box and leader route. Nearby objects are not interchangeable targets.
- Judge global composition, regional detail and local contact independently. A
  correct count does not compensate for lost detail or an unreadable interface.
- Record observed pixels as correct, erroneous, occluded or uncertain. If an edit
  changes the PNG, its prior coordinates/review no longer authorize another edit.

For implementation read only the relevant references: [visual planning](visual-planning.md),
[typed interfaces](typed-interfaces.md), [view evidence](view-evidence.md),
[drawing construction](drawing-construction.md) and [art direction](art-direction.md).


## Apply before freezing

Call `select_patterns` on the declared subject/site facts during stage 1, save the selection and unknowns, and use relevant context/projection/contact principles while comparing stage-3 massing. Re-select after camera/material decisions in stage 7. The finish compiler includes applicable rules again, but that late inclusion cannot change an invalid footprint, doorway or support. Rule selection is advisory; architectural and physical gates supply separate evidence.
