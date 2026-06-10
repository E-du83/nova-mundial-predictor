from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LAYER_ROOT = Path(__file__).resolve().parent
WORLDCUP_2022_ROOT = LAYER_ROOT / "historical_blind_tests" / "worldcup_2022"
DEFAULT_PREMATCH_PATH = WORLDCUP_2022_ROOT / "worldcup_2022_prematch_dataset.json"
DEFAULT_AUDIT_PATH = WORLDCUP_2022_ROOT / "worldcup_2022_data_leakage_audit.json"

RESULT_FIELDS = {
    "goals_a_90",
    "goals_b_90",
    "goals_a_final",
    "goals_b_final",
    "real_score",
    "winner_90",
    "winner_final",
    "first_goal_team",
    "first_goal_minute",
    "goals_timeline",
    "btts",
    "total_goals_90",
    "goal_diff_90",
}

LEAKAGE_PATTERNS = {
    "champion_leakage": ("champion", "campeon", "winner of tournament", "tournament winner"),
    "finalist_leakage": ("finalist", "finalista"),
    "exact_result_leakage": ("real_score", "resultado real", "marcador real", "goals_a_90", "goals_b_90"),
    "future_group_table_leakage": ("final_group", "posiciones finales", "final group positions"),
    "knockout_path_leakage": ("knockout path", "camino real", "future knockout", "semi_final_opponent"),
    "post_tournament_narrative_leakage": ("post_match", "post tournament", "after the match", "narrativa posterior"),
    "surprise_label_based_on_known_outcome": ("surprise", "sorpresa", "upset validated"),
    "future_match_information_leakage": ("future_match", "future match", "desempeno posterior", "later match"),
    "current_year_data_used_for_2022": ("2026", "current_year", "current data"),
    "2026_baseline_used_for_2022": ("worldcup_2026_real_teams_baseline", "baseline 2026", "2026 baseline"),
}

CRITICAL_TYPES = {
    "champion_leakage",
    "finalist_leakage",
    "exact_result_leakage",
    "future_group_table_leakage",
    "knockout_path_leakage",
    "future_match_information_leakage",
    "current_year_data_used_for_2022",
    "2026_baseline_used_for_2022",
    "result_dataset_fields_inside_prematch",
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _text_blob(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(f"{key} {_text_blob(item)}" for key, item in value.items())
    if isinstance(value, list):
        return " ".join(_text_blob(item) for item in value)
    return str(value)


def _result_fields_in_match(match: dict) -> list[str]:
    return sorted(field for field in RESULT_FIELDS if field in match)


def _warning(match_id: str, leakage_type: str, severity: str, detail: str) -> dict:
    return {
        "match_id": match_id,
        "leakage_type": leakage_type,
        "severity": severity,
        "detail": detail,
    }


def audit_prematch_dataset(
    prematch_path: str | Path = DEFAULT_PREMATCH_PATH,
    audit_path: str | Path = DEFAULT_AUDIT_PATH,
    write_report: bool = True,
) -> dict:
    prematch = _load_json(prematch_path)
    matches = prematch.get("matches", [])
    warnings = []
    warnings_by_match: dict[str, list[dict]] = {}

    for index, match in enumerate(matches):
        match_id = match.get("match_id", f"missing_match_id_{index}")
        match_warnings = []
        result_fields = _result_fields_in_match(match)
        if result_fields:
            match_warnings.append(
                _warning(
                    match_id,
                    "result_dataset_fields_inside_prematch",
                    "critical",
                    "Prematch row contains result-only fields: " + ", ".join(result_fields),
                )
            )

        searchable_match = {
            key: value
            for key, value in match.items()
            if key not in ("unavailable_context",)
        }
        searchable = _text_blob(searchable_match).lower()
        for leakage_type, patterns in LEAKAGE_PATTERNS.items():
            for pattern in patterns:
                if pattern in searchable:
                    severity = "critical" if leakage_type in CRITICAL_TYPES else "medium"
                    match_warnings.append(
                        _warning(
                            match_id,
                            leakage_type,
                            severity,
                            f"Found leakage marker '{pattern}' in prematch data.",
                        )
                    )
                    break

        if match_warnings:
            warnings.extend(match_warnings)
            warnings_by_match[match_id] = match_warnings

    critical_count = sum(1 for item in warnings if item["severity"] == "critical")
    medium_count = sum(1 for item in warnings if item["severity"] == "medium")
    low_count = sum(1 for item in warnings if item["severity"] == "low")
    blocked_matches = sorted(
        {
            item["match_id"]
            for item in warnings
            if item["severity"] == "critical"
        }
    )
    audit = {
        "total_matches_checked": len(matches),
        "leakage_warnings": warnings,
        "critical_leakage_count": critical_count,
        "medium_leakage_count": medium_count,
        "low_leakage_count": low_count,
        "cleared_for_blind_test": critical_count == 0,
        "blocked_matches": blocked_matches,
        "warnings_by_match": warnings_by_match,
        "generated_at": _now(),
        "audit_status": "blocked" if critical_count else "cleared",
    }
    if write_report:
        Path(audit_path).write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return audit


if __name__ == "__main__":
    result = audit_prematch_dataset()
    print(f"Data leakage audit: {result['audit_status']}")
