# Skyline from a roof: short request, bounded exterior evidence

Prompt: `Use $scene-layout-forge to draw a richly detailed city skyline from a rooftop, with varied towers, terraces, roof equipment and visible streets and plazas. Include five discreet English annotations.`

Use [urban_skyline.py](../../scripts/urban_skyline.py) as an executable starting point, following [scope and workflow](../../references/exterior-environments.md). Run with the original request in a UTF-8 file and `--annotations`. No reference image or prior conversation is required. Omit a seed for new exploration; seed 16 and family avenue reproduce the numerical regression case only.

Expected: multiple registered exterior envelopes, varied heights and setbacks, supported roof equipment/planting, connected nonoverlapping street surfaces and a real depth-tested guide. Five annotation destinations must be visible and their leader paths must not cover protected people/interfaces or other destinations. Facade bands continue around corners; finishing develops the planned architectural detail and distant atmosphere without replacing the topology.

Counterexamples: a single tower presented as a whole district; unrelated occupied-room graph copied to bypass checks; a street through a building; disconnected road surfaces; a roof cabinet with a support gap; a wider upper tier hanging beyond its support; hidden annotation destinations; or a facade-only model claimed to verify internal stairs/foundations.

Automated regression: `python -B -m unittest discover -s <skill>/scripts -p test_exterior_environment.py`. It runs actual strict geometry, real raster/annotation evidence, freeze, prompt compilation and persistent history preparation. It does not generate or evaluate artistic pixels. Use a fresh agent run for that separate test and retain failures instead of inventing approvals.
