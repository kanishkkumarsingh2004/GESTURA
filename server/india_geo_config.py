"""Geographic hierarchy and sign language classification for India-first dataset strategy.

Regions:
NORTH, SOUTH, EAST, WEST, CENTRAL, NORTHEAST
Covering all 28 states and 8 union territories.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

COUNTRY_NAME: str = "India"

INDIA_REGIONS: Dict[str, List[str]] = {
    "NORTH": [
        "Delhi",
        "Chandigarh",
        "Haryana",
        "Himachal Pradesh",
        "Jammu and Kashmir",
        "Ladakh",
        "Punjab",
        "Rajasthan",
        "Uttarakhand",
        "Uttar Pradesh",
    ],
    "SOUTH": [
        "Andhra Pradesh",
        "Karnataka",
        "Kerala",
        "Tamil Nadu",
        "Telangana",
        "Puducherry",
        "Lakshadweep",
    ],
    "EAST": [
        "Bihar",
        "Jharkhand",
        "Odisha",
        "West Bengal",
    ],
    "WEST": [
        "Goa",
        "Gujarat",
        "Maharashtra",
        "Dadra and Nagar Haveli and Daman and Diu",
    ],
    "CENTRAL": [
        "Chhattisgarh",
        "Madhya Pradesh",
    ],
    "NORTHEAST": [
        "Arunachal Pradesh",
        "Assam",
        "Manipur",
        "Meghalaya",
        "Mizoram",
        "Nagaland",
        "Sikkim",
        "Tripura",
    ],
}

VALID_REGIONS: set[str] = set(INDIA_REGIONS.keys())

# Create a lookup mapping from lowercase normalized state name -> canonical name and parent region
STATE_TO_REGION: Dict[str, tuple[str, str]] = {}
for region, states in INDIA_REGIONS.items():
    for state in states:
        STATE_TO_REGION[state.strip().lower()] = (state, region)

SIGN_LANGUAGE_TYPES: List[str] = [
    "Indian Sign Language (ISL)",
    "Regional ISL Variant",
    "Local Community Sign Language",
    "Other",
    "Unsure",
]

# Types that require additional variety/community/other name specification
VARIETY_REQUIRED_TYPES: set[str] = {
    "Regional ISL Variant",
    "Local Community Sign Language",
    "Other",
}


def to_slug(text: str) -> str:
    """Convert text into safe directory slug: e.g. 'Jammu and Kashmir' -> 'jammu_and_kashmir'."""
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower())
    return cleaned.strip("_")


def validate_india_geo(region: str, state: str) -> tuple[str, str]:
    """Validate that region and state are valid and hierarchically consistent.

    Returns:
        Canonical (region, state) tuple.
    Raises:
        ValueError if region or state is invalid or mismatched.
    """
    region_upper = region.strip().upper()
    if region_upper not in VALID_REGIONS:
        raise ValueError(
            f"Invalid region '{region}'. Must be one of: {', '.join(sorted(VALID_REGIONS))}"
        )

    state_lower = state.strip().lower()
    match = STATE_TO_REGION.get(state_lower)
    if not match:
        allowed = ", ".join(INDIA_REGIONS[region_upper])
        raise ValueError(
            f"Invalid state/UT '{state}'. Allowed states for region '{region_upper}': {allowed}"
        )

    canonical_state, parent_region = match
    if parent_region != region_upper:
        raise ValueError(
            f"State '{canonical_state}' belongs to region '{parent_region}', not '{region_upper}'"
        )

    return region_upper, canonical_state


def validate_sign_language_variety(
    sl_type: str, variety_name: Optional[str]
) -> tuple[str, Optional[str]]:
    """Validate sign language classification and conditional variety name."""
    clean_type = sl_type.strip()
    if clean_type not in SIGN_LANGUAGE_TYPES:
        raise ValueError(
            f"Invalid sign language type '{sl_type}'. Must be one of: {', '.join(SIGN_LANGUAGE_TYPES)}"
        )

    clean_variety = variety_name.strip() if variety_name else None
    if clean_type in VARIETY_REQUIRED_TYPES:
        if not clean_variety:
            raise ValueError(
                f"Variety/Community name is required when sign language type is '{clean_type}'"
            )

    return clean_type, clean_variety

