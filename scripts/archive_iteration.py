from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive an accepted or rejected iteration run.")
    parser.add_argument("--run", required=True, help="Run directory to archive.")
    parser.add_argument("--status", choices=["accepted", "rejected", "superseded"], default="accepted")
    parser.add_argument("--archive-root", default="archives")
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

    archive_record = {
        "archived_at": datetime.now(timezone.utc).isoformat(),
        "status": args.status,
        "source": str(run_path),
        "archive": str(destination),
    }
    (destination / "archive_record.json").write_text(
        json.dumps(archive_record, indent=2),
        encoding="utf-8",
    )

    print(f"Archived {run_path} -> {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
