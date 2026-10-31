"""Prediction service: converts raw model outputs into stable predictions.

Implements the prediction state machine:
    Idle -> Candidate (gesture detected)
    Candidate -> Confirmed (stable frames reached)
    Candidate -> Idle (confidence too low)
    Confirmed -> Announced (audio enabled)
    Confirmed -> Cooldown (audio disabled)
    Announced -> Cooldown (playback initiated)
    Cooldown -> Candidate / Idle
"""

from __future__ import annotations

import time
import uuid
from collections import deque
from dataclasses import dataclass
from typing import Optional

from model.inference import PredictionResult


@dataclass
class StablePredictionEvent:
    class_name: str
    confidence: float
    timestamp: float
    event_id: str


@dataclass
class DetectionConfig:
    confidence_threshold: float = 0.85
    confirmation_frames: int = 5
    smoothing_window: int = 5
    cooldown_seconds: float = 1.5
    unknown_class_enabled: bool = True


class PredictionService:
    """Buffers raw predictions and emits stable prediction events."""

    def __init__(self, config: DetectionConfig | None = None) -> None:
        self.config = config or DetectionConfig()
        self._window: deque[str] = deque(maxlen=max(1, self.config.smoothing_window))
        self._consecutive_count = 0
        self._last_confirmed: Optional[str] = None
        self._last_announce_time: float = 0.0
        self._state = "idle"

    def reset(self) -> None:
        """Reset session-specific stabilization state."""
        self._window.clear()
        self._consecutive_count = 0
        self._last_confirmed = None
        self._last_announce_time = 0.0
        self._state = "idle"

    def update(self, result: PredictionResult) -> Optional[StablePredictionEvent]:
        """Process a raw prediction and optionally emit a stable event."""
        class_name = result.class_name
        confidence = result.confidence

        # Unknown gesture handling.
        if self.config.unknown_class_enabled and class_name.upper() == "NONE":
            self._window.append("NONE")
            self._consecutive_count = 0
            self._state = "idle"
            self._last_confirmed = None
            return None

        # Confidence threshold.
        if confidence < self.config.confidence_threshold:
            self._window.append("")
            self._consecutive_count = 0
            self._state = "candidate"
            self._last_confirmed = None
            return None

        # Smoothing window.
        self._window.append(class_name)
        if not self._window:
            return None

        most_common = max(set(self._window), key=self._window.count)
        if most_common != class_name:
            class_name = most_common

        now = time.time()

        # Cooldown gating.
        if self._last_confirmed == class_name and (now - self._last_announce_time) < self.config.cooldown_seconds:
            self._state = "cooldown"
            return None

        # Consecutive frame confirmation.
        if class_name == self._last_confirmed:
            self._consecutive_count += 1
        else:
            self._consecutive_count = 1
            self._last_confirmed = class_name

        if self._consecutive_count < self.config.confirmation_frames:
            self._state = "candidate"
            return None

        # Confirmed -> announce.
        self._state = "announced"
        self._last_announce_time = now
        return StablePredictionEvent(
            class_name=class_name,
            confidence=confidence,
            timestamp=now,
            event_id=str(uuid.uuid4()),
        )

    @property
    def state(self) -> str:
        return self._state
