"""Camera view component: live preview, hand bounding box, and predictions."""

from __future__ import annotations

import threading

import av
import cv2
import mediapipe as mp
import numpy as np
import streamlit as st
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from streamlit_webrtc import WebRtcMode, webrtc_streamer

from model.inference import InferenceEngine
from utils.assets import ensure_hand_landmarker_model
from utils.preprocessing import Preprocessor, load_preprocessing_config

HAND_CONNECTIONS = vision.HandLandmarksConnections.HAND_CONNECTIONS
LANDMARK_STYLE = vision.drawing_styles.get_default_hand_landmarks_style()
CONNECTION_STYLE = vision.drawing_styles.get_default_hand_connections_style()

_detector: vision.HandLandmarker | None = None
_detector_error: str | None = None
_detector_lock = threading.Lock()

_lock = threading.Lock()


def _get_detector() -> vision.HandLandmarker | None:
    """Create (and download the model for) the hand landmarker on first use.

    Results are cached so the model is only downloaded once per process. A
    failed load is cached as ``None`` with the reason stored in
    ``_detector_error``.
    """
    global _detector, _detector_error
    if _detector is not None:
        return _detector
    if _detector_error is not None:
        return None
    with _detector_lock:
        if _detector is not None:
            return _detector
        if _detector_error is not None:
            return None
        try:
            model_path = ensure_hand_landmarker_model()
            _detector = vision.HandLandmarker.create_from_options(
                vision.HandLandmarkerOptions(
                    base_options=python.BaseOptions(model_asset_path=str(model_path)),
                    num_hands=1,
                    min_hand_detection_confidence=0.6,
                    min_hand_presence_confidence=0.5,
                    min_tracking_confidence=0.5,
                    running_mode=vision.RunningMode.IMAGE,
                )
            )
        except Exception as exc:  # noqa: BLE001 - surface a clear error instead of crashing
            _detector_error = str(exc)
            return None
    return _detector


def _square_bbox(bbox: tuple[int, int, int, int], width: int, height: int, pad: float = 0.25) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = bbox
    w = x2 - x1
    h = y2 - y1
    size = max(w, h)
    size = int(size * (1.0 + pad))
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    x1 = max(0, cx - size // 2)
    y1 = max(0, cy - size // 2)
    x2 = min(width, x1 + size)
    y2 = min(height, y1 + size)
    x1 = max(0, x2 - size)
    y1 = max(0, y2 - size)
    return x1, y1, x2, y2


def _process_frame(frame_bgr: np.ndarray, engine: InferenceEngine, preprocessor: Preprocessor, class_names: list[str]) -> np.ndarray:
    annotated = frame_bgr.copy()
    height, width = annotated.shape[:2]

    rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
    detector = _get_detector()
    results = None
    if detector is not None:
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        results = detector.detect(image)

    gesture = None
    confidence = None

    if results is not None and results.hand_landmarks:
        landmarks = results.hand_landmarks[0]
        vision.drawing_utils.draw_landmarks(
            annotated,
            landmarks,
            connections=HAND_CONNECTIONS,
            landmark_drawing_spec=LANDMARK_STYLE,
            connection_drawing_spec=CONNECTION_STYLE,
        )

        xs = [int(lm.x * width) for lm in landmarks]
        ys = [int(lm.y * height) for lm in landmarks]
        bbox = _square_bbox((min(xs), min(ys), max(xs), max(ys)), width, height)

        cv2.rectangle(annotated, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 3)

        hand_crop = frame_bgr[bbox[1]:bbox[3], bbox[0]:bbox[2]]
        if hand_crop.size:
            try:
                tensor = preprocessor.preprocess(hand_crop)
                result = engine.predict(tensor.squeeze(0).numpy())
                gesture = result.class_name
                confidence = result.confidence
                label = f"{gesture} {confidence:.0%}"
                cv2.putText(
                    annotated,
                    label,
                    (bbox[0], max(20, bbox[1] - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA,
                )
            except Exception:
                pass

    with _lock:
        st.session_state["current_gesture"] = gesture
        st.session_state["current_confidence"] = confidence
        if gesture:
            st.session_state["detection_enabled"] = True

    return annotated


def _video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
    engine: InferenceEngine = st.session_state["inference_engine"]
    preprocessor: Preprocessor = st.session_state["preprocessor"]
    class_names: list[str] = st.session_state.get("class_names", [])
    frame_bgr = frame.to_ndarray(format="bgr24")
    annotated = _process_frame(frame_bgr, engine, preprocessor, class_names)
    return av.VideoFrame.from_ndarray(annotated, format="bgr24")


def render_camera_feed(engine: InferenceEngine) -> None:
    """Render the live camera preview with hand bounding box and prediction."""
    st.markdown("### Live Camera Preview")
    detector = _get_detector()
    if detector is None:
        st.error(
            "Hand landmarker model unavailable. Check network connectivity so "
            "the MediaPipe model can be downloaded. "
            f"Error: {_detector_error}"
        )
    if "preprocessor" not in st.session_state:
        prep_config = load_preprocessing_config()
        st.session_state["preprocessor"] = Preprocessor(prep_config)
        st.session_state["class_names"] = engine.get_model_info().get("class_names", [])

    webrtc_streamer(
        key="gesture-camera",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        media_stream_constraints={"video": True, "audio": False},
        video_frame_callback=_video_frame_callback,
        async_processing=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Stop Camera", use_container_width=True):
            st.session_state["detection_enabled"] = False
            st.session_state["camera_status"] = "disconnected"
            st.session_state["current_gesture"] = None
            st.session_state["current_confidence"] = None
            st.rerun()
    with col2:
        status = st.session_state.get("camera_status", "active")
        st.caption(f"Camera status: {status}")
