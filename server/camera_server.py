"""Camera server: manages WebRTC camera streaming configuration and lifecycle."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CameraConfig:
    enabled: bool = True
    target_fps: int = 20
    frame_skip: int = 2


class CameraServer:
    """Coordinates camera stream startup, shutdown and status."""

    def __init__(self, config: CameraConfig | None = None) -> None:
        self.config = config or CameraConfig()
        self._running = False
        self._status = "disconnected"

    def start(self) -> None:
        self._running = True
        self._status = "active"

    def stop(self) -> None:
        self._running = False
        self._status = "disconnected"

    @property
    def running(self) -> bool:
        return self._running

    @property
    def status(self) -> str:
        return self._status
