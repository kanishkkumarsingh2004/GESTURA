"""Model export utility.

Exports a trained checkpoint to TorchScript or ONNX for deployment.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

from model.inference import InferenceEngine


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export a trained model")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--checkpoint", default=None, help="Path to checkpoint (.pth)")
    parser.add_argument("--format", choices=["torchscript", "onnx"], default="torchscript")
    parser.add_argument("--output", default="model/exports/gesture_classifier", help="Output path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    engine = InferenceEngine(config_path=args.config, checkpoint=args.checkpoint)
    engine.load_model()
    model = engine._model
    if model is None:
        print("Model not loaded")
        return 1
    model.eval()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    example = torch.randn(1, 3, 224, 224)

    if args.format == "torchscript":
        scripted = torch.jit.trace(model, example)
        torch.jit.save(scripted, str(output_path) + ".pt")
        print(f"Exported TorchScript to {output_path}.pt")
    else:
        try:
            import onnx  # type: ignore[import-not-found]  # noqa: F401 - optional dependency
            torch.onnx.export(model, example, str(output_path) + ".onnx", opset_version=13)  # type: ignore[arg-type]
            print(f"Exported ONNX to {output_path}.onnx")
        except ImportError:
            print("onnx not installed; install onnx to export to ONNX")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
