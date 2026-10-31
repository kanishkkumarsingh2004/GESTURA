"""Application entry point.

Lightweight orchestrator: initializes Streamlit, loads configuration,
configures logging, initializes session state and renders the selected page.
Contains no model architecture, training, camera processing or audio logic.
"""

from __future__ import annotations

import streamlit as st

from components.sidebar import render_sidebar
from utils.logging import get_app_logger

logger = get_app_logger(__name__)


def initialize_session_state() -> None:
    """Initialize session-scoped state with safe defaults."""
    defaults = {
        "model_loaded": False,
        "model_info": {},
        "camera_status": "disconnected",
        "detection_enabled": True,
        "audio_enabled": True,
        "current_gesture": None,
        "current_confidence": None,
        "prediction_history": [],
        "confidence_threshold": 0.85,
        "confirmation_frames": 5,
        "smoothing_window": 5,
        "cooldown_seconds": 1.5,
        "max_history": 1000,
        "target_fps": 20,
        "frame_skip": 2,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main() -> None:
    st.set_page_config(
        page_title="Gesture Recognition Assistant",
        page_icon="👋",
        layout="wide",
    )

    initialize_session_state()

    # Inject custom CSS for the dark theme design system.
    st.markdown(
        """
        <style>
        .stApp { background-color: #0f172a; color: #e2e8f0; }
        .stMetric { background: #1e293b; border: 1px solid #334155; border-radius: 0.5rem; padding: 0.75rem; }
        .stButton>button { background-color: #3b82f6; color: white; border-radius: 0.5rem; }
        .stButton>button:hover { background-color: #2563eb; }
        h1, h2, h3 { color: #f8fafc; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    logger.info("Application starting")
    render_sidebar()
    st.title("Gesture Recognition Assistant")
    st.caption("Real-time hand gesture recognition with spoken audio output")

    st.markdown(
        "Welcome to the Gesture Recognition Assistant. Use the sidebar to navigate "
        "to Live Detection, Prediction History, Model Information or Settings."
    )

    st.markdown("### Status")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Model", "Loaded" if st.session_state["model_loaded"] else "Not loaded")
    with col2:
        st.metric("Camera", st.session_state["camera_status"].capitalize())
    with col3:
        st.metric("Detection", "On" if st.session_state["detection_enabled"] else "Off")
    with col4:
        st.metric("Audio", "On" if st.session_state["audio_enabled"] else "Off")

    logger.info("Application initialized")


if __name__ == "__main__":
    main()
