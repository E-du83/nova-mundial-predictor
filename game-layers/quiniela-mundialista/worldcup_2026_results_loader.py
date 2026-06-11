from __future__ import annotations

import json
from pathlib import Path


LAYER_ROOT = Path(__file__).resolve().parent
DATA_ROOT = LAYER_ROOT / "data"
RESULTS_TEMPLATE_PATH = DATA_ROOT / "worldcup_2026_results_template.json"
GROUPS = tuple("ABCDEFGHIJKL")
SLOTS_PER_GROUP = 6
PENDING = "pending_result"


def _write_json_if_changed(path: Path, data: dict) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_results_template() -> dict:
    matches = []
    for group in GROUPS:
        for slot in range(1, SLOTS_PER_GROUP + 1):
            matches.append(
                {
                    "match_id": f"WG-{group}-{slot:02d}",
                    "phase": "group_stage",
                    "group": group,
                    "team_a": "pending_official_fixture",
                    "team_b": "pending_official_fixture",
                    "goals_a_90": PENDING,
                    "goals_b_90": PENDING,
                    "winner_90": PENDING,
                    "btts": PENDING,
                    "first_goal_team": PENDING,
                    "first_goal_minute": PENDING,
                    "source": "pending_official_source",
                    "source_status": "pending_manual_input",
                    "captured_at": "pending_manual_input",
                    "review_status": "pending",
                }
            )
    return {
        "dataset_name": "worldcup_2026_results_template",
        "tournament": "FIFA World Cup 2026",
        "source_status": "template_pending_manual_input",
        "captured_at": "pending_manual_input",
        "matches": matches,
    }


def ensure_results_template(path: str | Path = RESULTS_TEMPLATE_PATH) -> dict:
    data_path = Path(path)
    if not data_path.exists():
        template = build_results_template()
        _write_json_if_changed(data_path, template)
        return template
    return load_worldcup_2026_results(data_path)


def load_worldcup_2026_results(path=RESULTS_TEMPLATE_PATH) -> dict:
    data_path = Path(path)
    if not data_path.exists():
        return {
            "dataset_name": "worldcup_2026_results_missing",
            "source_status": "manual_snapshot_required",
            "captured_at": "pending_manual_input",
            "matches": [],
        }
    return json.loads(data_path.read_text(encoding="utf-8"))


def _is_pending(value) -> bool:
    return value in (
        None,
        "",
        PENDING,
        "pending_official_fixture",
        "pending_manual_input",
        "pending_official_source",
    ) or str(value).startswith("pending_")


def _is_final(match: dict) -> bool:
    return match.get("review_status") in ("final", "reviewed") or match.get("status") == "final"


def _is_number(value) -> bool:
    return isinstance(value, int) or (isinstance(value, str) and value.isdigit())


def validate_worldcup_2026_results(results: dict) -> dict:
    errors = []
    warnings = []
    final_results = 0
    pending_results = 0
    for index, match in enumerate(results.get("matches", []), start=1):
        match_id = match.get("match_id")
        if not match_id:
            errors.append(f"row {index} missing match_id")
        final = _is_final(match)
        if final:
            final_results += 1
            if _is_pending(match.get("team_a")) or _is_pending(match.get("team_b")):
                errors.append(f"{match_id} has final result without real teams")
            if not _is_number(match.get("goals_a_90")) or not _is_number(match.get("goals_b_90")):
                errors.append(f"{match_id} final result requires numeric goals")
            if _is_pending(match.get("source_status")):
                errors.append(f"{match_id} missing source_status")
            if _is_pending(match.get("captured_at")):
                errors.append(f"{match_id} missing captured_at")
        else:
            pending_results += 1
    validation_status = "invalid" if errors else ("ready" if final_results else "pending_results")
    return {
        "validation_status": validation_status,
        "matches_total": len(results.get("matches", [])),
        "final_results": final_results,
        "pending_results": pending_results,
        "results_complete": final_results == 72 and not errors,
        "errors": errors,
        "warnings": warnings,
        "source_status": results.get("source_status", "missing"),
    }
