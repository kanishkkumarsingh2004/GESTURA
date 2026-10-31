"""Dataset utilities and group-based splitter for community contributed gestures.

Ensures that:
1. Frames from the same contribution/video are NEVER split across train/val/test
   (strictly zero temporal data leakage).
2. Supports single-frame spatial CNN models (VGG16) via standard image directories and CSV splits.
3. Supports sequential models (CNN+LSTM, Video Transformers) via ordered sequence manifests
   with video IDs, frame indices, and millisecond timestamps.
"""

from __future__ import annotations

import csv
import json
import random
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ContributedFrame:
    frame_id: str
    frame_index: int
    timestamp_ms: float
    file_path: Path
    thumb_path: Path
    sharpness_score: float
    is_blurry: bool
    is_duplicate: bool
    is_dark: bool
    status: str  # "active" | "removed"


@dataclass
class ContributedGestureSample:
    contribution_id: str
    gesture_name: str
    meaning: str
    sign_language: str
    category: str
    gesture_type: str  # "static" | "dynamic" | "unknown"
    duration_seconds: float
    fps: float
    frames: List[ContributedFrame] = field(default_factory=list)

    @property
    def active_frames(self) -> List[ContributedFrame]:
        return [f for f in self.frames if f.status == "active"]


class GroupedContributionSplitter:
    """Partitions contributed gesture samples into train, validation, and test splits.

    Crucially, splitting operates at the *contribution/video* unit, ensuring
    all frames from a single video recording remain in exactly one partition.
    """

    def __init__(
        self,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        seed: int = 42,
    ) -> None:
        total = train_ratio + val_ratio + test_ratio
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Split ratios must sum to 1.0 (got {total})")
        self.train_ratio = train_ratio / total
        self.val_ratio = val_ratio / total
        self.test_ratio = test_ratio / total
        self.seed = seed

    def split_samples(
        self,
        samples: List[ContributedGestureSample],
    ) -> Dict[str, List[ContributedGestureSample]]:
        """Stratify-split contributions by gesture_name (at video level)."""
        rng = random.Random(self.seed)

        # Group contributions by gesture_name
        by_class: Dict[str, List[ContributedGestureSample]] = {}
        for s in samples:
            by_class.setdefault(s.gesture_name, []).append(s)

        splits: Dict[str, List[ContributedGestureSample]] = {
            "train": [],
            "validation": [],
            "test": [],
        }

        for gesture_name, class_samples in sorted(by_class.items()):
            shuffled = list(class_samples)
            rng.shuffle(shuffled)
            n = len(shuffled)

            if n == 1:
                # If only 1 sample exists, assign to train
                splits["train"].extend(shuffled)
            elif n == 2:
                # 1 to train, 1 to validation
                splits["train"].append(shuffled[0])
                splits["validation"].append(shuffled[1])
            else:
                n_train = max(1, int(round(self.train_ratio * n)))
                n_val = max(1, int(round(self.val_ratio * n)))
                if n_train + n_val >= n:
                    n_train = max(1, n - 2)
                    n_val = 1
                n_test = n - (n_train + n_val)
                if n_test <= 0:
                    n_test = 1
                    if n_train > 1:
                        n_train -= 1

                train_items = shuffled[:n_train]
                val_items = shuffled[n_train : n_train + n_val]
                test_items = shuffled[n_train + n_val :]

                splits["train"].extend(train_items)
                splits["validation"].extend(val_items)
                splits["test"].extend(test_items)

        return splits


