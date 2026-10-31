"""Download gesture datasets from Hugging Face, direct URLs, or HAGRID mirrors.

Supports:
  - Hugging Face Hub public datasets (no auth): --hf-repo --hf-file
  - Direct HTTP/HTTPS URLs: --url
  - HAGRID preset archives: --dataset --targets <gesture>

Downloaded archives are extracted and organized into data/raw/<CLASS>/ with a
configurable cap of images per class (--max-images-per-class).

Usage examples:
    # Download a Hugging Face gesture dataset file
    uv run --active python scripts/download_dataset.py \
        --hf-repo <user>/<dataset> --hf-file data.zip --dest data/raw/

    # Download a direct URL
    uv run --active python scripts/download_dataset.py \
        --url https://example.com/gestures.zip --dest data/raw/

    # Download HAGRID preset gestures (archives are ~40 GB each)
    uv run --active python scripts/download_dataset.py --dataset \
        --targets stop like peace --max-images-per-class 100
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
import zipfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CHUNK = 1024 * 1024
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}

# HAGRID preset URLs (SberCloud OBS). Each archive is tens of GB.
V2_URL = "https://rndml-team-cv.obs.ru-moscow-1.hc.sbercloud.ru/datasets/hagrid_v2/"
MAIN_URL = "https://rndml-team-cv.obs.ru-moscow-1.hc.sbercloud.ru/datasets/hagrid/hagrid_dataset_new_554800/"

HAGRID_URLS = {
    "call": f"{MAIN_URL}hagrid_dataset/call.zip",
    "dislike": f"{MAIN_URL}hagrid_dataset/dislike.zip",
    "fist": f"{MAIN_URL}hagrid_dataset/fist.zip",
    "four": f"{MAIN_URL}hagrid_dataset/four.zip",
    "like": f"{MAIN_URL}hagrid_dataset/like.zip",
    "mute": f"{MAIN_URL}hagrid_dataset/mute.zip",
    "ok": f"{MAIN_URL}hagrid_dataset/ok.zip",
    "one": f"{V2_URL}hagrid_v2_zip/one.zip",
    "palm": f"{MAIN_URL}hagrid_dataset/palm.zip",
    "peace_inverted": f"{MAIN_URL}hagrid_dataset/peace_inverted.zip",
    "peace": f"{MAIN_URL}hagrid_dataset/peace.zip",
    "rock": f"{V2_URL}hagrid_v2_zip/rock.zip",
    "stop_inverted": f"{MAIN_URL}hagrid_dataset/stop_inverted.zip",
    "stop": f"{MAIN_URL}hagrid_dataset/stop.zip",
    "three": f"{MAIN_URL}hagrid_dataset/three.zip",
    "three2": f"{MAIN_URL}hagrid_dataset/three2.zip",
    "two_up_inverted": f"{MAIN_URL}hagrid_dataset/two_up_inverted.zip",
    "two_up": f"{MAIN_URL}hagrid_dataset/two_up.zip",
    "grabbing": f"{V2_URL}hagrid_v2_zip/grabbing.zip",
    "grip": f"{V2_URL}hagrid_v2_zip/grip.zip",
    "holy": f"{V2_URL}hagrid_v2_zip/holy.zip",
    "point": f"{V2_URL}hagrid_v2_zip/point.zip",
    "three3": f"{V2_URL}hagrid_v2_zip/three3.zip",
    "timeout": f"{V2_URL}hagrid_v2_zip/timeout.zip",
    "xsign": f"{V2_URL}hagrid_v2_zip/xsign.zip",
    "hand_heart": f"{V2_URL}hagrid_v2_zip/hand_heart.zip",
    "hands_heart2": f"{V2_URL}hagrid_v2_zip/hands_heart2.zip",
    "little_finger": f"{V2_URL}hagrid_v2_zip/little_finger.zip",
    "middle_finger": f"{V2_URL}hagrid_v2_zip/middle_finger.zip",
    "take_picture": f"{V2_URL}hagrid_v2_zip/take_picture.zip",
    "three_gun": f"{V2_URL}hagrid_v2_zip/three_gun.zip",
    "thumb_index": f"{V2_URL}hagrid_v2_zip/thumb_index.zip",
    "thumb_index2": f"{V2_URL}hagrid_v2_zip/thumb_index2.zip",
    "no_gesture": f"{V2_URL}hagrid_v2_zip/no_gesture.zip",
    "annotations": f"{V2_URL}annotations_with_landmarks/annotations.zip",
}

HAGRID_GESTURES = tuple(sorted(HAGRID_URLS.keys() - {"annotations"}))


def _iter_images(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            files.append(path)
    return sorted(files)


def download_file(url: str, destination: Path) -> None:
    """Download a URL to destination using stdlib urllib (no shell injection)."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    req = Request(url, headers={"User-Agent": "gesture-recognition-downloader/1.0"})
    try:
        with urlopen(req, timeout=60) as response, open(destination, "wb") as out:
            shutil.copyfileobj(response, out, length=CHUNK)
    except (HTTPError, URLError, OSError) as exc:
        raise RuntimeError(f"Failed to download {url}: {exc}") from exc


