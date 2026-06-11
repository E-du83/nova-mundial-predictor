from __future__ import annotations

import copy
import json
from pathlib import Path

from worldcup_2026_fixture_validator import validate_fixture_snapshot, validate_worldcup_2026_fixture
from worldcup_2026_match_slot_engine import (
    GROUP_STAGE_FIXTURE_PATH,
    GROUP_STAGE_MATCHES,
    GROUPS,
    MATCH_SLOTS_PATH,
)


LAYER_ROOT = Path(__file__).resolve().parent
DATA_ROOT = LAYER_ROOT / "data"
SNAPSHOT_TEMPLATE_PATH = DATA_ROOT / "worldcup_2026_official_fixture_snapshot_template.json"
IMPORT_REPORT_PATH = DATA_ROOT / "worldcup_2026_fixture_import_report.json"


def _load_json(path: str | Path) -> dict:
    data_path = Path(path)
    if not data_path.exists():
        return {}
    return json.loads(data_path.read_text(encoding="utf-8"))


def _write_json_if_changed(path: str | Path, data: dict) -> None:
    data_path = Path(path)
    data_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if data_path.exists() and data_path.read_text(encoding="utf-8") == text:
        return
    data_path.write_text(text, encoding="utf-8")


def build_official_fixture_snapshot_template() -> dict:
    matches = []
    for group in GROUPS:
        for slot_number in range(1, 7):
            matches.append(
                {
                    "slot_id": f"WG-{group}-{slot_number:02d}",
                    "phase": "group_stage",
                    "group": group,
                    "matchday": "pending_verification",
                    "team_a": "pending_group_draw",
                    "team_b": "pending_group_draw",
                    "kickoff_utc": "pending_official_fixture",
                    "venue": "pending_official_fixture",
                    "city": "pending_official_fixture",
                    "country": "pending_official_fixture",
                    "source": "pending_official_source",
                    "source_status": "pending_manual_input",
                    "verification_status": "pending_verification",
                }
            )
    return {
        "snapshot_name": "worldcup_2026_official_fixture_snapshot",
        "tournament": "FIFA World Cup 2026",
        "snapshot_type": "manual_verified_fixture_snapshot",
        "source_status": "template_pending_manual_input",
        "source": "pending_official_source",
        "captured_at": "pending_manual_input",
        "captured_by": "pending_manual_input",
        "timezone_policy": "kickoff_time_utc_required",
        "total_group_stage_matches_expected": GROUP_STAGE_MATCHES,
        "groups_expected": len(GROUPS),
        "teams_per_group_expected": 4,
        "matches": matches,
    }


def ensure_official_fixture_snapshot_template(path: str | Path = SNAPSHOT_TEMPLATE_PATH) -> dict:
    template = build_official_fixture_snapshot_template()
    _write_json_if_changed(path, template)
    return template


def _snapshot_by_slot(snapshot: dict) -> dict:
    return {
        item.get("slot_id") or item.get("match_id"): item
        for item in snapshot.get("matches", [])
        if item.get("slot_id") or item.get("match_id")
    }


