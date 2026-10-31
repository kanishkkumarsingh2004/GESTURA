"""Comprehensive tests for the community gesture contribution pipeline.

Tests video ingestion, frame extraction, CV quality validation (blur/brightness/duplicate),
frame management, submission validation, approval workflow, and grouped leak-free splitting.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from data.contribution_dataset import (
    ContributedFrame,
    ContributedGestureSample,
    ContributionDatasetExporter,
    GroupedContributionSplitter,
)
from model.inference import PredictionResult
from server.api import GestureAPI
from server.contribution_service import ContributionService


class FakeEngine:
    """Mock engine that satisfies InferenceEngine interface without loading torch weights."""

    _loaded = True
    device = "cpu"

    def predict(self, image: Any) -> PredictionResult:  # noqa: ARG002
        return PredictionResult(
            class_id=0,
            class_name="HELLO",
            confidence=0.95,
            probabilities={"HELLO": 0.95, "NONE": 0.05},
            inference_time_ms=10.0,
        )

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "architecture": "vgg16",
            "num_classes": 2,
            "class_names": ["HELLO", "NONE"],
            "input_size": [224, 224],
            "device": "cpu",
            "loaded": True,
            "metadata": {},
        }


def _create_synthetic_video(
    filepath: Path,
    num_frames: int = 15,
    fps: float = 25.0,
    width: int = 320,
    height: int = 240,
    blurry: bool = False,
    dark: bool = False,
) -> None:
    """Helper to synthesize valid MP4 video files with predictable visual features."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(filepath), fourcc, fps, (width, height))

    for i in range(num_frames):
        if dark:
            frame = np.zeros((height, width, 3), dtype=np.uint8)
        elif blurry:
            # Low contrast uniform image produces very low Laplacian variance (<25)
            frame = np.full((height, width, 3), 120, dtype=np.uint8)
        else:
            # High contrast geometric shapes produce high Laplacian variance (>25)
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            cv2.putText(
                frame,
                f"GESTURE #{i}",
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (255, 255, 255),
                2,
            )
            cv2.rectangle(frame, (40, 70), (180, 180), (0, 255, 0), -1)
            cv2.circle(frame, (60 + (i * 10), 100), 25, (255, 0, 0), -1)
        out.write(frame)

    out.release()


@pytest.fixture()
def contrib_env(tmp_path: Path):
    """Provides an isolated ContributionService and FastAPI TestClient."""
    base_dir = tmp_path / "contributions"
    service = ContributionService(base_dir=base_dir)
    api = GestureAPI(engine=FakeEngine(), contribution_service=service)
    client = TestClient(api.build_app())
    return service, client, tmp_path


def test_upload_valid_video(contrib_env):
    service, client, tmp_path = contrib_env
    video_path = tmp_path / "sample.mp4"
    _create_synthetic_video(video_path, num_frames=20, fps=25.0)

    with open(video_path, "rb") as f:
        resp = client.post(
            "/contributions/upload",
            files={"file": ("sample.mp4", f, "video/mp4")},
        )

    assert resp.status_code == 201
    data = resp.json()
    assert "contribution_id" in data
    assert data["video_filename"] == "sample.mp4"
    assert data["duration_seconds"] > 0
    assert data["fps"] == 25.0
    assert data["status"] == "uploaded"


def test_upload_invalid_extension_rejected(contrib_env):
    _, client, tmp_path = contrib_env
    fake_txt = tmp_path / "test.txt"
    fake_txt.write_text("not a video")

    with open(fake_txt, "rb") as f:
        resp = client.post(
            "/contributions/upload",
            files={"file": ("test.txt", f, "text/plain")},
        )

    assert resp.status_code == 400
    assert "Unsupported format" in resp.json()["detail"]


