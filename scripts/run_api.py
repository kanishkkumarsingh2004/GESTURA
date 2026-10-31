"""Run the FastAPI gesture recognition API server.

Usage:
    uv run --active python scripts/run_api.py
    uv run --active python scripts/run_api.py --host 0.0.0.0 --port 8000
    uv run uvicorn server.api:app --host 0.0.0.0 --port 8000

Endpoints:
    GET    /health
    GET    /model/info
    GET    /gestures
    POST   /predict
    GET/POST/DELETE /session/{session_id}/...
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure the project root (parent of this scripts/ directory) is on sys.path so
# `import server` works whether this file is run as a script or as a module.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import uvicorn

from server.api import api


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the gesture recognition FastAPI server."
    )
    parser.add_argument("--host", default="0.0.0.0", help="Bind host (default 0.0.0.0)")
    parser.add_argument(
        "--port", type=int, default=8000, help="Bind port (default 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    # Ensure the model is loaded before binding the port so the first request
    # is not delayed by checkpoint loading.
    api.ensure_model_loaded()
    uvicorn.run(
        api.build_app(),
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
