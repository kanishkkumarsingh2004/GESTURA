"""Learning-rate scheduling for training.

Initial options: ReduceLROnPlateau, CosineAnnealingLR.
"""

from __future__ import annotations

import torch


def build_scheduler(
    optimizer: torch.optim.Optimizer,
    name: str = "reduce_lr_on_plateau",
    patience: int = 8,
    factor: float = 0.5,
    t_max: int = 50,
) -> torch.optim.lr_scheduler.LRScheduler:
    """Build a learning-rate scheduler by name.

    Args:
        optimizer: The optimizer to schedule.
        name: Scheduler identifier (reduce_lr_on_plateau, cosine_annealing).
        patience: Patience for ReduceLROnPlateau.
        factor: LR reduction factor for ReduceLROnPlateau.
        t_max: Max epochs for CosineAnnealingLR.

    Returns:
        A configured LR scheduler.
    """
    lowered = name.lower()
    if lowered in ("reduce_lr_on_plateau", "reducelronplateau", "plateau"):
        return torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="max", factor=factor, patience=patience
        )
    if lowered in ("cosine_annealing", "cosineannealinglr", "cosine"):
        return torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=t_max)
    raise ValueError(f"Unsupported scheduler: {name}")
