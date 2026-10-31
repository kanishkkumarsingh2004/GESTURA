"""CLI script to export approved user contributions into model training formats.

Features:
- Grouped leak-free splitting: keeps frames from the same video in the same split.
- Exports to class image folders: <dest>/<GESTURE_NAME>/<cid>_<fid>.jpg.
- Exports stratified CSV splits: image_path, class_id, class_name.
- Exports sequence manifest (JSON) for temporal / sequential models (CNN+LSTM / Transformers).
- Optional merge with existing data/splits/.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# Ensure project root is in sys.path when executed directly as a script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.contribution_dataset import (
    ContributionDatasetExporter,
    GroupedContributionSplitter,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export approved gesture contributions for ML model training"
    )
    parser.add_argument(
        "--contributions-dir",
        type=str,
        default="data/contributions/india",
        help="Path to contributions root directory (containing approved/)",
    )
    parser.add_argument(
        "--dest-raw",
        type=str,
        default="data/contributions/india/dataset",
        help="Destination directory for class image folders (<dest>/<GESTURE>/)",
    )
    parser.add_argument(
        "--splits-dir",
        type=str,
        default="data/splits/contributions/india",
        help="Output directory for train.csv, validation.csv, test.csv",
    )
    parser.add_argument(
        "--manifest-out",
        type=str,
        default="data/contributions/india/sequence_manifest.json",
        help="Path for sequential model JSON manifest",
    )
    parser.add_argument(
        "--preserve-regional-folders",
        action="store_true",
        help="Organize image folders hierarchically by region and state (<dest>/<region>/<state>/<gesture>/)",
    )
    parser.add_argument(
        "--no-stratify-variety",
        action="store_true",
        help="Merge identical gesture names across different varieties instead of stratifying separately",
    )
    parser.add_argument(
        "--split-ratios",
        nargs=3,
        type=float,
        default=[0.70, 0.15, 0.15],
        help="Train, Validation, Test ratios (e.g. 0.70 0.15 0.15)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic split assignment",
    )
    parser.add_argument(
        "--use-thumbnails",
        action="store_true",
        help="Export pre-resized 224x224 thumbnails instead of original resolution frames",
    )
    parser.add_argument(
        "--merge-with-existing-splits",
        type=str,
        default=None,
        help="Path to directory with existing train.csv/val.csv/test.csv to merge with",
    )
    return parser.parse_args()


def merge_splits(
    existing_dir: Path,
    new_dir: Path,
    merged_output_dir: Path,
) -> None:
    merged_output_dir.mkdir(parents=True, exist_ok=True)
    for split_name in ["train", "validation", "test"]:
        existing_file = existing_dir / f"{split_name}.csv"
        new_file = new_dir / f"{split_name}.csv"
        out_file = merged_output_dir / f"{split_name}.csv"

        seen_paths: set[str] = set()
        rows: list[list[str]] = []

        if existing_file.is_file():
            with open(existing_file, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                for row in reader:
                    if row and row[0] not in seen_paths:
                        seen_paths.add(row[0])
                        rows.append(row)

        if new_file.is_file():
            with open(new_file, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                _ = next(reader, None)
                for row in reader:
                    if row and row[0] not in seen_paths:
                        seen_paths.add(row[0])
                        rows.append(row)

        with open(out_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["image_path", "class_id", "class_name"])
            writer.writerows(rows)
        print(f"Merged {split_name}.csv: {len(rows)} samples total")


def main() -> int:
    args = parse_args()
    exporter = ContributionDatasetExporter(contributions_root=args.contributions_dir)
    samples = exporter.load_approved_samples()

    if not samples:
        print(f"No approved contributions found in {args.contributions_dir}/approved.")
        return 0

    print(f"Loaded {len(samples)} approved contribution(s).")
    total_active_frames = sum(len(s.active_frames) for s in samples)
    print(f"Total active frames across approved contributions: {total_active_frames}")

    # 1. Group-based split
    stratify_by_variety = not getattr(args, "no_stratify_variety", False)
    splitter = GroupedContributionSplitter(
        train_ratio=args.split_ratios[0],
        val_ratio=args.split_ratios[1],
        test_ratio=args.split_ratios[2],
        seed=args.seed,
    )
    splits = splitter.split_samples(
        samples, stratify_by_variety=stratify_by_variety
    )

    for s_name, s_list in splits.items():
        n_frames = sum(len(x.active_frames) for x in s_list)
        print(f"Split [{s_name}]: {len(s_list)} video(s), {n_frames} active frame(s)")

    # 2. Export image folders
    counts = exporter.export_image_folders(
        samples=samples,
        dest_root=args.dest_raw,
        use_thumbnails=args.use_thumbnails,
        preserve_regional_folders=getattr(args, "preserve_regional_folders", False),
    )
    print(f"Exported images to {args.dest_raw}: {counts}")

    # 3. Export split CSVs
    exporter.export_splits_csv(
        split_samples=splits,
        output_dir=args.splits_dir,
        use_thumbnails=args.use_thumbnails,
    )
    print(f"Exported split CSVs to {args.splits_dir}")

    # 4. Export sequence manifest
    exporter.export_sequence_manifest(
        split_samples=splits,
        output_path=args.manifest_out,
        as_json=True,
    )
    print(f"Exported sequence manifest to {args.manifest_out}")

    # 5. Optional merge
    if args.merge_with_existing_splits:
        existing_dir = Path(args.merge_with_existing_splits)
        merge_splits(
            existing_dir=existing_dir,
            new_dir=Path(args.splits_dir),
            merged_output_dir=existing_dir,
        )

    print("Contribution export completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

