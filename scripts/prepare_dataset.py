"""Organize downloaded gesture images into the project data layout.

Reads extracted HAGRID class folders (or any folder of class subdirectories),
copies images into data/raw/<CLASS>/ (raw data is never overwritten), and
generates stratified train/validation/test split manifests under data/splits/.
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}


def iter_images(root: Path) -> list[Path]:
    """Return sorted image file paths under root."""
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            files.append(path)
    return sorted(files)


def organize(
    source: Path,
    dest: Path,
    class_mapping: dict[str, int] | None = None,
    max_images_per_class: int = 1000,
) -> dict[str, int]:
    """Copy images from source class folders into dest/<CLASS>/.

    Raw destination files are never overwritten. Returns the resolved class
    mapping (class name -> index).
    """
    source = source.resolve()
    dest = dest.resolve()
    dest.mkdir(parents=True, exist_ok=True)

    if class_mapping is None:
        class_dirs = sorted(d for d in source.iterdir() if d.is_dir())
        class_mapping = {d.name: idx for idx, d in enumerate(class_dirs)}

    total = 0
    for class_name, _class_idx in class_mapping.items():
        src_class_dir = source / class_name
        if not src_class_dir.is_dir():
            continue
        dst_class_dir = dest / class_name
        dst_class_dir.mkdir(parents=True, exist_ok=True)
        copied = 0
        for image in iter_images(src_class_dir):
            if copied >= max_images_per_class:
                break
            dst = dst_class_dir / image.name
            if not dst.exists():
                shutil.copy2(image, dst)
            copied += 1
            total += 1
    return class_mapping


def write_splits(
    data_root: Path,
    class_mapping: dict[str, int],
    seed: int = 42,
) -> None:
    """Write train/validation/test CSV manifests (70/15/15 stratified)."""
    import random

    splits_dir = data_root.parent / "splits"
    splits_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed)
    manifests: dict[str, list[tuple[str, int, str]]] = {
        "train": [],
        "validation": [],
        "test": [],
    }

    for class_name, class_idx in class_mapping.items():
        class_dir = data_root / class_name
        images = iter_images(class_dir)
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
                manifests[split_name].append(
                    (str(image.resolve()), class_idx, class_name)
                )

    for split_name, rows in manifests.items():
        with open(splits_dir / f"{split_name}.csv", "w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["image_path", "class_id", "class_name"])
            writer.writerows(rows)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare gesture dataset for training"
    )
    parser.add_argument(
        "-s",
        "--source",
        type=str,
        default="./hagrid/dataset/",
        help="Source folder containing extracted class subdirectories",
    )
    parser.add_argument(
        "-d",
        "--dest",
        type=str,
        default="data/raw/",
        help="Destination raw data folder (data/raw/<CLASS>/)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for split generation",
    )
    parser.add_argument(
        "--max-images-per-class",
        type=int,
        default=1000,
        help="Maximum number of images to copy per class (default 1000)",
    )
    parser.add_argument(
        "--no-splits",
        action="store_true",
        help="Skip generating split manifests",
    )
    return parser.parse_args()


def main(argv: list[str] | None = None) -> int:
    params = parse_arguments()
    source = Path(params.source).expanduser().resolve()
    dest = Path(params.dest).expanduser().resolve()

    if not source.exists():
        print(f"Source folder not found: {source}")
        return 1

    class_mapping = organize(
        source,
        dest,
        max_images_per_class=params.max_images_per_class,
    )
    print(f"Organized images into {dest} across {len(class_mapping)} classes")
    for name, idx in sorted(class_mapping.items(), key=lambda kv: kv[1]):
        print(f"  {idx}: {name}")

    if not params.no_splits:
        write_splits(dest, class_mapping, seed=params.seed)
        print(f"Split manifests written to {dest.parent / 'splits'}")

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
