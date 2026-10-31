"""Unit tests for audio service duplicate prevention."""

from __future__ import annotations

from server.audio_service import AudioService


def test_audio_mapping_returns_text() -> None:
    service = AudioService()
    request = service.request_playback("HELLO")
    assert request is not None
    assert request.text == "Hello"


def test_duplicate_prevention() -> None:
    service = AudioService()
    service.request_playback("HELLO")
    duplicate = service.request_playback("HELLO")
    assert duplicate is None
