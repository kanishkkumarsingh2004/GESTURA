"""Reproducibility utilities.

Sets and records random seeds for Python, NumPy and PyTorch to make training
runs as reproducible as the selected hardware and operations allow.
"""

from __future__ import annotations

import os
import random
from typing import Any

import numpy as np
import torch


def set_seed(seed: int = 42, deterministic: bool = False) -> None:
    """Set random seeds for reproducibility.

    Args:
        seed: Random seed value.
        deterministic: Request deterministic CUDA algorithms where available.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    if deterministic:
        torch.use_deterministic_algorithms(True)
        os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"


def capture_environment() -> dict[str, Any]:
    """Capture environment information for experiment reproducibility."""
    info: dict[str, Any] = {
        "seed": None,
        "python_version": None,
        "torch_version": None,
        "torchvision_version": None,
        "cuda_available": torch.cuda.is_available(),
    }

    try:
        import sys

        info["python_version"] = sys.version
    except Exception:  # noqa: BLE001
        pass

    try:
        import torchvision

        info["torchvision_version"] = torchvision.__version__
    except Exception:  # noqa: BLE001
        pass

    try:
        info["torch_version"] = torch.__version__
    except Exception:  # noqa: BLE001
        pass

    return info
