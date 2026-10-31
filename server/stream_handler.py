"""WebRTC stream handler.

Receives incoming video frames, converts them to NumPy arrays and coordinates
frame processing. The callback remains lightweight: no Streamlit calls, no
model loading, no blocking audio, no unbounded thread creation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import av
import numpy as np


@dataclass
class FrameStats:
    frames_received: int = 0
    frames_processed: int = 0
    frames_dropped: int = 0
    last_fps: float = 0.0


class StreamHandler:
    """Handles WebRTC video frames and dispatches them to a processor."""

    def __init__(
        self,
        frame_processor: Optional[Callable[[np.ndarray], np.ndarray]] = None,
        frame_skip: int = 2,
    ) -> None:
        self.frame_processor = frame_processor
        self.frame_skip = max(1, frame_skip)
        self._counter = 0
        self.stats = FrameStats()

    def process_frame(self, frame: av.VideoFrame) -> av.VideoFrame:
        """Callback invoked by streamlit-webrtc for each incoming frame."""
        self.stats.frames_received += 1
        self._counter += 1

        # Frame sampling: only process selected frames to bound compute.
        if self._counter % self.frame_skip != 0:
            self.stats.frames_dropped += 1
            return frame

        image = frame.to_ndarray(format="bgr24")

        if self.frame_processor is not None:
            try:
                processed = self.frame_processor(image)
                self.stats.frames_processed += 1
                return av.VideoFrame.from_ndarray(processed, format="bgr24")
            except Exception:  # noqa: BLE001 - skip frame safely on processing error
                self.stats.frames_dropped += 1
                return frame

        self.stats.frames_processed += 1
        return frame

    def reset_stats(self) -> None:
        self.stats = FrameStats()
        self._counter = 0
