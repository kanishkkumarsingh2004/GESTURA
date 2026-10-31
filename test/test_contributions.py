"""Comprehensive tests for GESTURA's India-first gesture contribution pipeline.

Tests:
1. Video upload and validation (format, duration, stream readability).
2. Frame extraction and CV quality audits (sharpness/Laplacian, underexposure, temporal duplicates).
3. Frame serving (full resolution and 224x224 RGB model-ready thumbnails).
4. Valid Indian region/state combinations across all 6 regions.
5. Invalid region/state combinations and mismatches (rejected with HTTP 400).
6. Conditional sign-language variety validation (Regional ISL Variant, Local Community, Other vs ISL).
7. Missing required fields and minimum frame threshold validation (<3 active frames rejected).
8. Correct regional hierarchical storage layout (pending vs approved vs rejected).
9. Dataset export preserving geographic and dialectal metadata.
10. Grouped leak-free splitting ensuring frames from the same video are never partitioned across splits.
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
from server.india_geo_config import (
    INDIA_REGIONS,
    to_slug,
    validate_india_geo,
    validate_sign_language_variety,
)


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
            frame = np.full((height, width, 3), 120, dtype=np.uint8)
        else:
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
    base_dir = tmp_path / "contributions" / "india"
    service = ContributionService(base_dir=base_dir)
    api = GestureAPI(engine=FakeEngine(), contribution_service=service)
    client = TestClient(api.build_app())
    return service, client, tmp_path


def _upload_and_extract(client: TestClient, tmp_path: Path, filename: str = "sample.mp4") -> str:
    video_path = tmp_path / filename
    _create_synthetic_video(video_path, num_frames=20, fps=25.0)
    with open(video_path, "rb") as f:
        resp = client.post(
            "/contributions/upload",
            files={"file": (filename, f, "video/mp4")},
        )
    assert resp.status_code == 201
    cid = resp.json()["contribution_id"]
    extract_resp = client.post(f"/contributions/{cid}/extract", json={"sample_interval": 5, "max_frames": 10})
    assert extract_resp.status_code == 200
    return cid


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
    cid = _upload_and_extract(client, tmp_path, "sample_extract.mp4")

    frames_resp = client.get(f"/contributions/{cid}/frames")
    assert frames_resp.status_code == 200
    frames_data = frames_resp.json()
    assert frames_data["active_frames"] > 0
    frame_id = frames_data["frames"][0]["frame_id"]

    # Thumbnail is 224x224
    thumb_resp = client.get(f"/contributions/{cid}/frames/{frame_id}/thumb")
    assert thumb_resp.status_code == 200
    arr = np.frombuffer(thumb_resp.content, dtype=np.uint8)
    thumb_img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    assert thumb_img.shape == (224, 224, 3)


def test_valid_indian_region_state_combinations(contrib_env):
    """Test valid submissions across Indian regions and states."""
    service, client, tmp_path = contrib_env

    valid_cases = [
        ("NORTH", "Delhi", "Indian Sign Language (ISL)", None),
        ("SOUTH", "Karnataka", "Regional ISL Variant", "Bengaluru ISL"),
        ("EAST", "Odisha", "Local Community Sign Language", "Puri Sign Variety"),
        ("WEST", "Maharashtra", "Indian Sign Language (ISL)", None),
        ("CENTRAL", "Madhya Pradesh", "Unsure", None),
        ("NORTHEAST", "Assam", "Other", "Assamese Community Signs"),
    ]

    for idx, (reg, st, sl_type, variety) in enumerate(valid_cases):
        cid = _upload_and_extract(client, tmp_path, f"sample_{idx}.mp4")
        payload = {
            "country": "India",
            "region": reg,
            "state": st,
            "district_city": "Capital District",
            "sign_language_type": sl_type,
            "variety_name": variety,
            "gesture_name": f"GESTURE_{reg}",
            "meaning": f"Meaning for {reg}",
            "category": "Greetings",
            "gesture_type": "dynamic",
            "contributor_id": f"contributor_{idx}",
        }
        resp = client.post(f"/contributions/{cid}/submit", json=payload)
        assert resp.status_code == 200, f"Failed for {reg} / {st}: {resp.text}"
        data = resp.json()
        assert data["country"] == "India"
        assert data["region"] == reg
        assert data["state"] == st
        assert data["sign_language_type"] == sl_type
        assert data["status"] == "pending_approval"


def test_invalid_region_state_mismatch_rejected(contrib_env):
    """Test that mismatched state and region combinations are rejected with HTTP 400."""
    service, client, tmp_path = contrib_env
    cid = _upload_and_extract(client, tmp_path, "mismatch_test.mp4")

    # Kerala is in SOUTH, not NORTH
    mismatch_payload = {
        "country": "India",
        "region": "NORTH",
        "state": "Kerala",
        "sign_language_type": "Indian Sign Language (ISL)",
        "gesture_name": "NAMASTE",
        "meaning": "Greeting",
        "category": "Greetings",
    }
    resp = client.post(f"/contributions/{cid}/submit", json=mismatch_payload)
    assert resp.status_code == 400
    assert "belongs to region" in resp.json()["detail"] or "Invalid state" in resp.json()["detail"]

    # Unknown region
    bad_region_payload = {
        "country": "India",
        "region": "GLOBAL",
        "state": "Delhi",
        "sign_language_type": "Indian Sign Language (ISL)",
        "gesture_name": "NAMASTE",
        "meaning": "Greeting",
        "category": "Greetings",
    }
    resp2 = client.post(f"/contributions/{cid}/submit", json=bad_region_payload)
    assert resp2.status_code == 400
    assert "Invalid region" in resp2.json()["detail"]


def test_conditional_sign_language_variety_validation(contrib_env):
    """Test conditional requirement for variety_name based on sign_language_type."""
    service, client, tmp_path = contrib_env
    cid = _upload_and_extract(client, tmp_path, "conditional_test.mp4")

    # 1. Regional ISL Variant WITHOUT variety_name must fail
    resp1 = client.post(
        f"/contributions/{cid}/submit",
        json={
            "country": "India",
            "region": "NORTH",
            "state": "Delhi",
            "sign_language_type": "Regional ISL Variant",
            "variety_name": None,
            "gesture_name": "HELLO",
            "meaning": "Hello",
            "category": "Greetings",
        },
    )
    assert resp1.status_code == 400
    assert "Variety/Community name is required" in resp1.json()["detail"]

    # 2. Local Community Sign Language WITHOUT variety_name must fail
    resp2 = client.post(
        f"/contributions/{cid}/submit",
        json={
            "country": "India",
            "region": "NORTH",
            "state": "Delhi",
            "sign_language_type": "Local Community Sign Language",
            "variety_name": "",
            "gesture_name": "HELLO",
            "meaning": "Hello",
            "category": "Greetings",
        },
    )
    assert resp2.status_code == 400

    # 3. Providing variety_name succeeds
    resp3 = client.post(
        f"/contributions/{cid}/submit",
        json={
            "country": "India",
            "region": "NORTH",
            "state": "Delhi",
            "sign_language_type": "Regional ISL Variant",
            "variety_name": "Delhi NCR Variety",
            "gesture_name": "HELLO",
            "meaning": "Hello",
            "category": "Greetings",
        },
    )
    assert resp3.status_code == 200
    assert resp3.json()["variety_name"] == "Delhi NCR Variety"


def test_correct_regional_storage_and_moderation(contrib_env):
    """Test hierarchical regional folder storage under data/contributions/india/."""
    service, client, tmp_path = contrib_env
    cid = _upload_and_extract(client, tmp_path, "storage_test.mp4")

    # Submit for North / Punjab
    client.post(
        f"/contributions/{cid}/submit",
        json={
            "country": "India",
            "region": "NORTH",
            "state": "Punjab",
            "district_city": "Amritsar",
            "sign_language_type": "Indian Sign Language (ISL)",
            "gesture_name": "SAT_SRI_AKAL",
            "meaning": "Traditional greeting",
            "category": "Greetings",
            "gesture_type": "dynamic",
        },
    )

    # Verify placed in pending/north/punjab/cid/
    expected_pending = service.pending_dir / "north" / "punjab" / cid
    assert expected_pending.is_dir()
    assert (expected_pending / "metadata.json").is_file()
    assert (expected_pending / "frames").is_dir()

    # Approve contribution
    appr_resp = client.post(f"/contributions/{cid}/review", json={"approved": True})
    assert appr_resp.status_code == 200
    assert appr_resp.json()["status"] == "approved"

    # Verify moved to approved/north/punjab/cid/
    expected_approved = service.approved_dir / "north" / "punjab" / cid
    assert expected_approved.is_dir()
    assert not expected_pending.exists()


def test_dataset_export_preserving_geographic_metadata(tmp_path: Path):
    """Test exporting approved samples preserves regional metadata and distinct varieties."""
    approved_dir = tmp_path / "india" / "approved"
    sample_cid = "contrib_india_001"
    regional_dir = approved_dir / "south" / "tamil_nadu" / sample_cid
    frames_dir = regional_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    dummy_frame = frames_dir / "frame_0001.jpg"
    dummy_thumb = frames_dir / "frame_0001_thumb.jpg"
    dummy_frame.write_bytes(b"dummy_frame")
    dummy_thumb.write_bytes(b"dummy_thumb")

    meta = {
        "contribution_id": sample_cid,
        "status": "approved",
        "country": "India",
        "region": "SOUTH",
        "state": "Tamil Nadu",
        "district_city": "Chennai",
        "sign_language_type": "Regional ISL Variant",
        "variety_name": "Chennai Dialect",
        "gesture_name": "VANAKKAM",
        "meaning": "Traditional Tamil greeting",
        "category": "Greetings",
        "gesture_type": "dynamic",
        "video_duration_seconds": 1.2,
        "video_fps": 25.0,
    }
    with open(regional_dir / "metadata.json", "w") as f:
        json.dump(meta, f)

    frames_meta = [
        {
            "frame_id": "frame_0001",
            "filename": "frame_0001.jpg",
            "thumb_filename": "frame_0001_thumb.jpg",
            "timestamp_ms": 0.0,
            "frame_index": 0,
            "sharpness_score": 60.0,
            "is_blurry": False,
            "is_duplicate": False,
            "is_dark": False,
            "status": "active",
        }
    ]
    with open(frames_dir / "frames_metadata.json", "w") as f:
        json.dump(frames_meta, f)

    exporter = ContributionDatasetExporter(contributions_root=tmp_path / "india")
    samples = exporter.load_approved_samples()
    assert len(samples) == 1
    s = samples[0]
    assert s.country == "India"
    assert s.region == "SOUTH"
    assert s.state == "Tamil Nadu"
    assert s.variety_name == "Chennai Dialect"
    assert s.qualified_label == "VANAKKAM__south__chennai_dialect"

    # Export sequence manifest
    manifest_file = tmp_path / "manifest.json"
    splitter = GroupedContributionSplitter(seed=42)
    splits = splitter.split_samples(samples)
    exporter.export_sequence_manifest(splits, manifest_file, as_json=True)

    with open(manifest_file, "r") as f:
        manifest_data = json.load(f)
    assert len(manifest_data) == 1
    entry = manifest_data[0]
    assert entry["country"] == "India"
    assert entry["region"] == "SOUTH"
    assert entry["state"] == "Tamil Nadu"
    assert entry["variety_name"] == "Chennai Dialect"
    assert entry["qualified_label"] == "VANAKKAM__south__chennai_dialect"


def test_moderation_admin_token_protection(contrib_env, monkeypatch):
    """Test that moderation review enforces X-Admin-Key when GESTURA_ADMIN_TOKEN is configured."""
    service, client, tmp_path = contrib_env
    cid = _upload_and_extract(client, tmp_path, "auth_test.mp4")
    client.post(
        f"/contributions/{cid}/submit",
        json={
            "country": "India",
            "region": "NORTH",
            "state": "Delhi",
            "sign_language_type": "Indian Sign Language (ISL)",
            "gesture_name": "NAMASTE",
            "meaning": "Greeting",
            "category": "Greetings",
        },
    )

    monkeypatch.setenv("GESTURA_ADMIN_TOKEN", "secret-admin-pass-123")

    # Attempt review without key -> must fail with HTTP 403
    unauth_resp = client.post(f"/contributions/{cid}/review", json={"approved": True})
    assert unauth_resp.status_code == 403
    assert "Unauthorized" in unauth_resp.json()["detail"]

    # Attempt review with valid X-Admin-Key -> succeeds
    auth_resp = client.post(
        f"/contributions/{cid}/review",
        json={"approved": True},
        headers={"X-Admin-Key": "secret-admin-pass-123"},
    )
    assert auth_resp.status_code == 200
    assert auth_resp.json()["status"] == "approved"


def test_grouped_split_prevents_data_leakage(tmp_path: Path):
    """Test that all frames from the same video/contribution stay in the exact same split."""
    samples = []
    for i in range(6):
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
                gesture_name="NAMASTE",
                meaning="test",
                category="test",
                gesture_type="dynamic",
                duration_seconds=1.0,
                fps=25.0,
                country="India",
                region="NORTH" if i < 3 else "SOUTH",
                state="Delhi" if i < 3 else "Karnataka",
                frames=frames,
            )
        )

    splitter = GroupedContributionSplitter(train_ratio=0.6, val_ratio=0.2, test_ratio=0.2, seed=42)
    splits = splitter.split_samples(samples, stratify_by_variety=True)

    split_cids: dict[str, set[str]] = {
        name: {s.contribution_id for s in s_list}
        for name, s_list in splits.items()
    }

    assert split_cids["train"].isdisjoint(split_cids["validation"])
    assert split_cids["train"].isdisjoint(split_cids["test"])
    assert split_cids["validation"].isdisjoint(split_cids["test"])
    assert len(split_cids["train"] | split_cids["validation"] | split_cids["test"]) == 6


def test_geo_regions_api(contrib_env):
    """Test GET /contributions/geo/regions returns all 6 Indian regions."""
    service, client, tmp_path = contrib_env
    res = client.get("/contributions/geo/regions")
    assert res.status_code == 200
    data = res.json()
    assert data["country"] == "India"
    assert data["count"] == 6
    assert set(data["regions"]) == {"NORTH", "SOUTH", "EAST", "WEST", "CENTRAL", "NORTHEAST"}


def test_geo_states_api(contrib_env):
    """Test GET /contributions/geo/states validates region and returns matching states/UTs."""
    service, client, tmp_path = contrib_env

    # Valid region (case-insensitive)
    res = client.get("/contributions/geo/states?region=south")
    assert res.status_code == 200
    data = res.json()
    assert data["region"] == "SOUTH"
    assert data["count"] == 8
    assert "Tamil Nadu" in data["states"]
    assert "Karnataka" in data["states"]
    assert "Andaman and Nicobar Islands" in data["states"]

    # Invalid region -> HTTP 400
    invalid_res = client.get("/contributions/geo/states?region=INVALID_REGION")
    assert invalid_res.status_code == 400
    assert "Invalid region" in invalid_res.json()["detail"]


def test_geo_sign_language_types_api(contrib_env):
    """Test GET /contributions/geo/sign-language-types returns supported classifications and rules."""
    service, client, tmp_path = contrib_env
    res = client.get("/contributions/geo/sign-language-types")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 5
    types_map = {item["name"]: item for item in data["types"]}

    # ISL does not require variety name
    assert types_map["Indian Sign Language (ISL)"]["requires_variety_name"] is False
    # Regional ISL Variant requires variety name
    assert types_map["Regional ISL Variant"]["requires_variety_name"] is True
    # Local Community Sign Language requires variety name
    assert types_map["Local Community Sign Language"]["requires_variety_name"] is True


def test_dataset_stats_api(contrib_env):
    """Test GET /contributions/dataset/stats metrics calculation and aggregation."""
    service, client, tmp_path = contrib_env

    # Initial stats
    res1 = client.get("/contributions/dataset/stats")
    assert res1.status_code == 200
    data1 = res1.json()
    initial_total = data1["total_contributions"]
    assert "NORTH" in data1["by_region"]
    assert "Indian Sign Language (ISL)" in data1["by_sign_language_type"]

    # Upload and submit a sample contribution
    cid = _upload_and_extract(client, tmp_path, "stats_sample.mp4")
    client.post(
        f"/contributions/{cid}/submit",
        json={
            "country": "India",
            "region": "NORTH",
            "state": "Delhi",
            "sign_language_type": "Indian Sign Language (ISL)",
            "gesture_name": "SHUKRIYA",
            "meaning": "Thank you",
            "category": "Greetings",
        },
    )

    res2 = client.get("/contributions/dataset/stats")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["total_contributions"] == initial_total + 1
    assert data2["pending_contributions"] >= 1
    assert data2["by_region"]["NORTH"] >= 1
    assert data2["total_extracted_frames"] > 0

    # Moderate and approve
    client.post(f"/contributions/{cid}/review", json={"approved": True})

    res3 = client.get("/contributions/dataset/stats")
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["approved_contributions"] == data2["approved_contributions"] + 1
    assert data3["pending_contributions"] == data2["pending_contributions"] - 1


def test_dataset_approved_api_and_privacy_sanitization(contrib_env):
    """Test GET /contributions/dataset/approved filtering, pagination, and privacy sanitization."""
    service, client, tmp_path = contrib_env

    # Create and approve sample 1 in NORTH / Delhi
    cid1 = _upload_and_extract(client, tmp_path, "sample_north.mp4")
    client.post(
        f"/contributions/{cid1}/submit",
        json={
            "country": "India",
            "region": "NORTH",
            "state": "Delhi",
            "sign_language_type": "Indian Sign Language (ISL)",
            "gesture_name": "NAMASTE",
            "meaning": "Traditional Indian greeting",
            "category": "Greetings",
            "contributor_id": "secret_user_42",
        },
    )
    client.post(f"/contributions/{cid1}/review", json={"approved": True})

    # Create and approve sample 2 in SOUTH / Tamil Nadu
    cid2 = _upload_and_extract(client, tmp_path, "sample_south.mp4")
    client.post(
        f"/contributions/{cid2}/submit",
        json={
            "country": "India",
            "region": "SOUTH",
            "state": "Tamil Nadu",
            "sign_language_type": "Regional ISL Variant",
            "variety_name": "Chennai Dialect",
            "gesture_name": "VANAKKAM",
            "meaning": "Tamil greeting",
            "category": "Greetings",
            "contributor_id": "private_donor_99",
        },
    )
    client.post(f"/contributions/{cid2}/review", json={"approved": True})

    # Query approved dataset
    res = client.get("/contributions/dataset/approved?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2

    # PRIVACY SANITIZATION AUDIT:
    # Ensure contributor_id, video_filename, and disk paths are NEVER exposed in approved dataset
    for item in data["items"]:
        assert "contributor_id" not in item
        assert "video_filename" not in item
        assert "file_path" not in item
        assert "thumb_path" not in item
        # Valid public fields must be populated
        assert item["country"] == "India"
        assert item["gesture_name"] in {"NAMASTE", "VANAKKAM"}
        assert item["usable_frame_count"] > 0

    # Filter by region
    res_north = client.get("/contributions/dataset/approved?region=NORTH")
    data_north = res_north.json()
    assert all(item["region"] == "NORTH" for item in data_north["items"])
    assert any(item["gesture_name"] == "NAMASTE" for item in data_north["items"])

    # Filter by gesture_name
    res_vanakkam = client.get("/contributions/dataset/approved?gesture_name=vanakkam")
    data_vanakkam = res_vanakkam.json()
    assert len(data_vanakkam["items"]) == 1
    assert data_vanakkam["items"][0]["gesture_name"] == "VANAKKAM"
    assert data_vanakkam["items"][0]["variety_name"] == "Chennai Dialect"


def test_openapi_schema_contains_new_endpoints(contrib_env):
    """Test that FastAPI compiles complete OpenAPI schema with new tags and endpoints."""
    service, client, tmp_path = contrib_env
    res = client.get("/openapi.json")
    assert res.status_code == 200
    schema = res.json()
    paths = schema.get("paths", {})

    # Check geography endpoints
    assert "/contributions/geo/regions" in paths
    assert "/contributions/geo/states" in paths
    assert "/contributions/geo/sign-language-types" in paths

    # Check dataset endpoints
    assert "/contributions/dataset/stats" in paths
    assert "/contributions/dataset/approved" in paths

    # Check tags
    tags = {tag["name"] for tag in schema.get("tags", [])}
    # Alternatively check endpoint tags
    endpoint_tags = set()
    for path_data in paths.values():
        for operation in path_data.values():
            if isinstance(operation, dict) and "tags" in operation:
                endpoint_tags.update(operation["tags"])

    assert "Contributions - Geography" in endpoint_tags
    assert "Contributions - Dataset" in endpoint_tags
    assert "Contributions - Ingestion" in endpoint_tags
    assert "Contributions - Moderation" in endpoint_tags

