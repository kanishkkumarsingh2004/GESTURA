"""Inference engine exposing a clean interface to the application.

All predictions run in evaluation mode under torch.inference_mode().
Returns structured PredictionResult dataclasses.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch

from .classifier import ModelConfig, build_model_config
from .model_loader import load_for_inference


@dataclass
class PredictionResult:
    class_id: int
    class_name: str
    confidence: float
    probabilities: dict[str, float]
    inference_time_ms: float


class InferenceEngine:
    """Encapsulates a loaded PyTorch model and provides prediction.

    The model is loaded once and reused across frames. Thread-safe for
    read-only inference when accessed from multiple camera callbacks.
    """

    def __init__(
        self,
        config_path: str | Path = "config.yaml",
        checkpoint: str | Path | None = None,
        device: str | None = None,
    ) -> None:
        self.config_path = config_path
        self.checkpoint = checkpoint
        self.device = device
        self._model: torch.nn.Module | None = None
        self._metadata: Any = None
        self._config: ModelConfig | None = None
        self._class_names: list[str] = []
        self._loaded = False

    def load_model(self) -> None:
        """Load the model and configuration once."""

        if self.device is None:
            from utils.device import select_device

            self.device = str(select_device())

        self._model, self._metadata = load_for_inference(
            config_path=self.config_path,
            checkpoint=self.checkpoint,
            device=self.device,
        )
        self._config = build_model_config(self.config_path, checkpoint=self.checkpoint)
        self._class_names = self._config.class_names
        self._loaded = True

    def predict(self, image: np.ndarray) -> PredictionResult:
        """Run inference on a preprocessed image tensor or numpy array.

        Args:
            image: A CHW float tensor as numpy array, or HWC uint8 RGB array.
                If HWC uint8 is passed it is assumed already normalized to the
                model's expected input scale by the caller.

        Returns:
            A PredictionResult with class, confidence and probabilities.
        """
        if not self._loaded:
            self.load_model()

        if self._model is None or self._config is None:
            raise RuntimeError("InferenceEngine is not loaded")

        if image.ndim == 3 and image.shape[0] in (1, 3):
            tensor = torch.from_numpy(image.astype(np.float32)).unsqueeze(0)
        else:
            tensor = torch.from_numpy(image.astype(np.float32)).unsqueeze(0)

        device = torch.device(self.device or "cpu")
        tensor = tensor.to(device)

        start = time.perf_counter()
        with torch.inference_mode():
            logits = self._model(tensor)
            probs = torch.softmax(logits, dim=1)[0]
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        probs_np = probs.detach().cpu().numpy()
        class_id = int(probs_np.argmax())
        confidence = float(probs_np[class_id])

        probabilities = {
            name: float(probs_np[idx])
            for name, idx in self._config.class_mapping.items()
            if idx < len(probs_np)
        }

        return PredictionResult(
            class_id=class_id,
            class_name=self._class_names[class_id] if class_id < len(self._class_names) else str(class_id),
            confidence=confidence,
            probabilities=probabilities,
            inference_time_ms=elapsed_ms,
        )

    def get_model_info(self) -> dict[str, Any]:
        """Return model metadata and configuration summary."""
        if not self._loaded:
            self.load_model()
        return {
            "architecture": self._config.architecture if self._config else "unknown",
            "num_classes": self._config.num_classes if self._config else 0,
            "class_names": self._class_names,
            "input_size": [self._config.input_width, self._config.input_height] if self._config else [],
            "device": self.device,
            "loaded": self._loaded,
            "metadata": self._metadata.to_dict() if hasattr(self._metadata, "to_dict") else {},
        }

    def release(self) -> None:
        """Release the model reference."""
        self._model = None
        self._loaded = False
