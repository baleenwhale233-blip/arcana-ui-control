from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from providers import ProviderError, create_provider, load_provider_config, resolve_provider_name


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a controlled UI image iteration.")
    parser.add_argument("--request", required=True, help="Path to generation request JSON.")
    parser.add_argument("--provider", help="Override provider name.")
    args = parser.parse_args()

    request_path = Path(args.request)
    if not request_path.is_absolute():
        request_path = (Path.cwd() / request_path).resolve()

    request = load_json(request_path)
    config = load_provider_config(PROJECT_ROOT)
    provider_name, provider_source = resolve_provider_name(args.provider, request, config)

    output_dir = resolve_output_dir(request.get("output_dir"))
    output_dir.mkdir(parents=True, exist_ok=True)

    prompt = compile_prompt(request, provider_name)
    prompt_path = output_dir / "image_prompt.md"
    prompt_path.write_text(prompt, encoding="utf-8")
    shutil.copyfile(request_path, output_dir / "generation_request.json")

    result: dict[str, Any]
    actual_provider = provider_name
    fallback_reason = None

    try:
        result = run_provider(actual_provider, request, config, prompt, output_dir, request_path)
    except ProviderError as exc:
        if provider_source in {"config", "fallback"} and actual_provider == "openai":
            fallback_reason = str(exc)
            actual_provider = "manual"
            print(f"OpenAI default is unavailable; falling back to manual. Reason: {fallback_reason}")
            result = run_provider(actual_provider, request, config, prompt, output_dir, request_path)
        else:
            write_metadata(
                output_dir,
                request,
                provider_name,
                provider_source,
                None,
                error=str(exc),
            )
            print(f"Provider failed: {exc}")
            return 2

    audit_path = write_audit_if_possible(request, result, output_dir, request_path)
    write_metadata(
        output_dir,
        request,
        actual_provider,
        provider_source,
        result,
        fallback_reason=fallback_reason,
        audit_path=str(audit_path) if audit_path else None,
    )

    print(f"Output directory: {output_dir}")
    print(f"Prompt: {prompt_path}")
    if result.get("image_path"):
        print(f"Image: {result['image_path']}")
    if result.get("metadata", {}).get("handoff_path"):
        print(f"Handoff: {result['metadata']['handoff_path']}")
    print(f"Metadata: {output_dir / 'generation_metadata.json'}")
    return 0


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Request file does not exist: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def resolve_output_dir(value: Any) -> Path:
    if value:
        path = Path(str(value))
        return path if path.is_absolute() else PROJECT_ROOT / path
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return PROJECT_ROOT / "runs" / f"iteration-{timestamp}"


def compile_prompt(request: dict[str, Any], provider_name: str) -> str:
    template_path = PROJECT_ROOT / "templates" / "image_prompt.md"
    template = template_path.read_text(encoding="utf-8")
    context = {
        "mode": request.get("mode", "module_repair"),
        "screen_name": request.get("screen_name", "Unnamed Screen"),
        "provider": provider_name,
        "goal": request.get("goal", "Generate a controlled UI image iteration."),
        "target_module": render_value(request.get("target_module", "No target module provided.")),
        "change_ticket": render_value(request.get("change_ticket", "No change ticket provided.")),
        "design_dna": render_value(request.get("design_dna", "No design DNA provided.")),
        "locked_regions": render_value(request.get("locked_regions", "No locked regions provided.")),
        "output_requirements": render_value(request.get("output_requirements", "Save one candidate image.")),
    }
    for key, value in context.items():
        template = template.replace("{{" + key + "}}", str(value))
    return template


def render_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2, ensure_ascii=False)
    return str(value)


def run_provider(
    provider_name: str,
    request: dict[str, Any],
    config: dict[str, Any],
    prompt: str,
    output_dir: Path,
    request_path: Path,
) -> dict[str, Any]:
    provider = create_provider(provider_name, config)
    options = request.get("options") or {}
    base_image = resolve_input_path(request.get("base_image"), request_path)
    mask = resolve_input_path(request.get("mask"), request_path)
    region = request.get("region") or (request.get("target_module") or {}).get("bounds")

    if base_image:
        return provider.edit_image(base_image, prompt, output_dir, mask=mask, region=region, options=options)
    return provider.generate_image(prompt, output_dir, options=options)


def resolve_input_path(value: Any, request_path: Path) -> str | None:
    if not value:
        return None
    path = Path(str(value))
    if path.is_absolute():
        return str(path)

    request_relative = (request_path.parent / path).resolve()
    if request_relative.exists():
        return str(request_relative)
    return str((PROJECT_ROOT / path).resolve())


def write_audit_if_possible(
    request: dict[str, Any],
    result: dict[str, Any],
    output_dir: Path,
    request_path: Path,
) -> Path | None:
    audit_path = output_dir / "regression_audit.md"
    anchor = resolve_input_path(request.get("anchor_image"), request_path)
    image_path = result.get("image_path")

    if not anchor:
        audit_path.write_text(
            "# Regression Audit\n\nStatus: skipped\nReason: no anchor image was provided.\n",
            encoding="utf-8",
        )
        return audit_path

    if not image_path or not Path(str(image_path)).exists():
        audit_path.write_text(
            "\n".join(
                [
                    "# Regression Audit",
                    "",
                    "Status: pending",
                    f"Anchor image: {anchor}",
                    "Candidate image: not available yet",
                    "",
                    "Add the generated image to this run directory, then rerun comparison if needed.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return audit_path

    try:
        from compare_images import compare_images

        summary = compare_images(anchor, str(image_path), output_dir)
        audit_path.write_text(
            "\n".join(
                [
                    "# Regression Audit",
                    "",
                    "Status: generated",
                    f"Anchor image: {anchor}",
                    f"Candidate image: {image_path}",
                    "",
                    "## Simple Comparison",
                    "",
                    json.dumps(summary, indent=2, ensure_ascii=False),
                    "",
                ]
            ),
            encoding="utf-8",
        )
    except Exception as exc:
        audit_path.write_text(
            f"# Regression Audit\n\nStatus: comparison_failed\nReason: {exc}\n",
            encoding="utf-8",
        )
    return audit_path


def write_metadata(
    output_dir: Path,
    request: dict[str, Any],
    provider_name: str,
    provider_source: str,
    result: dict[str, Any] | None,
    error: str | None = None,
    fallback_reason: str | None = None,
    audit_path: str | None = None,
) -> None:
    metadata = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": request.get("mode"),
        "provider": provider_name,
        "provider_source": provider_source,
        "fallback_reason": fallback_reason,
        "result": result,
        "audit_path": audit_path,
        "error": error,
    }
    (output_dir / "generation_metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
