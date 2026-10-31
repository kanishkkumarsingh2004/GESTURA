"""Audio service: converts confirmed predictions into spoken output.

Audio playback runs on the browser side. The Python service only emits playback
requests and manages a bounded, session-specific queue with duplicate
prevention. It never blocks inference.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Optional


@dataclass
class AudioConfig:
    enabled: bool = True
    duplicate_prevention: bool = True
    max_queue_size: int = 10


@dataclass
class PlaybackRequest:
    text: str
    gesture: str
    timestamp: float


# Centralized gesture-to-text mapping (single source of truth).
GESTURE_TEXT = {
    "HELLO": "Hello",
    "YES": "Yes",
    "NO": "No",
    "THANK_YOU": "Thank you",
    "PLEASE": "Please",
    "STOP": "Stop",
    "HELP": "Help",
    "GOOD": "Good",
    "BAD": "Bad",
    "LOVE": "Love",
}


class AudioService:
    """Manages the playback queue and duplicate prevention."""

    def __init__(self, config: AudioConfig | None = None) -> None:
        self.config = config or AudioConfig()
        self._queue: deque[PlaybackRequest] = deque(maxlen=max(1, self.config.max_queue_size))
        self._last_announced: Optional[str] = None
        self.enabled = self.config.enabled

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    def mute(self) -> None:
        self.enabled = False

    def unmute(self) -> None:
        self.enabled = True

    def request_playback(self, gesture: str) -> Optional[PlaybackRequest]:
        """Convert a confirmed gesture into a playback request.

        Returns None when audio is disabled, the gesture is unsupported, or a
        duplicate is suppressed.
        """
        if not self.enabled:
            return None

        text = GESTURE_TEXT.get(gesture.upper())
        if text is None:
            return None

        if self.config.duplicate_prevention and gesture == self._last_announced:
            return None

        request = PlaybackRequest(text=text, gesture=gesture, timestamp=__import__("time").time())
        self._queue.append(request)
        self._last_announced = gesture
        return request

    def replay_latest(self) -> Optional[PlaybackRequest]:
        """Replay the most recent announcement if available."""
        if not self.enabled or self._last_announced is None:
            return None
        text = GESTURE_TEXT.get(self._last_announced.upper())
        if text is None:
            return None
        request = PlaybackRequest(text=text, gesture=self._last_announced, timestamp=__import__("time").time())
        self._queue.append(request)
        return request

    def clear_queue(self) -> None:
        self._queue.clear()

    @property
    def queue_size(self) -> int:
        return len(self._queue)

    @property
    def last_announced(self) -> Optional[str]:
        return self._last_announced
