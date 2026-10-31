"""Session manager: session-scoped state and lifecycle management.

Streamlit sessions share read-only model resources, but camera streams,
prediction state, audio queues and settings remain session-specific.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionState:
    camera_connected: bool = False
    detection_enabled: bool = False
    audio_enabled: bool = True
    latest_prediction: str | None = None
    prediction_history: list[dict[str, Any]] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=dict)

    def add_prediction(self, gesture: str, confidence: float, audio_played: bool) -> None:
        import time

        self.prediction_history.append(
            {
                "gesture": gesture,
                "confidence": confidence,
                "timestamp": time.time(),
                "audio_played": audio_played,
            }
        )
        # Bound history to prevent unbounded memory growth.
        max_history = self.settings.get("max_history", 1000)
        if len(self.prediction_history) > max_history:
            self.prediction_history = self.prediction_history[-max_history:]

    def clear_history(self) -> None:
        self.prediction_history.clear()

    def to_dict(self) -> dict[str, Any]:
        return {
            "camera_connected": self.camera_connected,
            "detection_enabled": self.detection_enabled,
            "audio_enabled": self.audio_enabled,
            "latest_prediction": self.latest_prediction,
            "prediction_history": self.prediction_history,
        }


class SessionManager:
    """Manages per-session lifecycle and resources."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}

    def get_or_create(self, session_id: str) -> SessionState:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState()
        return self._sessions[session_id]

    def remove(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def get(self, session_id: str) -> SessionState | None:
        return self._sessions.get(session_id)

    @property
    def active_session_count(self) -> int:
        return len(self._sessions)
