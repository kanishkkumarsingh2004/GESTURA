"""Training command entry point.

Loads configuration, initializes the dataset, model, optimizer and scheduler,
then starts training. Training is an offline process and is never run during
application startup.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

import torch
import numpy as np
from torch.utils.data import DataLoader, random_split

from data.dataset import GestureDataset, load_class_mapping_from_root
from utils.preprocessing import Preprocessor, load_preprocessing_config
from utils.reproducibility import capture_environment

from .trainer import Trainer, TrainerConfig


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train the gesture recognition model")
    parser.add_argument("--data-root", default="data/raw", help="Directory containing class subdirectories")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--output-dir", default="model", help="Checkpoint output directory")
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--learning-rate", type=float, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--device", default="auto", help="cuda, cpu or auto")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    class_mapping = load_class_mapping_from_root(args.data_root)
    num_classes = len(class_mapping)

    config = TrainerConfig(
        epochs=args.epochs if args.epochs is not None else 50,
        batch_size=args.batch_size if args.batch_size is not None else 32,
        learning_rate=args.learning_rate if args.learning_rate is not None else 0.0001,
        seed=args.seed if args.seed is not None else 42,
        device=args.device,
        num_classes=num_classes,
        architecture="vgg16",
        pretrained=True,
        class_mapping=class_mapping,
        output_dir=args.output_dir,
    )

    dataset = GestureDataset(args.data_root, class_mapping=class_mapping)

    # Deterministic split to avoid leakage at the sample level. For production
    # use, split at the recording-session / participant level.
    generator = torch.Generator().manual_seed(config.seed)
    train_size = int(0.7 * len(dataset))
    val_size = int(0.15 * len(dataset))
    test_size = len(dataset) - train_size - val_size
    train_ds, val_ds, test_ds = random_split(dataset, [train_size, val_size, test_size], generator=generator)

    prep_config = load_preprocessing_config(args.config)
    preprocessor = Preprocessor(prep_config)

    def collate(batch: list[tuple[Any, int]]) -> tuple[torch.Tensor, torch.Tensor]:
        images: list[torch.Tensor] = []
        labels: list[int] = []
        for image, label in batch:
            if not isinstance(image, np.ndarray):
                image = np.array(image.convert("RGB"))
            tensor = preprocessor.to_tensor(preprocessor.normalize(preprocessor.resize(image)))
            images.append(tensor)
            labels.append(label)
        return torch.stack(images), torch.tensor(labels)

    train_loader = DataLoader(train_ds, batch_size=config.batch_size, shuffle=True, collate_fn=collate)
    val_loader = DataLoader(val_ds, batch_size=config.batch_size, shuffle=False, collate_fn=collate)

    trainer = Trainer(config)
    trainer.fit(train_loader, val_loader, class_names=list(class_mapping.keys()))

    print("Training finished.")
    print(f"Environment: {capture_environment()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
