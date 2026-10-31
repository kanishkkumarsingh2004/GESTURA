"""Dataset utilities and group-based splitter for the India-first gesture contribution pipeline.

Ensures that:
1. Frames from the same contribution/video are NEVER split across train/val/test
   (strictly zero temporal data leakage).
2. Preserves regional and dialectal metadata (Country -> Region -> State -> Variety).
3. Distinguishes regional varieties so identical gesture names across different communities
   are never conflated without explicit validation.
4. Supports single-frame spatial CNN models (VGG16) and temporal sequential models
   (CNN+LSTM, Video Transformers).
"""

from __future__ import annotations

import csv
import json
import random
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from server.india_geo_config import COUNTRY_NAME, to_slug


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
    category: str
    gesture_type: str  # "static" | "dynamic" | "unknown"
    duration_seconds: float
    fps: float
    country: str = COUNTRY_NAME
    region: str = "UNKNOWN"
    state: str = "UNKNOWN"
    district_city: Optional[str] = None
    sign_language_type: str = "Indian Sign Language (ISL)"
    variety_name: Optional[str] = None
    sign_language: Optional[str] = None
    frames: List[ContributedFrame] = field(default_factory=list)

    @property
    def qualified_label(self) -> str:
        """Regional qualified label preventing cross-community gesture conflation."""
        parts = [self.gesture_name]
        if self.region and self.region != "UNKNOWN":
            parts.append(to_slug(self.region))
        if self.variety_name:
            parts.append(to_slug(self.variety_name))
        return "__".join(parts)

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
        stratify_by_variety: bool = True,
    ) -> Dict[str, List[ContributedGestureSample]]:
        """Stratify-split contributions while strictly grouping by video ID.

        If stratify_by_variety is True, samples are stratified by (gesture_name, region, variety),
        ensuring regional variants are kept distinct.
        """
        rng = random.Random(self.seed)

        by_class: Dict[str, List[ContributedGestureSample]] = {}
        for s in samples:
            key = s.qualified_label if stratify_by_variety else s.gesture_name
            by_class.setdefault(key, []).append(s)

        splits: Dict[str, List[ContributedGestureSample]] = {
            "train": [],
            "validation": [],
            "test": [],
        }

        for _class_key, class_samples in sorted(by_class.items()):
            shuffled = list(class_samples)
            rng.shuffle(shuffled)
            n = len(shuffled)

            if n == 1:
                splits["train"].extend(shuffled)
            elif n == 2:
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
    """Exports approved India contribution data to single-frame datasets and sequence manifests."""

    def __init__(self, contributions_root: Path | str = "data/contributions/india") -> None:
        self.contributions_root = Path(contributions_root).resolve()
        self.approved_dir = self.contributions_root / "approved"

    def load_approved_samples(self) -> List[ContributedGestureSample]:
        """Scan approved regional contributions and load active samples."""
        samples: List[ContributedGestureSample] = []
        if not self.approved_dir.is_dir():
            return samples

        # Recursively search for metadata.json under approved/ (handles region/state/cid hierarchy)
        for meta_file in sorted(self.approved_dir.rglob("metadata.json")):
            cdir = meta_file.parent
            frames_file = cdir / "frames" / "frames_metadata.json"
            if not frames_file.is_file():
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
                    category=meta.get("category", "General"),
                    gesture_type=meta.get("gesture_type", "dynamic"),
                    duration_seconds=meta.get("video_duration_seconds", 0.0),
                    fps=meta.get("video_fps", 25.0),
                    country=meta.get("country", COUNTRY_NAME),
                    region=meta.get("region", "UNKNOWN"),
                    state=meta.get("state", "UNKNOWN"),
                    district_city=meta.get("district_city"),
                    sign_language_type=meta.get("sign_language_type", "Indian Sign Language (ISL)"),
                    variety_name=meta.get("variety_name"),
                    sign_language=meta.get("sign_language", "Indian Sign Language (ISL)"),
                    frames=frames,
                )
            )

        return samples

    def export_image_folders(
        self,
        samples: List[ContributedGestureSample],
        dest_root: Path | str,
        use_thumbnails: bool = False,
        preserve_regional_folders: bool = False,
    ) -> Dict[str, int]:
        """Copy active frames into class folders.

        If preserve_regional_folders is True:
            dest_root/<REGION>/<STATE>/<GESTURE_NAME>/<cid>_<fid>.jpg
        Else:
            dest_root/<GESTURE_NAME>/<cid>_<fid>.jpg
        """
        dest_root = Path(dest_root).resolve()
        dest_root.mkdir(parents=True, exist_ok=True)
        counts: Dict[str, int] = {}

        for sample in samples:
            if preserve_regional_folders:
                class_dir = dest_root / to_slug(sample.region) / to_slug(sample.state) / sample.gesture_name
            else:
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
        """Write train.csv, validation.csv, test.csv preserving India geographic metadata."""
        out_dir = Path(output_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        if class_mapping is None:
            all_classes = sorted({s.gesture_name for split in split_samples.values() for s in split})
            class_mapping = {name: idx for idx, name in enumerate(all_classes)}

        for split_name, samples in split_samples.items():
            csv_path = out_dir / f"{split_name}.csv"
            with open(csv_path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow([
                    "image_path",
                    "class_id",
                    "class_name",
                    "country",
                    "region",
                    "state",
                    "district_city",
                    "sign_language_type",
                    "variety_name",
                ])
                for s in samples:
                    cid = class_mapping.get(s.gesture_name, 0)
                    for f in s.active_frames:
                        img_path = f.thumb_path if use_thumbnails and f.thumb_path.is_file() else f.file_path
                        writer.writerow([
                            str(img_path.resolve()),
                            cid,
                            s.gesture_name,
                            s.country,
                            s.region,
                            s.state,
                            s.district_city or "",
                            s.sign_language_type,
                            s.variety_name or "",
                        ])

    def export_sequence_manifest(
        self,
        split_samples: Dict[str, List[ContributedGestureSample]],
        output_path: Path | str,
        as_json: bool = True,
    ) -> None:
        """Export sequence manifest with geographic metadata and temporal ordering."""
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
                        "qualified_label": s.qualified_label,
                        "country": s.country,
                        "region": s.region,
                        "state": s.state,
                        "district_city": s.district_city,
                        "sign_language_type": s.sign_language_type,
                        "variety_name": s.variety_name,
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
                    "qualified_label",
                    "country",
                    "region",
                    "state",
                    "district_city",
                    "sign_language_type",
                    "variety_name",
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
                                s.qualified_label,
                                s.country,
                                s.region,
                                s.state,
                                s.district_city or "",
                                s.sign_language_type,
                                s.variety_name or "",
                                s.gesture_type,
                                split_name,
                                f.frame_id,
                                f.frame_index,
                                f.timestamp_ms,
                                str(f.file_path.resolve()),
                                str(f.thumb_path.resolve()),
                            ])
