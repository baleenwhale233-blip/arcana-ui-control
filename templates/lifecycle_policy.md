# State Lifecycle Policy

Keep active state small and archive complete iteration evidence.

## Long-Lived Active State

Keep these in `active/` after accepting an image:

- `anchor.png` or `anchor.<format>`: the current approved screen.
- `active_state.json`: pointer to the active anchor and source archive.
- `last_accepted_request.json`: the request that produced the current anchor.

## Archived Iteration Evidence

Keep full run evidence in `archives/`:

- `generation_request.json`
- `generation_metadata.json`
- `image_prompt.md`
- `CODEX_IMAGE_HANDOFF.md`, `AGENT_HANDOFF.md`, or `MANUAL_HANDOFF.md`
- `regression_audit.md`
- accepted or rejected candidate images

## Cleanup Rule

After accepting and archiving a run, it is safe to remove the original `runs/...` directory if the archive was created successfully.

Use:

```bash
python scripts/archive_iteration.py --run runs/module-repair-example --status accepted --cleanup-run
```

For rejected runs, archive first, then clean only if the rejection evidence is no longer useful in the active workspace.
