from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .agent_handoff_provider import AgentHandoffProvider
from .base_provider import ImageProvider, ProviderError
from .command_provider import CommandProvider
from .generic_http_provider import GenericHttpProvider
from .manual_provider import ManualProvider
from .openai_provider import OpenAIProvider


PROVIDER_CLASSES: dict[str, type[ImageProvider]] = {
    "openai": OpenAIProvider,
    "manual": ManualProvider,
    "agent_handoff": AgentHandoffProvider,
    "generic_http": GenericHttpProvider,
    "command": CommandProvider,
}


def load_provider_config(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root)
    local_path = root / "config" / "providers.local.json"
    example_path = root / "config" / "providers.example.json"
    path = local_path if local_path.exists() else example_path

    if not path.exists():
        return {"default_provider": "manual", "providers": {}}

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def resolve_provider_name(
    cli_provider: str | None,
    request: dict[str, Any],
    config: dict[str, Any],
) -> tuple[str, str]:
    if cli_provider:
        return cli_provider, "cli"
    if request.get("provider"):
        return str(request["provider"]), "request"
    if config.get("default_provider"):
        return str(config["default_provider"]), "config"
    return "manual", "fallback"


def create_provider(name: str, config: dict[str, Any]) -> ImageProvider:
    normalized = name.strip().lower()
    provider_class = PROVIDER_CLASSES.get(normalized)
    if not provider_class:
        known = ", ".join(sorted(PROVIDER_CLASSES))
        raise ProviderError(f"Unknown provider '{name}'. Known providers: {known}.")

    settings = (config.get("providers") or {}).get(normalized, {})
    return provider_class(settings=settings)
