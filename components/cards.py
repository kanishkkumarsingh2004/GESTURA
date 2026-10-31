"""Reusable metric and status cards."""

from __future__ import annotations

import streamlit as st


def metric_card(label: str, value: str, delta: str | None = None) -> None:
    """Render a single metric card."""
    st.metric(label=label, value=value, delta=delta)


def status_card(title: str, status: str, ok: bool = True) -> None:
    """Render a status indicator card."""
    color = "#10b981" if ok else "#ef4444"
    st.markdown(
        f"""
        <div style="padding:1rem;border-radius:0.5rem;background:#1f2937;border:1px solid #374151;margin-bottom:0.5rem;">
            <div style="color:#9ca3af;font-size:0.85rem;">{title}</div>
            <div style="color:{color};font-weight:600;">{status}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
