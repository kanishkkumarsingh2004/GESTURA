"""Dataset handling for gesture recognition.

Provides a PyTorch Dataset over raw gesture images with label mapping,
transforms, invalid sample handling and dataset statistics. Raw images are
treated as immutable and are never overwritten by preprocessing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image
from torch.utils.data import Dataset


@dataclass
class DatasetStats:
    total_samples: int
    num_classes: int
    samples_per_class: dict[str, int]
    class_mapping: dict[str, int]
    split: str


class GestureDataset(Dataset):
    """PyTorch Dataset loading gesture images from class subdirectories.

    Directory layout:
        root/
            HELLO/
                img1.jpg
                ...
            YES/
                ...
            ...

    Args:
        root: Root directory containing class subdirectories.
        class_mapping: Optional explicit class-to-index mapping. If omitted,
            it is derived from sorted subdirectory names.
        transform: Optional callable transform applied to each image.
        validate: Whether to validate images at initialization.
    """

    def __init__(
        self,
        root: str | Path,
        class_mapping: dict[str, int] | None = None,
        transform: Any = None,
        validate: bool = True,
    ) -> None:
        self.root = Path(root)
        self.transform = transform
        self.samples: list[tuple[str, int]] = []
        self.class_mapping: dict[str, int] = {}

        if not self.root.exists():
            raise FileNotFoundError(f"Dataset root not found: {self.root}")

        if class_mapping is not None:
            self.class_mapping = dict(class_mapping)
        else:
            self._discover_classes()

        self._load_samples(validate)

    def _discover_classes(self) -> None:
        class_dirs = sorted(
            entry for entry in self.root.iterdir() if entry.is_dir()
        )
        self.class_mapping = {entry.name: idx for idx, entry in enumerate(class_dirs)}
        if not self.class_mapping:
            raise ValueError(f"No class directories found in {self.root}")

    def _load_samples(self, validate: bool) -> None:
        valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}
        for class_name, class_idx in self.class_mapping.items():
            class_dir = self.root / class_name
            if not class_dir.is_dir():
                continue
            for image_path in class_dir.iterdir():
                if image_path.suffix.lower() not in valid_extensions:
                    continue
                if validate and not self._is_valid_image(image_path):
                    continue
                self.samples.append((str(image_path), class_idx))

    @staticmethod
    def _is_valid_image(path: Path) -> bool:
        try:
            with Image.open(path) as image:
                image.verify()
            return True
        except Exception:  # noqa: BLE001 - invalid sample skipped
            return False

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[Any, int]:
        image_path, label = self.samples[idx]
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Failed to load image {image_path}: {exc}") from exc

        if self.transform is not None:
            image = self.transform(image)

        return image, label

    def stats(self, split: str = "unknown") -> DatasetStats:
        samples_per_class: dict[str, int] = {}
        for class_name, class_idx in self.class_mapping.items():
            count = sum(1 for _, lbl in self.samples if lbl == class_idx)
            samples_per_class[class_name] = count
        return DatasetStats(
            total_samples=len(self.samples),
            num_classes=len(self.class_mapping),
            samples_per_class=samples_per_class,
            class_mapping=dict(self.class_mapping),
            split=split,
        )


def load_class_mapping_from_root(root: str | Path) -> dict[str, int]:
    """Derive a stable class mapping from sorted subdirectory names."""
    root_path = Path(root)
    class_dirs = sorted(entry for entry in root_path.iterdir() if entry.is_dir())
    return {entry.name: idx for idx, entry in enumerate(class_dirs)}
