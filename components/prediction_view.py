"""Prediction view component."""

from __future__ import annotations

import streamlit as st


def render_prediction(gesture: str | None, confidence: float | None) -> None:
    """Render the current prediction and confidence."""
    st.markdown("### Current Prediction")
    if gesture is None:
        st.info("No prediction yet.")
        return
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Gesture", gesture)
    with col2:
        st.metric("Confidence", f"{confidence:.1%}" if confidence is not None else "—")
