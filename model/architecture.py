"""Model architecture definitions for gesture recognition.

Implements a configurable PyTorch CNN classifier built on torchvision backbones
and the exact R_CNN architecture provided.
"""

from __future__ import annotations

from typing import Any, cast

import torch
import torch.nn as nn
import torch.nn.functional as F  # noqa: N812 - PyTorch convention uses `F`
import torchvision.models as weights_module


class Rcnn(nn.Module):
    """Exact R_CNN architecture as provided.

    Four convolutional layers with max pooling, followed by a two-layer
    fully connected classifier with softmax output. Returns both the
    convolutional feature map and the final class probabilities.
    """

    def __init__(self, num_classes: int = 10) -> None:
        super(Rcnn, self).__init__()
        self.conv1 = nn.Conv2d(in_channels=3, out_channels=64, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3, stride=1, padding=1)
        self.conv3 = nn.Conv2d(in_channels=128, out_channels=256, kernel_size=3, stride=1, padding=1)
        self.conv4 = nn.Conv2d(in_channels=256, out_channels=512, kernel_size=3, stride=1, padding=1)
        self.layer1 = nn.Linear(512 * 7 * 7, 1000)
        self.layer2 = nn.Linear(1000, num_classes)
        self.softmax = nn.Softmax(dim=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.relu = nn.ReLU()

    def convolayer(self, data):
        x = self.relu(self.conv1(data))
        x = self.pool(self.relu(self.conv2(x)))
        x = self.pool(self.relu(self.conv3(x)))
        x = self.pool(self.relu(self.conv4(x)))
        x = self.pool(self.pool(x))
        return x

    def nn_block(self, data):
        x = torch.flatten(data, 1)
        x = F.relu(self.layer1(x))
        x = self.softmax(self.layer2(x))
        return x

    def forward(self, x):
        x = self.convolayer(x)
        y = self.nn_block(x)
        return x, y


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
        architecture: Backbone name (e.g. ``vgg16``, ``resnet18``, ``r_cnn``).
        num_classes: Number of output gesture classes.
        pretrained: Load ImageNet pretrained backbone weights.
        device: Device to move the model to.

    Returns:
        Initialized model ready for training or inference.
    """
    lowered = architecture.lower()

    if lowered == "r_cnn":
        model = Rcnn(num_classes=num_classes)
        if device is not None:
            model = model.to(device)
        return model

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
    if lowered == "r_cnn":
        # R_CNN: freeze conv layers, keep the classifier head trainable.
        for name, param in model.named_parameters():
            if not name.startswith("layer"):
                param.requires_grad = False
        return model
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
