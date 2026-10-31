"""Safe model checkpoint loading and validation.

Resolves checkpoint paths, loads metadata, validates architecture compatibility,
loads model parameters using safe deserialization, and moves the model to the
selected device.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import torch

from .architecture import build_model
from .classifier import ModelConfig, ModelMetadata, build_model_config


class CheckpointError(Exception):
    """Raised when a checkpoint is missing, invalid, or incompatible."""


def resolve_checkpoint_path(checkpoint: str | Path | None) -> Path:
    """Resolve a checkpoint path, raising if it does not exist."""
    if checkpoint is None:
        raise CheckpointError("No checkpoint path provided")
    path = Path(checkpoint)
    if not path.exists():
        raise CheckpointError(f"Checkpoint not found: {path}")
    return path


def load_checkpoint_metadata(checkpoint_path: str | Path) -> dict[str, Any]:
    """Load sidecar JSON metadata next to a checkpoint, if present."""
    path = Path(checkpoint_path)
    metadata_path = path.with_suffix(".json")
    if not metadata_path.exists():
        return {}
    with open(metadata_path, "r", encoding="utf-8") as handle:
        metadata: dict[str, Any] = json.load(handle)
    return metadata


def load_model(
    config: ModelConfig,
    device: torch.device | str | None = None,
) -> tuple[torch.nn.Module, dict[str, Any]]:
    """Load a model from checkpoint using safe deserialization.

    Args:
        config: Model configuration containing architecture and class mapping.
        device: Target device for the model.

    Returns:
        A tuple of (model, metadata).

    Raises:
        CheckpointError: If the checkpoint is missing or incompatible.
    """
    if config.num_classes <= 0:
        raise CheckpointError("ModelConfig must define a positive num_classes")

    model = build_model(
        architecture=config.architecture,
        num_classes=config.num_classes,
        pretrained=False,
        device=device,
    )

    checkpoint_path = resolve_checkpoint_path(config.checkpoint)

    try:
        state_dict = torch.load(
            checkpoint_path,
            map_location=device or "cpu",
            weights_only=True,
        )
    except Exception as exc:  # noqa: BLE001 - surface as CheckpointError
        raise CheckpointError(f"Failed to load checkpoint {checkpoint_path}: {exc}") from exc

    metadata = load_checkpoint_metadata(checkpoint_path)

    if metadata:
        _validate_metadata_compatibility(config, metadata)

    try:
        model.load_state_dict(state_dict, strict=True)
    except RuntimeError as exc:
        raise CheckpointError(
            f"Checkpoint state dict incompatible with {config.architecture}: {exc}"
        ) from exc

    model.eval()
    return model, metadata


def _validate_metadata_compatibility(config: ModelConfig, metadata: dict[str, Any]) -> None:
    """Reject incompatible checkpoint metadata rather than loading silently."""
    arch = metadata.get("architecture")
    if arch is not None and arch != config.architecture:
        raise CheckpointError(
            f"Checkpoint architecture '{arch}' does not match config '{config.architecture}'"
        )

    meta_classes = metadata.get("num_classes")
    if meta_classes is not None and meta_classes != config.num_classes:
        raise CheckpointError(
            f"Checkpoint num_classes {meta_classes} does not match config {config.num_classes}"
        )

    meta_mapping = metadata.get("class_mapping")
    if meta_mapping is not None and dict(meta_mapping) != config.class_mapping:
        raise CheckpointError("Checkpoint class mapping does not match config class_mapping")


def load_for_inference(
    config_path: str | Path = "config.yaml",
    checkpoint: str | Path | None = None,
    device: torch.device | str | None = None,
) -> tuple[torch.nn.Module, ModelMetadata]:
    """Convenience loader returning a model ready for inference and its metadata."""
    config = build_model_config(config_path, checkpoint=checkpoint)
    model, raw_metadata = load_model(config, device=device)
    metadata = ModelMetadata.from_dict(raw_metadata) if raw_metadata else ModelMetadata(
        model_name="gesture_classifier",
        architecture=config.architecture,
        num_classes=config.num_classes,
        input_size=[config.input_width, config.input_height],
        class_mapping=config.class_mapping,
        preprocessing=config.preprocessing,
        checkpoint=str(config.checkpoint) if config.checkpoint else None,
    )
    return model, metadata
