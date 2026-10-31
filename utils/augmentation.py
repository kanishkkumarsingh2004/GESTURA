"""Configurable data augmentation preserving gesture semantics.

Only transformations that do not change gesture meaning are applied.
Horizontal flipping is offered but disabled by default because some gestures
are direction-sensitive.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class AugmentationConfig:
    enabled: bool = True
    random_rotation: bool = True
    rotation_degrees: float = 10.0
    random_scaling: bool = True
    scale_range: tuple[float, float] = (0.9, 1.1)
    horizontal_flip: bool = False
    brightness: bool = True
    brightness_range: tuple[float, float] = (0.8, 1.2)
    contrast: bool = True
    contrast_range: tuple[float, float] = (0.8, 1.2)
    translation: bool = True
    translate_range: float = 0.05
    random_crop: bool = True
    crop_scale: float = 0.9


class Augmenter:
    """Applies random augmentations to an image while preserving gesture semantics."""

    def __init__(self, config: AugmentationConfig | None = None) -> None:
        self.config = config or AugmentationConfig()

    def augment(self, image: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        """Apply a random subset of enabled augmentations to an image."""
        if not self.config.enabled:
            return image

        augmented = image.copy()

        if self.config.random_rotation and rng.random() < 0.5:
            augmented = self._rotate(augmented, rng)

        if self.config.random_scaling and rng.random() < 0.5:
            augmented = self._scale(augmented, rng)

        if self.config.horizontal_flip and rng.random() < 0.5:
            augmented = cv2.flip(augmented, 1)

        if self.config.brightness and rng.random() < 0.5:
            augmented = self._adjust_brightness(augmented, rng)

        if self.config.contrast and rng.random() < 0.5:
            augmented = self._adjust_contrast(augmented, rng)

        if self.config.translation and rng.random() < 0.5:
            augmented = self._translate(augmented, rng)

        if self.config.random_crop and rng.random() < 0.5:
            augmented = self._random_crop(augmented, rng)

        return augmented

    def _rotate(self, image: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        angle = rng.uniform(-self.config.rotation_degrees, self.config.rotation_degrees)
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(image, matrix, (w, h), borderMode=cv2.BORDER_REFLECT)

    def _scale(self, image: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        scale = rng.uniform(*self.config.scale_range)
        h, w = image.shape[:2]
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        return cv2.resize(resized, (w, h), interpolation=cv2.INTER_LINEAR)

    def _adjust_brightness(self, image: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        factor = rng.uniform(*self.config.brightness_range)
        adjusted = np.clip(image.astype(np.float32) * factor, 0, 255).astype(np.uint8)
        return adjusted  # type: ignore[return-value, no-any-return]

    def _adjust_contrast(self, image: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        factor = rng.uniform(*self.config.contrast_range)
        mean = image.mean()
        adjusted = np.clip((image.astype(np.float32) - mean) * factor + mean, 0, 255).astype(np.uint8)
        return adjusted  # type: ignore[return-value, no-any-return]

    def _translate(self, image: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        h, w = image.shape[:2]
        tx = int(rng.uniform(-self.config.translate_range, self.config.translate_range) * w)
        ty = int(rng.uniform(-self.config.translate_range, self.config.translate_range) * h)
        matrix = np.float32([[1, 0, tx], [0, 1, ty]])  # type: ignore[arg-type]
        return cv2.warpAffine(image, matrix, (w, h), borderMode=cv2.BORDER_REFLECT)  # type: ignore[call-overload, return-value, no-any-return, arg-type]

    def _random_crop(self, image: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        h, w = image.shape[:2]
        crop_h = max(1, int(h * self.config.crop_scale))
        crop_w = max(1, int(w * self.config.crop_scale))
        top = int(rng.uniform(0, max(1, h - crop_h + 1)))
        left = int(rng.uniform(0, max(1, w - crop_w + 1)))
        cropped = image[top : top + crop_h, left : left + crop_w]
        return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)
