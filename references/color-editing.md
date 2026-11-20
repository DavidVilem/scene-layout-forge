# Color the accepted illustration

The graphite drawing is the authoritative design. The output pair is ilustrada.png and coloreada.png, never final.png. First finish and review the original illustration. Then use the available image-editing tool with that PNG as the source; no additional skill or provider is mandatory. Tool availability depends on the runtime, so do not invent a tool name or silently use an API requiring credentials.

Use color_workflow.prepare with the existing illustration attempt and its accepted ilustrada.png. Inspect all referenced images, send the saved request, retain the exact generated original, and inspect it beside the source. Use restrained, subject-appropriate anime-background colors and soft selective shading while keeping fine graphite/ink strokes readable. Retain all construction detail and count/annotation constraints. User palettes take precedence. Do not apply yellow/sepia to the whole page; do not confuse neutral metal with a glossy photorealistic render.

Review six properties: composition (same camera/framing), linework (fine contours readable and aligned), connections (same pipe endpoints, supports, stairs and openings), annotations (same text and targets, or none), detail (no simplified or added parts/people), palette (requested color treatment achieved). Use notes describing what was actually compared. Visible geometry changes require a local correction. Unclear occluded details remain uncertain. The helper binds evidence; it does not automatically detect every moved line.

Two local color corrections are allowed. The prior colored attempt is the edit target and the illustrated source remains authoritative. Retain both references and their exact request. No destructive overwrites or deletion. Dimensions must match; do not silently upscale or crop to hide a mismatch. If unresolved changes remain, preserve the illustration and report an incomplete colored delivery rather than misrepresenting it as faithful.

Use color_workflow.accept to create coloreada.png beside ilustrada.png. The helper saves the pair record in history. Report actual dimensions for both PNGs. Do not assert a successful color run from unit tests: synthetic fixtures verify workflow control, not artistic quality.

Before coloring, resolve known perspective defects in the selected illustration. Compare the same named edge families after coloring under composition and linework; unchanged perspective is not proof that the source was correct. Uncertain occluded edges remain disclosed.
