"""Model configuration and metadata management.

Centralizes the class mapping, input dimensions, and model metadata so the
number of classes is never hardcoded independently across modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import yaml


@dataclass
class ModelConfig:
    architecture: str = "vgg16"
    pretrained: bool = True
    num_classes: int = 0
    input_width: int = 224
    input_height: int = 224
    checkpoint: str | Path | None = None
    class_mapping: dict[str, int] = field(default_factory=dict)
    preprocessing: dict[str, Any] = field(default_factory=dict)

    @property
    def class_names(self) -> list[str]:
        return sorted(self.class_mapping, key=lambda k: self.class_mapping[k])  # type: ignore[arg-type]

    @property
    def input_size(self) -> tuple[int, int]:
        return (self.input_width, self.input_height)


def load_class_mapping(config_path: str | Path = "config.yaml") -> dict[str, int]:
    """Load the centralized class mapping from config.yaml."""
    with open(config_path, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    mapping = config.get("class_mapping", {})
    if not mapping:
        raise ValueError("config.yaml must define a non-empty class_mapping")
    return cast(dict[str, int], mapping)


def build_model_config(
    config_path: str | Path = "config.yaml",
    checkpoint: str | Path | None = None,
) -> ModelConfig:
    """Build a ModelConfig from the centralized configuration file."""
    with open(config_path, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    model_section = config.get("model", {})
    class_mapping = load_class_mapping(config_path)

    return ModelConfig(
        architecture=model_section.get("architecture", "vgg16"),
        pretrained=model_section.get("pretrained", True),
        num_classes=len(class_mapping),
        input_width=model_section.get("input_width", 224),
        input_height=model_section.get("input_height", 224),
        checkpoint=checkpoint or model_section.get("checkpoint"),
        class_mapping=dict(class_mapping),
        preprocessing=config.get("preprocessing", {}),
    )


@dataclass
class ModelMetadata:
    model_name: str = "gesture_classifier"
    architecture: str = "vgg16"
    version: str = "1.0.0"
    num_classes: int = 0
    input_size: list[int] = field(default_factory=lambda: [224, 224])
    color_space: str = "RGB"
    normalization: str = "imagenet"
    checkpoint: str | None = None
    class_mapping: dict[str, int] = field(default_factory=dict)
    preprocessing: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "architecture": self.architecture,
            "version": self.version,
            "num_classes": self.num_classes,
            "input_size": self.input_size,
            "color_space": self.color_space,
            "normalization": self.normalization,
            "checkpoint": self.checkpoint,
            "class_mapping": self.class_mapping,
            "preprocessing": self.preprocessing,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelMetadata":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
