"""Download gesture image data from Hugging Face Hub into data/raw/<CLASS>/.

Follows the datasets/transformers pattern. Caps images at MAX_PER_CLASS per class.
Works with any HF dataset repo that contains image folders (imagefolder format).

Usage:
    .venv/bin/python scripts/download_from_hf.py --repo-id <user>/<dataset> \
        --dest data/raw/ --max-per-class 1000

    # If the repo is a dataset with a specific config/data dir:
    .venv/bin/python scripts/download_from_hf.py --repo-id <user>/<dataset> \
        --data-dir data --dest data/raw/ --max-per-class 1000
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Optional

from datasets import Image as HFImage, load_dataset, get_dataset_config_names
from huggingface_hub import list_repo_files
from PIL import Image as PILImage

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}


def _iter_local_images(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            files.append(path)
    return sorted(files)


def copy_limited(src_root: Path, dest_root: Path, max_per_class: int) -> dict[str, int]:
    """Copy images from src/<CLASS>/ into dest/<CLASS>/ capped at max_per_class."""
    src_root = src_root.resolve()
    dest_root = dest_root.resolve()
    dest_root.mkdir(parents=True, exist_ok=True)

    counts: dict[str, int] = {}
    class_dirs = sorted(d for d in src_root.iterdir() if d.is_dir())

    if not class_dirs:
        class_dirs = [src_root]
        class_name = src_root.name
        copied = 0
        for image in _iter_images(src_root):
            if copied >= max_per_class:
                break
            dst = dest_root / class_name / image.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                shutil.copy2(image, dst)
            copied += 1
        counts[class_name] = copied
        return counts

    for class_dir in class_dirs:
        class_name = class_dir.name
        dst_class_dir = dest_root / class_name
        copied = 0
        for image in _iter_images(class_dir):
            if copied >= max_per_class:
                break
            dst = dst_class_dir / image.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                shutil.copy2(image, dst)
            copied += 1
        counts[class_name] = copied
    return counts


def _iter_images(root: Path) -> list[Path]:
    return _iter_local_images(root)


def download_from_hf(repo_id: str, data_dir: Optional[str], dest: Path,
                     max_per_class: int) -> dict[str, int]:
    """Download an HF dataset (imagefolder) and organize into data/raw/<CLASS>/."""
    dest = Path(dest).expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)

    # Inspect repo files to confirm it is a dataset with images, not a model.
    try:
        files = list_repo_files(repo_id, repo_type="dataset")
    except Exception as exc:  # noqa: BLE001 - surface as a clear error
        raise RuntimeError(
            f"Could not list files for dataset '{repo_id}'. "
            f"Is it a dataset (not a model) and is it public/accessible? Error: {exc}"
        ) from exc

    image_files = [f for f in files if Path(f).suffix.lower() in IMAGE_EXTENSIONS]
    if not image_files:
        raise RuntimeError(
            f"Dataset '{repo_id}' contains no image files. "
            f"This repo appears to be a model (weights/configs only), not an image dataset. "
            f"Files: {files[:10]}..."
        )

    print(f"Found {len(image_files)} image files in dataset '{repo_id}'")

    # Load the dataset (streaming to avoid downloading everything at once).
    load_kwargs: dict = {"path": repo_id, "streaming": True}
    if data_dir:
        load_kwargs["data_dir"] = data_dir

    try:
        ds = load_dataset(**load_kwargs)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to load dataset '{repo_id}': {exc}") from exc

    # datasets returns a dict of splits; pick the first split that has images.
    split_names = list(ds.keys()) if isinstance(ds, dict) else ["train"]
    print(f"Splits available: {split_names}")

    counts: dict[str, int] = {}
    total_copied = 0

    for split_name in split_names:
        split_ds = ds[split_name] if isinstance(ds, dict) else ds
        # Cast the image column to HF Image so we can read bytes.
        if "image" in split_ds.features:
            split_ds = split_ds.cast_column("image", HFImage())

        # Determine class label source.
        label_column = None
        for cand in ("label", "labels", "class", "class_label", "gesture"):
            if cand in split_ds.features:
                label_column = cand
                break

        for sample in split_ds:
            img = sample.get("image")
            if img is None:
                continue
            # HF Image in streaming gives a dict with 'bytes' or a path.
            if isinstance(img, dict):
                image_bytes = img.get("bytes")
                path = img.get("path")
            else:
                image_bytes = None
                path = img

            if image_bytes is None and path is None:
                continue

            # Class name from label column or folder structure.
            if label_column:
                raw_label = sample.get(label_column)
                class_name = str(raw_label)
            elif path:
                class_name = Path(path).parent.name
            else:
                class_name = "unknown"

            dst_class_dir = dest / class_name
            dst_class_dir.mkdir(parents=True, exist_ok=True)

            already = len(list(dst_class_dir.iterdir())) if dst_class_dir.exists() else 0
            if already >= max_per_class:
                continue

            # Determine destination filename.
            if path:
                stem = Path(path).name
            else:
                stem = f"{total_copied}.jpg"
            dst = dst_class_dir / stem

            copied = 0
            for _ in range(1):
                if copied >= max_per_class - already:
                    break
                try:
                    if image_bytes is not None:
                        from io import BytesIO
                        pil_img = PILImage.open(BytesIO(image_bytes)).convert("RGB")
                        pil_img.save(dst, format="JPEG")
                    elif path:
                        shutil.copy2(path, dst)
                    else:
                        continue
                except Exception:  # noqa: BLE001 - skip corrupt samples
                    continue
                copied += 1
                total_copied += 1

            counts[class_name] = counts.get(class_name, 0) + copied

            # Early exit if every class is full.
            if all(c >= max_per_class for c in counts.values()):
                break

    return counts


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download gesture image data from Hugging Face Hub into data/raw/<CLASS>/"
    )
    parser.add_argument(
        "--repo-id", required=True,
        help="HF dataset repo id (e.g. s17660101713/hagrid-subset). NOTE: a model repo has no images."
    )
    parser.add_argument(
        "--data-dir", default=None,
        help="Subdirectory inside the repo containing the image data (optional)."
    )
    parser.add_argument(
        "--dest", type=str, default="data/raw/",
        help="Destination root (data/raw/<CLASS>/)."
    )
    parser.add_argument(
        "--max-per-class", type=int, default=1000,
        help="Max images to download per class (default 1000)."
    )
    return parser.parse_args()


def main(argv: Optional[list[str]] = None) -> int:
    params = parse_arguments()
    try:
        counts = download_from_hf(
            repo_id=params.repo_id,
            data_dir=params.data_dir,
            dest=Path(params.dest),
            max_per_class=params.max_per_class,
        )
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    total = sum(counts.values())
    print(f"Downloaded {total} images across {len(counts)} classes -> {params.dest}")
    for name, cnt in sorted(counts.items()):
        print(f"  {name}: {cnt}")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
