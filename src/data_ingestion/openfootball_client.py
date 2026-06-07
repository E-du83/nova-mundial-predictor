"""
Safe openfootball/worldcup.json scaffold.

This module only loads local snapshots. It documents how openfootball data can
be connected without making internet access mandatory.
"""

import json
from pathlib import Path


SOURCE_ID = "openfootball_worldcup"
OPENFOOTBALL_REFERENCE = "https://github.com/openfootball/worldcup.json"


def load_openfootball_snapshot(path: str | Path) -> dict:
    snapshot_path = Path(path)
    if not snapshot_path.exists():
        return {
            "source_id": SOURCE_ID,
            "status": "pending_manual_snapshot",
            "usable": False,
            "path": str(snapshot_path),
            "message": "No local openfootball snapshot found.",
            "reference": OPENFOOTBALL_REFERENCE,
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
        }

    return {
        "source_id": SOURCE_ID,
        "status": "local_snapshot_loaded",
        "usable": True,
        "path": str(snapshot_path),
        "data": data,
        "reference": OPENFOOTBALL_REFERENCE,
    }


def connection_notes() -> dict:
    return {
        "source_id": SOURCE_ID,
        "reference": OPENFOOTBALL_REFERENCE,
        "mode": "offline_first",
        "notes": [
            "Prefer a manually verified local JSON snapshot.",
            "Do not scrape aggressively.",
            "Validate license and fields before using in recommendations.",
            "If no snapshot exists, return pending_manual_snapshot instead of failing.",
        ],
    }
