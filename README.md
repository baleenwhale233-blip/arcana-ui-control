# Arcana UI Creative Control

Arcana UI Creative Control is a lightweight skill and scripts project for controlled UI image generation and iterative design refinement.

It helps agents generate and repair UI screenshots without letting the rest of the screen drift. The core method is explicit creative control: approved state, locked regions, change tickets, prompts, provider settings, audits, and archives all live in files.

## Why Skill + Scripts, Not MCP

This project is intentionally not an MCP server, REST API, database, web app, or production platform. UI image iteration needs portable state more than infrastructure. Any agent can read and write these markdown and JSON artifacts, then call small Python scripts.

## Workflow

The intended loop is:

```text
choose source -> observe -> freeze -> diagnose -> propose -> choose provider -> generate -> audit -> accept/reject -> archive
```

The approved screen state should be explicit in `screen_manifest.json`, `locked_invariants.md`, `design_dna.md`, and iteration logs. Never depend on hidden conversation memory.

The first decision is how the original screen enters the workflow:

- `codex_image_seed`: generate the first image directly in Codex with built-in image generation.
- `uploaded_anchor`: use a user-provided image as the approved anchor.
- `provider_seed`: generate the first image through a configured provider.
- `manual_seed`: write a handoff package for a human-operated image tool.

## Providers

Image generation is interchangeable. Providers implement:

- `generate_image(prompt, output_dir, options=None)`
- `edit_image(base_image, prompt, output_dir, mask=None, region=None, options=None)`

Available providers:

- `openai`: recommended default when configured.
- `codex_handoff`: writes a package for Codex built-in image generation.
- `manual`: writes a package for a human to paste into any image tool.
- `agent_handoff`: writes `AGENT_HANDOFF.md` for another agent.
- `generic_http`: posts JSON to a custom HTTP image service.
- `command`: runs a local command-line generator.

Config is read from `config/providers.local.json` when present, otherwise `config/providers.example.json`.

## OpenAI Default Mode

OpenAI uses `OPENAI_API_KEY` from the environment and the optional `openai` Python package.

Setup:

```bash
python scripts/setup_provider.py
python -m pip install openai
export OPENAI_API_KEY="..."
```

If OpenAI is selected explicitly and is not configured, the script fails with clear next steps. If OpenAI is selected only by the default config, generation falls back to manual mode so the workflow can still continue.

## Quick Start

```bash
python scripts/setup_provider.py
python scripts/generate_iteration.py --request examples/module_repair_request.example.json --provider manual
```

When already working inside Codex, use Codex handoff to prepare a prompt package for the built-in image tool without needing a local API key:

```bash
python scripts/generate_iteration.py --request examples/module_repair_request.example.json --provider codex_handoff
```

Expected output:

- output directory created
- compiled `image_prompt.md`
- copied `generation_request.json`
- `MANUAL_HANDOFF.md` or `CODEX_IMAGE_HANDOFF.md`
- `generation_metadata.json`

## State Lifecycle

The project separates active state from iteration evidence:

- `active/`: current approved anchor, `active_state.json`, and `last_accepted_request.json`.
- `runs/`: current working iterations.
- `archives/`: complete historical evidence for accepted, rejected, or superseded runs.

`generate_iteration.py` clears known generated artifacts from the target run directory before writing a new run, so old handoff files and stale `candidate.*` images do not contaminate the next archive. Use `--keep-existing-output` only when you intentionally want to preserve existing files in that run directory.

After an image is accepted, archive the run:

```bash
python scripts/archive_iteration.py --run runs/module-repair-example --status accepted
```

If the run contains `candidate.png`, this updates `active/anchor.png` and `active/active_state.json`.

To remove the original run after safely archiving it:

```bash
python scripts/archive_iteration.py --run runs/module-repair-example --status accepted --cleanup-run
```

## Custom Providers

Use `generic_http` when you have an internal image endpoint. Use `command` when you have a local CLI tool.

Both providers keep the same request and output artifact format, so you can replace providers without changing the skill workflow.

## Agent Compatibility

This project is Codex-first in wording, but the state is neutral. Claude Code, Cursor agents, local scripts, or humans can continue from the same files by reading the request, compiled prompt, manifest, audit, and iteration log.

## Current Limitations

- Image comparison is simple and heuristic.
- Mask generation is not automatic.
- Provider adapters are intentionally small skeletons.
- No server-side job queue, auth, database, or persistent daemon exists.
- Human judgment is still required to accept or reject visual iterations.
