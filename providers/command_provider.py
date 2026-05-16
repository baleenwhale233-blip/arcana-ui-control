from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path
from typing import Any

from .base_provider import ImageProvider, ProviderError


class CommandProvider(ImageProvider):
    name = "command"

    def generate_image(
        self,
        prompt: str,
        output_dir: str | Path,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._run_command("generate", prompt, output_dir, None, None, None, options)

    def edit_image(
        self,
        base_image: str | Path,
        prompt: str,
        output_dir: str | Path,
        mask: str | Path | None = None,
        region: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._run_command("edit", prompt, output_dir, str(base_image), str(mask) if mask else None, region, options)

    def _run_command(
        self,
        mode: str,
        prompt: str,
        output_dir: str | Path,
        base_image: str | None,
        mask: str | None,
        region: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        command = self.settings.get("command")
        if not command:
            raise ProviderError("command provider requires providers.command.command in config.")

        out = self.ensure_output_dir(output_dir)
        prompt_path = out / "command_prompt.txt"
        prompt_path.write_text(prompt, encoding="utf-8")

        env = os.environ.copy()
        env.update(
            {
                "ARCANA_MODE": mode,
                "ARCANA_OUTPUT_DIR": str(out),
                "ARCANA_PROMPT_FILE": str(prompt_path),
                "ARCANA_BASE_IMAGE": base_image or "",
                "ARCANA_MASK": mask or "",
                "ARCANA_REGION": str(region or {}),
                "ARCANA_OPTIONS": str(options or {}),
            }
        )

        completed = subprocess.run(
            shlex.split(command),
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        (out / "command_stdout.txt").write_text(completed.stdout, encoding="utf-8")
        (out / "command_stderr.txt").write_text(completed.stderr, encoding="utf-8")

        if completed.returncode != 0:
            raise ProviderError(
                f"command provider failed with exit code {completed.returncode}. "
                f"See {out / 'command_stderr.txt'}."
            )

        candidate = out / self.settings.get("expected_output", "candidate.png")
        return self.result(
            candidate if candidate.exists() else None,
            mode,
            {"command": command, "returncode": completed.returncode},
        )
