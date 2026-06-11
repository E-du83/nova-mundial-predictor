from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from worldcup_2026_match_slot_engine import (
    FIXTURE_STATUS_PATH,
    GROUPS,
    GROUP_STAGE_FIXTURE_PATH,
    GROUP_STAGE_MATCHES,
    GROUP_STRUCTURE_PATH,
    MATCH_SLOTS_PATH,
)


LAYER_ROOT = Path(__file__).resolve().parent
VALIDATION_REPORT_PATH = LAYER_ROOT / "data" / "worldcup_2026_fixture_validation_report.json"
PENDING_VALUES = {
    "pending_group_draw",
    "pending_official_fixture",
    "manual_snapshot_required",
    "pending_verification",
    "pending_manual_input",
    "pending_official_source",
    "template_pending_manual_input",
}


def _load_json(path: str | Path) -> dict:
    data_path = Path(path)
    if not data_path.exists():
        return {}
    return json.loads(data_path.read_text(encoding="utf-8"))


def _write_json_if_changed(path: Path, data: dict) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    path.write_text(text, encoding="utf-8")


def _valid_utc_or_pending(value) -> bool:
    if value in PENDING_VALUES:
        return True
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return value.endswith("Z") or "+00:00" in value


def _valid_venue_or_pending(value) -> bool:
    return value in PENDING_VALUES or (isinstance(value, str) and bool(value.strip()))


def _baseline_teams(path: str | Path | None = None) -> set[str]:
    if path is None:
        path = LAYER_ROOT.parents[1] / "data" / "worldcup_2026_real_teams_baseline_v1.json"
    data = _load_json(path)
    return set(data.keys())


def validate_fixture_snapshot(
    snapshot_path: str | Path,
    structural_slots_path: str | Path = MATCH_SLOTS_PATH,
    baseline_path: str | Path | None = None,
) -> dict:
    snapshot = _load_json(snapshot_path)
    structural_slots = _load_json(structural_slots_path).get("matches", [])
    baseline = _baseline_teams(baseline_path)
    structural_by_id = {item.get("match_id"): item for item in structural_slots}
    valid_slot_ids = set(structural_by_id)
    matches = snapshot.get("matches", [])
    source_status = snapshot.get("source_status")
    snapshot_confirmed = source_status == "official_confirmed"
    errors = []
    warnings = []
    valid_matches = []
    blocked_matches = []
    seen_slot_ids = set()
    seen_matchups = set()

    required_snapshot_fields = ("source_status", "source", "captured_at", "captured_by")
    for field in required_snapshot_fields:
        if field not in snapshot:
            errors.append(f"snapshot missing {field}")

    if snapshot.get("total_group_stage_matches_expected", GROUP_STAGE_MATCHES) != GROUP_STAGE_MATCHES:
        errors.append("snapshot expected group-stage match count must be 72")
    if len(matches) != GROUP_STAGE_MATCHES:
        errors.append(f"snapshot must contain exactly 72 matches before import; found {len(matches)}")

    for match in matches:
        slot_id = match.get("slot_id") or match.get("match_id")
        match_errors = []
        if not slot_id:
            match_errors.append("missing slot_id")
        elif slot_id not in valid_slot_ids:
            match_errors.append(f"invalid slot_id {slot_id}")
        elif slot_id in seen_slot_ids:
            match_errors.append(f"duplicate slot_id {slot_id}")
        seen_slot_ids.add(slot_id)

        group = match.get("group")
        if group not in GROUPS:
            match_errors.append(f"invalid group {group}")
        elif slot_id in structural_by_id and structural_by_id[slot_id].get("group") != group:
            match_errors.append(f"group mismatch for {slot_id}")
        if match.get("phase") != "group_stage":
            match_errors.append("phase must be group_stage")
        if "source_status" not in match:
            match_errors.append("missing source_status")
        if "verification_status" not in match:
            match_errors.append("missing verification_status")

        team_a = match.get("team_a")
        team_b = match.get("team_b")
        kickoff = match.get("kickoff_utc")
        venue = match.get("venue")
        verification = match.get("verification_status")
        match_confirmed = snapshot_confirmed or verification == "official_confirmed"

        if team_a not in PENDING_VALUES and team_b not in PENDING_VALUES:
            matchup = (group, tuple(sorted((str(team_a), str(team_b)))))
            if matchup in seen_matchups:
                match_errors.append(f"duplicate matchup in group {group}")
            seen_matchups.add(matchup)

        if match_confirmed:
            if team_a in PENDING_VALUES or team_b in PENDING_VALUES:
                match_errors.append("confirmed snapshot cannot use pending teams")
            if not _valid_utc_or_pending(kickoff):
                match_errors.append("confirmed snapshot has invalid kickoff UTC")
            elif kickoff in PENDING_VALUES:
                warnings.append(f"{slot_id}: kickoff_utc pending_verification; allowed for pre-tournament quiniela")
            if not _valid_venue_or_pending(venue):
                match_errors.append("confirmed snapshot has invalid venue")
            elif venue in PENDING_VALUES:
                warnings.append(f"{slot_id}: venue pending_verification; allowed for pre-tournament quiniela")
            for team in (team_a, team_b):
                if team not in PENDING_VALUES and team not in baseline:
                    match_errors.append(f"team not found in baseline: {team}")
        else:
            if team_a in PENDING_VALUES or team_b in PENDING_VALUES:
                warnings.append(f"{slot_id}: teams pending; not importable as confirmed fixture")
            for team in (team_a, team_b):
                if team not in PENDING_VALUES and team not in baseline:
                    warnings.append(f"{slot_id}: team pending baseline verification: {team}")

        if match_errors:
            blocked_matches.append({"slot_id": slot_id or "missing", "errors": match_errors})
        else:
            valid_matches.append(slot_id)

    if source_status != "official_confirmed":
        warnings.append("snapshot source_status is not official_confirmed; importer must not update active fixture")

    return {
        "snapshot_name": snapshot.get("snapshot_name", "missing"),
        "source_status": source_status or "missing",
        "snapshot_confirmed": snapshot_confirmed,
        "matches_in_snapshot": len(matches),
        "matches_valid": len(valid_matches),
        "matches_blocked": len(blocked_matches),
        "valid_slot_ids": valid_matches,
        "blocked_matches": blocked_matches,
        "errors": errors,
        "warnings": sorted(set(warnings)),
        "validation_status": "valid_confirmed_snapshot"
        if snapshot_confirmed and not errors and not blocked_matches
        else "pending_or_blocked",
    }


