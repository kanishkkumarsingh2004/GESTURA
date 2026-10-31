"""Pydantic request/response schemas for the FastAPI gesture API."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class GestureMapEntry(BaseModel):
    class_id: int
    class_name: str
    text: str


class GesturesResponse(BaseModel):
    classes: list[GestureMapEntry]
    count: int


class ModelInfoResponse(BaseModel):
    architecture: str
    num_classes: int
    class_names: list[str]
    input_size: list[int]
    device: str
    loaded: bool
    metadata: dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str = "1.0.0"


class AudioPlaybackInfo(BaseModel):
    played: bool
    text: Optional[str] = None
    gesture: Optional[str] = None
    reason: Optional[str] = None


class StableEventInfo(BaseModel):
    event_id: str
    class_name: str
    confidence: float
    timestamp: float


class PredictResponse(BaseModel):
    session_id: str
    class_id: int
    class_name: str
    confidence: float
    probabilities: dict[str, float]
    inference_time_ms: float
    detection_enabled: bool
    audio_enabled: bool
    stable: bool
    stable_event: Optional[StableEventInfo] = None
    audio: AudioPlaybackInfo


class DetectionStatusResponse(BaseModel):
    session_id: str
    camera_connected: bool
    detection_enabled: bool
    audio_enabled: bool
    latest_prediction: Optional[str]
    latest_confidence: Optional[float]
    state: str
    history_count: int


class AudioStatusResponse(BaseModel):
    session_id: str
    enabled: bool
    last_announced: Optional[str]
    queue_size: int


class SessionCreateResponse(BaseModel):
    session_id: str


class DetectionControlResponse(BaseModel):
    session_id: str
    detection_enabled: bool
    camera_status: str


class AudioControlResponse(BaseModel):
    session_id: str
    audio_enabled: bool


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
