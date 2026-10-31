"""Centralized authentication and authorization dependencies for administrative moderation endpoints.

Security Model:
- Shared administrative secret token supplied via environment variable `GESTURA_ADMIN_TOKEN`.
- Clients supply the token via the `X-Admin-Key` HTTP request header.
- Verification uses constant-time comparison (hmac.compare_digest) to prevent timing attacks.
- If GESTURA_ADMIN_TOKEN is unset or empty, requests return HTTP 503 (Service Unavailable)
  to ensure the system fails closed rather than inadvertently exposing moderation operations.
- Missing headers return HTTP 401 (Unauthorized).
- Incorrect keys return HTTP 403 (Forbidden).
"""

from __future__ import annotations

import hmac
import os
from typing import Optional

from fastapi import Header, HTTPException, status

ADMIN_TOKEN_ENV_VAR = "GESTURA_ADMIN_TOKEN"
ADMIN_KEY_HEADER = "X-Admin-Key"


def verify_admin_key(
    x_admin_key: Optional[str] = Header(
        None,
        alias=ADMIN_KEY_HEADER,
        description="Administrative secret key for moderation access",
    ),
) -> str:
    """FastAPI dependency that validates administrator credentials for moderation endpoints.

    Raises:
        HTTPException(503): If GESTURA_ADMIN_TOKEN is not configured or is empty.
        HTTPException(401): If X-Admin-Key header is missing.
        HTTPException(403): If X-Admin-Key does not match GESTURA_ADMIN_TOKEN in constant time.

    Returns:
        The validated admin key.
    """
    admin_token = os.getenv(ADMIN_TOKEN_ENV_VAR)

    # 1. Configuration safety: fail-closed if token is unset, empty, or whitespace
    if not admin_token or not admin_token.strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Admin authentication is not configured on this server "
                f"({ADMIN_TOKEN_ENV_VAR} is unset or empty)."
            ),
        )

    # 2. Require X-Admin-Key header
    if not x_admin_key or not x_admin_key.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing required admin authentication key. Provide '{ADMIN_KEY_HEADER}' header.",
        )

    # 3. Constant-time comparison using hmac.compare_digest
    is_valid = hmac.compare_digest(
        x_admin_key.strip().encode("utf-8"),
        admin_token.strip().encode("utf-8"),
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin authentication key.",
        )

    return x_admin_key

