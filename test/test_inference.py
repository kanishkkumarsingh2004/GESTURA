"""Unit tests for inference engine (synthetic, no model weights required)."""

from __future__ import annotations

from model.inference import InferenceEngine, PredictionResult


def test_prediction_result_dataclass() -> None:
    result = PredictionResult(
        class_id=0,
        class_name="HELLO",
        confidence=0.9,
        probabilities={"HELLO": 0.9},
        inference_time_ms=12.5,
    )
    assert result.class_name == "HELLO"
    assert result.confidence == 0.9


def test_inference_engine_initial_state() -> None:
    engine = InferenceEngine()
    assert not engine._loaded
