from __future__ import annotations

import argparse
from pathlib import Path


def make_sheet(anchor_image: str, candidate_image: str, output_path: str) -> Path:
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError("make_comparison_sheet requires Pillow: python -m pip install pillow") from exc

    anchor_path = Path(anchor_image)
    candidate_path = Path(candidate_image)
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(anchor_path).convert("RGB") as anchor, Image.open(candidate_path).convert("RGB") as candidate:
        height = 720
        anchor.thumbnail((720, height))
        candidate.thumbnail((720, height))
        width = anchor.width + candidate.width + 48
        sheet = Image.new("RGB", (width, height + 64), "white")
        sheet.paste(anchor, (16, 48))
        sheet.paste(candidate, (anchor.width + 32, 48))
        draw = ImageDraw.Draw(sheet)
        draw.text((16, 16), "Approved Anchor", fill=(0, 0, 0))
        draw.text((anchor.width + 32, 16), "Candidate", fill=(0, 0, 0))
        sheet.save(out_path)

    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a side-by-side comparison sheet.")
    parser.add_argument("--anchor", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(make_sheet(args.anchor, args.candidate, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
