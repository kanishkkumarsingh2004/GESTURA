"""Prediction History page: bounded session prediction records."""

from __future__ import annotations

import streamlit as st

from components.sidebar import render_sidebar


def render_prediction_history() -> None:
    render_sidebar()
    st.title("Prediction History")

    if "prediction_history" not in st.session_state:
        st.session_state["prediction_history"] = []

    history = st.session_state["prediction_history"]
    max_history = st.session_state.get("max_history", 1000)

    st.caption(f"Showing up to {max_history} records.")
    if history:
        for entry in history[-50:][::-1]:
            st.write(
                f"{entry.get('gesture', '—')} — "
                f"{entry.get('confidence', 0):.1%} — "
                f"audio: {'played' if entry.get('audio_played') else 'skipped'}"
            )
    else:
        st.info("No predictions recorded this session.")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear Session History", use_container_width=True, type="primary"):
            st.session_state["prediction_history"] = []
            st.rerun()
    with col2:
        st.number_input(
            "Max history records", 10, 10000,
            max_history, 10, key="max_history",
        )


if __name__ == "__main__":
    render_prediction_history()
