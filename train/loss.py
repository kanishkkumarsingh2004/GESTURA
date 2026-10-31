"""Configurable loss functions for training.

Initial choice: CrossEntropyLoss. Future support includes weighted cross-entropy
and focal loss.
"""

from __future__ import annotations

import torch
import torch.nn as nn


def build_loss(name: str = "cross_entropy", weight: list[float] | None = None) -> nn.Module:
    """Build a loss function by name.

    Args:
        name: Loss identifier (cross_entropy, weighted_cross_entropy, focal).
        weight: Optional per-class weights for weighted cross-entropy.

    Returns:
        A configured nn.Module loss function.
    """
    lowered = name.lower()
    if lowered in ("cross_entropy", "crossentropy", "ce"):
        weight_tensor = torch.tensor(weight, dtype=torch.float32) if weight is not None else None
        return nn.CrossEntropyLoss(weight=weight_tensor)
    if lowered in ("weighted_cross_entropy", "weightedce"):
        if weight is None:
            raise ValueError("weighted_cross_entropy requires per-class weights")
        weight_tensor = torch.tensor(weight, dtype=torch.float32)
        return nn.CrossEntropyLoss(weight=weight_tensor)
    raise ValueError(f"Unsupported loss function: {name}")
