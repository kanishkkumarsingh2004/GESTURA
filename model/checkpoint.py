"""Checkpoint management for training.

Saves model weights, optimizer state, scheduler state, epoch number, best
validation accuracy, class mapping, model configuration and preprocessing
configuration. Preserves the best validation checkpoint independently from the
latest checkpoint.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch


@dataclass
class CheckpointBundle:
    model_state_dict: dict[str, Any]
    optimizer_state_dict: dict[str, Any] | None
    scheduler_state_dict: dict[str, Any] | None
    epoch: int
    best_val_accuracy: float
    class_mapping: dict[str, int]
    model_config: dict[str, Any]
    preprocessing_config: dict[str, Any]


def save_checkpoint(
    bundle: CheckpointBundle,
    output_dir: str | Path,
    filename: str = "checkpoint.pth",
    is_best: bool = False,
) -> Path:
    """Save a training checkpoint.

    Args:
        bundle: Training state to persist.
        output_dir: Directory to write the checkpoint into.
        filename: Checkpoint filename.
        is_best: Whether this is the best validation checkpoint.

    Returns:
        Path to the saved checkpoint file.
    """
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    payload = {
        "epoch": bundle.epoch,
        "best_val_accuracy": bundle.best_val_accuracy,
        "class_mapping": bundle.class_mapping,
        "model_config": bundle.model_config,
        "preprocessing_config": bundle.preprocessing_config,
        "model_state_dict": bundle.model_state_dict,
        "optimizer_state_dict": bundle.optimizer_state_dict,
        "scheduler_state_dict": bundle.scheduler_state_dict,
    }

    checkpoint_path = directory / filename
    torch.save(payload, checkpoint_path)

    metadata = {
        "epoch": bundle.epoch,
        "best_val_accuracy": bundle.best_val_accuracy,
        "class_mapping": bundle.class_mapping,
        "model_config": bundle.model_config,
        "preprocessing_config": bundle.preprocessing_config,
    }
    metadata_path = checkpoint_path.with_suffix(".json")
    with open(metadata_path, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    if is_best:
        best_path = directory / "best_model.pt"
        shutil.copy2(checkpoint_path, best_path)
        best_meta = directory / "best_model.json"
        shutil.copy2(metadata_path, best_meta)

    return checkpoint_path


def load_checkpoint(
    checkpoint_path: str | Path,
    map_location: str | torch.device = "cpu",
) -> CheckpointBundle:
    """Load a checkpoint bundle using safe deserialization."""
    path = Path(checkpoint_path)
    if not path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {path}")

    payload = torch.load(path, map_location=map_location, weights_only=True)

    return CheckpointBundle(
        model_state_dict=payload["model_state_dict"],
        optimizer_state_dict=payload.get("optimizer_state_dict"),
        scheduler_state_dict=payload.get("scheduler_state_dict"),
        epoch=int(payload.get("epoch", 0)),
        best_val_accuracy=float(payload.get("best_val_accuracy", 0.0)),
        class_mapping=payload.get("class_mapping", {}),
        model_config=payload.get("model_config", {}),
        preprocessing_config=payload.get("preprocessing_config", {}),
    )


def load_best_checkpoint(output_dir: str | Path) -> CheckpointBundle:
    """Load the best validation checkpoint from a run directory."""
    directory = Path(output_dir)
    best_path = directory / "best_model.pt"
    if not best_path.exists():
        raise FileNotFoundError(f"Best checkpoint not found: {best_path}")
    return load_checkpoint(best_path)
