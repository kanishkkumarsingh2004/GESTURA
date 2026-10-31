# Training Documentation

## Running training

Training is offline and independent of the Streamlit app:

```bash
uv run --active python -m train.train --data-root data/raw --epochs 50 --batch-size 32
```

Checkpoints (latest + best validation) are saved to `outputs/checkpoints/`.

## Configuration

Training hyperparameters live in `config.yaml` under the `training` key:

```yaml
training:
  epochs: 50
  batch_size: 32
  learning_rate: 0.0001
  weight_decay: 0.0001
  optimizer: adamw
  loss: cross_entropy
  early_stopping: true
  patience: 8
  seed: 42
```

## Architecture

The initial model is VGG16 with ImageNet pretrained weights and a replaceable
classification head (`model/architecture.py`). Future benchmarks can add
ResNet / MobileNetV3.

## Reproducibility

Seeds are set via `utils/reproducibility.py`. Perfect determinism is not
guaranteed across hardware.

## Evaluation

After training, evaluate the held-out test set:

```bash
uv run python scripts/evaluate.py --checkpoint outputs/checkpoints/best_model.pth
```

Metrics are written to `outputs/metrics/evaluation.json`.
