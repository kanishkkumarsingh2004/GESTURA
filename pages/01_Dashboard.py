"""Dashboard page: application overview, model status, camera status."""

from __future__ import annotations

import streamlit as st

from components.cards import metric_card, status_card
from components.sidebar import render_sidebar
from utils.logging import get_app_logger

logger = get_app_logger(__name__)


def render_dashboard() -> None:
    render_sidebar()
    st.title("Dashboard")

    # Model status
    model_loaded = st.session_state.get("model_loaded", False)
    model_info = st.session_state.get("model_info", {})
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Model", "Loaded" if model_loaded else "Not loaded", None)
    with col2:
        metric_card("Architecture", str(model_info.get("architecture", "—")), None)
    with col3:
        metric_card("Classes", str(model_info.get("num_classes", "—")), None)
    with col4:
        metric_card("Device", str(model_info.get("device", "—")), None)

    st.markdown("---")
    st.subheader("System Status")
    cam_status = st.session_state.get("camera_status", "disconnected")
    status_card("Camera", cam_status.capitalize(), ok=cam_status == "active")
    status_card("Detection", "Enabled" if st.session_state.get("detection_enabled", False) else "Disabled",
                ok=st.session_state.get("detection_enabled", False))

    st.markdown("---")
    st.subheader("Supported Gestures")
    class_names = model_info.get("class_names", [])
    if class_names:
        cols = st.columns(min(len(class_names), 4))
        for i, name in enumerate(class_names):
            cols[i % len(cols)].button(name, disabled=True, key=f"dash_gesture_{i}")
    else:
        st.info("No model loaded.")

    st.markdown("---")
    st.subheader("Recent Predictions")
    history = st.session_state.get("prediction_history", [])
    if history:
        for entry in history[-10:][::-1]:
            st.write(f"{entry.get('gesture', '—')} — {entry.get('confidence', 0):.1%}")
    else:
        st.info("No predictions yet.")

    st.markdown("---")
    st.subheader("Quick Access")
    if st.button("Go to Live Detection", type="primary", use_container_width=True):
        st.switch_page("pages/02_Live_Detection.py")


if __name__ == "__main__":
    render_dashboard()
