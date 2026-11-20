# New-subject illustrations without a whole-subject materializer

These are fresh-session behavioral cases, not prevalidated images. Run each from its short brief; do not copy another case's layout. Use [the general walkthrough](../../references/walkthrough.md).

## Pipe tunnel
Brief: "Illustrate a passage through a tunnel densely filled with long and short pipes along its sides."
Resolve: long enclosed gallery, central walking strip, asymmetric banks of varied diameter, curved ceiling, repeated ribs, supporting brackets, short returns with explicit ends. Detail by depth: foreground flanges and clamps; mid-distance elbows, branch junctions and hanger rhythm; distant simplified continuous runs. Do not turn 'many' into ten arbitrary isolated segments. No annotations or people by default. The supplied optional builder `scripts/tunnel_guide.py` checks the main bank clearance and repetition only; it does not claim hydraulic functionality or certified support loads. Review the artistic result separately.

## Observatory workshop
Brief: "Draw a mountain observatory workshop."
Resolve a building fitted to slope, visible entrance and credible equipment access, varied bench/storage/inspection activities, roof and wall attachments, atmospheric mountains through openings. Choose an oblique interior or exterior with useful visibility rather than copying a tunnel or four-room slab. Telescope interfaces are unverified if only visually specified. Do not refuse because no observatory materializer exists.

## Urban skyline
Brief: "Draw the skyline from the roof of a tower."
Resolve a roof edge as foreground anchor, mixed tower silhouettes, connected street glimpses and continuing distant city. Check represented supports and setbacks where modeled. Do not demand hidden room programs or underground foundation drawings. Annotations only on request.

## Mechanical assembly
Brief: "Draw a workshop winch with its couplings visible."
Plan the fixed and rotating parts, input/output axis, drum bearings and fixed brake support. Reuse typed connections when modeled. An actual misaligned shaft is a failure to repair, whereas unseen internal gear teeth are unverified. Generation and pixel review are still required; an unsupported checker does not certify the mechanism and does not alone prohibit illustration.

For each case retain the complete history and report numerical coverage separately from visual findings. Repeat an open brief to assess layout diversity; exact visual novelty is not guaranteed by stochastic generation.


Revision 18: route-bearing cases also record a start/end inventory. The tunnel's short branches join an actual tee and end in a blind flange. Observatory cables end at instruments or cable trays with continuation; skyline scenes do not require inventing pipe networks. Mechanical assemblies retain shafts and supports; add pipe-route records only for actual pipes or wiring. No flow or load parameters are requested.

## Rotated vessel beside a terminal
Use the original contract example in ../../references/perspective-review.md. A vessel rotated from the facade is valid; disagreement between its own straight roof and sill families needs investigation. Cropped or curved edges remain uncertain. Correct a confirmed contradiction before color; keep the detailed terminal, view and history. Do not approve perspective solely because boarding is visible.


## Repeated short requests: independent creation

Request: “Illustrate a railway terminal and create its 3D explorer.” Repeating this request starts another create run. First concept might be a transverse hall with a steel portal; another could use longitudinal sawtooth bays and a recessed entrance. These are possibilities, not fixed templates. Select from the site and circulation needs; retain complete entrances and support continuity in either case. Do not load yesterday's image as an edit reference or copy yesterday's reconstruction specification. Complete fresh graphite generation, review, coloring, then bind the 3D build using `illustration_attempt=attempt` and the current colored image.

Contrast: “Repair the entrance of the previous terminal” authorizes an edit run with `reuse_reason` quoting that request and explicitly identified source. “Reconstruct this existing image in 3D” authorizes standalone reconstruction. Never select those modes merely to bypass a failed create guard.

Retain rejected candidates and failure records. A decoded-pixel duplicate check does not prove that two different images depict distinct architectural designs; review massing, layout, entrances and circulation separately. A new camera alone is not a new building.


## Multi-output continuation

For "Illustrate a mountain visitor center and create its 3D explorer", start the delivery pipeline after preparing the fresh illustration attempt, with `requested_3d=True`. A generated base returns `review_illustration`; acceptance prepares `edit_color`; accepted color returns `build_3d`; a rendered candidate returns `review_or_repair_3d`. Only the accepted explorer completes this request. An ordinary "Illustrate a visitor center" stops after the accepted color pair and never builds 3D. Follow [the executable loop](../../references/delivery-loop.md).
