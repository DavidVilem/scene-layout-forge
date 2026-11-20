# Short-request behavior probes

These are text-only agent trials, not executable geometry fixtures or evidence of passed visual evaluations. They intentionally omit long style instructions. Start each in a fresh session with this skill, no prior images or conversation. The agent should use written defaults while preserving explicit overrides. Deliver one illustrated/color pair per independently requested trial: ilustrada.png and coloreada.png.

| Prompt | Expected decision |
|---|---|
| Draw a mountain cable-car terminal. | Plausible access, terrain and station context; choose a useful overall view; restrained people only if useful; meaningful attached detail |
| Draw a dense riverside business district. | Multiple related building families, connected streets and riverfront access; no cloned tower grid or isolated toy plinth |
| Draw the interior of a generic research aircraft cockpit. | No invented make/model; intentional exterior through glazing and clear controls; no automatic flight, crew or frontal close-up |
| Draw a pump isolated on white, without people. | Honor isolation; do not add workshop, landscape or figures |
| Draw a technical room plan, no perspective. | True plan, usable openings and circulation; no unsolicited scenic perspective |
| Draw a generic mechanical coupling. | Identity sufficient for a concept; choose suitable minimal context or a declared isolated explanatory study if that better serves the brief; do not introduce a factory |

Inspect context, variety, view, exact labels, geometry and retained execution history independently. Written expected behavior is not an automatic test of generated image quality. See [context policy](../../references/context-composition.md).

Repeat a short request in independent sessions without reference images. Compare the chosen spatial graphs and realized geometry, not just rendering texture. Optional reproducibility request: "Use design seed 42". A fresh seed permits variation but does not guarantee every run is different. A user who asks for the same design should instead retain the original seed and contract.

Additional probes:

| Prompt | Observable decisions |
|---|---|
| Draw a mountain bunker cut in half showing six connected levels. | Six levels; distinct room functions; real stair voids and reachable landings; mountain context; no six cabinet-shaped elevator cars |
| Draw an aircraft maintenance hangar with three technicians. | Aircraft-specific forms and servicing access; supported platforms; no inherited treatment-tank network |
| Draw a small urban pumping station in plan, without labels. | Orthographic plan, real openings and declared fluid endpoints; honor no-label override |

Each trial delivers ilustrada.png and its matching colored edit coloreada.png. Multiple candidates are internal planning artifacts, not an unsolicited gallery.
