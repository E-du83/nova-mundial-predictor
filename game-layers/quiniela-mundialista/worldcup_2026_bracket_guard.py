from __future__ import annotations

import json
from pathlib import Path

from worldcup_2026_bracket_structure import (
    BRACKET_SLOTS_PATH,
    THIRD_PLACE_RULES_PATH,
    write_default_bracket_files,
)
from worldcup_2026_third_place_selector import rank_third_placed_teams


LAYER_ROOT = Path(__file__).resolve().parent
DATA_ROOT = LAYER_ROOT / "data"
BRACKET_GUARD_REPORT_PATH = DATA_ROOT / "worldcup_2026_bracket_guard_report.json"
DEFAULT_GROUP_STANDINGS_PATH = DATA_ROOT / "worldcup_2026_group_standings_final.json"


def _load_json(path: str | Path | None) -> dict:
    if isinstance(path, dict):
        return path
    if path is None:
        return {}
    data_path = Path(path)
    if not data_path.exists():
        return {}
    return json.loads(data_path.read_text(encoding="utf-8"))


def _write_json_if_changed(path: Path, data: dict) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _is_pending(value) -> bool:
    return value in {
        None,
        "",
        "pending_group_results",
        "pending_real_data",
        "pending_official_fixture",
        "pending_group_draw",
        "manual_snapshot_required",
    } or str(value).startswith("pending_")


def _standings_rows(group_standings: dict) -> list[dict]:
    if not group_standings:
        return []
    if isinstance(group_standings.get("groups"), dict):
        rows = []
        for group, table in group_standings["groups"].items():
            for item in table:
                row = dict(item)
                row.setdefault("group", group)
                rows.append(row)
        return rows
    if isinstance(group_standings.get("standings"), list):
        return list(group_standings["standings"])
    return []


def _validate_group_standings(group_standings: dict) -> tuple[list[str], list[str], list[dict]]:
    blocked = []
    warnings = []
    rows = _standings_rows(group_standings)
    if not rows:
        return ["final group standings missing"], warnings, []
    groups = sorted({row.get("group") for row in rows})
    if len(groups) != 12:
        blocked.append(f"expected 12 groups, found {len(groups)}")
    third_place_rows = []
    for group in groups:
        group_rows = [row for row in rows if row.get("group") == group]
        if len(group_rows) != 4:
            blocked.append(f"group {group} expected 4 teams, found {len(group_rows)}")
            continue
        positions = sorted(row.get("position") for row in group_rows)
        if positions != [1, 2, 3, 4]:
            blocked.append(f"group {group} positions must be 1,2,3,4")
        for row in group_rows:
            if _is_pending(row.get("team")):
                blocked.append(f"group {group} has pending team")
            if row.get("position") == 3:
                third_place_rows.append(row)
    if len(third_place_rows) != 12:
        blocked.append(f"expected 12 third-place teams, found {len(third_place_rows)}")
    return blocked, warnings, third_place_rows


def _bracket_slots_status(bracket_slots: dict) -> str:
    slots = bracket_slots.get("slots", [])
    if not bracket_slots:
        return "missing"
    if len(slots) != 32:
        return "partial"
    required_rounds = {
        "round_of_32": 16,
        "round_of_16": 8,
        "quarter_finals": 4,
        "semi_finals": 2,
        "third_place": 1,
        "final": 1,
    }
    for round_name, count in required_rounds.items():
        if sum(1 for slot in slots if slot.get("round") == round_name) != count:
            return "partial"
    return "OK"


def evaluate_bracket_readiness(
    group_standings_path=None,
    bracket_slots_path=None,
    third_place_rules_path=None,
) -> dict:
    write_default_bracket_files()
    group_standings = _load_json(group_standings_path or DEFAULT_GROUP_STANDINGS_PATH)
    bracket_slots = _load_json(bracket_slots_path or BRACKET_SLOTS_PATH)
    third_place_rules = _load_json(third_place_rules_path or THIRD_PLACE_RULES_PATH)
    blocked_reasons, warnings, third_place_rows = _validate_group_standings(group_standings)
    slots_status = _bracket_slots_status(bracket_slots)
    if slots_status != "OK":
        blocked_reasons.append(f"bracket slots status is {slots_status}")
    matrix_status = third_place_rules.get("third_place_combination_matrix_status", "missing")
    if matrix_status != "verified_official_snapshot":
        warnings.append("Third-place combination matrix is pending official manual snapshot.")
    selector = rank_third_placed_teams(third_place_rows) if third_place_rows else {
        "selector_status": "blocked",
        "qualified_third_placed": [],
        "blocked_reason": ["third-place rows missing"],
        "warnings": [],
        "unresolved_tiebreaks": [],
    }
    if selector["selector_status"] != "ready":
        blocked_reasons.extend(selector.get("blocked_reason", []))
    if matrix_status != "verified_official_snapshot" and not blocked_reasons:
        guard_status = "blocked_third_place_rules"
    elif blocked_reasons:
        guard_status = "blocked_pending_group_results"
    else:
        guard_status = "ready_for_bracket_build"
    if slots_status == "OK" and guard_status != "ready_for_bracket_build" and group_standings:
        guard_status = "partial"
    report = {
        "bracket_guard_status": guard_status,
        "ready_for_knockout_projection": guard_status == "ready_for_bracket_build",
        "ready_for_knockout_picks": False,
        "blocked_reasons": sorted(set(blocked_reasons)),
        "warnings": sorted(set(warnings + selector.get("warnings", []))),
        "qualified_teams_count": 24 + len(selector.get("qualified_third_placed", []))
        if selector.get("selector_status") == "ready"
        else 0,
        "third_place_status": selector.get("selector_status", "blocked"),
        "third_place_matrix_status": matrix_status,
        "bracket_slots_status": slots_status,
        "selector_summary": {
            "qualified_third_placed_count": len(selector.get("qualified_third_placed", [])),
            "unresolved_tiebreaks": selector.get("unresolved_tiebreaks", []),
        },
    }
    _write_json_if_changed(BRACKET_GUARD_REPORT_PATH, report)
    return report
