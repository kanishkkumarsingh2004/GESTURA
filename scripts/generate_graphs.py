"""Generate model statistical graphs (confusion matrix, etc.) into graphs/."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.visualization import plot_confusion_matrix


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate model graphs")
    parser.add_argument("--metrics", default="outputs/metrics/evaluation.json")
    parser.add_argument("--output-dir", default="graphs")
    args = parser.parse_args()

    metrics_path = Path(args.metrics)
    with open(metrics_path, encoding="utf-8") as handle:
        report = json.load(handle)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    plot_confusion_matrix(
        report["confusion_matrix"],
        report["class_names"],
        out_dir / "confusion_matrix.png",
    )
    print(f"Graphs saved to {out_dir}")


if __name__ == "__main__":
    main()
