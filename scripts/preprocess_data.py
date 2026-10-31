"""Preprocessing utility.

Reads raw images from data/raw/<CLASS>/ and writes processed copies to
data/processed/<CLASS>/ without modifying the originals.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2

from utils.preprocessing import Preprocessor, load_preprocessing_config


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preprocess raw gesture images")
    parser.add_argument("--raw-root", default="data/raw", help="Raw dataset root")
    parser.add_argument("--processed-root", default="data/processed", help="Processed output root")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    raw_root = Path(args.raw_root)
    processed_root = Path(args.processed_root)
    if not raw_root.exists():
        print(f"Raw root not found: {raw_root}")
        return 1

    prep_config = load_preprocessing_config(args.config)
    preprocessor = Preprocessor(prep_config)

    processed_root.mkdir(parents=True, exist_ok=True)
    total = 0
    for class_dir in sorted(raw_root.iterdir()):
        if not class_dir.is_dir():
            continue
        out_class_dir = processed_root / class_dir.name
        out_class_dir.mkdir(parents=True, exist_ok=True)
        for image_path in sorted(class_dir.iterdir()):
            if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
                continue
            frame = cv2.imread(str(image_path))
            if frame is None:
                print(f"Skipping unreadable image: {image_path}")
                continue
            tensor = preprocessor.preprocess(frame)
            # Save a processed preview (denormalized) for inspection.
            import numpy as np
            arr = tensor.squeeze(0).numpy().transpose(1, 2, 0)
            mean = np.array(prep_config.mean)
            std = np.array(prep_config.std)
            arr = np.clip((arr * std + mean) * 255, 0, 255).astype("uint8")
            arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(out_class_dir / image_path.name), arr)
            total += 1

    print(f"Preprocessed {total} images into {processed_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
