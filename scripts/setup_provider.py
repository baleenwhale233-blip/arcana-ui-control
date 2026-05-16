from __future__ import annotations

import shutil
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    config_dir = project_root / "config"
    example_path = config_dir / "providers.example.json"
    local_path = config_dir / "providers.local.json"

    if not example_path.exists():
        print(f"Missing example config: {example_path}")
        return 1

    if local_path.exists():
        print(f"Provider config already exists: {local_path}")
    else:
        shutil.copyfile(example_path, local_path)
        print(f"Created provider config: {local_path}")

    print(
        """
Provider setup
--------------
Default provider is OpenAI. To use it:

  python -m pip install openai
  export OPENAI_API_KEY="your_api_key"
  python scripts/generate_iteration.py --request examples/module_repair_request.example.json --provider openai

Manual fallback always works without network or API keys:

  python scripts/generate_iteration.py --request examples/module_repair_request.example.json --provider manual

Codex handoff is best when you are already inside Codex and want built-in image generation:

  python scripts/generate_iteration.py --request examples/module_repair_request.example.json --provider codex_handoff

Other provider choices:

  codex_handoff  writes CODEX_IMAGE_HANDOFF.md for Codex built-in image generation
  agent_handoff   writes AGENT_HANDOFF.md for another agent
  generic_http    posts prompt JSON to a configured endpoint
  command         runs a configured local CLI command

Edit config/providers.local.json to change defaults, models, endpoints, or command settings.
""".strip()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
