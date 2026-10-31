"""FastAPI HTTP API exposing gesture recognition to external frontends.

Provides REST endpoints for image-based prediction, model metadata, gesture
vocabulary, and per-session detection/audio state. The PyTorch model is loaded
once and shared (read-only) across sessions; per-session prediction
stabilization and audio state are isolated. Camera frames are processed in
memory and never persisted.
"""

from __future__ import annotations

import threading
from typing import Any, Optional
from uuid import uuid4

import cv2
import numpy as np
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse

from model.inference import InferenceEngine, PredictionResult
from server.api_models import (
    AudioControlResponse,
    AudioPlaybackInfo,
    AudioStatusResponse,
    DetectionControlResponse,
    DetectionStatusResponse,
    ErrorResponse,
    GestureMapEntry,
    GesturesResponse,
    HealthResponse,
    ModelInfoResponse,
    PredictResponse,
    StableEventInfo,
)
from server.audio_service import GESTURE_TEXT, AudioService
from server.auth import verify_admin_key
from server.camera_server import CameraServer
from server.contribution_models import (
    ApprovedDatasetResponse,
    ContributionListResponse,
    ContributionMetadata,
    ContributionUploadResponse,
    DatasetStatsResponse,
    ExtractFramesRequest,
    ExtractFramesResponse,
    FrameListResponse,
    GeoRegionsResponse,
    GeoStatesResponse,
    ReviewContributionRequest,
    SignLanguageTypeItem,
    SignLanguageTypesResponse,
    SubmitContributionRequest,
)
from server.contribution_service import ContributionService
from server.india_geo_config import (
    get_all_regions,
    get_sign_language_type_details,
    get_states_for_region,
)
from server.prediction_service import PredictionService, StablePredictionEvent
from server.session_manager import SessionState
from utils.logging import get_app_logger
from utils.preprocessing import (
    PreprocessingError,
    Preprocessor,
    load_preprocessing_config,
)

logger = get_app_logger("api")

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class _SessionScope:
    """Per-session mutable state isolated from other sessions."""

    __slots__ = (
        "session_id",
        "prediction_service",
        "audio_service",
        "camera_server",
        "session_state",
        "latest_confidence",
    )

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.prediction_service = PredictionService()
        self.audio_service = AudioService()
        self.camera_server = CameraServer()
        self.session_state = SessionState()
        self.latest_confidence: Optional[float] = None


