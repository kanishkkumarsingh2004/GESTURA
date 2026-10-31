"""Camera view component for live preview rendering."""

from __future__ import annotations

import streamlit as st


def render_camera_placeholder() -> None:
    """Render the live camera preview container."""
    st.markdown("### Live Camera Preview")
    st.info("Camera stream appears here once detection is started.")


def render_camera_controls(running: bool) -> None:
    """Render start/stop camera controls."""
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Camera", disabled=running, type="primary", use_container_width=True):
            st.session_state["camera_start"] = True
    with col2:
        if st.button("Stop Camera", disabled=not running, use_container_width=True):
            st.session_state["camera_stop"] = True