def validate_worldcup_2026_fixture(
    group_structure_path: str | Path = GROUP_STRUCTURE_PATH,
    fixture_path: str | Path = GROUP_STAGE_FIXTURE_PATH,
    slots_path: str | Path = MATCH_SLOTS_PATH,
    fixture_status_path: str | Path = FIXTURE_STATUS_PATH,
    output_path: str | Path = VALIDATION_REPORT_PATH,
    write_report: bool = True,
) -> dict:
    group_structure = _load_json(group_structure_path)
    fixture = _load_json(fixture_path)
    slots_data = _load_json(slots_path)
    status = _load_json(fixture_status_path)
    groups = group_structure.get("groups", [])
    slots = slots_data.get("matches", fixture.get("matches", []))

    group_names = [item.get("group_name") for item in groups]
    slot_ids = [item.get("match_id") for item in slots]
    duplicate_slot_ids = sorted({item for item in slot_ids if slot_ids.count(item) > 1})
    invalid_groups = sorted(
        {
            item.get("group")
            for item in slots
            if item.get("group") not in GROUPS
        }
        | {group for group in group_names if group not in GROUPS}
    )
    group_counts = {
        group: sum(1 for item in slots if item.get("group") == group)
        for group in GROUPS
    }
    groups_over_limit = sorted(group for group, count in group_counts.items() if count > 6)
    non_group_stage = [
        item.get("match_id", "unknown")
        for item in slots
        if item.get("phase") != "group_stage"
    ]

    seen_matches = set()
    duplicate_matches = []
    confirmed_fixture_count = 0
    pending_fixture_count = 0
    invalid_utc = []
    invalid_venues = []
    fictional_confirmed = []

    for item in slots:
        team_a = item.get("team_a")
        team_b = item.get("team_b")
        matchup = tuple(sorted((str(team_a), str(team_b))))
        matchup_key = (item.get("group"), matchup)
        if team_a not in PENDING_VALUES and team_b not in PENDING_VALUES:
            if matchup_key in seen_matches:
                duplicate_matches.append(item.get("match_id", "unknown"))
            seen_matches.add(matchup_key)
        status_value = item.get("status")
        if status_value == "confirmed_fixture":
            confirmed_fixture_count += 1
            if team_a in PENDING_VALUES or team_b in PENDING_VALUES:
                fictional_confirmed.append(item.get("match_id", "unknown"))
        else:
            pending_fixture_count += 1
        if not _valid_utc_or_pending(item.get("kickoff_utc")):
            invalid_utc.append(item.get("match_id", "unknown"))
        if not _valid_venue_or_pending(item.get("venue")):
            invalid_venues.append(item.get("match_id", "unknown"))

    warnings = []
    if fixture.get("fixture_type") == "structural_placeholder":
        warnings.append("Fixture is structural placeholder; full group simulation must remain disabled.")
    if pending_fixture_count:
        warnings.append("Official group draw, kickoff UTC and venues are pending.")
    if fictional_confirmed:
        warnings.append("Some slots are confirmed without concrete teams; this is invalid.")

    valid_group_structure = (
        group_structure.get("teams_total") == 48
        and group_structure.get("groups_total") == 12
        and group_structure.get("teams_per_group") == 4
        and set(group_names) == set(GROUPS)
    )
    valid_slot_count = len(slots) == GROUP_STAGE_MATCHES and all(count == 6 for count in group_counts.values())
    valid_fixture = all(
        [
            valid_group_structure,
            valid_slot_count,
            not duplicate_slot_ids,
            not duplicate_matches,
            not invalid_groups,
            not groups_over_limit,
            not non_group_stage,
            not invalid_utc,
            not invalid_venues,
            not fictional_confirmed,
        ]
    )

    report = {
        "tournament": "FIFA World Cup 2026",
        "fixture_type": fixture.get("fixture_type", "missing"),
        "official_status": fixture.get("official_status", "missing"),
        "groups_detected": len(groups),
        "slots_detected": len(slots),
        "valid_group_structure": valid_group_structure,
        "valid_slot_count": valid_slot_count,
        "duplicate_slot_ids": duplicate_slot_ids,
        "duplicate_matches": duplicate_matches,
        "invalid_groups": invalid_groups,
        "groups_over_limit": groups_over_limit,
        "non_group_stage_slots": non_group_stage,
        "invalid_utc": invalid_utc,
        "invalid_venues": invalid_venues,
        "pending_fixture_count": pending_fixture_count,
        "confirmed_fixture_count": confirmed_fixture_count,
        "ready_for_full_group_simulation": bool(valid_fixture and confirmed_fixture_count == GROUP_STAGE_MATCHES),
        "fixture_status": status.get("data_status", "missing"),
        "warnings": warnings,
        "audit_status": "cleared_placeholder" if valid_fixture else "blocked",
    }
    if write_report:
        _write_json_if_changed(Path(output_path), report)
    return report