def extract_zip(archive: Path, output_dir: Path) -> None:
    """Extract a zip archive with path-traversal protection."""
    output_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        for member in zf.infolist():
            member_path = (output_dir / member.filename).resolve()
            if output_dir.resolve() not in member_path.parents:
                raise RuntimeError(f"Unsafe path in archive: {member.filename}")
        zf.extractall(output_dir)


def copy_limited(src_root: Path, dest_root: Path, max_per_class: int) -> dict[str, int]:
    """Copy images from extracted class folders into dest/<CLASS>/ capped at max_per_class.

    Returns per-class counts copied.
    """
    src_root = src_root.resolve()
    dest_root = dest_root.resolve()
    dest_root.mkdir(parents=True, exist_ok=True)

    counts: dict[str, int] = {}
    class_dirs = sorted(d for d in src_root.iterdir() if d.is_dir())

    # If no class subdirectories, treat the whole root as one class named by folder.
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


def write_splits(data_root: Path, seed: int = 42) -> None:
    """Write train/validation/test CSV manifests (70/15/15 stratified)."""
    import random

    splits_dir = data_root.parent / "splits"
    splits_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed)
    manifests = {"train": [], "validation": [], "test": []}

    class_mapping = {
        d.name: idx for idx, d in enumerate(sorted(d for d in data_root.iterdir() if d.is_dir()))
    }

    for class_name, class_idx in class_mapping.items():
        images = [p for p in _iter_images(data_root / class_name) if p.is_file()]
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


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download and prepare gesture datasets")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--hf-repo", help="Hugging Face dataset repo id (e.g. user/dataset)")
    group.add_argument("--url", help="Direct HTTP/HTTPS URL to a dataset zip/archive")
    group.add_argument(
        "--dataset",
        action="store_true",
        help="Use HAGRID preset gesture archives",
    )
    parser.add_argument("--hf-file", help="File name inside the HF repo to download")
    parser.add_argument(
        "-t",
        "--targets",
        nargs="+",
        default=list(HAGRID_GESTURES),
        help="HAGRID gesture targets (only with --dataset)",
    )
    parser.add_argument(
        "-p",
        "--save_path",
        type=str,
        default="./hagrid/dataset/",
        help="Save path for downloaded archives",
    )
    parser.add_argument(
        "-x",
        "--extract",
        action="store_true",
        help="Extract downloaded zip archives",
    )
    parser.add_argument(
        "-d",
        "--dest",
        type=str,
        default="data/raw/",
        help="Destination organized folder (data/raw/<CLASS>/)",
    )
    parser.add_argument(
        "--max-images-per-class",
        type=int,
        default=1000,
        help="Max images to copy per class (default 1000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for split generation",
    )
    parser.add_argument(
        "--no-splits",
        action="store_true",
        help="Skip generating split manifests",
    )
    return parser.parse_args()


def main(argv: list[str] | None = None) -> int:
    params = parse_arguments()
    save_path = Path(params.save_path).expanduser().resolve()
    dest = Path(params.dest).expanduser().resolve()

    downloaded_archives: list[Path] = []

    if params.hf_repo:
        if not params.hf_file:
            print("--hf-file is required with --hf-repo")
            return 1
        url = f"https://huggingface.co/datasets/{params.hf_repo}/resolve/main/{params.hf_file}"
        dest_archive = save_path / Path(params.hf_file).name
        print(f"Downloading HF {params.hf_repo}/{params.hf_file} -> {dest_archive}")
        download_file(url, dest_archive)
        downloaded_archives.append(dest_archive)

    elif params.url:
        dest_archive = save_path / Path(params.url).name
        print(f"Downloading {params.url} -> {dest_archive}")
        download_file(params.url, dest_archive)
        downloaded_archives.append(dest_archive)

    elif params.dataset:
        targets = params.targets
        for target in targets:
            if target not in HAGRID_URLS:
                print(f"Unknown target: {target}. Available: {', '.join(sorted(HAGRID_URLS))}")
                return 1
        for target in targets:
            dest_archive = save_path / f"{target}.zip"
            print(f"Downloading HAGRID {target} -> {dest_archive}")
            download_file(HAGRID_URLS[target], dest_archive)
            downloaded_archives.append(dest_archive)

    # Extract archives
    for archive in downloaded_archives:
        if params.extract and archive.suffix.lower() == ".zip":
            extract_to = save_path / archive.stem
            print(f"Extracting {archive} -> {extract_to}")
            extract_zip(archive, extract_to)

    # Organize into data/raw/<CLASS>/
    # Source is either the extracted folders or save_path itself.
    source_root = save_path
    # If extraction happened, look for extracted subdirectories containing images.
    if params.extract:
        extracted_dirs = [d for d in save_path.iterdir() if d.is_dir() and _iter_images(d)]
        if extracted_dirs:
            source_root = save_path  # organize from all extracted class folders

    counts = copy_limited(source_root, dest, params.max_images_per_class)
    total = sum(counts.values())
    print(f"Organized {total} images across {len(counts)} classes -> {dest}")
    for name, cnt in sorted(counts.items()):
        print(f"  {name}: {cnt}")

    if not params.no_splits:
        write_splits(dest, seed=params.seed)
        print(f"Split manifests written to {dest.parent / 'splits'}")

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
