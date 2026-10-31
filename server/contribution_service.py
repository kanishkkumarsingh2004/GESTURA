"""Video processing, frame extraction, quality validation and India-first dataset organization service."""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import time
import uuid
from pathlib import Path
from typing import Any, List, Optional, Tuple

import cv2
import numpy as np
from fastapi import HTTPException, UploadFile, status

from server.contribution_models import (
    ApprovedDatasetResponse,
    ContributionMetadata,
    ContributionSummary,
    DatasetStatsResponse,
    ExtractFramesResponse,
    FrameMetadata,
    PublicApprovedContribution,
    QualityReport,
    SubmitContributionRequest,
)
from server.india_geo_config import (
    COUNTRY_NAME,
    INDIA_REGIONS,
    SIGN_LANGUAGE_TYPES,
    to_slug,
    validate_india_geo,
    validate_sign_language_variety,
)
from utils.logging import get_logger

logger = get_logger("contributions", log_file="outputs/logs/contributions.log")

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_DURATION_SECONDS = 60.0  # 1 minute max for single gesture sample
MIN_DURATION_SECONDS = 0.3  # Minimum 300ms
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".webm", ".avi", ".mkv"}

ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+$")


class ContributionService:
    """Manages the full contribution lifecycle for the India-first dataset strategy.

    Storage Layout:
      data/contributions/india/
        pending/
          _drafts/<cid>/                     (temporary staging prior to annotation)
          <region_slug>/<state_slug>/<cid>/  (annotated pending approval)
        approved/
          <region_slug>/<state_slug>/<cid>/  (reviewed and approved for training)
        rejected/
          <region_slug>/<state_slug>/<cid>/  (rejected samples with reasons)
    """

    def __init__(self, base_dir: Path | str = "data/contributions/india") -> None:
        self.base_dir = Path(base_dir).resolve()
        self.pending_dir = self.base_dir / "pending"
        self.approved_dir = self.base_dir / "approved"
        self.rejected_dir = self.base_dir / "rejected"

        self.pending_dir.mkdir(parents=True, exist_ok=True)
        (self.pending_dir / "_drafts").mkdir(parents=True, exist_ok=True)
        self.approved_dir.mkdir(parents=True, exist_ok=True)
        self.rejected_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ Validation
    def _validate_id(self, contribution_id: str) -> str:
        if not contribution_id or not ID_PATTERN.match(contribution_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid contribution ID format",
            )
        return contribution_id

    def _get_contribution_dir(self, contribution_id: str) -> Tuple[Path, str]:
        """Locate contribution directory across pending, approved, or rejected hierarchies."""
        cid = self._validate_id(contribution_id)
        for state_dir, state_name in [
            (self.pending_dir, "pending"),
            (self.approved_dir, "approved"),
            (self.rejected_dir, "rejected"),
        ]:
            if not state_dir.is_dir():
                continue

            # Check direct or draft location
            candidate = state_dir / cid
            if candidate.is_dir() and (candidate / "metadata.json").is_file():
                return candidate, state_name

            draft_candidate = state_dir / "_drafts" / cid
            if draft_candidate.is_dir() and (draft_candidate / "metadata.json").is_file():
                return draft_candidate, state_name

            # Check regional hierarchies: region_slug/state_slug/cid
            for candidate in state_dir.glob(f"*/*/{cid}"):
                if candidate.is_dir() and (candidate / "metadata.json").is_file():
                    return candidate, state_name

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contribution '{cid}' not found",
        )

    def _read_metadata(self, contrib_dir: Path) -> dict[str, Any]:
        meta_file = contrib_dir / "metadata.json"
        if not meta_file.is_file():
            raise HTTPException(status_code=404, detail="Metadata file missing")
        with open(meta_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_metadata(self, contrib_dir: Path, data: dict[str, Any]) -> None:
        meta_file = contrib_dir / "metadata.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _read_frames_metadata(self, contrib_dir: Path) -> list[dict[str, Any]]:
        frames_file = contrib_dir / "frames" / "frames_metadata.json"
        if not frames_file.is_file():
            return []
        with open(frames_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_frames_metadata(self, contrib_dir: Path, frames: list[dict[str, Any]]) -> None:
        frames_dir = contrib_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        frames_file = frames_dir / "frames_metadata.json"
        with open(frames_file, "w", encoding="utf-8") as f:
            json.dump(frames, f, indent=2)

    # ------------------------------------------------------------------ Upload Video
    async def handle_video_upload(self, file: UploadFile) -> ContributionMetadata:
        """Validate, store uploaded video, and initialize contribution draft."""
        original_filename = file.filename or "video.mp4"
        ext = Path(original_filename).suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            )

        # Generate unique contribution ID
        cid = f"contrib_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        contrib_dir = self.pending_dir / "_drafts" / cid
        contrib_dir.mkdir(parents=True, exist_ok=True)
        frames_dir = contrib_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)

        video_path = contrib_dir / f"original_video{ext}"

        # Write chunks with size cap
        total_bytes = 0
        try:
            with open(video_path, "wb") as out_file:
                while chunk := await file.read(1024 * 1024):  # 1MB chunks
                    total_bytes += len(chunk)
                    if total_bytes > MAX_UPLOAD_BYTES:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"Video exceeds maximum allowed size of {MAX_UPLOAD_BYTES // (1024 * 1024)} MB",
                        )
                    out_file.write(chunk)
        except Exception:
            shutil.rmtree(contrib_dir, ignore_errors=True)
            raise

        # Inspect video stream via OpenCV
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            shutil.rmtree(contrib_dir, ignore_errors=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is corrupted or unreadable as a video stream",
            )

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        cap.release()

        duration = (total_frames / fps) if fps > 0 and total_frames > 0 else 0.0

        if duration > MAX_DURATION_SECONDS:
            shutil.rmtree(contrib_dir, ignore_errors=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Video duration ({duration:.1f}s) exceeds maximum allowed {MAX_DURATION_SECONDS}s",
            )

        if total_frames < 3:
            shutil.rmtree(contrib_dir, ignore_errors=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video must contain at least 3 frames",
            )

        now = time.time()
        metadata = ContributionMetadata(
            contribution_id=cid,
            status="uploaded",
            video_filename=original_filename,
            video_duration_seconds=round(duration, 2),
            video_fps=round(fps, 2),
            video_resolution=[width, height],
            total_video_frames=total_frames,
            sample_interval=max(1, int(fps // 5)),
            usable_frame_count=0,
            country=COUNTRY_NAME,
            created_at=now,
            updated_at=now,
        )

        self._write_metadata(contrib_dir, metadata.model_dump())
        logger.info("New contribution uploaded: %s (%s, %.1fs)", cid, original_filename, duration)
        return metadata

    # ------------------------------------------------------------------ Frame Extraction
    def extract_and_validate_frames(
        self,
        contribution_id: str,
        sample_interval: int = 5,
        max_frames: int = 40,
    ) -> ExtractFramesResponse:
        """Extract frames, perform sharpness/dark/duplicate checks, and generate model-ready crops."""
        contrib_dir, state = self._get_contribution_dir(contribution_id)
        if state != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot re-extract frames for {state} contribution",
            )

        meta = self._read_metadata(contrib_dir)

        # Locate original video
        video_files = list(contrib_dir.glob("original_video.*"))
        if not video_files:
            raise HTTPException(status_code=404, detail="Original video file missing")
        video_path = video_files[0]

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Unable to read video file")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frames_dir = contrib_dir / "frames"
        # Clear existing frames
        for f in frames_dir.glob("*.jpg"):
            f.unlink(missing_ok=True)

        extracted_metadata: list[dict[str, Any]] = []
        warnings: list[str] = []

        frame_idx = 0
        extracted_count = 0
        prev_gray: Optional[np.ndarray] = None

        blurry_count = 0
        duplicate_count = 0
        dark_count = 0

        while True:
            ret, frame = cap.read()
            if not ret or extracted_count >= max_frames:
                break

            if frame_idx % sample_interval == 0:
                extracted_count += 1
                fid = f"frame_{extracted_count:04d}"
                timestamp_ms = (frame_idx / fps) * 1000.0

                h, w = frame.shape[:2]
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # 1. Sharpness via Laplacian variance
                laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
                is_blurry = laplacian_var < 25.0
                if is_blurry:
                    blurry_count += 1

                # 2. Brightness check (dark/blank)
                mean_brightness = float(np.mean(gray))
                is_dark = mean_brightness < 15.0
                if is_dark:
                    dark_count += 1

                # 3. Duplicate check against previous extracted frame
                is_duplicate = False
                if prev_gray is not None:
                    diff = float(np.mean(np.abs(gray.astype(np.float32) - prev_gray.astype(np.float32))) / 255.0)
                    if diff < 0.02:  # Less than 2% visual variation
                        is_duplicate = True
                        duplicate_count += 1
                prev_gray = gray

                # Save full frame
                frame_filename = f"{fid}.jpg"
                cv2.imwrite(str(frames_dir / frame_filename), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])

                # Save model-ready 224x224 thumbnail
                thumb_filename = f"{fid}_thumb.jpg"
                thumb_resized = cv2.resize(frame, (224, 224), interpolation=cv2.INTER_LINEAR)
                cv2.imwrite(str(frames_dir / thumb_filename), thumb_resized, [cv2.IMWRITE_JPEG_QUALITY, 85])

                is_active = not (is_blurry and is_dark)

                frame_entry = {
                    "frame_id": fid,
                    "filename": frame_filename,
                    "thumb_filename": thumb_filename,
                    "timestamp_ms": round(timestamp_ms, 1),
                    "frame_index": frame_idx,
                    "width": w,
                    "height": h,
                    "sharpness_score": round(laplacian_var, 1),
                    "is_blurry": bool(is_blurry),
                    "is_duplicate": bool(is_duplicate),
                    "is_dark": bool(is_dark),
                    "status": "active" if is_active else "removed",
                }
                extracted_metadata.append(frame_entry)

            frame_idx += 1

        cap.release()

        if extracted_count == 0:
            raise HTTPException(status_code=400, detail="No frames could be extracted from video")

        if blurry_count > extracted_count * 0.4:
            warnings.append(f"High blur detected ({blurry_count}/{extracted_count} frames below sharpness threshold).")
        if dark_count > 0:
            warnings.append(f"{dark_count} dark or underexposed frame(s) identified.")
        if duplicate_count > extracted_count * 0.5:
            warnings.append(f"High static redundancy ({duplicate_count} near-identical frames detected).")

        usable_count = sum(1 for f in extracted_metadata if f["status"] == "active")

        quality_report = QualityReport(
            total_frames_extracted=extracted_count,
            usable_frames_count=usable_count,
            blurry_frames_count=blurry_count,
            duplicate_frames_count=duplicate_count,
            dark_frames_count=dark_count,
            warnings=warnings,
        )

        meta["sample_interval"] = sample_interval
        meta["usable_frame_count"] = usable_count
        meta["status"] = "extracted"
        meta["updated_at"] = time.time()
        meta["quality_report"] = quality_report.model_dump()

        self._write_metadata(contrib_dir, meta)
        self._write_frames_metadata(contrib_dir, extracted_metadata)

        logger.info(
            "Extracted %d frames from %s (%d usable, interval=%d)",
            extracted_count,
            contribution_id,
            usable_count,
            sample_interval,
        )

        return ExtractFramesResponse(
            contribution_id=contribution_id,
            sample_interval=sample_interval,
            total_extracted=extracted_count,
            usable_count=usable_count,
            quality_report=quality_report,
            frames=[FrameMetadata(**f) for f in extracted_metadata],
        )

    # ------------------------------------------------------------------ Frame Management
    def get_frames(self, contribution_id: str) -> list[FrameMetadata]:
        contrib_dir, _ = self._get_contribution_dir(contribution_id)
        raw_frames = self._read_frames_metadata(contrib_dir)
        return [FrameMetadata(**f) for f in raw_frames]

    def get_frame_file_path(self, contribution_id: str, frame_id: str, thumb: bool = False) -> Path:
        contrib_dir, _ = self._get_contribution_dir(contribution_id)
        fid = self._validate_id(frame_id)
        filename = f"{fid}_thumb.jpg" if thumb else f"{fid}.jpg"
        frame_path = contrib_dir / "frames" / filename
        if not frame_path.is_file():
            raise HTTPException(status_code=404, detail=f"Frame '{frame_id}' not found")
        return frame_path

    def delete_frame(self, contribution_id: str, frame_id: str) -> dict[str, Any]:
        """Mark or remove an individual frame from contribution dataset."""
        contrib_dir, state = self._get_contribution_dir(contribution_id)
        if state != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot remove frames from {state} contribution",
            )

        frames = self._read_frames_metadata(contrib_dir)
        fid = self._validate_id(frame_id)

        target = None
        for f in frames:
            if f["frame_id"] == fid:
                target = f
                break

        if not target:
            raise HTTPException(status_code=404, detail="Frame not found")

        target["status"] = "removed"
        self._write_frames_metadata(contrib_dir, frames)

        meta = self._read_metadata(contrib_dir)
        usable = sum(1 for item in frames if item["status"] == "active")
        meta["usable_frame_count"] = usable
        meta["updated_at"] = time.time()
        self._write_metadata(contrib_dir, meta)

        return {"contribution_id": contribution_id, "frame_id": fid, "status": "removed", "usable_count": usable}

    # ------------------------------------------------------------------ Submit (India-First)
    def submit_contribution(self, contribution_id: str, req: SubmitContributionRequest) -> ContributionMetadata:
        """Finalize submission with India-specific geographic and linguistic semantics."""
        contrib_dir, state = self._get_contribution_dir(contribution_id)
        if state != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contribution is already in {state} state",
            )

        meta = self._read_metadata(contrib_dir)
        frames = self._read_frames_metadata(contrib_dir)
        active_count = sum(1 for f in frames if f["status"] == "active")

        if active_count < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"At least 3 valid active frames are required for submission (currently {active_count})",
            )

        # 1. Validate geographic hierarchy (Country fixed to India, Region -> State)
        try:
            canonical_region, canonical_state = validate_india_geo(req.region, req.state)
        except ValueError as err:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

        # 2. Validate sign language classification & variety
        try:
            clean_sl_type, clean_variety = validate_sign_language_variety(
                req.sign_language_type, req.variety_name
            )
        except ValueError as err:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

        clean_name = re.sub(r"[^A-Za-z0-9_]+", "_", req.gesture_name.strip()).upper()
        if not clean_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gesture name cannot be empty")

        cid = meta["contribution_id"]

        meta["country"] = COUNTRY_NAME
        meta["region"] = canonical_region
        meta["state"] = canonical_state
        meta["district_city"] = req.district_city.strip() if req.district_city else None
        meta["sign_language_type"] = clean_sl_type
        meta["variety_name"] = clean_variety
        meta["sign_language"] = (
            f"ISL ({clean_variety})" if clean_variety else clean_sl_type
        )
        meta["gesture_name"] = clean_name
        meta["meaning"] = req.meaning.strip()
        meta["category"] = req.category.strip()
        meta["description"] = req.description.strip() if req.description else None
        meta["gesture_type"] = req.gesture_type
        meta["contributor_id"] = req.contributor_id or "anonymous"
        meta["usable_frame_count"] = active_count
        meta["status"] = "pending_approval"
        meta["updated_at"] = time.time()

        # Place into canonical regional storage: data/contributions/india/pending/{region}/{state}/{cid}
        region_slug = to_slug(canonical_region)
        state_slug = to_slug(canonical_state)
        target_dir = self.pending_dir / region_slug / state_slug / cid
        target_dir.parent.mkdir(parents=True, exist_ok=True)

        self._write_metadata(contrib_dir, meta)

        if contrib_dir.resolve() != target_dir.resolve():
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.move(str(contrib_dir), str(target_dir))
            contrib_dir = target_dir

        logger.info(
            "Contribution %s submitted for approval: %s [%s / %s - %s]",
            cid,
            clean_name,
            canonical_region,
            canonical_state,
            clean_sl_type,
        )
        return ContributionMetadata(**meta)

    # ------------------------------------------------------------------ Query & Moderation
    def get_contribution(self, contribution_id: str) -> ContributionMetadata:
        contrib_dir, _ = self._get_contribution_dir(contribution_id)
        meta = self._read_metadata(contrib_dir)
        return ContributionMetadata(**meta)

    def list_contributions(
        self,
        status_filter: Optional[str] = None,
        region_filter: Optional[str] = None,
    ) -> list[ContributionSummary]:
        results: list[ContributionSummary] = []
        for state_dir in [self.pending_dir, self.approved_dir, self.rejected_dir]:
            if not state_dir.is_dir():
                continue
            for meta_path in state_dir.rglob("metadata.json"):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    st = meta.get("status", "unknown")
                    if status_filter and st != status_filter:
                        continue
                    r = meta.get("region")
                    if region_filter and r != region_filter:
                        continue
                    results.append(
                        ContributionSummary(
                            contribution_id=meta["contribution_id"],
                            country=meta.get("country", COUNTRY_NAME),
                            region=r,
                            state=meta.get("state"),
                            district_city=meta.get("district_city"),
                            sign_language_type=meta.get("sign_language_type"),
                            variety_name=meta.get("variety_name"),
                            sign_language=meta.get("sign_language"),
                            gesture_name=meta.get("gesture_name"),
                            meaning=meta.get("meaning"),
                            category=meta.get("category"),
                            gesture_type=meta.get("gesture_type"),
                            video_duration_seconds=meta.get("video_duration_seconds", 0.0),
                            usable_frame_count=meta.get("usable_frame_count", 0),
                            status=st,
                            created_at=meta.get("created_at", 0.0),
                        )
                    )
                except Exception as err:
                    logger.warning("Error reading contribution metadata %s: %s", meta_path, err)

        results.sort(key=lambda x: x.created_at, reverse=True)
        return results

    def review_contribution(
        self,
        contribution_id: str,
        approved: bool,
        rejection_reason: Optional[str] = None,
    ) -> ContributionMetadata:
        """Moderate a contribution: move to approved or rejected regional dataset storage."""
        contrib_dir, current_state = self._get_contribution_dir(contribution_id)
        meta = self._read_metadata(contrib_dir)

        cid = meta["contribution_id"]
        meta["updated_at"] = time.time()

        region = meta.get("region") or "general"
        state = meta.get("state") or "general"
        region_slug = to_slug(region)
        state_slug = to_slug(state)

        if approved:
            meta["status"] = "approved"
            meta["rejection_reason"] = None
            dest_dir = self.approved_dir / region_slug / state_slug / cid
        else:
            meta["status"] = "rejected"
            meta["rejection_reason"] = rejection_reason or "Does not meet dataset quality criteria"
            dest_dir = self.rejected_dir / region_slug / state_slug / cid

        dest_dir.parent.mkdir(parents=True, exist_ok=True)
        self._write_metadata(contrib_dir, meta)

        if dest_dir.resolve() != contrib_dir.resolve():
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            shutil.move(str(contrib_dir), str(dest_dir))

        status_str = "APPROVED" if approved else "REJECTED"
        logger.info("Contribution %s %s [Region: %s, State: %s]", cid, status_str, region, state)
        return ContributionMetadata(**meta)

    # ------------------------------------------------------------------ Dataset Aggregations & Public API
    def get_dataset_stats(self) -> DatasetStatsResponse:
        """Calculate aggregate metrics across all contributions in the system."""
        total = 0
        pending = 0
        approved = 0
        rejected = 0
        total_frames = 0

        # Pre-seed regions and sign language types with 0 counts
        by_region: dict[str, int] = {r: 0 for r in INDIA_REGIONS.keys()}
        by_state: dict[str, int] = {}
        by_sign_language_type: dict[str, int] = {t: 0 for t in SIGN_LANGUAGE_TYPES}

        # Track processed contribution IDs to prevent duplicate counts
        seen_cids: set[str] = set()

        for state_dir in [self.pending_dir, self.approved_dir, self.rejected_dir]:
            if not state_dir.is_dir():
                continue
            for meta_path in state_dir.rglob("metadata.json"):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    cid = meta.get("contribution_id")
                    if not cid or cid in seen_cids:
                        continue
                    seen_cids.add(cid)

                    total += 1
                    status_val = meta.get("status", "unknown")
                    if status_val == "approved":
                        approved += 1
                    elif status_val == "rejected":
                        rejected += 1
                    else:
                        pending += 1

                    # Region breakdown
                    region = meta.get("region")
                    if region and region in by_region:
                        by_region[region] += 1
                    elif region:
                        by_region[region] = by_region.get(region, 0) + 1

                    # State breakdown
                    state = meta.get("state")
                    if state:
                        by_state[state] = by_state.get(state, 0) + 1

                    # Sign language classification breakdown
                    sl_type = meta.get("sign_language_type")
                    if sl_type and sl_type in by_sign_language_type:
                        by_sign_language_type[sl_type] += 1
                    elif sl_type:
                        by_sign_language_type[sl_type] = by_sign_language_type.get(sl_type, 0) + 1

                    # Frame count calculation
                    frames = meta.get("usable_frame_count", 0)
                    qr = meta.get("quality_report")
                    if isinstance(qr, dict) and "total_frames_extracted" in qr:
                        frames = qr.get("total_frames_extracted", frames)
                    total_frames += frames
                except Exception as err:
                    logger.warning("Error reading metadata at %s for stats: %s", meta_path, err)

        return DatasetStatsResponse(
            total_contributions=total,
            pending_contributions=pending,
            approved_contributions=approved,
            rejected_contributions=rejected,
            by_region=by_region,
            by_state=by_state,
            by_sign_language_type=by_sign_language_type,
            total_extracted_frames=total_frames,
        )

    def get_approved_contributions(
        self,
        page: int = 1,
        page_size: int = 20,
        region: Optional[str] = None,
        state: Optional[str] = None,
        sign_language_type: Optional[str] = None,
        gesture_name: Optional[str] = None,
    ) -> ApprovedDatasetResponse:
        """Return paginated public metadata for approved contributions.

        Sanitization guarantee:
        Private contributor ID, raw video filename, and local disk paths
        are completely stripped from the response.
        """
        if not self.approved_dir.is_dir():
            return ApprovedDatasetResponse(
                items=[], total=0, page=page, page_size=page_size, total_pages=1
            )

        items: list[PublicApprovedContribution] = []
        seen_cids: set[str] = set()

        for meta_path in self.approved_dir.rglob("metadata.json"):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                cid = meta.get("contribution_id")
                if not cid or cid in seen_cids:
                    continue
                seen_cids.add(cid)

                if meta.get("status") != "approved":
                    continue

                # Apply optional filters
                if region:
                    meta_region = (meta.get("region") or "").strip().upper()
                    if meta_region != region.strip().upper():
                        continue

                if state:
                    meta_state = (meta.get("state") or "").strip().lower()
                    if meta_state != state.strip().lower():
                        continue

                if sign_language_type:
                    meta_slt = (meta.get("sign_language_type") or "").strip().lower()
                    if meta_slt != sign_language_type.strip().lower():
                        continue

                if gesture_name:
                    meta_gesture = (meta.get("gesture_name") or "").strip().lower()
                    if gesture_name.strip().lower() not in meta_gesture:
                        continue

                items.append(
                    PublicApprovedContribution(
                        contribution_id=meta["contribution_id"],
                        gesture_name=meta.get("gesture_name") or "UNKNOWN",
                        meaning=meta.get("meaning") or "",
                        category=meta.get("category") or "General",
                        gesture_type=meta.get("gesture_type") or "dynamic",
                        country=meta.get("country", COUNTRY_NAME),
                        region=meta.get("region") or "UNKNOWN",
                        state=meta.get("state") or "UNKNOWN",
                        district_city=meta.get("district_city"),
                        sign_language_type=meta.get("sign_language_type") or "Indian Sign Language (ISL)",
                        variety_name=meta.get("variety_name"),
                        video_duration_seconds=meta.get("video_duration_seconds", 0.0),
                        usable_frame_count=meta.get("usable_frame_count", 0),
                        created_at=meta.get("created_at", 0.0),
                    )
                )
            except Exception as err:
                logger.warning("Error reading approved metadata %s: %s", meta_path, err)

        # Sort by creation time descending (newest first)
        items.sort(key=lambda x: x.created_at, reverse=True)

        total = len(items)
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paged_items = items[start_idx:end_idx]

        return ApprovedDatasetResponse(
            items=paged_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