class GestureAPI:
    """FastAPI application wrapping the gesture recognition services."""

    def __init__(
        self,
        config_path: str = "config.yaml",
        engine: Optional[InferenceEngine] = None,
        contribution_service: Optional[ContributionService] = None,
    ) -> None:
        self.config_path = config_path
        self.preprocessor = Preprocessor(load_preprocessing_config(config_path))
        self.engine: InferenceEngine = engine or InferenceEngine(
            config_path=config_path
        )
        self.contribution_service: ContributionService = (
            contribution_service or ContributionService()
        )
        self._engine_lock = threading.Lock()
        self._sessions: dict[str, _SessionScope] = {}
        self._sessions_lock = threading.Lock()

    # ------------------------------------------------------------------ lifecycle
    def ensure_model_loaded(self) -> None:
        """Load the model once, lazily, on first request."""
        if not self.engine._loaded:  # noqa: SLF001 - internal coordinator
            try:
                self.engine.load_model()
            except Exception as exc:  # noqa: BLE001 - surface a clean 503
                logger.error("Model load failed: %s", exc)
                raise RuntimeError(f"Failed to load model: {exc}") from exc

    # ---------------------------------------------------------------- sessions
    def _resolve_session_id(
        self, session_id: Optional[str], header: Optional[str]
    ) -> str:
        if session_id:
            return session_id
        if header:
            return header
        return str(uuid4())

    def _get_or_create(self, session_id: str) -> _SessionScope:
        with self._sessions_lock:
            scope = self._sessions.get(session_id)
            if scope is None:
                scope = _SessionScope(session_id)
                self._sessions[session_id] = scope
            return scope

    def _remove_session(self, session_id: str) -> None:
        with self._sessions_lock:
            self._sessions.pop(session_id, None)

    # ------------------------------------------------------------- image input
    @staticmethod
    def _decode_image(data: bytes) -> np.ndarray:
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Image exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB",
            )
        arr = np.frombuffer(data, dtype=np.uint8)
        image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if image is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is not a valid image",
            )
        return image

    def _predict_frame(self, image_bgr: np.ndarray) -> PredictionResult:
        """Preprocess and run inference on a single frame (thread-safe)."""
        try:
            tensor = self.preprocessor.preprocess(image_bgr)  # 1xCxHxW
        except PreprocessingError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid frame: {exc}",
            ) from exc
        chw = tensor.squeeze(0).numpy().astype(np.float32)
        with self._engine_lock:
            result = self.engine.predict(chw)
        return result

    # ---------------------------------------------------------------- audio
    def _audio_playback(self, scope: _SessionScope, gesture: str) -> AudioPlaybackInfo:
        if not scope.audio_service.enabled:
            return AudioPlaybackInfo(played=False, reason="audio_disabled")
        text = GESTURE_TEXT.get(gesture.upper())
        if text is None:
            return AudioPlaybackInfo(
                played=False, gesture=gesture, reason="unsupported_gesture"
            )
        request = scope.audio_service.request_playback(gesture)
        if request is None:
            return AudioPlaybackInfo(
                played=False,
                gesture=gesture,
                text=text,
                reason="duplicate_suppressed",
            )
        return AudioPlaybackInfo(
            played=True, text=request.text, gesture=request.gesture
        )

    # ---------------------------------------------------------------- app
    def build_app(self) -> FastAPI:
        app = FastAPI(title="Gesture Recognition API", version="1.0.0")

        @app.get("/health", response_model=HealthResponse)
        def health() -> HealthResponse:
            try:
                self.ensure_model_loaded()
            except RuntimeError:
                return HealthResponse(status="degraded", model_loaded=False)
            return HealthResponse(status="ok", model_loaded=True)

        @app.get("/model/info", response_model=ModelInfoResponse)
        def model_info() -> ModelInfoResponse:
            try:
                self.ensure_model_loaded()
            except RuntimeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=str(exc),
                ) from exc
            info = self.engine.get_model_info()
            return ModelInfoResponse(**info)

        @app.get("/gestures", response_model=GesturesResponse)
        def gestures() -> GesturesResponse:
            try:
                self.ensure_model_loaded()
            except RuntimeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=str(exc),
                ) from exc
            info = self.engine.get_model_info()
            class_names: list[str] = info.get("class_names", [])
            entries: list[GestureMapEntry] = []
            for idx, name in enumerate(class_names):
                entries.append(
                    GestureMapEntry(
                        class_id=idx,
                        class_name=name,
                        text=GESTURE_TEXT.get(name.upper(), name),
                    )
                )
            return GesturesResponse(classes=entries, count=len(entries))

        @app.post(
            "/predict",
            response_model=PredictResponse,
            responses={400: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
        )
        async def predict(
            image: UploadFile = File(...),
            session_id: Optional[str] = Form(None),
            x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
        ) -> PredictResponse:
            resolved_id = self._resolve_session_id(session_id, x_session_id)
            scope = self._get_or_create(resolved_id)

            try:
                self.ensure_model_loaded()
            except RuntimeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=str(exc),
                ) from exc

            data = await image.read()
            image_bgr = self._decode_image(data)

            result = self._predict_frame(image_bgr)
            scope.latest_confidence = result.confidence

            # Run prediction stabilization for this session only.
            event: Optional[StablePredictionEvent] = scope.prediction_service.update(
                result
            )
            stable = event is not None

            audio = AudioPlaybackInfo(played=False, reason="not_stable")
            if stable and scope.session_state.detection_enabled:
                scope.session_state.latest_prediction = result.class_name
                scope.session_state.add_prediction(
                    gesture=result.class_name,
                    confidence=result.confidence,
                    audio_played=False,
                )
                audio = self._audio_playback(scope, result.class_name)
                if audio.played:
                    # Mark the history entry's latest audio state.
                    if scope.session_state.prediction_history:
                        scope.session_state.prediction_history[-1]["audio_played"] = (
                            True
                        )

            return PredictResponse(
                session_id=resolved_id,
                class_id=result.class_id,
                class_name=result.class_name,
                confidence=result.confidence,
                probabilities=result.probabilities,
                inference_time_ms=result.inference_time_ms,
                detection_enabled=scope.session_state.detection_enabled,
                audio_enabled=scope.session_state.audio_enabled,
                stable=stable,
                stable_event=(
                    StableEventInfo(
                        event_id=event.event_id,
                        class_name=event.class_name,
                        confidence=event.confidence,
                        timestamp=event.timestamp,
                    )
                    if event
                    else None
                ),
                audio=audio,
            )

        @app.get(
            "/session/{session_id}/status",
            response_model=DetectionStatusResponse,
        )
        def detection_status(session_id: str) -> DetectionStatusResponse:
            scope = self._get_or_create(session_id)
            return DetectionStatusResponse(
                session_id=session_id,
                camera_connected=scope.session_state.camera_connected,
                detection_enabled=scope.session_state.detection_enabled,
                audio_enabled=scope.session_state.audio_enabled,
                latest_prediction=scope.session_state.latest_prediction,
                latest_confidence=scope.latest_confidence,
                state=scope.prediction_service.state,
                history_count=len(scope.session_state.prediction_history),
            )

        @app.post(
            "/session/{session_id}/detection/start",
            response_model=DetectionControlResponse,
        )
        def detection_start(session_id: str) -> DetectionControlResponse:
            scope = self._get_or_create(session_id)
            scope.camera_server.start()
            scope.session_state.camera_connected = True
            scope.session_state.detection_enabled = True
            return DetectionControlResponse(
                session_id=session_id,
                detection_enabled=True,
                camera_status=scope.camera_server.status,
            )

        @app.post(
            "/session/{session_id}/detection/stop",
            response_model=DetectionControlResponse,
        )
        def detection_stop(session_id: str) -> DetectionControlResponse:
            scope = self._get_or_create(session_id)
            scope.camera_server.stop()
            scope.session_state.camera_connected = False
            scope.session_state.detection_enabled = False
            return DetectionControlResponse(
                session_id=session_id,
                detection_enabled=False,
                camera_status=scope.camera_server.status,
            )

        @app.post(
            "/session/{session_id}/audio/enable",
            response_model=AudioControlResponse,
        )
        def audio_enable(session_id: str) -> AudioControlResponse:
            scope = self._get_or_create(session_id)
            scope.audio_service.enable()
            scope.session_state.audio_enabled = True
            return AudioControlResponse(session_id=session_id, audio_enabled=True)

        @app.post(
            "/session/{session_id}/audio/disable",
            response_model=AudioControlResponse,
        )
        def audio_disable(session_id: str) -> AudioControlResponse:
            scope = self._get_or_create(session_id)
            scope.audio_service.disable()
            scope.session_state.audio_enabled = False
            return AudioControlResponse(session_id=session_id, audio_enabled=False)

        @app.get(
            "/session/{session_id}/audio/status",
            response_model=AudioStatusResponse,
        )
        def audio_status(session_id: str) -> AudioStatusResponse:
            scope = self._get_or_create(session_id)
            return AudioStatusResponse(
                session_id=session_id,
                enabled=scope.audio_service.enabled,
                last_announced=scope.audio_service.last_announced,
                queue_size=scope.audio_service.queue_size,
            )

        @app.get(
            "/session/{session_id}/history",
            response_model=dict[str, Any],
        )
        def history(session_id: str) -> dict[str, Any]:
            scope = self._get_or_create(session_id)
            return {
                "session_id": session_id,
                "count": len(scope.session_state.prediction_history),
                "history": list(scope.session_state.prediction_history),
            }

        @app.delete("/session/{session_id}/history")
        def clear_history(session_id: str) -> dict[str, str]:
            scope = self._get_or_create(session_id)
            scope.session_state.clear_history()
            return {"session_id": session_id, "history": "cleared"}

        @app.post("/session/{session_id}/reset", response_model=dict[str, str])
        def reset_session(session_id: str) -> dict[str, str]:
            scope = self._get_or_create(session_id)
            scope.prediction_service.reset()
            scope.audio_service.clear_queue()
            scope.session_state.clear_history()
            scope.session_state.latest_prediction = None
            scope.latest_confidence = None
            return {"session_id": session_id, "status": "reset"}

        @app.delete("/session/{session_id}")
        def remove_session(session_id: str) -> dict[str, str]:
            self._remove_session(session_id)
            return {"session_id": session_id, "status": "removed"}

        # ------------------------------------------------ contributions - geography
        @app.get(
            "/contributions/geo/regions",
            response_model=GeoRegionsResponse,
            tags=["Contributions - Geography"],
            summary="List configured Indian regions",
            description="Returns all six configured Indian geographical regions for gesture contribution provenance.",
        )
        def get_geo_regions() -> GeoRegionsResponse:
            regions = get_all_regions()
            return GeoRegionsResponse(
                country="India",
                regions=regions,
                count=len(regions),
            )

        @app.get(
            "/contributions/geo/states",
            response_model=GeoStatesResponse,
            tags=["Contributions - Geography"],
            summary="List states and UTs for an Indian region",
            description="Returns all states and union territories belonging to the specified Indian geographical region.",
        )
        def get_geo_states(
            region: str = Query(..., description="Indian region name (e.g. NORTH, SOUTH, EAST, WEST, CENTRAL, NORTHEAST)"),
        ) -> GeoStatesResponse:
            try:
                states = get_states_for_region(region)
                return GeoStatesResponse(
                    region=region.strip().upper(),
                    states=states,
                    count=len(states),
                )
            except ValueError as err:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(err),
                ) from err

        @app.get(
            "/contributions/geo/sign-language-types",
            response_model=SignLanguageTypesResponse,
            tags=["Contributions - Geography"],
            summary="List supported sign language types and validation requirements",
            description="Returns supported sign language classifications (ISL, Regional ISL Variant, etc.) and validation rules.",
        )
        def get_geo_sign_language_types() -> SignLanguageTypesResponse:
            details = get_sign_language_type_details()
            items = [SignLanguageTypeItem(**d) for d in details]
            return SignLanguageTypesResponse(
                types=items,
                count=len(items),
            )

        # ------------------------------------------------ contributions - dataset
        @app.get(
            "/contributions/dataset/stats",
            response_model=DatasetStatsResponse,
            tags=["Contributions - Dataset"],
            summary="Get dataset contribution statistics",
            description="Returns aggregated metrics on contributions: totals, pending, approved, rejected, breakdowns by region, state, sign language variety, and total extracted frames.",
        )
        def get_dataset_stats() -> DatasetStatsResponse:
            return self.contribution_service.get_dataset_stats()

        @app.get(
            "/contributions/dataset/approved",
            response_model=ApprovedDatasetResponse,
            tags=["Contributions - Dataset"],
            summary="List approved contributions (public dataset)",
            description="Returns paginated metadata for approved contributions. Excludes private contributor details, raw video files, and internal server filesystem paths.",
        )
        def get_approved_dataset(
            page: int = Query(1, ge=1, description="Page number (1-based)"),
            page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
            region: Optional[str] = Query(None, description="Filter by Indian region (NORTH, SOUTH, etc.)"),
            state: Optional[str] = Query(None, description="Filter by Indian state or UT"),
            sign_language_type: Optional[str] = Query(None, description="Filter by sign language variety type"),
            gesture_name: Optional[str] = Query(None, description="Filter by gesture name (partial match)"),
        ) -> ApprovedDatasetResponse:
            return self.contribution_service.get_approved_contributions(
                page=page,
                page_size=page_size,
                region=region,
                state=state,
                sign_language_type=sign_language_type,
                gesture_name=gesture_name,
            )

        # ------------------------------------------------ contributions - ingestion
        @app.post(
            "/contributions/upload",
            response_model=ContributionUploadResponse,
            status_code=status.HTTP_201_CREATED,
            tags=["Contributions - Ingestion"],
            summary="Upload gesture video sample",
            description="Uploads an MP4/WebM/MOV gesture video, validates file format, duration and size limits, and creates a staging contribution record.",
        )
        async def upload_contribution(
            file: UploadFile = File(...),
        ) -> ContributionUploadResponse:
            meta = await self.contribution_service.handle_video_upload(file)
            return ContributionUploadResponse(
                contribution_id=meta.contribution_id,
                video_filename=meta.video_filename,
                duration_seconds=meta.video_duration_seconds,
                fps=meta.video_fps,
                resolution=meta.video_resolution,
                total_video_frames=meta.total_video_frames,
                status=meta.status,
            )

        @app.post(
            "/contributions/{contribution_id}/extract",
            response_model=ExtractFramesResponse,
            tags=["Contributions - Ingestion"],
            summary="Extract and analyze video frames",
            description="Extracts candidate gesture frames at sample_interval, generates thumbnails, and computes blur/duplicate/darkness metrics.",
        )
        def extract_contribution_frames(
            contribution_id: str,
            payload: ExtractFramesRequest = ExtractFramesRequest(),
        ) -> ExtractFramesResponse:
            return self.contribution_service.extract_and_validate_frames(
                contribution_id=contribution_id,
                sample_interval=payload.sample_interval,
                max_frames=payload.max_frames,
            )

        @app.get(
            "/contributions/{contribution_id}",
            response_model=ContributionMetadata,
            tags=["Contributions - Ingestion"],
            summary="Get contribution status and metadata",
            description="Retrieves the complete internal metadata for a contribution.",
        )
        def get_contribution(contribution_id: str) -> ContributionMetadata:
            return self.contribution_service.get_contribution(contribution_id)

        @app.get(
            "/contributions/{contribution_id}/frames",
            response_model=FrameListResponse,
            tags=["Contributions - Ingestion"],
            summary="List extracted frame metadata",
            description="Returns all extracted frames and their status (active or removed) for a contribution.",
        )
        def get_contribution_frames(contribution_id: str) -> FrameListResponse:
            frames = self.contribution_service.get_frames(contribution_id)
            active = sum(1 for f in frames if f.status == "active")
            return FrameListResponse(
                contribution_id=contribution_id,
                total_frames=len(frames),
                active_frames=active,
                frames=frames,
            )

        @app.get(
            "/contributions/{contribution_id}/frames/{frame_id}",
            tags=["Contributions - Ingestion"],
            summary="Retrieve full frame image",
            description="Streams the full resolution JPEG image of an extracted frame.",
        )
        def get_contribution_frame_file(
            contribution_id: str, frame_id: str
        ) -> FileResponse:
            file_path = self.contribution_service.get_frame_file_path(
                contribution_id, frame_id, thumb=False
            )
            return FileResponse(file_path, media_type="image/jpeg")

        @app.get(
            "/contributions/{contribution_id}/frames/{frame_id}/thumb",
            tags=["Contributions - Ingestion"],
            summary="Retrieve thumbnail image",
            description="Streams the lightweight thumbnail JPEG image of an extracted frame.",
        )
        def get_contribution_frame_thumb(
            contribution_id: str, frame_id: str
        ) -> FileResponse:
            file_path = self.contribution_service.get_frame_file_path(
                contribution_id, frame_id, thumb=True
            )
            return FileResponse(file_path, media_type="image/jpeg")

        @app.delete(
            "/contributions/{contribution_id}/frames/{frame_id}",
            tags=["Contributions - Ingestion"],
            summary="Exclude frame from contribution",
            description="Marks an extracted frame as removed/unusable so it is excluded from dataset export.",
        )
        def delete_contribution_frame(
            contribution_id: str, frame_id: str
        ) -> dict[str, Any]:
            return self.contribution_service.delete_frame(
                contribution_id, frame_id
            )

        @app.post(
            "/contributions/{contribution_id}/submit",
            response_model=ContributionMetadata,
            tags=["Contributions - Ingestion"],
            summary="Submit gesture metadata and annotations",
            description="Validates India geographic hierarchy, sign language classification, gesture semantics, and moves contribution to pending review.",
        )
        def submit_contribution(
            contribution_id: str,
            payload: SubmitContributionRequest,
        ) -> ContributionMetadata:
            return self.contribution_service.submit_contribution(
                contribution_id, payload
            )

        # ------------------------------------------------ contributions - moderation
        @app.get(
            "/contributions",
            response_model=ContributionListResponse,
            tags=["Contributions - Moderation"],
            summary="List contributions with optional filters (Admin only)",
            description="Lists contributions across pending, approved, and rejected datasets with optional status and region filters. Requires administrative authentication via X-Admin-Key.",
        )
        def list_contributions(
            status: Optional[str] = Query(None, description="Filter by status (pending, approved, rejected)"),
            region: Optional[str] = Query(None, description="Filter by region (NORTH, SOUTH, etc.)"),
            _admin_key: str = Depends(verify_admin_key),
        ) -> ContributionListResponse:
            items = self.contribution_service.list_contributions(
                status_filter=status, region_filter=region
            )
            return ContributionListResponse(
                count=len(items), contributions=items
            )

        @app.post(
            "/contributions/{contribution_id}/review",
            response_model=ContributionMetadata,
            tags=["Contributions - Moderation"],
            summary="Review and approve/reject contribution (Admin only)",
            description="Approves or rejects a submitted contribution. Requires administrative authentication via X-Admin-Key.",
        )
        def review_contribution(
            contribution_id: str,
            payload: ReviewContributionRequest,
            _admin_key: str = Depends(verify_admin_key),
        ) -> ContributionMetadata:
            return self.contribution_service.review_contribution(
                contribution_id=contribution_id,
                approved=payload.approved,
                rejection_reason=payload.rejection_reason,
            )

        return app


# Module-level application instance for `uvicorn server.api:app`.
api = GestureAPI()
app = api.build_app()
