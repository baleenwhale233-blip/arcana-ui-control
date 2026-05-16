from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def compare_images(anchor_image: str, candidate_image: str, output_dir: str | Path | None = None) -> dict[str, Any]:
    try:
        from PIL import Image, ImageChops, ImageStat
    except ImportError as exc:
        raise RuntimeError("compare_images requires Pillow: python -m pip install pillow") from exc

    anchor_path = Path(anchor_image)
    candidate_path = Path(candidate_image)
    if not anchor_path.exists():
        raise FileNotFoundError(f"Anchor image does not exist: {anchor_path}")
    if not candidate_path.exists():
        raise FileNotFoundError(f"Candidate image does not exist: {candidate_path}")

    with Image.open(anchor_path).convert("RGB") as anchor, Image.open(candidate_path).convert("RGB") as candidate:
        anchor_size = anchor.size
        candidate_size = candidate.size
        common_size = (256, 256)
        a = anchor.resize(common_size)
        c = candidate.resize(common_size)
        diff = ImageChops.difference(a, c)
        stat = ImageStat.Stat(diff)
        mean_diff = sum(stat.mean) / len(stat.mean)
        normalized = round(mean_diff / 255, 4)

    summary = {
        "anchor_image": str(anchor_path),
        "candidate_image": str(candidate_path),
        "anchor_size": anchor_size,
        "candidate_size": candidate_size,
        "mean_pixel_delta_0_to_1": normalized,
        "note": "This is a simple heuristic. Use human review for locked-region drift decisions.",
    }

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "comparison_summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two UI images with a simple pixel heuristic.")
    parser.add_argument("--anchor", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output-dir")
    args = parser.parse_args()

    print(json.dumps(compare_images(args.anchor, args.candidate, args.output_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