def test_frame_extraction_and_cv_quality_validation(contrib_env):
    service, client, tmp_path = contrib_env
    video_path = tmp_path / "sharp_sample.mp4"
    _create_synthetic_video(video_path, num_frames=25, fps=25.0)

    with open(video_path, "rb") as f:
        upload_resp = client.post(
            "/contributions/upload",
            files={"file": ("sharp_sample.mp4", f, "video/mp4")},
        )
    cid = upload_resp.json()["contribution_id"]

    # Extract frames
    extract_resp = client.post(
        f"/contributions/{cid}/extract",
        json={"sample_interval": 5, "max_frames": 10},
    )
    assert extract_resp.status_code == 200
    extract_data = extract_resp.json()

    assert extract_data["contribution_id"] == cid
    assert extract_data["total_extracted"] == 5
    assert extract_data["usable_count"] == 5
    assert len(extract_data["frames"]) == 5

    report = extract_data["quality_report"]
    assert report["total_frames_extracted"] == 5
    assert report["usable_frames_count"] == 5
    assert report["blurry_frames_count"] == 0

    first_frame = extract_data["frames"][0]
    assert first_frame["status"] == "active"
    assert first_frame["sharpness_score"] > 25.0
    assert first_frame["is_blurry"] is False


def test_frame_retrieval_and_thumbnails(contrib_env):
    service, client, tmp_path = contrib_env
    video_path = tmp_path / "video.mp4"
    _create_synthetic_video(video_path, num_frames=15, fps=25.0)

    with open(video_path, "rb") as f:
        upload_resp = client.post(
            "/contributions/upload",
            files={"file": ("video.mp4", f, "video/mp4")},
        )
    cid = upload_resp.json()["contribution_id"]

    client.post(
        f"/contributions/{cid}/extract",
        json={"sample_interval": 5, "max_frames": 10},
    )

    # Frame list endpoint
    frames_resp = client.get(f"/contributions/{cid}/frames")
    assert frames_resp.status_code == 200
    frames_data = frames_resp.json()
    assert frames_data["active_frames"] > 0
    frame_id = frames_data["frames"][0]["frame_id"]

    # Full resolution frame image endpoint
    img_resp = client.get(f"/contributions/{cid}/frames/{frame_id}")
    assert img_resp.status_code == 200
    assert img_resp.headers["content-type"] == "image/jpeg"
    assert len(img_resp.content) > 0

    # Model-ready thumbnail endpoint (224x224)
    thumb_resp = client.get(f"/contributions/{cid}/frames/{frame_id}/thumb")
    assert thumb_resp.status_code == 200
    assert thumb_resp.headers["content-type"] == "image/jpeg"

    # Verify thumbnail dimensions
    arr = np.frombuffer(thumb_resp.content, dtype=np.uint8)
    thumb_img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    assert thumb_img.shape == (224, 224, 3)


def test_frame_deletion_and_usable_count(contrib_env):
    service, client, tmp_path = contrib_env
    video_path = tmp_path / "video.mp4"
    _create_synthetic_video(video_path, num_frames=20, fps=25.0)

    with open(video_path, "rb") as f:
        upload_resp = client.post(
            "/contributions/upload",
            files={"file": ("video.mp4", f, "video/mp4")},
        )
    cid = upload_resp.json()["contribution_id"]

    client.post(f"/contributions/{cid}/extract", json={"sample_interval": 5, "max_frames": 10})
    frames = client.get(f"/contributions/{cid}/frames").json()["frames"]
    initial_count = len(frames)
    target_fid = frames[0]["frame_id"]

    # Delete/exclude frame
    del_resp = client.delete(f"/contributions/{cid}/frames/{target_fid}")
    assert del_resp.status_code == 200
    del_data = del_resp.json()
    assert del_data["status"] == "removed"
    assert del_data["usable_count"] == initial_count - 1

    # Verify updated frame list
    updated_frames = client.get(f"/contributions/{cid}/frames").json()["frames"]
    matching = [f for f in updated_frames if f["frame_id"] == target_fid]
    assert matching[0]["status"] == "removed"


