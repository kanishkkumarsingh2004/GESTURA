"""Pydantic models for the Contribute a Gesture pipeline."""

from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel, Field


class FrameMetadata(BaseModel):
    frame_id: str
    filename: str
    thumb_filename: str
    timestamp_ms: float
    frame_index: int
    width: int
    height: int
    sharpness_score: float
    is_blurry: bool
    is_duplicate: bool
    is_dark: bool
    status: str = "active"  # "active" | "removed"


class QualityReport(BaseModel):
    total_frames_extracted: int
    usable_frames_count: int
    blurry_frames_count: int
    duplicate_frames_count: int
    dark_frames_count: int
    warnings: List[str] = Field(default_factory=list)


class ContributionMetadata(BaseModel):
    contribution_id: str
    status: str = "uploaded"  # uploaded, extracted, pending_approval, approved, rejected
    video_filename: str
    video_duration_seconds: float
    video_fps: float
    video_resolution: List[int]
    total_video_frames: int

    # Gesture information (filled during submission)
    gesture_name: Optional[str] = None
    meaning: Optional[str] = None
    sign_language: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    gesture_type: Optional[str] = "dynamic"  # "static", "dynamic", "unknown"
    contributor_id: Optional[str] = "anonymous"

    # Extraction settings & results
    sample_interval: int = 5
    usable_frame_count: int = 0
    quality_report: Optional[QualityReport] = None

    rejection_reason: Optional[str] = None
    created_at: float
    updated_at: float


class ContributionUploadResponse(BaseModel):
    contribution_id: str
    video_filename: str
    duration_seconds: float
    fps: float
    resolution: List[int]
    total_video_frames: int
    status: str


class ExtractFramesRequest(BaseModel):
    sample_interval: int = Field(default=5, ge=1, le=60, description="Extract every N-th frame")
    max_frames: int = Field(default=40, ge=3, le=120, description="Maximum frames to extract")


class ExtractFramesResponse(BaseModel):
    contribution_id: str
    sample_interval: int
    total_extracted: int
    usable_count: int
    quality_report: QualityReport
    frames: List[FrameMetadata]


class FrameListResponse(BaseModel):
    contribution_id: str
    total_frames: int
    active_frames: int
    frames: List[FrameMetadata]


class SubmitContributionRequest(BaseModel):
    gesture_name: str = Field(..., min_length=2, max_length=50)
    meaning: str = Field(..., min_length=2, max_length=200)
    sign_language: str = Field(..., min_length=2, max_length=50)
    category: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=1000)
    gesture_type: str = Field(default="dynamic", pattern="^(static|dynamic|unknown)$")
    contributor_id: Optional[str] = Field(default="anonymous", max_length=100)


class ReviewContributionRequest(BaseModel):
    approved: bool
    rejection_reason: Optional[str] = None


class ContributionSummary(BaseModel):
    contribution_id: str
    gesture_name: Optional[str]
    meaning: Optional[str]
    sign_language: Optional[str]
    category: Optional[str]
    gesture_type: Optional[str]
    video_duration_seconds: float
    usable_frame_count: int
    status: str
    created_at: float


class ContributionListResponse(BaseModel):
    count: int
    contributions: List[ContributionSummary]

