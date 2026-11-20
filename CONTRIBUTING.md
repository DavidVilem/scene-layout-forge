# Contributing

Use a Python 3.11+ virtual environment and install requirements.txt. Build examples into a separate project work directory, never into the package. Keep original procedural source in examples; no personal paths, user artwork, output images, credentials, dependency copies or caches.

For core changes run both unittest suites listed in README, `scripts/check_examples.py` and `scripts/check_package.py`. Add a positive scene and a deliberately invalid case for a new constraint. Changes to art direction need an actual agent/visual evaluation using evals, not wording-match tests. Record failures and untested cases honestly.

Keep the entrypoint short and route to focused references. Preserve public script entry points when changing implementation. User prompts must work from any installed location and without a previous chat. Choose a distribution license before public publication; organizational inspiration does not transfer another project's license automatically.
