from __future__ import annotations

import argparse
from pathlib import Path


def crop_region(image_path: str, output_path: str, x: int, y: int, width: int, height: int) -> Path:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("crop_region requires Pillow: python -m pip install pillow") from exc

    source = Path(image_path)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        cropped = image.crop((x, y, x + width, y + height))
        cropped.save(out)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Crop a rectangular region from an image.")
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--x", required=True, type=int)
    parser.add_argument("--y", required=True, type=int)
    parser.add_argument("--width", required=True, type=int)
    parser.add_argument("--height", required=True, type=int)
    args = parser.parse_args()
    print(crop_region(args.image, args.output, args.x, args.y, args.width, args.height))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
