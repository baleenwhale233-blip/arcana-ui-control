from __future__ import annotations

from pathlib import Path
from typing import Any

from .base_provider import ImageProvider


class CodexHandoffProvider(ImageProvider):
    name = "codex_handoff"

    def generate_image(
        self,
        prompt: str,
        output_dir: str | Path,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        path = self._write_handoff(prompt, output_dir, "generate", None, None, None, options)
        return self.result(
            None,
            "generate",
            {
                "handoff_path": str(path),
                "instructions": "Ask Codex to use built-in image generation with this prompt, then save or attach the result as candidate.png.",
            },
        )

    def edit_image(
        self,
        base_image: str | Path,
        prompt: str,
        output_dir: str | Path,
        mask: str | Path | None = None,
        region: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        path = self._write_handoff(prompt, output_dir, "edit", base_image, mask, region, options)
        return self.result(
            None,
            "edit",
            {
                "handoff_path": str(path),
                "base_image": str(base_image),
                "mask": str(mask) if mask else None,
                "region": region,
                "instructions": "Ask Codex to use built-in image editing/generation with this prompt and the provided anchor image.",
            },
        )

    def _write_handoff(
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
        (out / "codex_image_prompt.txt").write_text(prompt, encoding="utf-8")
        path = out / "CODEX_IMAGE_HANDOFF.md"
        path.write_text(
            "\n".join(
                [
                    "# Codex Image Handoff",
                    "",
                    "Use the current Codex session's built-in image generation capability.",
                    "",
                    f"Mode: {mode}",
                    f"Base image: {base_image or 'none'}",
                    f"Mask: {mask or 'none'}",
                    f"Region: {region or 'none'}",
                    f"Options: {options or {}}",
                    "",
                    "## Steps",
                    "1. Read `codex_image_prompt.txt`.",
                    "2. Generate or edit one UI screen image using the built-in image tool.",
                    "3. Treat the result as `candidate.png` for this run.",
                    "4. Review locked regions before accepting the result.",
                    "5. If accepted, archive the run with `scripts/archive_iteration.py`.",
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
