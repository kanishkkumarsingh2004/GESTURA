"""Unit tests for preprocessing."""

from __future__ import annotations

import numpy as np
import pytest

from utils.preprocessing import PreprocessingConfig, PreprocessingError, Preprocessor


def test_preprocessor_output_shape() -> None:
    preprocessor = Preprocessor(PreprocessingConfig(input_width=224, input_height=224))
    frame = np.zeros((100, 150, 3), dtype=np.uint8)
    tensor = preprocessor.preprocess(frame)
    assert tensor.shape == (1, 3, 224, 224)


def test_preprocessor_rejects_empty_frame() -> None:
    preprocessor = Preprocessor()
    with pytest.raises(PreprocessingError):
        preprocessor.preprocess(np.zeros((0, 0, 3), dtype=np.uint8))
