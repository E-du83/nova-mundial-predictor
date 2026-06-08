"""
Safe openfootball/worldcup.json scaffold.

This module only loads local snapshots. It documents how openfootball data can
be connected without making internet access mandatory.
"""

import json
from pathlib import Path


SOURCE_ID = "openfootball_worldcup"
OPENFOOTBALL_REFERENCE = "https://github.com/openfootball/worldcup.json"
MINIMUM_TOP_LEVEL_KEYS = ("name", "matches")


def load_openfootball_snapshot(path: str | Path) -> dict:
    snapshot_path = Path(path)
    if not snapshot_path.exists():
        return {
            "source_id": SOURCE_ID,
            "source_status": "manual_snapshot_required",
            "status": "manual_snapshot_required",
            "usable": False,
            "path": str(snapshot_path),
            "message": "No local openfootball snapshot found.",
            "reference": OPENFOOTBALL_REFERENCE,
            "requires_api_key": False,
        }

    try:
        data = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "source_id": SOURCE_ID,
            "status": "invalid_json",
            "usable": False,
            "path": str(snapshot_path),
            "message": f"JSON parse error: {exc}",
            "reference": OPENFOOTBALL_REFERENCE,
            "requires_api_key": False,
        }

    missing_keys = [
        key
        for key in MINIMUM_TOP_LEVEL_KEYS
        if key not in data
    ]
    if missing_keys:
        return {
            "source_id": SOURCE_ID,
            "source_status": "missing_required_fields",
            "status": "missing_required_fields",
            "usable": False,
            "path": str(snapshot_path),
            "missing_fields": missing_keys,
            "reference": OPENFOOTBALL_REFERENCE,
            "requires_api_key": False,
        }

    return {
        "source_id": SOURCE_ID,
        "source_status": "local_snapshot_loaded",
        "status": "local_snapshot_loaded",
        "data_status": "ready_snapshot",
        "usable": True,
        "path": str(snapshot_path),
        "data": data,
        "match_count": len(data.get("matches", [])) if isinstance(data.get("matches"), list) else 0,
        "reference": OPENFOOTBALL_REFERENCE,
        "requires_api_key": False,
        "cost": "free",
    }


def connection_notes() -> dict:
    return {
        "source_id": SOURCE_ID,
        "reference": OPENFOOTBALL_REFERENCE,
        "mode": "offline_first",
        "requires_api_key": False,
        "notes": [
            "openfootball/worldcup.json is open data and does not require an API key.",
            "Prefer a manually verified local JSON snapshot.",
            "Do not scrape aggressively.",
            "Validate license and fields before using in recommendations.",
            "If no snapshot exists, return pending_manual_snapshot instead of failing.",
        ],
    }


def validate_worldcup_matches(data: dict) -> dict:
    matches = data.get("matches")
    if not isinstance(matches, list):
        return {
            "usable": False,
            "status": "missing_matches_list",
            "missing_fields": ["matches"],
        }
    required = {"team1", "team2"}
    invalid_indexes = []
    for index, match in enumerate(matches):
        if not isinstance(match, dict) or not required.issubset(match):
            invalid_indexes.append(index)
    return {
        "usable": not invalid_indexes,
        "status": "valid_matches" if not invalid_indexes else "missing_match_fields",
        "match_count": len(matches),
        "invalid_indexes": invalid_indexes,
        "required_match_fields": sorted(required),
    }
