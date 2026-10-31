"""Sidebar navigation and status component."""

from __future__ import annotations

import streamlit as st


def render_sidebar() -> None:
    """Render the application sidebar with navigation and quick status."""
    with st.sidebar:
        st.markdown("## Gesture Assistant")
        st.markdown("---")
        st.page_link("app.py", label="Dashboard", icon="🏠")
        st.page_link("pages/02_Live_Detection.py", label="Live Detection", icon="📹")
        st.page_link("pages/03_Prediction_History.py", label="Prediction History", icon="📜")
        st.page_link("pages/04_Model_Information.py", label="Model Information", icon="🧠")
        st.page_link("pages/05_Settings.py", label="Settings", icon="⚙️")
        st.markdown("---")
        st.caption("Real-Time Gesture Recognition v1.0.0")
