"""Model evaluation script.

Loads a saved checkpoint, reproduces training preprocessing, evaluates the
held-out test dataset and writes metrics to outputs/metrics.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from torch.utils.data import DataLoader
from torchvision import transforms

from data.dataset import GestureDataset
from model.inference import InferenceEngine
from utils.metrics import evaluate_predictions
from utils.preprocessing import load_preprocessing_config
from utils.visualization import plot_confusion_matrix


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate a trained checkpoint")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--checkpoint", default=None, help="Path to checkpoint (.pth)")
    parser.add_argument("--data-root", default="data/raw", help="Test dataset root")
    parser.add_argument("--output", default="outputs/metrics/evaluation.json", help="Metrics output path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    engine = InferenceEngine(config_path=args.config, checkpoint=args.checkpoint)
    engine.load_model()
    info = engine.get_model_info()
    class_names = info.get("class_names", [])

    prep_config = load_preprocessing_config(args.config)

    transform = transforms.Compose([
        transforms.Resize((prep_config.input_height, prep_config.input_width)),
        transforms.ToTensor(),
        transforms.Normalize(mean=prep_config.mean, std=prep_config.std),
    ])

    dataset = GestureDataset(args.data_root, transform=transform)
    loader = DataLoader(dataset, batch_size=32, shuffle=False)

    y_true: list[int] = []
    y_pred: list[int] = []
    latencies: list[float] = []
    import time
    for images, labels in loader:
        for image, label in zip(images, labels, strict=False):
            start = time.perf_counter()
            prediction_result = engine.predict(image.numpy())
            latencies.append((time.perf_counter() - start) * 1000.0)
            y_true.append(int(label))
            y_pred.append(class_names.index(prediction_result.class_name))

    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    eval_result = evaluate_predictions(y_true, y_pred, class_names, inference_latency_ms=avg_latency)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "accuracy": eval_result.accuracy,
        "precision": eval_result.precision,
        "recall": eval_result.recall,
        "f1": eval_result.f1,
        "per_class_accuracy": eval_result.per_class_accuracy,
        "confusion_matrix": eval_result.confusion_matrix,
        "class_names": eval_result.class_names,
        "inference_latency_ms": eval_result.inference_latency_ms,
        "num_samples": eval_result.num_samples,
    }
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    print(eval_result.report)
    print(f"\nMetrics saved to {output_path}")

    try:
        plot_confusion_matrix(eval_result.confusion_matrix, eval_result.class_names,
                              "outputs/plots/confusion_matrix.png")
        print("Confusion matrix plot saved to outputs/plots/confusion_matrix.png")
    except Exception as exc:  # noqa: BLE001 - plotting optional
        print(f"Could not save confusion matrix plot: {exc}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
