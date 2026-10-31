"""Model Information page: actual model metadata from the loaded model."""

from __future__ import annotations

import streamlit as st

from components.sidebar import render_sidebar
from model.inference import InferenceEngine


@st.cache_resource
def _get_inference_engine() -> InferenceEngine:
    return InferenceEngine()


def render_model_information() -> None:
    render_sidebar()
    st.title("Model Information")

    engine = _get_inference_engine()

    if st.button("Load / Refresh Model", use_container_width=True):
        try:
            engine.load_model()
            st.success("Model loaded successfully.")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Failed to load model: {exc}")

    info = engine.get_model_info()

    st.markdown("### Model Metadata")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Architecture:**", info.get("architecture", "—"))
        st.write("**Number of classes:**", info.get("num_classes", "—"))
        st.write("**Device:**", info.get("device", "—"))
        st.write("**Loaded:**", "Yes" if info.get("loaded") else "No")
    with col2:
        st.write("**Input size:**", " × ".join(map(str, info.get("input_size", []))) or "—")
        metadata = info.get("metadata", {})
        st.write("**Version:**", metadata.get("version", "—"))
        st.write("**Checkpoint:**", metadata.get("checkpoint", "—"))

    st.markdown("### Supported Gestures")
    class_names = info.get("class_names", [])
    if class_names:
        for name in class_names:
            st.write(f"- {name}")
    else:
        st.info("No class information available.")

    st.markdown("### Preprocessing")
    prep = metadata.get("preprocessing", {})
    if prep:
        st.json(prep)
    else:
        st.info("No preprocessing metadata recorded.")


if __name__ == "__main__":
    render_model_information()
