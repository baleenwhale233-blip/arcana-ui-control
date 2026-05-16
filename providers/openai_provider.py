from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

from .base_provider import ImageProvider, ProviderError


class OpenAIProvider(ImageProvider):
    name = "openai"

    def generate_image(
        self,
        prompt: str,
        output_dir: str | Path,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        client = self._client()
        out = self.ensure_output_dir(output_dir)
        opts = self._options(options)

        response = client.images.generate(
            model=opts["model"],
            prompt=prompt,
            size=opts["size"],
            quality=opts["quality"],
            output_format=opts["output_format"],
            n=1,
        )
        image_path = self._save_first_image(response, out, opts["output_format"])
        return self.result(image_path, "generate", {"model": opts["model"], "size": opts["size"]})

    def edit_image(
        self,
        base_image: str | Path,
        prompt: str,
        output_dir: str | Path,
        mask: str | Path | None = None,
        region: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        client = self._client()
        out = self.ensure_output_dir(output_dir)
        opts = self._options(options)
        base_path = Path(base_image)

        if not base_path.exists():
            raise ProviderError(f"OpenAI edit requested but base image does not exist: {base_path}")

        kwargs: dict[str, Any] = {
            "model": opts["model"],
            "image": base_path.open("rb"),
            "prompt": prompt,
            "size": opts["size"],
            "quality": opts["quality"],
            "output_format": opts["output_format"],
            "n": 1,
        }
        mask_handle = None
        try:
            if mask:
                mask_path = Path(mask)
                if not mask_path.exists():
                    raise ProviderError(f"OpenAI edit requested but mask does not exist: {mask_path}")
                mask_handle = mask_path.open("rb")
                kwargs["mask"] = mask_handle

            response = client.images.edit(**kwargs)
        finally:
            kwargs["image"].close()
            if mask_handle:
                mask_handle.close()

        image_path = self._save_first_image(response, out, opts["output_format"])
        return self.result(
            image_path,
            "edit",
            {
                "model": opts["model"],
                "size": opts["size"],
                "base_image": str(base_path),
                "mask": str(mask) if mask else None,
                "region": region,
            },
        )

    def _client(self) -> Any:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ProviderError(
                "OpenAI provider is not configured: OPENAI_API_KEY is missing. "
                "Set OPENAI_API_KEY, or rerun with --provider manual or --provider agent_handoff."
            )

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderError(
                "OpenAI provider requires the optional 'openai' package. "
                "Install it with: python -m pip install openai. "
                "Or rerun with --provider manual."
            ) from exc

        return OpenAI(api_key=api_key)

    def _options(self, options: dict[str, Any] | None) -> dict[str, Any]:
        merged = dict(self.settings)
        merged.update(options or {})
        return {
            "model": merged.get("model", "gpt-image-1.5"),
            "size": merged.get("size", "1536x1024"),
            "quality": merged.get("quality", "medium"),
            "output_format": merged.get("output_format", "png"),
        }

    def _save_first_image(self, response: Any, output_dir: Path, output_format: str) -> Path:
        data = response.data[0]
        image_path = output_dir / f"candidate.{output_format}"

        b64_json = getattr(data, "b64_json", None)
        if b64_json:
            image_path.write_bytes(base64.b64decode(b64_json))
            return image_path

        url = getattr(data, "url", None)
        if url:
            raise ProviderError(
                "OpenAI returned an image URL instead of base64 data. "
                "Download the URL manually or configure the SDK/model to return base64 image data."
            )

        raise ProviderError("OpenAI response did not contain image data.")
