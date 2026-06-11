from __future__ import annotations

import json
from pathlib import Path

from worldcup_2026_fixture_validator import PENDING_VALUES, VALIDATION_REPORT_PATH
from worldcup_2026_match_slot_engine import GROUP_STAGE_FIXTURE_PATH, GROUP_STAGE_MATCHES


LAYER_ROOT = Path(__file__).resolve().parent
ROOT = LAYER_ROOT.parents[1]
BASELINE_PATH = ROOT / "data" / "worldcup_2026_real_teams_baseline_v1.json"
GUARD_REPORT_PATH = LAYER_ROOT / "data" / "worldcup_2026_fixture_guard_report.json"


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


def _is_pending(value) -> bool:
    return value in PENDING_VALUES or str(value).startswith("pending_")


def _valid_utc(value) -> bool:
    if _is_pending(value):
        return False
    return isinstance(value, str) and (value.endswith("Z") or "+00:00" in value)


def evaluate_group_stage_simulation_readiness(
    fixture_path=GROUP_STAGE_FIXTURE_PATH,
    baseline_path=BASELINE_PATH,
    validation_report_path=None,
) -> dict:
    fixture = _load_json(fixture_path)
    baseline = _load_json(baseline_path)
    validation = _load_json(validation_report_path or VALIDATION_REPORT_PATH)
    matches = fixture.get("matches", [])
    fixture_type = fixture.get("fixture_type", "missing")
    official_status = fixture.get("official_status", "missing")
    block_reason = []
    warnings = []
    baseline_missing = []
    pending_team_slots = []
    missing_kickoff = []
    missing_venue = []

    slot_ids = [item.get("match_id") for item in matches]
    duplicate_slot_ids = sorted({item for item in slot_ids if slot_ids.count(item) > 1})
    seen_matchups = set()
    duplicate_matches = []
    confirmed_matches = 0

    for item in matches:
        if item.get("status") == "confirmed_fixture":
            confirmed_matches += 1
        team_a = item.get("team_a")
        team_b = item.get("team_b")
        if _is_pending(team_a) or _is_pending(team_b):
            pending_team_slots.append(item.get("match_id", "unknown"))
        else:
            matchup = (item.get("group"), tuple(sorted((str(team_a), str(team_b)))))
            if matchup in seen_matchups:
                duplicate_matches.append(item.get("match_id", "unknown"))
            seen_matchups.add(matchup)
            for team in (team_a, team_b):
                if team not in baseline:
                    baseline_missing.append(team)
        if not _valid_utc(item.get("kickoff_utc")):
            missing_kickoff.append(item.get("match_id", "unknown"))
        if _is_pending(item.get("venue")):
            missing_venue.append(item.get("match_id", "unknown"))

    pending_matches = len(matches) - confirmed_matches
    if fixture_type == "structural_placeholder":
        block_reason.append("fixture_type is structural_placeholder")
    if len(matches) != GROUP_STAGE_MATCHES:
        block_reason.append(f"expected 72 group-stage matches, found {len(matches)}")
    if confirmed_matches < GROUP_STAGE_MATCHES:
        block_reason.append(f"confirmed_matches {confirmed_matches} < 72")
    if pending_team_slots:
        block_reason.append("fixture still has pending teams")
    if missing_kickoff:
        block_reason.append("fixture still has missing or pending kickoff UTC")
    if missing_venue:
        block_reason.append("fixture still has missing or pending venues")
    if baseline_missing:
        block_reason.append("fixture includes teams missing from baseline")
    if duplicate_slot_ids:
        block_reason.append("duplicate slot IDs detected")
    if duplicate_matches:
        block_reason.append("duplicate matches detected")
    if validation.get("audit_status") not in ("cleared", "cleared_placeholder"):
        block_reason.append(f"validation audit status is {validation.get('audit_status', 'missing')}")

    if fixture_type == "structural_placeholder":
        warnings.append("Full Group Stage Picks Runner must remain blocked until official fixture import succeeds.")
    if missing_kickoff or missing_venue:
        warnings.append("Partial simulation can only be considered manually when confirmed teams exist.")

    ready_for_partial = bool(
        confirmed_matches > 0
        and fixture_type != "structural_placeholder"
        and not duplicate_slot_ids
        and not duplicate_matches
        and not baseline_missing
    )
    ready_for_full = bool(
        not block_reason
        and confirmed_matches == GROUP_STAGE_MATCHES
        and pending_matches == 0
        and official_status == "official_confirmed"
    )
    if ready_for_full:
        guard_status = "ready"
    elif ready_for_partial:
        guard_status = "partial_ready"
    elif fixture_type == "structural_placeholder":
        guard_status = "blocked_placeholder"
    else:
        guard_status = "blocked_invalid"

    report = {
        "ready_for_full_group_simulation": ready_for_full,
        "ready_for_partial_simulation": ready_for_partial,
        "block_reason": sorted(set(block_reason)),
        "warnings": sorted(set(warnings)),
        "confirmed_matches": confirmed_matches,
        "pending_matches": pending_matches,
        "baseline_team_missing": sorted(set(baseline_missing)),
        "pending_team_slots": pending_team_slots,
        "missing_kickoff_slots": missing_kickoff,
        "missing_venue_slots": missing_venue,
        "duplicate_slot_ids": duplicate_slot_ids,
        "duplicate_matches": duplicate_matches,
        "fixture_type": fixture_type,
        "official_status": official_status,
        "validation_audit_status": validation.get("audit_status", "missing"),
        "guard_status": guard_status,
    }
    _write_json_if_changed(GUARD_REPORT_PATH, report)
    return report
