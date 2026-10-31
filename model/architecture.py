"""Model architecture definitions for gesture recognition.

Implements a configurable PyTorch CNN classifier built on torchvision backbones.
The initial architecture is VGG16 with transfer learning support and a replaceable
classification head.
"""

from __future__ import annotations

from typing import Any, cast

import torch
import torch.nn as nn
import torchvision.models as weights_module


def _resolve_weights(pretrained: bool, architecture: str) -> Any | None:
    """Resolve torchvision pretrained weights for a given architecture."""
    if not pretrained:
        return None

    weight_map: dict[str, str] = {
        "vgg16": "VGG16_Weights",
        "resnet18": "ResNet18_Weights",
        "mobilenet_v3_small": "MobileNet_V3_Small_Weights",
        "mobilenet_v3_large": "MobileNet_V3_Large_Weights",
    }

    weights_name = weight_map.get(architecture.lower())
    if weights_name is None:
        return None

    weights_class = getattr(weights_module, weights_name, None)
    if weights_class is None:
        return None

    try:
        return weights_class.DEFAULT
    except AttributeError:
        return None


def _replace_head(model: nn.Module, architecture: str, num_classes: int) -> nn.Module:
    """Replace the classification head of a backbone for num_classes outputs."""
    lowered = architecture.lower()

    if lowered.startswith("vgg"):
        first_linear = cast(nn.Linear, model.classifier[0])  # type: ignore[index]
        in_features = int(first_linear.in_features)
        model.classifier = nn.Sequential(  # type: ignore[assignment]
            nn.Linear(in_features, 4096),
            nn.ReLU(True),
            nn.Dropout(),
            nn.Linear(4096, 4096),
            nn.ReLU(True),
            nn.Dropout(),
            nn.Linear(4096, num_classes),
        )
    elif lowered.startswith("resnet"):
        fc = cast(nn.Linear, model.fc)  # type: ignore[assignment]
        in_features = int(fc.in_features)
        model.fc = nn.Linear(in_features, num_classes)
    elif "mobilenet" in lowered:
        last_linear = cast(nn.Linear, model.classifier[-1])  # type: ignore[index]
        in_features = int(last_linear.in_features)
        model.classifier[-1] = nn.Linear(in_features, num_classes)  # type: ignore[index, assignment, operator]
    else:
        raise ValueError(f"Unsupported architecture for head replacement: {architecture}")

    return model


def build_model(
    architecture: str,
    num_classes: int,
    pretrained: bool = True,
    device: torch.device | str | None = None,
) -> nn.Module:
    """Factory function to build a gesture classification model.

    Args:
        architecture: Backbone name (e.g. ``vgg16``, ``resnet18``).
        num_classes: Number of output gesture classes.
        pretrained: Load ImageNet pretrained backbone weights.
        device: Device to move the model to.

    Returns:
        Initialized model ready for training or inference.
    """
    lowered = architecture.lower()
    weights = _resolve_weights(pretrained, lowered)

    model_fn = getattr(__import__("torchvision.models", fromlist=[lowered]), lowered, None)
    if model_fn is None:
        raise ValueError(f"Unknown architecture: {architecture}")

    model = model_fn(weights=weights)
    model = _replace_head(model, lowered, num_classes)

    if device is not None:
        model = model.to(device)

    return model


def count_parameters(model: nn.Module) -> int:
    """Return the total number of trainable parameters."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def freeze_backbone(model: nn.Module, architecture: str) -> nn.Module:
    """Freeze backbone parameters so only the classification head trains."""
    lowered = architecture.lower()
    if lowered.startswith("vgg"):
        for param in model.features.parameters():  # type: ignore[union-attr]
            param.requires_grad = False
    elif lowered.startswith("resnet"):
        for name, param in model.named_parameters():
            if not name.startswith("fc."):
                param.requires_grad = False
    elif "mobilenet" in lowered:
        for name, param in model.named_parameters():
            if not name.startswith("classifier."):
                param.requires_grad = False
    return model


def unfreeze_backbone(model: nn.Module) -> nn.Module:
    """Unfreeze all model parameters."""
    for param in model.parameters():
        param.requires_grad = True
    return model
