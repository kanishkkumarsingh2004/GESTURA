"""Live Detection page: camera streaming, real-time predictions, audio."""

from __future__ import annotations

import streamlit as st
from streamlit_webrtc import WebRtcMode, webrtc_streamer

from components.audio_controls import render_audio_controls
from components.camera_view import render_camera_controls, render_camera_placeholder
from components.prediction_view import render_prediction
from components.sidebar import render_sidebar
from model.inference import InferenceEngine
from server.audio_service import GESTURE_TEXT, AudioService
from server.prediction_service import DetectionConfig, PredictionService
from utils.logging import get_app_logger

logger = get_app_logger(__name__)


def _init_session_state() -> None:
    defaults = {
        "model_loaded": False,
        "model_info": {},
        "inference_engine": None,
        "prediction_service": None,
        "audio_service": None,
        "camera_status": "disconnected",
        "detection_enabled": False,
        "audio_enabled": True,
        "current_gesture": None,
        "current_confidence": None,
        "prediction_history": [],
        "camera_start": False,
        "camera_stop": False,
        "audio_enable": False,
        "audio_disable": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_resource
def _get_inference_engine() -> InferenceEngine:
    return InferenceEngine()


def render_live_detection() -> None:
    render_sidebar()
    _init_session_state()
    st.title("Live Detection")

    inference_engine: InferenceEngine = _get_inference_engine()

    # Lazy load model once per session.
    if not st.session_state["model_loaded"]:
        try:
            inference_engine.load_model()
            st.session_state["model_loaded"] = True
            st.session_state["model_info"] = inference_engine.get_model_info()
            st.session_state["prediction_service"] = PredictionService(
                config=DetectionConfig(
                    confidence_threshold=st.session_state.get("confidence_threshold", 0.85),
                    confirmation_frames=st.session_state.get("confirmation_frames", 5),
                    smoothing_window=st.session_state.get("smoothing_window", 5),
                    cooldown_seconds=st.session_state.get("cooldown_seconds", 1.5),
                )
            )
            st.session_state["audio_service"] = AudioService()
            st.session_state["audio_service"].enabled = st.session_state["audio_enabled"]
            logger.info("Model loaded for inference")
        except Exception as exc:  # noqa: BLE001 - surface friendly message
            st.error(f"Model unavailable: {exc}")
            logger.error("Model load failed: %s", exc)

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("Camera")
        render_camera_placeholder()
        render_camera_controls(st.session_state["detection_enabled"])

        # Handle camera start/stop actions.
        if st.session_state.pop("camera_start", False):
            st.session_state["detection_enabled"] = True
            st.session_state["camera_status"] = "active"
            st.rerun()
        if st.session_state.pop("camera_stop", False):
            st.session_state["detection_enabled"] = False
            st.session_state["camera_status"] = "disconnected"
            st.session_state["current_gesture"] = None
            st.session_state["current_confidence"] = None
            if st.session_state.get("prediction_service"):
                st.session_state["prediction_service"].reset()
            st.rerun()

        status = st.session_state["camera_status"]
        st.caption(f"Camera status: {status}")

        st.markdown("### Detection")
        render_prediction(
            st.session_state.get("current_gesture"),
            st.session_state.get("current_confidence"),
        )

    with col_right:
        st.subheader("Audio")
        render_audio_controls(st.session_state["audio_enabled"])

        if st.session_state.pop("audio_enable", False):
            st.session_state["audio_enabled"] = True
            if st.session_state.get("audio_service"):
                st.session_state["audio_service"].enable()
            st.rerun()
        if st.session_state.pop("audio_disable", False):
            st.session_state["audio_enabled"] = False
            if st.session_state.get("audio_service"):
                st.session_state["audio_service"].disable()
            st.rerun()

        latest = st.session_state.get("current_gesture")
        if latest:
            st.markdown("**Latest spoken phrase:**")
            st.write(GESTURE_TEXT.get(latest.upper(), latest))

        st.markdown("### Detection Settings")
        st.number_input(
            "Confidence threshold", 0.0, 1.0,
            st.session_state.get("confidence_threshold", 0.85),
            0.05, key="confidence_threshold",
        )
        st.number_input(
            "Confirmation frames", 1, 20,
            st.session_state.get("confirmation_frames", 5),
            1, key="confirmation_frames",
        )
        st.number_input(
            "Cooldown (seconds)", 0.0, 10.0,
            st.session_state.get("cooldown_seconds", 1.5),
            0.5, key="cooldown_seconds",
        )

    st.markdown("---")
    st.subheader("Prediction History (this session)")
    history = st.session_state.get("prediction_history", [])
    if history:
        for entry in history[-20:][::-1]:
            st.write(f"{entry.get('gesture', '—')} — {entry.get('confidence', 0):.1%}")
    else:
        st.info("No predictions yet.")

    if st.button("Clear History", use_container_width=True):
        st.session_state["prediction_history"] = []
        st.rerun()


# WebRTC streamer configured but frame processing is orchestrated by the
# prediction service; the browser camera remains the source of frames.
webrtc_streamer(
    key="gesture-camera",
    mode=WebRtcMode.SENDRECV,
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={"video": True, "audio": False},
)


if __name__ == "__main__":
    render_live_detection()
