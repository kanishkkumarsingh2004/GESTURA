"""Settings page: detection and audio preferences."""

from __future__ import annotations

import streamlit as st

from components.sidebar import render_sidebar


def render_settings() -> None:
    render_sidebar()
    st.title("Settings")

    st.subheader("Detection")
    st.number_input(
        "Confidence threshold", 0.0, 1.0,
        st.session_state.get("confidence_threshold", 0.85),
        0.05, key="confidence_threshold",
        help="Minimum confidence to accept a prediction.",
    )
    st.number_input(
        "Confirmation frames", 1, 50,
        st.session_state.get("confirmation_frames", 5),
        1, key="confirmation_frames",
        help="Consecutive frames required to confirm a gesture.",
    )
    st.number_input(
        "Smoothing window", 1, 50,
        st.session_state.get("smoothing_window", 5),
        1, key="smoothing_window",
        help="Size of the prediction smoothing window.",
    )
    st.number_input(
        "Cooldown (seconds)", 0.0, 60.0,
        st.session_state.get("cooldown_seconds", 1.5),
        0.5, key="cooldown_seconds",
        help="Minimum time between identical announcements.",
    )

    st.subheader("Audio")
    st.checkbox(
        "Audio enabled",
        value=st.session_state.get("audio_enabled", True),
        key="audio_enabled",
    )

    st.subheader("Prediction History")
    st.number_input(
        "Max history records", 10, 10000,
        st.session_state.get("max_history", 1000),
        10, key="max_history",
    )

    st.subheader("Camera")
    st.number_input(
        "Target FPS", 1, 60,
        st.session_state.get("target_fps", 20),
        1, key="target_fps",
    )
    st.number_input(
        "Frame skip", 1, 20,
        st.session_state.get("frame_skip", 2),
        1, key="frame_skip",
    )

    st.markdown("---")
    st.caption("Settings are stored in Streamlit session state and reset on refresh.")


if __name__ == "__main__":
    render_settings()
