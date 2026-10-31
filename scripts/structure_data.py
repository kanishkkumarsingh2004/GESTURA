"""Restructure data/raw/ into a clean per-class layout.

Walks every image under data/raw/, derives a gesture class name from the
gesture folder (the `NN_name` leaf anywhere in the path, e.g. `07_ok`,
`01_palm`, or a flat class dir like `fist`), normalizes it to uppercase,
merges duplicates, caps at 1000 images per class, and copies into
data/raw/<CLASS>/.

After reviewing output, remove the old nested directories
(multimodhandgestrec, MultiModHandGestRec) and merged small flat dirs.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

RAW = Path("data/raw")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}
MAX_PER_CLASS = 1000

# Session / modality / split container folders to ignore.
CONTAINER_NAMES = {
    "train", "test", "val", "validation",
    "train_pose", "test_pose", "test_gesture",
    "near-infrared", "skeletal", "rgb", "depth",
}

# Map raw gesture tokens to clean canonical class names.
CLASS_ALIASES = {
    "palm": "PALM",
    "palm_m": "PALM_M",
    "palm_u": "PALM_U",
    "index": "INDEX",
    "index_left": "INDEX_LEFT",
    "index_right": "INDEX_RIGHT",
    "l": "INDEX_LEFT",
    "fist": "FIST",
    "fist_moved": "FIST",
    "ok": "OK",
    "thumb-up": "THUMBS_UP",
    "thumb_down": "THUMBS_DOWN",
    "thumbs-down": "THUMBS_DOWN",
    "thumbs-up": "THUMBS_UP",
    "thumbs_down": "THUMBS_DOWN",
    "thumbs_up": "THUMBS_UP",
    "no-gesture": "NONE",
    "no_gesture": "NONE",
    "none": "NONE",
    "down": "DOWN",
    "up": "UP",
    "left": "LEFT",
    "right": "RIGHT",
    "two": "TWO",
    "three": "THREE",
    "four": "FOUR",
    "five": "FIVE",
    "c": "C",
    "hang": "HANG",
    "heavy": "HEAVY",
}


def canonical_name(raw: str) -> str:
    key = raw.strip().lower().replace(" ", "_").replace("-", "_")
    return CLASS_ALIASES.get(key, key.upper())


def find_gesture_in_path(image: Path, root: Path) -> str | None:
    """Walk up from image.parent to root, return gesture token from first
    folder matching NN_name (e.g. 07_ok) or a known flat class dir."""
    current = image.parent
    while current != root and current != current.parent:
        name = current.name
        # NN_name pattern: e.g. 07_ok, 01_palm
        m = re.match(r"^\d{1,2}_(.+)$", name)
        if m:
            return m.group(1)
        # Flat class dir: not a container, not a pure number/session id.
        if (
            name
            and name.lower() not in CONTAINER_NAMES
            and not re.match(r"^\d{1,2}$", name)
            and not name.startswith(".")
        ):
            return name
        current = current.parent
    return None


def iter_images(root: Path):
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            yield path


def restructure() -> dict[str, int]:
    collected: dict[str, list[Path]] = {}

    for image in iter_images(RAW):
        gesture = find_gesture_in_path(image, RAW)
        if gesture is None:
            continue
        cls = canonical_name(gesture)
        collected.setdefault(cls, []).append(image)

    counts: dict[str, int] = {}
    for cls, images in sorted(collected.items()):
        dest_dir = RAW / cls
        dest_dir.mkdir(parents=True, exist_ok=True)
        copied = 0
        for image in images:
            if copied >= MAX_PER_CLASS:
                break
            dst = dest_dir / image.name
            if dst.exists():
                stem = image.stem
                suffix = image.suffix
                i = 1
                while dst.exists():
                    dst = dest_dir / f"{stem}_{i}{suffix}"
                    i += 1
            try:
                shutil.copy2(image, dst)
                copied += 1
            except (OSError, shutil.SameFileError):
                continue
        counts[cls] = copied
        print(f"  {cls}: {copied} images")

    return counts


def main() -> int:
    if not RAW.exists():
        print(f"{RAW} not found", file=sys.stderr)
        return 1

    print(f"Restructuring images from {RAW} -> max {MAX_PER_CLASS}/class\n")
    counts = restructure()
    total = sum(counts.values())
    print(f"\nTotal: {total} images across {len(counts)} classes")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