def test_submission_lifecycle_and_moderation(contrib_env):
    service, client, tmp_path = contrib_env
    video_path = tmp_path / "video.mp4"
    _create_synthetic_video(video_path, num_frames=25, fps=25.0)

    with open(video_path, "rb") as f:
        upload_resp = client.post(
            "/contributions/upload",
            files={"file": ("video.mp4", f, "video/mp4")},
        )
    cid = upload_resp.json()["contribution_id"]
    client.post(f"/contributions/{cid}/extract", json={"sample_interval": 5, "max_frames": 10})

    # Submit contribution
    submit_payload = {
        "gesture_name": "THANK_YOU",
        "meaning": "Expression of gratitude",
        "sign_language": "ISL",
        "category": "Greetings",
        "description": "Flat hand moves forward from chin",
        "gesture_type": "dynamic",
        "contributor_id": "test_contributor",
    }
    submit_resp = client.post(f"/contributions/{cid}/submit", json=submit_payload)
    assert submit_resp.status_code == 200
    sub_data = submit_resp.json()
    assert sub_data["status"] == "pending_approval"
    assert sub_data["gesture_name"] == "THANK_YOU"
    assert sub_data["sign_language"] == "ISL"

    # List contributions with status filter
    list_resp = client.get("/contributions?status=pending_approval")
    assert list_resp.status_code == 200
    contributions = list_resp.json()["contributions"]
    assert any(c["contribution_id"] == cid for c in contributions)

    # Approve contribution (promotes to approved dataset)
    review_resp = client.post(
        f"/contributions/{cid}/review",
        json={"approved": True},
    )
    assert review_resp.status_code == 200
    assert review_resp.json()["status"] == "approved"

    # Verify filesystem location moved to approved/
    approved_dir = service.approved_dir / cid
    assert approved_dir.is_dir()
    assert (approved_dir / "metadata.json").is_file()
    assert (approved_dir / "frames" / "frames_metadata.json").is_file()


def test_grouped_split_prevents_data_leakage(tmp_path: Path):
    """Test that all frames from the same video/contribution stay in the exact same split."""
    samples = []
    # Create 6 contributions across 2 classes
    for i in range(6):
        gesture = "HELLO" if i < 3 else "THANK_YOU"
        cid = f"contrib_{i}"
        frames = [
            ContributedFrame(
                frame_id=f"frame_{f:04d}",
                frame_index=f * 5,
                timestamp_ms=float(f * 200),
                file_path=tmp_path / f"{cid}_f{f}.jpg",
                thumb_path=tmp_path / f"{cid}_f{f}_thumb.jpg",
                sharpness_score=50.0,
                is_blurry=False,
                is_duplicate=False,
                is_dark=False,
                status="active",
            )
            for f in range(4)
        ]
        samples.append(
            ContributedGestureSample(
                contribution_id=cid,
                gesture_name=gesture,
                meaning="test",
                sign_language="ISL",
                category="test",
                gesture_type="dynamic",
                duration_seconds=1.0,
                fps=25.0,
                frames=frames,
            )
        )

    splitter = GroupedContributionSplitter(train_ratio=0.6, val_ratio=0.2, test_ratio=0.2, seed=42)
    splits = splitter.split_samples(samples)

    # Collect contribution IDs per split
    split_cids: dict[str, set[str]] = {
        name: {s.contribution_id for s in s_list}
        for name, s_list in splits.items()
    }

    # Verify mutual exclusivity of contribution IDs (NO leakage)
    assert split_cids["train"].isdisjoint(split_cids["validation"])
    assert split_cids["train"].isdisjoint(split_cids["test"])
    assert split_cids["validation"].isdisjoint(split_cids["test"])

    # Total contributions should equal 6
    total_split_cids = split_cids["train"] | split_cids["validation"] | split_cids["test"]
    assert len(total_split_cids) == 6

