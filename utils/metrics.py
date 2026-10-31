"""Evaluation metrics for model testing.

Computes accuracy, precision, recall, F1-score, per-class accuracy, confusion
matrix and inference latency using scikit-learn.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)


@dataclass
class EvaluationResult:
    accuracy: float
    precision: float
    recall: float
    f1: float
    per_class_accuracy: dict[str, float]
    confusion_matrix: list[list[int]]
    class_names: list[str]
    inference_latency_ms: float
    num_samples: int
    report: str = field(default_factory=str)


def evaluate_predictions(
    y_true: list[int] | np.ndarray,
    y_pred: list[int] | np.ndarray,
    class_names: list[str],
    inference_latency_ms: float = 0.0,
) -> EvaluationResult:
    """Compute evaluation metrics from true and predicted labels."""
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    accuracy = float(accuracy_score(y_true, y_pred))
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    per_class_p, per_class_r, per_class_f, per_class_support = precision_recall_fscore_support(
        y_true, y_pred, average=None, zero_division=0
    )

    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(class_names))))
    per_class_accuracy: dict[str, float] = {}
    for idx, name in enumerate(class_names):
        support = per_class_support[idx] if idx < len(per_class_support) else 0
        if support > 0:
            per_class_accuracy[name] = float(cm[idx, idx]) / float(support)
        else:
            per_class_accuracy[name] = 0.0

    report = classification_report(
        y_true, y_pred, target_names=class_names, zero_division=0
    )

    return EvaluationResult(
        accuracy=accuracy,
        precision=float(precision),
        recall=float(recall),
        f1=float(f1),
        per_class_accuracy=per_class_accuracy,
        confusion_matrix=cm.tolist(),
        class_names=list(class_names),
        inference_latency_ms=float(inference_latency_ms),
        num_samples=int(len(y_true)),
        report=report,
    )


def measure_inference_latency(predict_fn: Any, samples: list[Any], runs: int = 10) -> float:
    """Measure average inference latency in milliseconds over repeated runs."""
    latencies: list[float] = []
    for _ in range(runs):
        for sample in samples:
            start = time.perf_counter()
            predict_fn(sample)
            latencies.append((time.perf_counter() - start) * 1000.0)
    if not latencies:
        return 0.0
    return float(sum(latencies) / len(latencies))