class ContributionDatasetExporter:
    """Exports approved contribution data to single-frame datasets and sequence manifests."""

    def __init__(self, contributions_root: Path | str = "data/contributions") -> None:
        self.contributions_root = Path(contributions_root).resolve()
        self.approved_dir = self.contributions_root / "approved"

    def load_approved_samples(self) -> List[ContributedGestureSample]:
        """Scan approved contributions directory and load active samples."""
        samples: List[ContributedGestureSample] = []
        if not self.approved_dir.is_dir():
            return samples

        for cdir in sorted(self.approved_dir.iterdir()):
            meta_file = cdir / "metadata.json"
            frames_file = cdir / "frames" / "frames_metadata.json"
            if not meta_file.is_file() or not frames_file.is_file():
                continue

            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
            with open(frames_file, "r", encoding="utf-8") as f:
                raw_frames = json.load(f)

            if meta.get("status") != "approved":
                continue

            frames: List[ContributedFrame] = []
            for rf in raw_frames:
                frame_path = cdir / "frames" / rf["filename"]
                thumb_path = cdir / "frames" / rf["thumb_filename"]
                frames.append(
                    ContributedFrame(
                        frame_id=rf["frame_id"],
                        frame_index=rf["frame_index"],
                        timestamp_ms=rf["timestamp_ms"],
                        file_path=frame_path,
                        thumb_path=thumb_path,
                        sharpness_score=rf.get("sharpness_score", 0.0),
                        is_blurry=rf.get("is_blurry", False),
                        is_duplicate=rf.get("is_duplicate", False),
                        is_dark=rf.get("is_dark", False),
                        status=rf.get("status", "active"),
                    )
                )

            samples.append(
                ContributedGestureSample(
                    contribution_id=meta["contribution_id"],
                    gesture_name=meta.get("gesture_name", "UNKNOWN").upper(),
                    meaning=meta.get("meaning", ""),
                    sign_language=meta.get("sign_language", "UNKNOWN"),
                    category=meta.get("category", "General"),
                    gesture_type=meta.get("gesture_type", "dynamic"),
                    duration_seconds=meta.get("video_duration_seconds", 0.0),
                    fps=meta.get("video_fps", 25.0),
                    frames=frames,
                )
            )

        return samples

    def export_image_folders(
        self,
        samples: List[ContributedGestureSample],
        dest_root: Path | str,
        use_thumbnails: bool = False,
    ) -> Dict[str, int]:
        """Copy active frames into class folders: dest_root/<GESTURE_NAME>/<cid>_<fid>.jpg.

        Returns mapping of gesture_name -> count of exported images.
        """
        dest_root = Path(dest_root).resolve()
        dest_root.mkdir(parents=True, exist_ok=True)
        counts: Dict[str, int] = {}

        for sample in samples:
            class_dir = dest_root / sample.gesture_name
            class_dir.mkdir(parents=True, exist_ok=True)
            for frame in sample.active_frames:
                src = frame.thumb_path if use_thumbnails and frame.thumb_path.is_file() else frame.file_path
                if not src.is_file():
                    continue
                dst = class_dir / f"{sample.contribution_id}_{frame.frame_id}.jpg"
                if not dst.exists():
                    shutil.copy2(src, dst)
                counts[sample.gesture_name] = counts.get(sample.gesture_name, 0) + 1

        return counts

    def export_splits_csv(
        self,
        split_samples: Dict[str, List[ContributedGestureSample]],
        output_dir: Path | str,
        class_mapping: Optional[Dict[str, int]] = None,
        use_thumbnails: bool = False,
    ) -> None:
        """Write train.csv, validation.csv, test.csv in data/splits/ format:
        image_path,class_id,class_name
        """
        out_dir = Path(output_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        # Derive class_mapping if not provided
        if class_mapping is None:
            all_classes = sorted({s.gesture_name for split in split_samples.values() for s in split})
            class_mapping = {name: idx for idx, name in enumerate(all_classes)}

        for split_name, samples in split_samples.items():
            csv_path = out_dir / f"{split_name}.csv"
            with open(csv_path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["image_path", "class_id", "class_name"])
                for s in samples:
                    cid = class_mapping.get(s.gesture_name, 0)
                    for f in s.active_frames:
                        img_path = f.thumb_path if use_thumbnails and f.thumb_path.is_file() else f.file_path
                        writer.writerow([str(img_path.resolve()), cid, s.gesture_name])

    def export_sequence_manifest(
        self,
        split_samples: Dict[str, List[ContributedGestureSample]],
        output_path: Path | str,
        as_json: bool = True,
    ) -> None:
        """Export sequence manifest with temporal ordering for sequential models (CNN+LSTM/Transformers)."""
        out_path = Path(output_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if as_json:
            manifest = []
            for split_name, samples in split_samples.items():
                for s in samples:
                    frames_sorted = sorted(s.active_frames, key=lambda x: x.frame_index)
                    manifest.append({
                        "contribution_id": s.contribution_id,
                        "gesture_name": s.gesture_name,
                        "sign_language": s.sign_language,
                        "category": s.category,
                        "gesture_type": s.gesture_type,
                        "split": split_name,
                        "duration_seconds": s.duration_seconds,
                        "fps": s.fps,
                        "frame_count": len(frames_sorted),
                        "frames": [
                            {
                                "frame_id": f.frame_id,
                                "frame_index": f.frame_index,
                                "timestamp_ms": f.timestamp_ms,
                                "image_path": str(f.file_path.resolve()),
                                "thumb_path": str(f.thumb_path.resolve()),
                                "sharpness_score": f.sharpness_score,
                            }
                            for f in frames_sorted
                        ],
                    })
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
        else:
            with open(out_path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow([
                    "contribution_id",
                    "gesture_name",
                    "sign_language",
                    "gesture_type",
                    "split",
                    "frame_id",
                    "frame_index",
                    "timestamp_ms",
                    "image_path",
                    "thumb_path",
                ])
                for split_name, samples in split_samples.items():
                    for s in samples:
                        frames_sorted = sorted(s.active_frames, key=lambda x: x.frame_index)
                        for f in frames_sorted:
                            writer.writerow([
                                s.contribution_id,
                                s.gesture_name,
                                s.sign_language,
                                s.gesture_type,
                                split_name,
                                f.frame_id,
                                f.frame_index,
                                f.timestamp_ms,
                                str(f.file_path.resolve()),
                                str(f.thumb_path.resolve()),
                            ])

