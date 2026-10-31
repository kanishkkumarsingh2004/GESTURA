"""Charts component for training history and confusion matrix."""

from __future__ import annotations

from pathlib import Path

import streamlit as st


def render_image_chart(image_path: str | Path, caption: str = "") -> None:
    """Render a saved plot image if it exists."""
    path = Path(image_path)
    if path.exists():
        st.image(str(path), caption=caption, use_container_width=True)
    else:
        st.info(f"No chart available at {path}")
