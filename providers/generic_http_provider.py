from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .base_provider import ImageProvider, ProviderError


class GenericHttpProvider(ImageProvider):
    name = "generic_http"

    def generate_image(
        self,
        prompt: str,
        output_dir: str | Path,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._request("generate", prompt, output_dir, None, None, None, options)

    def edit_image(
        self,
        base_image: str | Path,
        prompt: str,
        output_dir: str | Path,
        mask: str | Path | None = None,
        region: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._request("edit", prompt, output_dir, str(base_image), str(mask) if mask else None, region, options)

    def _request(
        self,
        mode: str,
        prompt: str,
        output_dir: str | Path,
        base_image: str | None,
        mask: str | None,
        region: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        endpoint = self.settings.get("endpoint")
        if not endpoint:
            raise ProviderError("generic_http provider requires providers.generic_http.endpoint in config.")

        out = self.ensure_output_dir(output_dir)
        payload = {
            "mode": mode,
            "prompt": prompt,
            "base_image": base_image,
            "mask": mask,
            "region": region,
            "options": options or {},
        }
        headers = {"Content-Type": "application/json"}
        if self.settings.get("api_key"):
            headers["Authorization"] = f"Bearer {self.settings['api_key']}"

        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=int(self.settings.get("timeout_seconds", 120))) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise ProviderError(f"generic_http request failed: {exc}") from exc

        image_path = self._save_response_image(body, out)
        return self.result(image_path, mode, {"endpoint": endpoint, "response": body})

    def _save_response_image(self, body: dict[str, Any], output_dir: Path) -> Path | None:
        if body.get("image_base64"):
            output_format = body.get("output_format", "png")
            image_path = output_dir / f"candidate.{output_format}"
            image_path.write_bytes(base64.b64decode(body["image_base64"]))
            return image_path
        if body.get("image_path"):
            return Path(body["image_path"])
        return None
