from __future__ import annotations

from pathlib import Path
from typing import Any

from .base_provider import ImageProvider


class ManualProvider(ImageProvider):
    name = "manual"

    def generate_image(
        self,
        prompt: str,
        output_dir: str | Path,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        path = self._write_handoff(prompt, output_dir, "generate", None, None, options)
        return self.result(
            image_path=None,
            mode="generate",
            metadata={
                "handoff_path": str(path),
                "instructions": "Paste the prompt into an image tool, then place the generated image in this output directory.",
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
        path = self._write_handoff(prompt, output_dir, "edit", base_image, mask, options, region)
        return self.result(
            image_path=None,
            mode="edit",
            metadata={
                "handoff_path": str(path),
                "base_image": str(base_image),
                "mask": str(mask) if mask else None,
                "region": region,
                "instructions": "Open the base image in your image tool, apply the prompt to the target region, then place the result in this output directory.",
            },
        )

    def _write_handoff(
        self,
        prompt: str,
        output_dir: str | Path,
        mode: str,
        base_image: str | Path | None,
        mask: str | Path | None,
        options: dict[str, Any] | None,
        region: dict[str, Any] | None = None,
    ) -> Path:
        out = self.ensure_output_dir(output_dir)
        prompt_path = out / "manual_prompt.txt"
        prompt_path.write_text(prompt, encoding="utf-8")

        handoff_path = out / "MANUAL_HANDOFF.md"
        handoff_path.write_text(
            "\n".join(
                [
                    "# Manual Image Generation Handoff",
                    "",
                    f"Mode: {mode}",
                    f"Base image: {base_image or 'none'}",
                    f"Mask: {mask or 'none'}",
                    f"Region: {region or 'none'}",
                    f"Options: {options or {}}",
                    "",
                    "## Steps",
                    "1. Open your preferred image generation or editing tool.",
                    "2. Paste `manual_prompt.txt` as the prompt.",
                    "3. If editing, upload the base image and mask/region if your tool supports them.",
                    "4. Save the generated image into this output directory.",
                    "5. Name the image `candidate.png` or update `generation_metadata.json` with the final path.",
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
        return handoff_path
