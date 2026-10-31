"""Navbar / header component."""

from __future__ import annotations

import streamlit as st


def render_navbar(title: str = "Gesture Recognition Assistant") -> None:
    """Render a minimal app header."""
    st.markdown(
        f"""
        <div class="navbar">
            <h1>{title}</h1>
            <span class="status-badge">Real-time inference</span>
        </div>
        """,
        unsafe_allow_html=False,
    )
    st.markdown(f"### {title}")
