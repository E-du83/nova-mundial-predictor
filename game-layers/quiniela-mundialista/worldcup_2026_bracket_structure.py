from __future__ import annotations

import json
from pathlib import Path


LAYER_ROOT = Path(__file__).resolve().parent
DATA_ROOT = LAYER_ROOT / "data"

KNOCKOUT_STRUCTURE_PATH = DATA_ROOT / "worldcup_2026_knockout_structure.json"
BRACKET_SLOTS_PATH = DATA_ROOT / "worldcup_2026_bracket_slots.json"
THIRD_PLACE_RULES_PATH = DATA_ROOT / "worldcup_2026_third_place_rules.json"

GENERATED_AT = "2026-06-10T00:00:00Z"
ROUNDS = {
    "round_of_32": ("R32", 16),
    "round_of_16": ("R16", 8),
    "quarter_finals": ("QF", 4),
    "semi_finals": ("SF", 2),
    "third_place": ("TP", 1),
    "final": ("F", 1),
}


def _write_json_if_changed(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    path.write_text(text, encoding="utf-8")


def build_knockout_structure() -> dict:
    return {
        "tournament": "FIFA World Cup 2026",
        "data_status": "worldcup_2026_knockout_structure_v1",
        "total_teams": 48,
        "groups": 12,
        "group_stage_qualifiers": {
            "top_two_each_group": 24,
            "best_third_placed": 8,
            "total_round_of_32_teams": 32,
        },
        "knockout_rounds": {
            "round_of_32": 16,
            "round_of_16": 8,
            "quarter_finals": 4,
            "semi_finals": 2,
            "third_place": 1,
            "final": 1,
        },
        "total_knockout_matches": 32,
        "total_tournament_matches": 104,
        "source_policy": "official_structure_required",
        "status": "scaffold_pending_group_results",
        "warnings": [
            "This is a knockout scaffold only.",
            "No real qualified teams or third-place combinations are asserted.",
        ],
    }


def _slot(match_id: str, round_name: str, depends_on: list[str] | None = None) -> dict:
    return {
        "match_id": match_id,
        "round": round_name,
        "team_a_source": "pending_group_results",
        "team_b_source": "pending_group_results",
        "team_a": "pending_group_results",
        "team_b": "pending_group_results",
        "status": "pending_group_results",
        "source_status": "manual_snapshot_required",
        "kickoff_utc": "pending_official_fixture",
        "venue": "pending_official_fixture",
        "depends_on": depends_on or ["final_group_standings", "official_bracket_mapping"],
    }


def _winner_sources(prefix: str, start: int, count: int) -> list[str]:
    return [f"winner:{prefix}-{number:02d}" for number in range(start, start + count)]


def build_bracket_slots() -> dict:
    slots = []
    for number in range(1, 17):
        slots.append(_slot(f"R32-{number:02d}", "round_of_32"))
    for number in range(1, 9):
        prior_start = (number - 1) * 2 + 1
        slots.append(_slot(f"R16-{number:02d}", "round_of_16", _winner_sources("R32", prior_start, 2)))
    for number in range(1, 5):
        prior_start = (number - 1) * 2 + 1
        slots.append(_slot(f"QF-{number:02d}", "quarter_finals", _winner_sources("R16", prior_start, 2)))
    for number in range(1, 3):
        prior_start = (number - 1) * 2 + 1
        slots.append(_slot(f"SF-{number:02d}", "semi_finals", _winner_sources("QF", prior_start, 2)))
    slots.append(_slot("TP-01", "third_place", ["loser:SF-01", "loser:SF-02"]))
    slots.append(_slot("F-01", "final", ["winner:SF-01", "winner:SF-02"]))
    return {
        "tournament": "FIFA World Cup 2026",
        "data_status": "worldcup_2026_bracket_slots_v1",
        "source_status": "manual_snapshot_required",
        "status": "scaffold_pending_group_results",
        "total_slots": len(slots),
        "round_counts": {round_name: count for round_name, (_, count) in ROUNDS.items()},
        "slots": slots,
        "warnings": [
            "Bracket slots are structural only.",
            "No qualified teams, best third-placed teams, venues or kickoff times are asserted.",
        ],
    }


def build_third_place_rules() -> dict:
    return {
        "tournament": "FIFA World Cup 2026",
        "data_status": "worldcup_2026_third_place_rules_v1",
        "total_groups": 12,
        "third_place_candidates": 12,
        "best_third_place_qualifiers": 8,
        "ranking_criteria_order": [
            "points",
            "goal_difference",
            "goals_for",
            "fair_play_points / disciplinary record",
            "fifa_ranking_or_lot_drawing depending official rule availability",
        ],
        "source_status": "pending_official_rules_verification",
        "implementation_status": "scaffold",
        "third_place_combination_matrix_status": "manual_snapshot_required",
        "warning": (
            "Exact official tie-break implementation must be verified against FIFA competition "
            "regulations before operational use."
        ),
    }


def write_default_bracket_files() -> dict:
    structure = build_knockout_structure()
    slots = build_bracket_slots()
    third_place_rules = build_third_place_rules()
    _write_json_if_changed(KNOCKOUT_STRUCTURE_PATH, structure)
    _write_json_if_changed(BRACKET_SLOTS_PATH, slots)
    _write_json_if_changed(THIRD_PLACE_RULES_PATH, third_place_rules)
    return {
        "knockout_structure_path": str(KNOCKOUT_STRUCTURE_PATH),
        "bracket_slots_path": str(BRACKET_SLOTS_PATH),
        "third_place_rules_path": str(THIRD_PLACE_RULES_PATH),
        "total_knockout_matches": structure["total_knockout_matches"],
        "total_slots": slots["total_slots"],
        "third_place_combination_matrix_status": third_place_rules[
            "third_place_combination_matrix_status"
        ],
    }
