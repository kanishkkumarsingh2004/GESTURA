"""Unit tests for prediction stabilization."""

from __future__ import annotations

import time

from model.inference import PredictionResult
from server.prediction_service import DetectionConfig, PredictionService


def test_stable_event_emitted_after_confirmation_frames() -> None:
    service = PredictionService(config=DetectionConfig(
        confidence_threshold=0.5,
        confirmation_frames=3,
        cooldown_seconds=0.0,
    ))
    event = None
    for _ in range(5):
        event = service.update(PredictionResult(0, "HELLO", 0.9, {}, 0.0))
    assert event is not None
    assert event.class_name == "HELLO"


def test_below_threshold_not_confirmed() -> None:
    service = PredictionService(config=DetectionConfig(
        confidence_threshold=0.9,
        confirmation_frames=3,
        cooldown_seconds=0.0,
    ))
    event = None
    for _ in range(10):
        event = service.update(PredictionResult(0, "HELLO", 0.5, {}, 0.0))
    assert event is None


def test_duplicate_suppressed_during_cooldown() -> None:
    service = PredictionService(config=DetectionConfig(
        confidence_threshold=0.5,
        confirmation_frames=2,
        cooldown_seconds=10.0,
    ))
    first = None
    second = None
    for _ in range(5):
        event = service.update(PredictionResult(0, "HELLO", 0.9, {}, 0.0))
        if event is not None and first is None:
            first = event
    time.sleep(0.01)
    for _ in range(5):
        event = service.update(PredictionResult(0, "HELLO", 0.9, {}, 0.0))
        if event is not None:
            second = event
    assert first is not None
    assert second is None
