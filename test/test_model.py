"""Unit tests for the model layer."""

from __future__ import annotations

import torch

from model.architecture import build_model, count_parameters


def test_build_model_returns_module() -> None:
    model = build_model("vgg16", num_classes=12, pretrained=False)
    assert isinstance(model, torch.nn.Module)


def test_model_output_shape() -> None:
    model = build_model("vgg16", num_classes=12, pretrained=False)
    model.eval()
    with torch.inference_mode():
        output = model(torch.randn(2, 3, 224, 224))
    assert output.shape == (2, 12)


def test_count_parameters_positive() -> None:
    model = build_model("vgg16", num_classes=12, pretrained=False)
    assert count_parameters(model) > 0


def test_num_classes_configurable() -> None:
    model = build_model("vgg16", num_classes=5, pretrained=False)
    model.eval()
    with torch.inference_mode():
        output = model(torch.randn(1, 3, 224, 224))
    assert output.shape == (1, 5)
