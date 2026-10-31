"""Audio controls component."""

from __future__ import annotations

import streamlit as st


def render_audio_controls(enabled: bool) -> None:
    """Render audio enable/mute/replay controls."""
    st.markdown("### Audio")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Enable Audio", disabled=enabled, use_container_width=True):
            st.session_state["audio_enable"] = True
    with col2:
        if st.button("Disable Audio", disabled=not enabled, use_container_width=True):
            st.session_state["audio_disable"] = True

    status = "Enabled" if enabled else "Disabled"
    st.caption(f"Audio: {status}")
