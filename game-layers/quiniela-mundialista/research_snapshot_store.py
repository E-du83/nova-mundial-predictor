from __future__ import annotations

import json
import re
from pathlib import Path

from research_snapshot_validator import validate_research_snapshot


LAYER_ROOT = Path(__file__).resolve().parent
SNAPSHOT_DIR = LAYER_ROOT / "data" / "research_snapshots"


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "pending_match"


def _snapshot_filename(snapshot: dict) -> str:
    captured = str(snapshot.get("captured_at", "pending_date"))[:10].replace("-", "")
    if not captured or captured.startswith("pending"):
        captured = "pendingdate"
    team_a = _safe_slug(str(snapshot.get("team_a", "team_a")))
    team_b = _safe_slug(str(snapshot.get("team_b", "team_b")))
    return f"{captured}_{team_a}_vs_{team_b}_snapshot.json"


def save_research_snapshot(snapshot, dry_run=True, force=False) -> dict:
    validation = validate_research_snapshot(snapshot)
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    filename = _snapshot_filename(snapshot)
    path = SNAPSHOT_DIR / filename
    result = {
        "dry_run": dry_run,
        "files_written": 0,
        "snapshot_path": str(path),
        "validation_status": validation["validation_status"],
        "status": "dry_run_not_written" if dry_run else "pending_write",
        "warnings": list(validation["warnings"]),
    }
    if dry_run:
        return result
    if path.exists() and not force:
        result["status"] = "blocked_existing_snapshot"
        result["warnings"].append("Snapshot exists; use force=True to overwrite.")
        return result
    path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    result["files_written"] = 1
    result["status"] = "written"
    return result


def load_research_snapshot(snapshot_id) -> dict:
    if not SNAPSHOT_DIR.exists():
        return {}
    for path in SNAPSHOT_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("snapshot_id") == snapshot_id or path.stem == snapshot_id:
            return data
    return {}


def list_research_snapshots() -> list[dict]:
    if not SNAPSHOT_DIR.exists():
        return []
    items = []
    for path in sorted(SNAPSHOT_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        validation = validate_research_snapshot(data)
        items.append(
            {
                "snapshot_id": data.get("snapshot_id", path.stem),
                "match": data.get("match", "pending_manual_input"),
                "team_a": data.get("team_a", "pending_manual_input"),
                "team_b": data.get("team_b", "pending_manual_input"),
                "path": str(path),
                "validation_status": validation["validation_status"],
                "valid_for_tactical_bridge": validation["valid_for_tactical_bridge"],
                "valid_for_market_weighting": validation["valid_for_market_weighting"],
                "valid_for_prediction_context": validation["valid_for_prediction_context"],
            }
        )
    return items


def find_research_snapshot_for_match(team_a: str, team_b: str) -> dict:
    requested = {team_a.strip().lower(), team_b.strip().lower()}
    for item in list_research_snapshots():
        current = {str(item.get("team_a", "")).strip().lower(), str(item.get("team_b", "")).strip().lower()}
        if current == requested:
            return item
    return {
        "snapshot_available": False,
        "validation_status": "missing",
        "valid_for_tactical_bridge": False,
        "valid_for_market_weighting": False,
        "valid_for_prediction_context": False,
    }
