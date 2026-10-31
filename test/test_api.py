"""Tests for the FastAPI gesture recognition API.

Uses a fake inference engine so tests do not load the real model checkpoint.
"""

from __future__ import annotations

from typing import Any, Dict

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from model.inference import PredictionResult
from server.api import GestureAPI


class FakeEngine:
    """Stand-in for InferenceEngine that returns a fixed prediction."""

    _loaded = True
    device = "cpu"

    def predict(self, image: Any) -> PredictionResult:  # noqa: ARG002
        return PredictionResult(
            class_id=0,
            class_name="HELLO",
            confidence=0.95,
            probabilities={"HELLO": 0.95, "NONE": 0.05},
            inference_time_ms=12.0,
        )

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "architecture": "vgg16",
            "num_classes": 22,
            "class_names": ["HELLO", "NONE"],
            "input_size": [224, 224],
            "device": "cpu",
            "loaded": True,
            "metadata": {},
        }


def _make_api() -> GestureAPI:
    return GestureAPI(engine=FakeEngine())


def _png_bytes() -> bytes:
    frame = np.zeros((64, 64, 3), dtype=np.uint8)
    success, encoded = cv2.imencode(".png", frame)
    assert success
    return encoded.tobytes()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(_make_api().build_app())


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True


def test_model_info_endpoint(client: TestClient) -> None:
    response = client.get("/model/info")
    assert response.status_code == 200
    body = response.json()
    assert body["architecture"] == "vgg16"
    assert body["loaded"] is True


def test_gestures_endpoint(client: TestClient) -> None:
    response = client.get("/gestures")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    names = {entry["class_name"] for entry in body["classes"]}
    assert names == {"HELLO", "NONE"}


def test_predict_returns_prediction(client: TestClient) -> None:
    response = client.post(
        "/predict",
        files={"image": ("frame.png", _png_bytes(), "image/png")},
        headers={"X-Session-Id": "session-a"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "session-a"
    assert body["class_name"] == "HELLO"
    assert body["confidence"] == 0.95
    assert body["inference_time_ms"] == 12.0
    assert body["stable"] is False  # needs confirmation_frames consecutive hits


def test_predict_stabilizes_after_confirmation_frames(client: TestClient) -> None:
    headers = {"X-Session-Id": "session-b"}
    stable_seen = False
    for _ in range(8):
        response = client.post(
            "/predict",
            files={"image": ("frame.png", _png_bytes(), "image/png")},
            headers=headers,
        )
        assert response.status_code == 200
        if response.json()["stable"]:
            stable_seen = True
            break
    assert stable_seen is True


def test_predict_rejects_invalid_image(client: TestClient) -> None:
    response = client.post(
        "/predict",
        files={"image": ("frame.txt", b"not an image", "text/plain")},
        headers={"X-Session-Id": "session-c"},
    )
    assert response.status_code == 400


def test_session_isolation(client: TestClient) -> None:
    client.post(
        "/predict",
        files={"image": ("frame.png", _png_bytes(), "image/png")},
        headers={"X-Session-Id": "session-isolate-1"},
    )
    client.post(
        "/predict",
        files={"image": ("frame.png", _png_bytes(), "image/png")},
        headers={"X-Session-Id": "session-isolate-2"},
    )
    status_a = client.get("/session/session-isolate-1/status").json()
    status_b = client.get("/session/session-isolate-2/status").json()
    assert status_a["session_id"] == "session-isolate-1"
    assert status_b["session_id"] == "session-isolate-2"


def test_detection_start_stop(client: TestClient) -> None:
    sid = "session-ctrl"
    start = client.post(f"/session/{sid}/detection/start")
    assert start.status_code == 200
    assert start.json()["detection_enabled"] is True
    status = client.get(f"/session/{sid}/status").json()
    assert status["detection_enabled"] is True
    stop = client.post(f"/session/{sid}/detection/stop")
    assert stop.json()["detection_enabled"] is False


def test_audio_enable_disable(client: TestClient) -> None:
    sid = "session-audio"
    client.post(f"/session/{sid}/audio/disable")
    status = client.get(f"/session/{sid}/audio/status").json()
    assert status["enabled"] is False
    client.post(f"/session/{sid}/audio/enable")
    status = client.get(f"/session/{sid}/audio/status").json()
    assert status["enabled"] is True


def test_history_clear(client: TestClient) -> None:
    sid = "session-history"
    client.post(
        "/predict",
        files={"image": ("frame.png", _png_bytes(), "image/png")},
        headers={"X-Session-Id": sid},
    )
    history = client.get(f"/session/{sid}/history").json()
    assert history["count"] >= 0
    cleared = client.delete(f"/session/{sid}/history")
    assert cleared.status_code == 200


def test_reset_session(client: TestClient) -> None:
    sid = "session-reset"
    client.post(f"/session/{sid}/reset")
    response = client.post(f"/session/{sid}/reset")
    assert response.status_code == 200
    assert response.json()["status"] == "reset"


def test_remove_session(client: TestClient) -> None:
    sid = "session-remove"
    client.post(f"/session/{sid}/detection/start")
    removed = client.delete(f"/session/{sid}")
    assert removed.status_code == 200
    assert removed.json()["status"] == "removed"
