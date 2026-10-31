"""Training and evaluation visualizations.

Generates loss/accuracy curves and confusion matrix plots saved to outputs/plots.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np


def plot_training_history(
    history: dict[str, list[float]],
    output_path: str | Path = "outputs/plots/training_history.png",
) -> Path:
    """Plot training and validation loss/accuracy curves."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    if "train_loss" in history:
        axes[0].plot(history["train_loss"], label="Train Loss")
    if "val_loss" in history:
        axes[0].plot(history["val_loss"], label="Val Loss")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Loss")
    axes[0].set_title("Loss")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    if "train_acc" in history:
        axes[1].plot(history["train_acc"], label="Train Acc")
    if "val_acc" in history:
        axes[1].plot(history["val_acc"], label="Val Acc")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Accuracy")
    axes[1].set_title("Accuracy")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_confusion_matrix(
    confusion_matrix: list[list[int]],
    class_names: list[str],
    output_path: str | Path = "outputs/plots/confusion_matrix.png",
) -> Path:
    """Plot a normalized confusion matrix."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    cm = np.array(confusion_matrix, dtype=np.float64)
    row_sums = cm.sum(axis=1, keepdims=True)
    normalized = np.divide(cm, row_sums, out=np.zeros_like(cm), where=row_sums != 0)

    fig, ax = plt.subplots(figsize=(12, 10))
    im = ax.imshow(normalized, interpolation="nearest", cmap="Blues")
    ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    tick_count = len(class_names)
    ax.set_xticks(np.arange(tick_count))
    ax.set_yticks(np.arange(tick_count))
    ax.set_xticklabels(class_names, rotation=90, ha="center", fontsize=7)
    ax.set_yticklabels(class_names, fontsize=7)
    ax.set_ylabel("True label", fontsize=10)
    ax.set_xlabel("Predicted label", fontsize=10)
    ax.set_title("Confusion Matrix (normalized)", fontsize=12, pad=15)

    thresh = normalized.max() / 2.0 if normalized.size else 0.5
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                j,
                i,
                f"{normalized[i, j]:.2f}",
                ha="center",
                va="center",
                color="white" if normalized[i, j] > thresh else "black",
                fontsize=5,
            )

    plt.tight_layout(pad=2.0)
    plt.subplots_adjust(bottom=0.25, left=0.25)
    plt.savefig(path, dpi=150)
    plt.close(fig)
    return path
