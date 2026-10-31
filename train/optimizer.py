"""Optimizer construction for training.

Initial choice: AdamW.
"""

from __future__ import annotations

from typing import Iterable

import torch


def build_optimizer(
    model_parameters: Iterable[torch.nn.Parameter],
    name: str = "adamw",
    learning_rate: float = 0.0001,
    weight_decay: float = 0.0001,
) -> torch.optim.Optimizer:
    """Build an optimizer by name.

    Args:
        model_parameters: Iterable of model parameters to optimize.
        name: Optimizer identifier (adamw, adam, sgd).
        learning_rate: Learning rate.
        weight_decay: Weight decay (L2 regularization).

    Returns:
        A configured torch.optim.Optimizer.
    """
    lowered = name.lower()
    if lowered in ("adamw",):
        return torch.optim.AdamW(model_parameters, lr=learning_rate, weight_decay=weight_decay)
    if lowered in ("adam",):
        return torch.optim.Adam(model_parameters, lr=learning_rate, weight_decay=weight_decay)
    if lowered in ("sgd",):
        return torch.optim.SGD(model_parameters, lr=learning_rate, weight_decay=weight_decay, momentum=0.9)
    raise ValueError(f"Unsupported optimizer: {name}")
