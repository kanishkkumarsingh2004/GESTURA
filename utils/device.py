"""Centralized device selection with CUDA detection and CPU fallback."""

from __future__ import annotations

import torch


def select_device(preference: str = "auto") -> torch.device:
    """Select the best available device.

    Args:
        preference: ``auto``, ``cuda``, or ``cpu``.

    Returns:
        A torch.device. Falls back to CPU when CUDA is requested but unavailable.
    """
    if preference == "cuda":
        if torch.cuda.is_available():
            return torch.device("cuda")
        return torch.device("cpu")

    if preference == "cpu":
        return torch.device("cpu")

    # auto
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def device_info() -> dict[str, str | bool]:
    """Return human-readable device information."""
    cuda_available = torch.cuda.is_available()
    return {
        "cuda_available": str(cuda_available),
        "device": str(select_device("auto")),
        "cuda_device_count": str(torch.cuda.device_count()) if cuda_available else "0",
    }
