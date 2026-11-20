Current default: illustration -> colored edit -> explicitly requested 3D reconstruction. A 3D model is never a prerequisite for these image stages.

# Two independent spatial examples

## New botanical pavilion

Brief: Create a botanical pavilion with illustrated and colored images and a detailed 3D maquette.

Develop a fresh site, roof, supported glazing and accessible entrance in the illustration plan. Generate and review graphite pixels, then edit that image into its colored version. Inspect the colored design and author its geometry, camera and hidden-region assumptions. Build with the accepted colored source and `illustration_attempt`; inspect the fixed HTML, compare source fidelity and accept only after review. The procedural `examples/presentation-maquette/build.py` can teach component construction, but is not the pavilion design to copy.

Failure exercise: passing an unrelated previous colored image must fail current-pair identity checks. Missing entrances or disconnected routes must be corrected in reconstruction, not concealed by changing the original images.

## One photograph of a pump assembly

Brief: Reconstruct this image as an interactive maquette.

Start `single_image` with the supplied photograph. Mark the motor, coupling, pump casing, base and visible pipe endpoints. Fit a camera only if reliable depth-varying correspondences exist; otherwise record an estimated camera. Model the casing with revolved or explicit meshes, shafts with aligned geometry and open space under supports. Infer the unseen rear casing separately. Snapshot, create the HTML and inspect the actual rendered connection endpoints. Preserve the original image unchanged. Export the accepted scene as GLB after comparison.

Failure exercise: displace the coupling endpoint and check that an existing declared contact fails. Change the source or snapshot bytes and check identity rejection. A functioning orbit control cannot override either failure.


## Short museum request: initialization is not delivery

Request: "Illustrate a museum and create its detailed fixed 3D explorer; preserve entrances, routes, structure and surroundings."

Choose a museum-specific site, exhibition spaces and public route; consider alternatives without borrowing a previous building. Create the history, plan the illustration and actually invoke image generation. Review the pixels, perform the colored edit and review it. Only then author the spatial specification from the colored image and build the explicitly requested fixed explorer. No model or snapshot blocks the image stages. Inspect fidelity and browser behavior before acceptance. Keep each linked history identifiable.

A history containing only `operation.json`, `run.json` and the original brief is an initialized run, not a failed renderer or generated model. The progress diagnostic must report `initialized_only`. Continue the workflow; do not deliver that status as the requested result. A tool exception or missing capability requires its actual evidence and a concrete next action. Do not relax connection or fidelity checks to manufacture completion.
