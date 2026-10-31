"""Training loop implementation.

Handles batch iteration, forward/backward propagation, validation,
checkpointing and metric recording.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import torch
from torch.utils.data import DataLoader

from model.architecture import build_model
from model.checkpoint import CheckpointBundle, save_checkpoint
from utils.reproducibility import set_seed

from .callbacks import BestCheckpointTracker, EarlyStopping


@dataclass
class TrainerConfig:
    epochs: int = 50
    batch_size: int = 32
    learning_rate: float = 0.0001
    weight_decay: float = 0.0001
    optimizer: str = "adamw"
    loss: str = "cross_entropy"
    scheduler: str = "reduce_lr_on_plateau"
    patience: int = 8
    seed: int = 42
    device: str = "auto"
    num_classes: int = 0
    architecture: str = "vgg16"
    pretrained: bool = True
    class_mapping: dict[str, int] = field(default_factory=dict)
    output_dir: str = "model"
    resume_from: str | Path | None = None


@dataclass
class EpochMetrics:
    epoch: int
    train_loss: float
    train_accuracy: float
    val_loss: float
    val_accuracy: float
    learning_rate: float


class Trainer:
    """Runs the training loop independently of the Streamlit application."""

    def __init__(self, config: TrainerConfig) -> None:
        self.config = config
        set_seed(config.seed)
        self.device = self._resolve_device(config.device)
        self.model = self._build_model()
        self.history: list[dict[str, float]] = []

    def _resolve_device(self, preference: str) -> torch.device:
        from utils.device import select_device

        return select_device(preference)

    def _build_model(self) -> torch.nn.Module:
        model = build_model(
            architecture=self.config.architecture,
            num_classes=self.config.num_classes,
            pretrained=self.config.pretrained,
            device=self.device,
        )
        return cast(torch.nn.Module, model)

    def fit(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        class_names: list[str],
    ) -> list[dict[str, float]]:
        """Run the full training loop.

        Returns the recorded training history.
        """
        from .loss import build_loss as build_loss_fn
        from .optimizer import build_optimizer as build_opt
        from .scheduler import build_scheduler as build_sch

        criterion = build_loss_fn(self.config.loss)
        optimizer = build_opt(
            self.model.parameters(),
            name=self.config.optimizer,
            learning_rate=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
        )
        scheduler = build_sch(optimizer, name=self.config.scheduler, patience=self.config.patience, t_max=self.config.epochs)

        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
        best_tracker = self._create_best_tracker()
        early_stopping = self._create_early_stopping()

        self.model.to(self.device)
        self.model.train()

        for epoch in range(1, self.config.epochs + 1):
            train_loss, train_acc = self._train_epoch(train_loader, criterion, optimizer)
            val_loss, val_acc = self._validate(val_loader, criterion)

            current_lr = optimizer.param_groups[0]["lr"]
            self.history.append(
                {
                    "epoch": epoch,
                    "train_loss": train_loss,
                    "train_accuracy": train_acc,
                    "val_loss": val_loss,
                    "val_accuracy": val_acc,
                    "learning_rate": current_lr,
                }
            )

            print(
                f"Epoch {epoch}/{self.config.epochs} | "
                f"train_loss {train_loss:.4f} train_acc {train_acc:.4f} | "
                f"val_loss {val_loss:.4f} val_acc {val_acc:.4f} | lr {current_lr:.6f}"
            )

            is_best = best_tracker.update(val_acc, epoch)
            self._save_checkpoint(epoch, val_acc, optimizer, scheduler, is_best=is_best)

            if isinstance(scheduler, torch.optim.lr_scheduler.ReduceLROnPlateau):
                scheduler.step(val_acc)
            else:
                scheduler.step()

            if early_stopping.step(val_acc):
                print("Early stopping triggered.")
                break

        print(f"Training complete. Best val accuracy {best_tracker.best_accuracy:.4f} at epoch {best_tracker.best_epoch}")
        return self.history

    def _train_epoch(
        self, loader: DataLoader, criterion: torch.nn.Module, optimizer: torch.optim.Optimizer
    ) -> tuple[float, float]:
        running_loss = 0.0
        correct = 0
        total = 0
        for images, labels in loader:
            images = images.to(self.device)
            labels = labels.to(self.device)

            optimizer.zero_grad()
            outputs = self.model(images)
            if isinstance(outputs, tuple):
                # R_CNN returns (features, probs) where probs is softmaxed.
                # CrossEntropyLoss == NLLLoss(log_softmax(logits))
                # == NLLLoss(log(probs)), so use NLLLoss on log probs.
                probs = outputs[1]
                loss = criterion(torch.log(probs + 1e-8), labels)
                _, predicted = probs.max(1)
            else:
                loss = criterion(outputs, labels)
                _, predicted = outputs.max(1)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

        return running_loss / total, correct / total

    def _validate(self, loader: DataLoader, criterion: torch.nn.Module) -> tuple[float, float]:
        self.model.eval()
        running_loss = 0.0
        correct = 0
        total = 0
        with torch.inference_mode():
            for images, labels in loader:
                images = images.to(self.device)
                labels = labels.to(self.device)
                outputs = self.model(images)
                if isinstance(outputs, tuple):
                    probs = outputs[1]
                    loss = criterion(torch.log(probs + 1e-8), labels)
                    _, predicted = probs.max(1)
                else:
                    loss = criterion(outputs, labels)
                    _, predicted = outputs.max(1)

                running_loss += loss.item() * images.size(0)
                total += labels.size(0)
                correct += predicted.eq(labels).sum().item()
        self.model.train()
        return running_loss / total, correct / total

    def _create_best_tracker(self) -> BestCheckpointTracker:
        return BestCheckpointTracker()

    def _create_early_stopping(self) -> EarlyStopping:
        return EarlyStopping(patience=self.config.patience)

    def _save_checkpoint(
        self, epoch: int, val_acc: float, optimizer: torch.optim.Optimizer, scheduler: Any, is_best: bool
    ) -> None:
        bundle = CheckpointBundle(
            model_state_dict=self.model.state_dict(),
            optimizer_state_dict=optimizer.state_dict(),
            scheduler_state_dict=scheduler.state_dict(),
            epoch=epoch,
            best_val_accuracy=float(val_acc),
            class_mapping=self.config.class_mapping,
            model_config={
                "architecture": self.config.architecture,
                "num_classes": self.config.num_classes,
                "input_width": 224,
                "input_height": 224,
            },
            preprocessing_config={},
        )
        save_checkpoint(
            bundle,
            output_dir=self.config.output_dir,
            filename=f"checkpoint_epoch_{epoch}.pt",
            is_best=is_best,
        )
