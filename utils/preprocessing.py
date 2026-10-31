"""Image preprocessing pipeline shared by training and inference.

Converts camera frames and dataset images into model-compatible tensors using
the ImageNet normalization values defined in config.yaml.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np
import torch


@dataclass
class PreprocessingConfig:
    input_width: int = 224
    input_height: int = 224
    color_space: str = "RGB"
    interpolation: str = "bilinear"
    normalization: str = "imagenet"
    mean: tuple[float, float, float] = (0.485, 0.456, 0.406)
    std: tuple[float, float, float] = (0.229, 0.224, 0.225)


_INTERPOLATION_MAP = {
    "nearest": cv2.INTER_NEAREST,
    "bilinear": cv2.INTER_LINEAR,
    "bicubic": cv2.INTER_CUBIC,
    "area": cv2.INTER_AREA,
    "lanczos": cv2.INTER_LANCZOS4,
}


class PreprocessingError(Exception):
    """Raised when a frame cannot be preprocessed."""


class Preprocessor:
    """Applies consistent preprocessing to images for training and inference."""

    def __init__(self, config: PreprocessingConfig | None = None) -> None:
        self.config = config or PreprocessingConfig()

    def validate_frame(self, frame: np.ndarray) -> None:
        """Validate that a frame is non-empty and decodable."""
        if frame is None:
            raise PreprocessingError("Frame is None")
        if not isinstance(frame, np.ndarray):
            raise PreprocessingError("Frame is not a numpy array")
        if frame.size == 0:
            raise PreprocessingError("Frame is empty")
        if frame.ndim not in (2, 3):
            raise PreprocessingError(f"Frame has unsupported dimensions: {frame.ndim}")

    def to_rgb(self, frame: np.ndarray) -> np.ndarray:
        """Convert a BGR OpenCV frame to RGB."""
        if frame.ndim == 2:
            return cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def resize(self, frame: np.ndarray) -> np.ndarray:
        """Resize the frame to the configured input dimensions."""
        interpolation = _INTERPOLATION_MAP.get(self.config.interpolation, cv2.INTER_LINEAR)
        return cv2.resize(
            frame,
            (self.config.input_width, self.config.input_height),
            interpolation=interpolation,
        )

    def normalize(self, frame: np.ndarray) -> np.ndarray:
        """Normalize pixel values to [0, 1] then apply ImageNet mean/std."""
        normalized = frame.astype(np.float32) / 255.0
        mean = np.array(self.config.mean, dtype=np.float32)
        std = np.array(self.config.std, dtype=np.float32)
        return (normalized - mean) / std

    def to_tensor(self, frame: np.ndarray) -> torch.Tensor:
        """Convert an HWC numpy array to a CHW torch tensor."""
        tensor = torch.from_numpy(frame.transpose(2, 0, 1)).float()
        return tensor

    def preprocess(self, frame: np.ndarray) -> torch.Tensor:
        """Run the full preprocessing pipeline on a camera frame.

        Returns a 1xCxHxW torch tensor ready for model input.
        """
        self.validate_frame(frame)
        rgb = self.to_rgb(frame)
        resized = self.resize(rgb)
        normalized = self.normalize(resized)
        tensor = self.to_tensor(normalized)
        return tensor.unsqueeze(0)

    def preprocess_pil(self, image: Any) -> torch.Tensor:
        """Preprocess a PIL image into a model-ready tensor."""
        frame = np.array(image.convert("RGB"))
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return self.preprocess(frame)


def load_preprocessing_config(config_path: str = "config.yaml") -> PreprocessingConfig:
    """Load preprocessing configuration from config.yaml."""
    import yaml

    with open(config_path, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    prep = config.get("preprocessing", {})
    model_section = config.get("model", {})

    return PreprocessingConfig(
        input_width=int(prep.get("input_width", model_section.get("input_width", 224))),
        input_height=int(prep.get("input_height", model_section.get("input_height", 224))),
        color_space=str(prep.get("color_space", "RGB")),
        interpolation=str(prep.get("interpolation", "bilinear")),
        normalization=str(prep.get("normalization", "imagenet")),
        mean=tuple(prep.get("mean", [0.485, 0.456, 0.406])),
        std=tuple(prep.get("std", [0.229, 0.224, 0.225])),
    )
