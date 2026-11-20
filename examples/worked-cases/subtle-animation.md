# Subject-adaptive animation examples

Read the [animation procedure](../../references/subtle-animation.md) only when motion is requested. These are design examples, not fixed layouts or asset coordinates.

## Short requests

- "Draw a mountain observatory and animate its colored version subtly." Finish the pair; inspect whether trees, sky, lights or visible instruments permit two or three motivated effects. Do not rotate the dome or telescope without separating their layers and preserving supports.
- "Animate the colored city: clouds, trees, people and cars." Plan masks for sky and foliage; moving people/cars require reconstructed backgrounds, foreground occluders and pose/path assets. Do not label a cloud-only preview as completed walking/traffic. Start with feasible ambient motion and explicitly record outstanding articulated/travel scope.
- "Animate this colored tank at idle." If a visible exhaust exists, attach subtle exhaust there, keep barrel/tracks/ground contact fixed. No firing, driving or people invented from the word tank. Record why exhaust is applicable or omit it if the view cannot support it.
- "Make a loop of a colored pipe tunnel." Use visible indicator lights or ventilation, when present; pipes, flanges and brackets stay fixed. Do not invent leaks or pulse the entire picture. If no motivated effect is visible, choose a restrained lighting change supported by the existing fixtures and disclose its scope.

## API walkthrough

The executing agent inspects the source, then constructs masks in its history workspace. A mask value of 0 protects that pixel; 255 permits an effect. The protected mask takes precedence by rejecting overlaps, rather than silently removing intended motion. Coordinates and paths are instance-specific and are never copied from this example blindly.

```python
import animation_workflow as motion

# colored_path points to the already reviewed coloreada.png; its illustrated sibling exists.
# foliage_mask and protected_mask were prepared at actual source size after inspection.
plan = {
    'seconds': 6, 'fps': 24, 'protected_mask': str(protected_mask),
    'effects': [{
        'id': 'foliage', 'kind': 'breeze', 'mask': str(foliage_mask),
        'dx': 1.5, 'dy': 0.4, 'cycles': 2, 'feather': 3,
        'reason': 'Light breeze in visible foliage',
        'anchor': 'Trunk and planter remain outside the mask',
        'occlusion': 'Foreground railing is protected',
        'limits': 'Local oscillation, no articulated branches or moving cast shadows'
    }]
}
job = motion.prepare(project, colored_path, plan, original_brief, parent_history)
report = motion.render(job)
# Inspect playback, decoded samples and loop. Supply observed statuses/notes for all six keys.
motion.accept(job, actual_visual_observations)
```

## Failure probes

Reject empty/out-of-bounds masks, mismatched source dimensions, motion touching protected labels/joints, unsupported kinds, nonfinite parameters, sprite motion without a reconstructed clean plate, altered source/candidate bytes, and an existing destination. Retain the failed attempt. Visual failures (double car, stretched branch, smoke through a wall, loop jump) require a new corrected attempt; a matching hash does not turn them into passes.


## Forward-time examples (revision 21)

- "Animate the colored city naturally." Inspect clouds, foliage, people, cars, lights and possible water. Record each candidate and select motions from actual context. Clouds advance, tree crowns oscillate; driving cars need paths/clean plates, walking people need prepared pose sequences. Do not force a return to their initial positions. Deliver a forward-time clip unless a natural loop is requested and feasible.
- "A spinning workshop fan." Separate rotor from housing and foreground grille; use continuous rotation in one direction. A rocking rotor is a failed interpretation. Motion must not affect grille/supports.
- "People walking through the station." Prepare registered pose frames, reconstructed background, clear path, scale progression and fixed foreground occluders. Review feet, step distance, identity and motion, and disclose any unfinished requested walker. A one-frame sprite moving along a path is not walking.

For the earlier foliage-only example, schema_version 2 adds:

```python
plan['schema_version'] = 2
plan['timeline'] = 'once'
plan['inventory'] = [{'id':'terrace-tree', 'category':'foliage',
    'evidence':'Visible crown beside the terrace railing', 'decision':'animate',
    'reason':'Light wind; planter and rail stay fixed'}]
plan['effects'][0].update(target='terrace-tree', category='foliage', motion='oscillate')
```

A prepared vehicle layer uses motion='travel', path=[[0,0,0,1],[1,20,-8,0.95]] and a path_review explaining a clear lane and perspective. Its sprite/clean_plate/removal_mask/pivot must be supplied; these numbers are an API example, not a default path for arbitrary artwork. Forward travel may end elsewhere. Never reverse the last half to close the clip.
