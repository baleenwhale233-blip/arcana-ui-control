---
name: arcana-ui-creative-control
description: Use this skill to generate, lock, repair, refine, audit, and archive UI image iterations with explicit file-based state, provider adapters, locked regions, and regression artifacts.
---

# Arcana UI Creative Control

Use this skill when a coding or design agent needs controlled UI image generation with less random drift between iterations. The workflow is lightweight and file-based: markdown and JSON artifacts are the source of truth.

## Workflow

Follow this loop:

1. observe: read the current brief, manifest, anchor image, and iteration log.
2. freeze: write the approved screen state, locked regions, and invariants.
3. diagnose: identify the specific drift, weak module, or design issue.
4. propose: write a concise change ticket and prompt.
5. choose provider: OpenAI, manual, agent_handoff, generic_http, or command.
6. generate: run `scripts/generate_iteration.py`.
7. audit: compare against the approved anchor and write drift notes.
8. accept/reject: update the request or iteration log.
9. archive: run `scripts/archive_iteration.py` for accepted work.

Do not rely on chat memory. Put decisions in `templates/*.md`, request JSON, or output artifacts.

## Modes

- Concept Mode: create new UI directions, direction cards, and prompt candidates.
- Anchor Lock Mode: capture an approved screen, modules, locked regions, and design DNA.
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
python scripts/generate_iteration.py --request examples/module_repair_request.example.json --provider manual
python scripts/generate_iteration.py --request examples/module_repair_request.example.json --provider agent_handoff
```

## Generate Iterations

Manual mode writes a handoff package with a compiled prompt and placement instructions:

```bash
python scripts/generate_iteration.py --request examples/module_repair_request.example.json --provider manual
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
