"""Reusable training callbacks.

Early stopping, best checkpoint selection, training progress logging and
metric tracking.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("training")


class EarlyStopping:
    """Stops training when validation accuracy stops improving."""

    def __init__(self, patience: int = 8, min_delta: float = 0.0) -> None:
        self.patience = patience
        self.min_delta = min_delta
        self.best_accuracy: float | None = None
        self.counter = 0
        self.early_stop = False

    def step(self, val_accuracy: float) -> bool:
        """Record a validation accuracy and return True if training should stop."""
        if self.best_accuracy is None:
            self.best_accuracy = val_accuracy
            return False

        if val_accuracy > self.best_accuracy + self.min_delta:
            self.best_accuracy = val_accuracy
            self.counter = 0
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
                logger.info("Early stopping triggered at best accuracy %.4f", self.best_accuracy)
        return self.early_stop


class BestCheckpointTracker:
    """Tracks the best validation checkpoint seen during training."""

    def __init__(self) -> None:
        self.best_accuracy: float = 0.0
        self.best_epoch: int = 0
        self.is_best: bool = False

    def update(self, val_accuracy: float, epoch: int) -> bool:
        """Update best state if current accuracy improves. Returns True if new best."""
        if val_accuracy > self.best_accuracy:
            self.best_accuracy = val_accuracy
            self.best_epoch = epoch
            self.is_best = True
        else:
            self.is_best = False
        return self.is_best
