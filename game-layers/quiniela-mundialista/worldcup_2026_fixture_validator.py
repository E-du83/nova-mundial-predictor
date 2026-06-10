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
