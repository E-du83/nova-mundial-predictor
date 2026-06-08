"""
World Football Elo offline loader.

Use verified local CSV/manual snapshots. This module does not scrape the web.
"""

import csv
from pathlib import Path


SOURCE_ID = "world_football_elo"
WORLD_ELO_REFERENCE = "https://www.eloratings.net/"
MINIMUM_FIELDS = {"team", "elo", "rank", "source", "date_collected", "notes"}


def load_world_elo_csv(path: str | Path) -> dict:
    csv_path = Path(path)
    if not csv_path.exists():
        return {
            "source_id": SOURCE_ID,
            "source_status": "manual_snapshot_required",
            "status": "manual_snapshot_required",
            "usable": False,
            "path": str(csv_path),
            "message": "No verified local World Football Elo CSV found.",
            "reference": WORLD_ELO_REFERENCE,
        }

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        missing_fields = sorted(MINIMUM_FIELDS - fieldnames)
        if missing_fields:
            return {
                "source_id": SOURCE_ID,
                "status": "missing_required_fields",
                "usable": False,
                "path": str(csv_path),
                "missing_fields": missing_fields,
                "reference": WORLD_ELO_REFERENCE,
            }
        rows = list(reader)

    return {
        "source_id": SOURCE_ID,
        "status": "local_snapshot_loaded",
        "data_status": "ready_snapshot",
        "usable": True,
        "path": str(csv_path),
        "rows": rows,
        "row_count": len(rows),
        "source_status": "manual_snapshot_loaded",
        "freshness": "pending_freshness_verification",
        "weighting_role": "high_weight_signal_when_date_and_source_are_verified",
        "reference": WORLD_ELO_REFERENCE,
    }


def manual_snapshot_requirements() -> dict:
    return {
        "source_id": SOURCE_ID,
        "required_fields": sorted(MINIMUM_FIELDS),
        "optional_fields": ["matches", "source_url"],
        "notes": [
            "Use a manually verified CSV snapshot.",
            "Mark freshness before using it as final 2026 input.",
            "World Football Elo can change after each international match.",
            "Do not invent Elo values; missing snapshots stay manual_snapshot_required.",
        ],
    }


def to_team_signal(snapshot: dict) -> dict:
    if not snapshot.get("usable"):
        return {
            "source_id": SOURCE_ID,
            "data_status": snapshot.get("status", "manual_snapshot_required"),
            "signals": {},
            "weighting_role": "not_active_until_verified_snapshot_exists",
        }
    signals = {}
    for row in snapshot.get("rows", []):
        team = row.get("team")
        if not team:
            continue
        signals[team] = {
            "elo": row.get("elo"),
            "rank": row.get("rank"),
            "source": row.get("source"),
            "date_collected": row.get("date_collected"),
            "notes": row.get("notes", ""),
            "weight": "high_when_freshness_verified",
        }
    return {
        "source_id": SOURCE_ID,
        "data_status": "ready_snapshot",
        "signals": signals,
        "team_count": len(signals),
        "weighting_role": "high_weight_signal_when_verified",
    }
