"""Dataset collection utility.

Captures gesture images from a local camera into data/raw/<CLASS>/ directories.
Intended for explicit dataset collection only; does not run during inference.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2

GESTURE_CLASSES = [
    "HELLO", "YES", "NO", "THANK_YOU", "PLEASE", "STOP", "HELP",
    "GOOD", "BAD", "LOVE", "NONE",
]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect gesture dataset images")
    parser.add_argument("--data-root", default="data/raw", help="Output root directory")
    parser.add_argument("--gesture", required=True, help="Gesture class to collect")
    parser.add_argument("--count", type=int, default=50, help="Number of images to capture")
    parser.add_argument("--camera", type=int, default=0, help="Local camera index")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    gesture = args.gesture.upper()
    if gesture not in GESTURE_CLASSES:
        print(f"Unsupported gesture: {gesture}. Supported: {GESTURE_CLASSES}")
        return 1

    out_dir = Path(args.data_root) / gesture
    out_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"Cannot open camera index {args.camera}")
        return 1

    print(f"Collecting {args.count} images for {gesture} into {out_dir}")
    print("Press SPACE to capture, q to quit.")

    captured = 0
    while captured < args.count:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame")
            break

        cv2.putText(
            frame,
            f"{gesture} - {captured}/{args.count}",
            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2,
        )
        cv2.imshow("Data Collection", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(" "):
            path = out_dir / f"{gesture}_{int(time.time()*1000)}.jpg"
            cv2.imwrite(str(path), frame)
            captured += 1
            print(f"Captured {captured}/{args.count}: {path}")
        elif key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"Collection complete: {captured} images")
    return 0


if __name__ == "__main__":
    sys.exit(main())
