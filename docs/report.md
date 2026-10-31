# Gesture Recognition Project Report

## Overview
Real-time hand gesture recognition and audio assistant built with PyTorch, OpenCV, and Streamlit.

## Environment
- Python 3.11 (.venv via uv)
- PyTorch 2.6.0+cu124 (CUDA 12.4)
- GPU: NVIDIA GeForce RTX 4070 Laptop GPU (CUDA available)

## Training
- Entry point: `uv run python -m train.train --data-root data/raw`
- Checkpoints saved to `model/` as `.pt` files (`best_model.pt`, `checkpoint_epoch_N.pt`)

## Evaluation
- Entry point: `uv run python scripts/evaluate.py`
- Metrics saved to `outputs/metrics/evaluation.json`

## Graphs
- Entry point: `uv run python scripts/generate_graphs.py`
- Outputs saved to `graphs/` (confusion matrix, etc.)

## Key Components
- `model/`: architecture, checkpointing, inference, loader
- `train/`: trainer, optimizer, scheduler, loss, callbacks
- `utils/`: metrics, preprocessing, visualization, device selection
- `data/`: dataset handling
- `scripts/`: evaluate, generate_graphs