def _updated_fixture(current_fixture: dict, snapshot: dict) -> dict:
    updated = copy.deepcopy(current_fixture)
    snapshot_matches = _snapshot_by_slot(snapshot)
    updated_matches = []
    for match in updated.get("matches", []):
        slot_id = match.get("match_id")
        incoming = snapshot_matches.get(slot_id)
        if not incoming:
            updated_matches.append(match)
            continue
        next_match = copy.deepcopy(match)
        next_match["phase"] = incoming.get("phase", next_match.get("phase"))
        next_match["group"] = incoming.get("group", next_match.get("group"))
        next_match["team_a"] = incoming.get("team_a", next_match.get("team_a"))
        next_match["team_b"] = incoming.get("team_b", next_match.get("team_b"))
        next_match["kickoff_utc"] = incoming.get("kickoff_utc", next_match.get("kickoff_utc"))
        next_match["venue"] = incoming.get("venue", next_match.get("venue"))
        next_match["status"] = "confirmed_fixture"
        next_match["fixture_assignment"] = {
            **next_match.get("fixture_assignment", {}),
            "assignment_status": "confirmed_fixture",
            "source": incoming.get("source", snapshot.get("source", "pending_official_source")),
            "source_status": incoming.get("source_status", snapshot.get("source_status")),
            "verification_status": incoming.get("verification_status", "pending_verification"),
            "city": incoming.get("city", "pending_official_fixture"),
            "country": incoming.get("country", "pending_official_fixture"),
            "captured_at": snapshot.get("captured_at", "pending_manual_input"),
            "captured_by": snapshot.get("captured_by", "pending_manual_input"),
        }
        next_match["fixture_source"] = {
            "snapshot_name": snapshot.get("snapshot_name", "worldcup_2026_official_fixture_snapshot"),
            "source": snapshot.get("source", incoming.get("source", "pending_official_source")),
            "source_status": snapshot.get("source_status", "pending_verification"),
        }
        updated_matches.append(next_match)

    updated["fixture_type"] = "confirmed_fixture"
    updated["official_status"] = "official_confirmed"
    updated["source_status"] = "official_confirmed"
    updated["matches"] = updated_matches
    updated["matches_confirmed"] = sum(1 for item in updated_matches if item.get("status") == "confirmed_fixture")
    updated["matches_pending"] = len(updated_matches) - updated["matches_confirmed"]
    return updated


def import_fixture_snapshot(
    snapshot_path,
    current_fixture_path=GROUP_STAGE_FIXTURE_PATH,
    output_fixture_path=GROUP_STAGE_FIXTURE_PATH,
    validation_report_path=IMPORT_REPORT_PATH,
    dry_run=True,
) -> dict:
    snapshot = _load_json(snapshot_path)
    current_fixture = _load_json(current_fixture_path)
    validation = validate_fixture_snapshot(snapshot_path)
    errors = list(validation.get("errors", []))
    warnings = list(validation.get("warnings", []))
    snapshot_confirmed = validation.get("snapshot_confirmed", False)
    matches_in_snapshot = validation.get("matches_in_snapshot", 0)
    matches_valid = validation.get("matches_valid", 0)
    matches_blocked = validation.get("matches_blocked", 0)
    would_update = 0
    updated_matches = 0
    ready_after_import = False

    if not snapshot_confirmed:
        errors.append("snapshot source_status must be official_confirmed before import")
        matches_blocked = matches_in_snapshot
    if matches_in_snapshot != GROUP_STAGE_MATCHES:
        errors.append("snapshot must contain exactly 72 group-stage matches")
    if matches_blocked:
        errors.append("snapshot contains blocked matches")

    if not errors:
        snapshot_ids = set(_snapshot_by_slot(snapshot))
        active_ids = {item.get("match_id") for item in current_fixture.get("matches", [])}
        would_update = len(snapshot_ids & active_ids)
        candidate = _updated_fixture(current_fixture, snapshot)
        validation_candidate_path = Path(output_fixture_path)
        if not dry_run:
            _write_json_if_changed(output_fixture_path, candidate)
            updated_matches = would_update
            validate_worldcup_2026_fixture(fixture_path=output_fixture_path, write_report=True)
        else:
            validation_result = validate_worldcup_2026_fixture(
                fixture_path=current_fixture_path,
                write_report=False,
            )
            warnings.append(
                f"dry_run only; active fixture validation remains {validation_result.get('audit_status', 'missing')}"
            )
        ready_after_import = candidate.get("matches_confirmed", 0) == GROUP_STAGE_MATCHES

    if errors:
        import_status = "blocked"
    elif dry_run:
        import_status = "dry_run_ok"
    elif updated_matches == GROUP_STAGE_MATCHES:
        import_status = "imported"
    else:
        import_status = "partial"

    report = {
        "import_status": import_status,
        "dry_run": bool(dry_run),
        "matches_in_snapshot": matches_in_snapshot,
        "matches_valid": matches_valid,
        "matches_blocked": matches_blocked,
        "would_update_matches": would_update,
        "updated_matches": updated_matches,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "ready_for_full_group_simulation_after_import": bool(ready_after_import and not dry_run and not errors),
        "snapshot_validation_status": validation.get("validation_status", "missing"),
    }
    _write_json_if_changed(validation_report_path, report)
    return report
