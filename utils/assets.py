"""Asset management: ensures MediaPipe task model binaries are available locally.

Model binaries are not committed to the repository (see ``.gitignore``) and are
downloaded on first use into the local model cache directory (``.model_cache/``).
"""

from __future__ import annotations

from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

HAND_LANDMARKER_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)

CACHE_DIR = Path(".model_cache")
MODEL_FILENAME = "hand_landmarker.task"
CHUNK_SIZE = 1024 * 1024


def ensure_hand_landmarker_model(cache_dir: str | Path | None = None) -> Path:
    """Return the path to the MediaPipe hand landmarker task model.

    Downloads the model from Google's MediaPipe model storage into the cache
    directory on first use, then reuses the cached file.
    """
    cache = Path(cache_dir or CACHE_DIR).expanduser().resolve()
    cache.mkdir(parents=True, exist_ok=True)
    model_path = cache / MODEL_FILENAME
    if model_path.exists():
        return model_path
    _download(HAND_LANDMARKER_URL, model_path)
    return model_path


def _download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "gesture-recognition/1.0"})
    try:
        with urlopen(request, timeout=120) as response, open(destination, "wb") as out:
            while True:
                chunk = response.read(CHUNK_SIZE)
                if not chunk:
                    break
                out.write(chunk)
    except (HTTPError, URLError, OSError) as exc:  # noqa: BLE001 - surface a clear error
        raise RuntimeError(
            f"Failed to download MediaPipe hand landmarker model from {url}: {exc}"
        ) from exc
