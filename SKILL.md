---
name: arcana-ui-creative-control
description: Use this skill to generate, lock, repair, refine, audit, and archive UI image iterations with explicit file-based state, provider adapters, locked regions, and regression artifacts.
---

# Arcana UI Creative Control

Use this skill when a coding or design agent needs controlled UI image generation with less random drift between iterations. The workflow is lightweight and file-based: markdown and JSON artifacts are the source of truth.

## First Decision: Source Image

Before the normal loop, ask how the first screen image should enter the workflow:

1. Codex image seed: generate the original UI image directly with Codex/image2, then treat the accepted result as the anchor.
2. Uploaded anchor: use a user-provided image file as the original approved screen.
3. Provider seed: use a configured provider such as OpenAI, generic_http, or command to generate the original screen.
4. Manual seed: write a handoff package for a human to create the first image.

Record this choice in the request `source` object. If the user uploads or provides an existing image, set `source.type` to `uploaded_anchor` and point `source.image_path` at the file.

## Workflow

Follow this loop:

1. choose source: Codex/image2 seed, uploaded anchor, provider seed, or manual seed.
2. observe: read the current brief, manifest, anchor image, and iteration log.
3. freeze: write the approved screen state, locked regions, and invariants.
4. diagnose: identify the specific drift, weak module, or design issue.
5. propose: write a concise change ticket and prompt.
6. choose provider: OpenAI, codex_handoff, manual, agent_handoff, generic_http, or command.
7. generate: run `scripts/generate_iteration.py`.
8. audit: compare against the approved anchor and write drift notes.
9. accept/reject: update the request or iteration log.
10. archive: run `scripts/archive_iteration.py` for accepted work.

Do not rely on chat memory. Put decisions in `templates/*.md`, request JSON, or output artifacts.

## Modes

- Concept Mode: create new UI directions, direction cards, and prompt candidates. Often starts with `source.type: codex_image_seed`.
- Anchor Lock Mode: capture an approved screen, modules, locked regions, and design DNA. Often starts with `source.type: uploaded_anchor`.
- Module Repair Mode: edit one target module while preserving locked regions.
- Refinement Mode: polish hierarchy, spacing, typography, and component quality without changing information architecture.
- Regression Audit Mode: compare a new image against the approved anchor and document unwanted drift.

## Provider Choice

Provider order is: CLI argument, request field, config default, manual fallback.

Run setup first:

```bash
python scripts/setup_provider.py
```

Default config recommends OpenAI. OpenAI uses `OPENAI_API_KEY` from the environment and the optional `openai` Python package. If OpenAI is unavailable, use:

```bash
python scripts/generate_iteration.py --request examples/module_repair_request.example.json --provider codex_handoff
python scripts/generate_iteration.py --request examples/module_repair_request.example.json --provider manual
python scripts/generate_iteration.py --request examples/module_repair_request.example.json --provider agent_handoff
```

## Generate Iterations

Manual mode writes a handoff package with a compiled prompt and placement instructions:

```bash
python scripts/generate_iteration.py --request examples/module_repair_request.example.json --provider manual
```

Codex handoff mode writes a package designed for the current Codex session to call its built-in image generation capability:

```bash
python scripts/generate_iteration.py --request examples/module_repair_request.example.json --provider codex_handoff
```

OpenAI mode attempts image generation or editing:

```bash
python scripts/generate_iteration.py --request examples/module_repair_request.example.json --provider openai
```

If the request contains `base_image`, the provider uses edit mode. Otherwise it uses generation mode.

## Archive Accepted Iterations

After accepting an output, archive it with:

```bash
python scripts/archive_iteration.py --run runs/module-repair-example --status accepted
```

Keep rejected iterations too. They are useful regression evidence.
