from __future__ import annotations

from pathlib import Path
from typing import Any

from .base_provider import ImageProvider


class AgentHandoffProvider(ImageProvider):
    name = "agent_handoff"

    def generate_image(
        self,
        prompt: str,
        output_dir: str | Path,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        path = self._write_agent_handoff(prompt, output_dir, "generate", None, None, None, options)
        return self.result(None, "generate", {"handoff_path": str(path)})

    def edit_image(
        self,
        base_image: str | Path,
        prompt: str,
        output_dir: str | Path,
        mask: str | Path | None = None,
        region: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        path = self._write_agent_handoff(prompt, output_dir, "edit", base_image, mask, region, options)
        return self.result(
            None,
            "edit",
            {
                "handoff_path": str(path),
                "base_image": str(base_image),
                "mask": str(mask) if mask else None,
                "region": region,
            },
        )

    def _write_agent_handoff(
        self,
        prompt: str,
        output_dir: str | Path,
        mode: str,
        base_image: str | Path | None,
        mask: str | Path | None,
        region: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> Path:
        out = self.ensure_output_dir(output_dir)
        path = out / "AGENT_HANDOFF.md"
        path.write_text(
            "\n".join(
                [
                    "# Agent Handoff",
                    "",
                    "You are continuing a controlled UI image generation iteration.",
                    "",
                    f"Mode: {mode}",
                    f"Base image: {base_image or 'none'}",
                    f"Mask: {mask or 'none'}",
                    f"Region: {region or 'none'}",
                    f"Options: {options or {}}",
                    "",
                    "## Required Behavior",
                    "- Preserve locked regions and approved design DNA.",
                    "- Change only the requested target module unless explicitly allowed.",
                    "- Return or save one candidate image and describe any unavoidable drift.",
                    "",
                    "## Prompt",
                    "",
                    "```text",
                    prompt,
                    "```",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return path
