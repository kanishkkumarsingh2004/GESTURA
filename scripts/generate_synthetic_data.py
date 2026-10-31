"""Generate synthetic gesture images for training/testing.

Creates simple, distinguishable synthetic hand-like shapes (different colors
and geometry) per gesture class under data/raw/<CLASS>/ and writes stratified
split manifests to data/splits/. This lets you run the full training pipeline
without downloading the multi-gigabyte HAGRID archives.

Usage:
    uv run --active python scripts/generate_synthetic_data.py \
        --count-per-class 100 \
        --dest data/raw/
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

import cv2
import numpy as np

CLASSES = [
    "HELLO", "YES", "NO", "THANK_YOU", "PLEASE", "STOP", "HELP",
    "GOOD", "BAD", "LOVE", "NONE",
]

IMAGE_SIZE = 224


def _hand_color(rng: np.random.Generator) -> tuple[int, int, int]:
    return (int(rng.integers(40, 200)), int(rng.integers(40, 200)), int(rng.integers(40, 200)))


def _draw_hello(frame: np.ndarray, rng: np.random.Generator) -> None:
    """Open palm, fingers spread."""
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2
    color = _hand_color(rng)
    # Palm
    cv2.ellipse(frame, (cx, cy + 20), (40, 70), 0, 0, 360, color, -1)
    # Fingers spread upward
    for i in range(5):
        fx = cx - 60 + i * 30
        cv2.ellipse(frame, (fx, cy - 60), (12, 45), 0, 0, 360, color, -1)


def _draw_yes(frame: np.ndarray, rng: np.random.Generator) -> None:
    """Fist with thumb up."""
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2
    color = _hand_color(rng)
    cv2.ellipse(frame, (cx, cy), (45, 55), 0, 0, 360, color, -1)
    cv2.ellipse(frame, (cx - 40, cy - 50), (16, 35), 0, 0, 360, color, -1)


def _draw_no(frame: np.ndarray, rng: np.random.Generator) -> None:
    """Two hands / crossed, or open hand sideways."""
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2
    color = _hand_color(rng)
    cv2.ellipse(frame, (cx, cy), (50, 40), 0, 0, 360, color, -1)
    cv2.line(frame, (cx - 55, cy - 45), (cx + 55, cy + 45), (0, 0, 0), 8)


def _draw_thank_you(frame: np.ndarray, rng: np.random.Generator) -> None:
    """Hand near chin, fingers together."""
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2
    color = _hand_color(rng)
    cv2.ellipse(frame, (cx - 20, cy - 30), (40, 50), 0, 0, 360, color, -1)
    cv2.rectangle(frame, (cx - 45, cy - 55), (cx + 5, cy - 5), color, -1)


def _draw_please(frame: np.ndarray, rng: np.random.Generator) -> None:
    """Hand on chest, flat."""
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2
    color = _hand_color(rng)
    cv2.ellipse(frame, (cx, cy), (55, 35), 0, 0, 360, color, -1)


def _draw_stop(frame: np.ndarray, rng: np.random.Generator) -> None:
    """Open palm facing forward."""
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2
    color = _hand_color(rng)
    cv2.ellipse(frame, (cx, cy), (45, 75), 0, 0, 360, color, -1)
    for i in range(5):
        fx = cx - 55 + i * 28
        cv2.ellipse(frame, (fx, cy - 70), (14, 50), 0, 0, 360, color, -1)


def _draw_help(frame: np.ndarray, rng: np.random.Generator) -> None:
    """One hand over another."""
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2
    color = _hand_color(rng)
    cv2.ellipse(frame, (cx, cy + 25), (50, 40), 0, 0, 360, color, -1)
    cv2.ellipse(frame, (cx, cy - 20), (40, 30), 0, 0, 360, color, -1)


def _draw_good(frame: np.ndarray, rng: np.random.Generator) -> None:
    """Thumbs up."""
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2
    color = _hand_color(rng)
    cv2.ellipse(frame, (cx, cy), (45, 55), 0, 0, 360, color, -1)
    cv2.ellipse(frame, (cx + 45, cy - 40), (18, 40), 0, 0, 360, color, -1)


def _draw_bad(frame: np.ndarray, rng: np.random.Generator) -> None:
    """Fist."""
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2
    color = _hand_color(rng)
    cv2.ellipse(frame, (cx, cy), (48, 48), 0, 0, 360, color, -1)


def _draw_love(frame: np.ndarray, rng: np.random.Generator) -> None:
    """Hand over heart."""
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2
    color = _hand_color(rng)
    cv2.ellipse(frame, (cx, cy + 10), (50, 60), 0, 0, 360, color, -1)
    cv2.ellipse(frame, (cx - 25, cy - 30), (18, 22), 0, 0, 360, (200, 40, 40), -1)
    cv2.ellipse(frame, (cx + 25, cy - 30), (18, 22), 0, 0, 360, (200, 40, 40), -1)


def _draw_none(frame: np.ndarray, rng: np.random.Generator) -> None:
    """Random abstract / no hand pattern."""
    h, w = frame.shape[:2]
    for _ in range(rng.integers(3, 8)):
        x = int(rng.integers(0, w))
        y = int(rng.integers(0, h))
        r = int(rng.integers(5, 40))
        color = tuple(int(c) for c in rng.integers(0, 255, size=3))
        cv2.circle(frame, (x, y), r, color, -1)


_DRAWERS = {
    "HELLO": _draw_hello,
    "YES": _draw_yes,
    "NO": _draw_no,
    "THANK_YOU": _draw_thank_you,
    "PLEASE": _draw_please,
    "STOP": _draw_stop,
    "HELP": _draw_help,
    "GOOD": _draw_good,
    "BAD": _draw_bad,
    "LOVE": _draw_love,
    "NONE": _draw_none,
}


def generate_image(rng: np.random.Generator, cls: str) -> np.ndarray:
    """Generate one synthetic gesture image."""
    frame = np.zeros((IMAGE_SIZE, IMAGE_SIZE, 3), dtype=np.uint8)
    # Random background
    bg = tuple(int(c) for c in rng.integers(20, 80, size=3))
    frame[:] = bg
    drawer = _DRAWERS.get(cls, _draw_none)
    drawer(frame, rng)
    # Add slight noise / rotation for variety
    angle = float(rng.uniform(-15, 15))
    m = cv2.getRotationMatrix2D((IMAGE_SIZE // 2, IMAGE_SIZE // 2), angle, 1.0)
    frame = cv2.warpAffine(frame, m, (IMAGE_SIZE, IMAGE_SIZE), borderValue=bg)
    noise = rng.integers(0, 25, size=frame.shape, dtype=np.uint8)
    frame = cv2.add(frame, noise)
    return frame


def generate_dataset(dest: Path, count_per_class: int, seed: int = 42) -> None:
    """Generate synthetic images per class into dest/<CLASS>/."""
    dest = dest.resolve()
    rng = np.random.default_rng(seed)

    for cls in CLASSES:
        class_dir = dest / cls
        class_dir.mkdir(parents=True, exist_ok=True)
        existing = len(list(class_dir.glob("*.png")))
        needed = max(0, count_per_class - existing)
        for i in range(needed):
            img = generate_image(rng, cls)
            path = class_dir / f"{cls}_{existing + i:04d}.png"
            cv2.imwrite(str(path), img)
        print(f"{cls}: {existing + needed} images")


def write_splits(data_root: Path, seed: int = 42) -> None:
    """Write train/validation/test CSV manifests (70/15/15 stratified)."""
    import random

    splits_dir = data_root.parent / "splits"
    splits_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed)
    manifests = {"train": [], "validation": [], "test": []}

    class_dirs = sorted(d for d in data_root.iterdir() if d.is_dir())
    class_mapping = {d.name: idx for idx, d in enumerate(class_dirs)}

    for class_name, class_idx in class_mapping.items():
        images = sorted((data_root / class_name).glob("*.png"))
        images = [p for p in images if p.is_file()]
        rng.shuffle(images)
        n = len(images)
        n_train = int(0.70 * n)
        n_val = int(0.15 * n)
        for split_name, subset in (
            ("train", images[:n_train]),
            ("validation", images[n_train : n_train + n_val]),
            ("test", images[n_train + n_val :]),
        ):
            for image in subset:
                manifests[split_name].append((str(image.resolve()), class_idx, class_name))

    for split_name, rows in manifests.items():
        with open(splits_dir / f"{split_name}.csv", "w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["image_path", "class_id", "class_name"])
            writer.writerows(rows)
    print(f"Split manifests written to {splits_dir}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic gesture dataset")
    parser.add_argument(
        "-d",
        "--dest",
        type=str,
        default="data/raw/",
        help="Destination raw data folder (data/raw/<CLASS>/)",
    )
    parser.add_argument(
        "-c",
        "--count-per-class",
        type=int,
        default=100,
        help="Number of synthetic images to generate per class (default 100)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed",
    )
    parser.add_argument(
        "--no-splits",
        action="store_true",
        help="Skip generating split manifests",
    )
    return parser.parse_args()


def main(argv: list[str] | None = None) -> int:
    params = parse_arguments()
    dest = Path(params.dest).expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)

    generate_dataset(dest, params.count_per_class, seed=params.seed)
    total = sum(1 for _ in dest.rglob("*.png"))
    print(f"Generated {total} synthetic images across {len(CLASSES)} classes -> {dest}")

    if not params.no_splits:
        write_splits(dest, seed=params.seed)

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
