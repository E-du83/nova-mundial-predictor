from __future__ import annotations

import json
from pathlib import Path


LAYER_ROOT = Path(__file__).resolve().parent
DATA_ROOT = LAYER_ROOT / "data"

GROUP_STRUCTURE_PATH = DATA_ROOT / "worldcup_2026_group_structure.json"
FIXTURE_STATUS_PATH = DATA_ROOT / "worldcup_2026_fixture_status.json"
GROUP_STAGE_FIXTURE_PATH = DATA_ROOT / "worldcup_2026_group_stage_fixture.json"
MATCH_SLOTS_PATH = DATA_ROOT / "worldcup_2026_match_slots.json"

GROUPS = tuple("ABCDEFGHIJKL")
SLOTS_PER_GROUP = 6
GROUP_STAGE_MATCHES = len(GROUPS) * SLOTS_PER_GROUP
GENERATED_AT = "2026-06-10T00:00:00Z"


def _write_json_if_changed(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    path.write_text(text, encoding="utf-8")


def build_group_structure() -> dict:
    groups = [
        {
            "group_name": group,
            "teams": "pending_group_draw",
            "match_slots": SLOTS_PER_GROUP,
            "status": "pending_group_draw",
        }
        for group in GROUPS
    ]
    return {
        "tournament": "FIFA World Cup 2026",
        "data_status": "pending_group_draw",
        "source_status": "manual_snapshot_required",
        "fixture_structure": "official_tournament_structure",
        "teams_total": 48,
        "groups_total": len(GROUPS),
        "teams_per_group": 4,
        "group_stage_matches_per_group": SLOTS_PER_GROUP,
        "total_group_stage_matches": GROUP_STAGE_MATCHES,
        "total_tournament_matches": 104,
        "groups": groups,
        "warnings": [
            "Group draw is not loaded in this local snapshot.",
            "Do not infer teams or matchups from placeholders.",
        ],
    }


def build_match_slots() -> dict:
    slots = []
    for group in GROUPS:
        for slot_number in range(1, SLOTS_PER_GROUP + 1):
            slots.append(
                {
                    "match_id": f"WG-{group}-{slot_number:02d}",
                    "phase": "group_stage",
                    "group": group,
                    "slot_number": slot_number,
                    "team_a": "pending_group_draw",
                    "team_b": "pending_group_draw",
                    "kickoff_utc": "pending_official_fixture",
                    "venue": "pending_official_fixture",
                    "status": "pending_group_draw",
                    "slot_structure": {
                        "stable_slot_id": f"WG-{group}-{slot_number:02d}",
                        "group": group,
                        "slot_number": slot_number,
                    },
                    "fixture_assignment": {
                        "assignment_status": "pending_official_fixture",
                        "source_status": "manual_snapshot_required",
                    },
                    "match_result": {
                        "result_status": "not_played",
                        "score": "pending_match_result",
                    },
                }
            )
    return {
        "tournament": "FIFA World Cup 2026",
        "data_status": "structural_placeholder",
        "source_status": "manual_snapshot_required",
        "fixture_structure": "group_stage_slots",
        "total_slots": len(slots),
        "expected_slots": GROUP_STAGE_MATCHES,
        "matches": slots,
    }


def build_group_stage_fixture(slots_data: dict | None = None) -> dict:
    slots_data = slots_data or build_match_slots()
    matches = slots_data.get("matches", [])
    pending = sum(1 for item in matches if item.get("status") != "confirmed_fixture")
    confirmed = len(matches) - pending
    return {
        "tournament": "FIFA World Cup 2026",
        "fixture_type": "structural_placeholder",
        "official_status": "pending_official_fixture",
        "generated_at": GENERATED_AT,
        "source_status": "manual_snapshot_required",
        "total_matches": len(matches),
        "matches_confirmed": confirmed,
        "matches_pending": pending,
        "matches": matches,
        "warnings": [
            "This file contains structural slots only.",
            "No official team matchups, kickoff times or venues are asserted.",
        ],
    }


def build_fixture_status(
    group_structure: dict | None = None,
    fixture: dict | None = None,
) -> dict:
    group_structure = group_structure or build_group_structure()
    fixture = fixture or build_group_stage_fixture()
    return {
        "tournament": "FIFA World Cup 2026",
        "data_status": "fixture_structure_ready_pending_official_fixture",
        "fixture_type": fixture.get("fixture_type", "structural_placeholder"),
        "official_status": fixture.get("official_status", "pending_official_fixture"),
        "groups_configured": len(group_structure.get("groups", [])),
        "teams_total": group_structure.get("teams_total", 48),
        "total_group_stage_matches": group_structure.get("total_group_stage_matches", GROUP_STAGE_MATCHES),
        "total_tournament_matches": group_structure.get("total_tournament_matches", 104),
        "fixture_slots_loaded": fixture.get("total_matches", 0),
        "confirmed_fixture_matches": fixture.get("matches_confirmed", 0),
        "pending_fixture_matches": fixture.get("matches_pending", 0),
        "ready_for_full_group_simulation": False,
        "replacement_contract": {
            "slot_structure": "stable",
            "fixture_assignment": "replace only with verified official fixture snapshot",
            "match_result": "kept separate from prematch fixture data",
        },
        "warnings": [
            "Fixture is a structural placeholder until official group draw and match schedule are loaded.",
            "Do not mark placeholder matchups as confirmed.",
        ],
    }


def write_default_fixture_files() -> dict:
    group_structure = build_group_structure()
    slots = build_match_slots()
    fixture = build_group_stage_fixture(slots)
    status = build_fixture_status(group_structure, fixture)

    _write_json_if_changed(GROUP_STRUCTURE_PATH, group_structure)
    _write_json_if_changed(MATCH_SLOTS_PATH, slots)
    _write_json_if_changed(GROUP_STAGE_FIXTURE_PATH, fixture)
    _write_json_if_changed(FIXTURE_STATUS_PATH, status)
    return {
        "group_structure_path": str(GROUP_STRUCTURE_PATH),
        "match_slots_path": str(MATCH_SLOTS_PATH),
        "group_stage_fixture_path": str(GROUP_STAGE_FIXTURE_PATH),
        "fixture_status_path": str(FIXTURE_STATUS_PATH),
        "groups_configured": len(group_structure["groups"]),
        "slots_created": slots["total_slots"],
        "fixture_type": fixture["fixture_type"],
        "official_status": fixture["official_status"],
    }
