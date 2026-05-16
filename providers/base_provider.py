from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ProviderError(RuntimeError):
    """Raised when an image provider cannot complete a request."""


class ImageProvider(ABC):
    """Small provider interface used by generation scripts."""

    name = "base"

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        self.settings = settings or {}

    @abstractmethod
    def generate_image(
        self,
        prompt: str,
        output_dir: str | Path,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate an image from a text prompt."""

    @abstractmethod
    def edit_image(
        self,
        base_image: str | Path,
        prompt: str,
        output_dir: str | Path,
        mask: str | Path | None = None,
        region: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Edit an existing image, optionally constrained by mask or region."""

    def ensure_output_dir(self, output_dir: str | Path) -> Path:
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def result(
        self,
        image_path: str | Path | None,
        mode: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "image_path": str(image_path) if image_path else None,
            "provider": self.name,
            "mode": mode,
            "metadata": metadata or {},
        }
