from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive an accepted or rejected iteration run.")
    parser.add_argument("--run", required=True, help="Run directory to archive.")
    parser.add_argument("--status", choices=["accepted", "rejected", "superseded"], default="accepted")
    parser.add_argument("--archive-root", default="archives")
    parser.add_argument("--active-root", default="active")
    parser.add_argument("--candidate", help="Candidate image to promote when status is accepted.")
    parser.add_argument("--no-promote-active", action="store_true", help="Do not update active state.")
    parser.add_argument("--cleanup-run", action="store_true", help="Delete the original run after archiving.")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    run_path = Path(args.run)
    if not run_path.is_absolute():
        run_path = project_root / run_path
    if not run_path.exists() or not run_path.is_dir():
        print(f"Run directory does not exist: {run_path}")
        return 1

    archive_root = Path(args.archive_root)
    if not archive_root.is_absolute():
        archive_root = project_root / archive_root
    archive_root.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    destination = archive_root / f"{run_path.name}-{args.status}-{timestamp}"
    shutil.copytree(run_path, destination)

    metadata = load_json(run_path / "generation_metadata.json")
    candidate = resolve_candidate(args.candidate, run_path, metadata)

    archive_record = {
        "archived_at": datetime.now(timezone.utc).isoformat(),
        "status": args.status,
        "source": str(run_path),
        "archive": str(destination),
        "candidate": str(candidate) if candidate else None,
    }
    (destination / "archive_record.json").write_text(
        json.dumps(archive_record, indent=2),
        encoding="utf-8",
    )

    active_state_path = None
    if args.status == "accepted" and not args.no_promote_active:
        active_root = Path(args.active_root)
        if not active_root.is_absolute():
            active_root = project_root / active_root
        active_state_path = promote_active_state(run_path, destination, active_root, candidate, archive_record)

    if args.cleanup_run:
        shutil.rmtree(run_path)

    print(f"Archived {run_path} -> {destination}")
    if active_state_path:
        print(f"Updated active state: {active_state_path}")
    if args.cleanup_run:
        print(f"Cleaned run directory: {run_path}")
    return 0


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def resolve_candidate(candidate_arg: str | None, run_path: Path, metadata: dict[str, Any]) -> Path | None:
    if candidate_arg:
        candidate = Path(candidate_arg)
        if not candidate.is_absolute():
            candidate = (Path.cwd() / candidate).resolve()
        return candidate if candidate.exists() else None

    result = metadata.get("result") or {}
    image_path = result.get("image_path")
    if image_path and Path(image_path).exists():
        return Path(image_path)

    for name in ("candidate.png", "candidate.jpg", "candidate.jpeg", "candidate.webp"):
        candidate = run_path / name
        if candidate.exists():
            return candidate

    return None


def promote_active_state(
    run_path: Path,
    archive_path: Path,
    active_root: Path,
    candidate: Path | None,
    archive_record: dict[str, Any],
) -> Path:
    active_root.mkdir(parents=True, exist_ok=True)

    active_anchor = None
    if candidate:
        suffix = candidate.suffix or ".png"
        active_anchor = active_root / f"anchor{suffix}"
        shutil.copyfile(candidate, active_anchor)

    request_path = run_path / "generation_request.json"
    active_request = None
    if request_path.exists():
        active_request = active_root / "last_accepted_request.json"
        shutil.copyfile(request_path, active_request)

    state = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "status": archive_record["status"],
        "archive": archive_record["archive"],
        "source_run": archive_record["source"],
        "active_anchor": str(active_anchor) if active_anchor else None,
        "last_accepted_request": str(active_request) if active_request else None,
        "notes": "Keep active/ small. Full prompts, metadata, audits, and handoff files live in archives/.",
    }
    state_path = active_root / "active_state.json"
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state_path


if __name__ == "__main__":
    raise SystemExit(main())
