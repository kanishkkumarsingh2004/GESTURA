"""Unit tests for augmentation."""

from __future__ import annotations

import numpy as np

from utils.augmentation import AugmentationConfig, Augmenter


def test_augmentation_returns_same_shape() -> None:
    rng = np.random.default_rng(42)
    augmenter = Augmenter(AugmentationConfig(horizontal_flip=False))
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    out = augmenter.augment(image, rng)
    assert out.shape == image.shape
