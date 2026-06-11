from __future__ import annotations

import json
from pathlib import Path

from worldcup_2026_fixture_loader import load_worldcup_2026_fixture


LAYER_ROOT = Path(__file__).resolve().parent
STANDINGS_SNAPSHOT_PATH = LAYER_ROOT / "data" / "worldcup_2026_standings_snapshot.json"


def _write_json_if_changed(path: Path, data: dict) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _is_pending(value) -> bool:
    return value in (None, "", "pending_official_fixture", "pending_result") or str(value).startswith("pending_")


def _is_final(match: dict) -> bool:
    return match.get("review_status") in ("final", "reviewed") or match.get("status") == "final"


def _empty_row(team: str) -> dict:
    return {
        "team": team,
        "played": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "goals_for": 0,
        "goals_against": 0,
        "goal_difference": 0,
        "points": 0,
        "btts_count": 0,
        "clean_sheets": 0,
        "source_status": "derived_from_final_results",
        "standings_status": "partial",
    }


def _apply_result(row_a: dict, row_b: dict, goals_a: int, goals_b: int) -> None:
    row_a["played"] += 1
    row_b["played"] += 1
    row_a["goals_for"] += goals_a
    row_a["goals_against"] += goals_b
    row_b["goals_for"] += goals_b
    row_b["goals_against"] += goals_a
    if goals_a and goals_b:
        row_a["btts_count"] += 1
        row_b["btts_count"] += 1
    if goals_b == 0:
        row_a["clean_sheets"] += 1
    if goals_a == 0:
        row_b["clean_sheets"] += 1
    if goals_a > goals_b:
        row_a["wins"] += 1
        row_b["losses"] += 1
        row_a["points"] += 3
    elif goals_b > goals_a:
        row_b["wins"] += 1
        row_a["losses"] += 1
        row_b["points"] += 3
    else:
        row_a["draws"] += 1
        row_b["draws"] += 1
        row_a["points"] += 1
        row_b["points"] += 1


def build_group_standings(results: dict, fixture: dict | None = None, write: bool = False) -> dict:
    fixture_bundle = fixture or load_worldcup_2026_fixture()
    if fixture_bundle.get("structural_placeholder") or fixture_bundle.get("fixture_type") == "structural_placeholder":
        standings = {
            "data_status": "worldcup_2026_standings_snapshot_v1",
            "standings_status": "blocked_placeholder_fixture",
            "groups_calculated": 0,
            "groups": {},
            "warnings": ["Fixture is placeholder; standings cannot be calculated from pending teams."],
        }
        if write:
            _write_json_if_changed(STANDINGS_SNAPSHOT_PATH, standings)
        return standings
    final_matches = [match for match in results.get("matches", []) if _is_final(match)]
    if not final_matches:
        standings = {
            "data_status": "worldcup_2026_standings_snapshot_v1",
            "standings_status": "pending_results",
            "groups_calculated": 0,
            "groups": {},
            "warnings": ["No final results available."],
        }
        if write:
            _write_json_if_changed(STANDINGS_SNAPSHOT_PATH, standings)
        return standings
    groups: dict[str, dict[str, dict]] = {}
    skipped = []
    for match in final_matches:
        team_a = match.get("team_a")
        team_b = match.get("team_b")
        if _is_pending(team_a) or _is_pending(team_b):
            skipped.append(match.get("match_id", "unknown"))
            continue
        try:
            goals_a = int(match["goals_a_90"])
            goals_b = int(match["goals_b_90"])
        except (KeyError, TypeError, ValueError):
            skipped.append(match.get("match_id", "unknown"))
            continue
        group = match.get("group", "pending_group")
        groups.setdefault(group, {})
        groups[group].setdefault(team_a, _empty_row(team_a))
        groups[group].setdefault(team_b, _empty_row(team_b))
        _apply_result(groups[group][team_a], groups[group][team_b], goals_a, goals_b)
    output_groups = {}
    for group, rows_by_team in groups.items():
        rows = []
        for row in rows_by_team.values():
            row["goal_difference"] = row["goals_for"] - row["goals_against"]
            rows.append(row)
        rows.sort(key=lambda item: (item["points"], item["goal_difference"], item["goals_for"]), reverse=True)
        for index, row in enumerate(rows, start=1):
            row["position"] = index
        output_groups[group] = rows
    standings_status = "ready" if len(output_groups) == 12 and not skipped else "partial"
    standings = {
        "data_status": "worldcup_2026_standings_snapshot_v1",
        "standings_status": standings_status,
        "groups_calculated": len(output_groups),
        "groups": output_groups,
        "warnings": ["Official tie-break rules beyond points, goal difference and goals for are not applied."]
        + ([f"Skipped invalid final result slots: {', '.join(skipped)}"] if skipped else []),
    }
    if write:
        _write_json_if_changed(STANDINGS_SNAPSHOT_PATH, standings)
    return standings
