from __future__ import annotations

import json
from pathlib import Path


LAYER_ROOT = Path(__file__).resolve().parent
WORLDCUP_2022_ROOT = LAYER_ROOT / "historical_blind_tests" / "worldcup_2022"
PREMATCH_PATH = WORLDCUP_2022_ROOT / "worldcup_2022_prematch_dataset.json"
RESULTS_PATH = WORLDCUP_2022_ROOT / "worldcup_2022_results_dataset.json"
CONFIG_PATH = WORLDCUP_2022_ROOT / "worldcup_2022_blind_test_config.json"
AUDIT_PATH = WORLDCUP_2022_ROOT / "worldcup_2022_data_leakage_audit.json"
REPORT_PATH = WORLDCUP_2022_ROOT / "worldcup_2022_blind_test_report.json"

VALID_PHASES = {
    "group_stage",
    "round_of_16",
    "quarter_final",
    "semi_final",
    "third_place",
    "final",
}

RESULT_ONLY_FIELDS = {
    "goals_a_90",
    "goals_b_90",
    "goals_a_final",
    "goals_b_final",
    "winner_90",
    "winner_final",
    "first_goal_team",
    "first_goal_minute",
    "goals_timeline",
    "real_score",
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _duplicates(values: list[str]) -> list[str]:
    seen = set()
    duplicated = set()
    for value in values:
        if value in seen:
            duplicated.add(value)
        seen.add(value)
    return sorted(duplicated)


def _validate_prematch(prematch: dict, config: dict) -> list[str]:
    warnings = []
    allowed_phases = set(config.get("allowed_phases") or VALID_PHASES)
    match_ids = []
    for index, match in enumerate(prematch.get("matches", [])):
        match_id = match.get("match_id")
        if not match_id:
            warnings.append(f"prematch[{index}]: missing match_id")
        else:
            match_ids.append(match_id)
        if not match.get("team_a") or not match.get("team_b"):
            warnings.append(f"{match_id or index}: missing team_a/team_b")
        if match.get("phase") not in allowed_phases:
            warnings.append(f"{match_id or index}: invalid phase {match.get('phase')}")
        if "cutoff_datetime" not in match:
            warnings.append(f"{match_id or index}: missing cutoff_datetime")
        if "source_status" not in match:
            warnings.append(f"{match_id or index}: missing source_status")
        leaked_fields = sorted(field for field in RESULT_ONLY_FIELDS if field in match)
        if leaked_fields:
            warnings.append(f"{match_id or index}: result fields inside prematch: {', '.join(leaked_fields)}")
    for duplicate in _duplicates(match_ids):
        warnings.append(f"duplicate prematch match_id: {duplicate}")
    return warnings


def _validate_results(results: dict, config: dict) -> list[str]:
    warnings = []
    allowed_phases = set(config.get("allowed_phases") or VALID_PHASES)
    match_ids = []
    for index, result in enumerate(results.get("results", [])):
        match_id = result.get("match_id")
        if not match_id:
            warnings.append(f"results[{index}]: missing match_id")
        else:
            match_ids.append(match_id)
        if not result.get("team_a") or not result.get("team_b"):
            warnings.append(f"{match_id or index}: missing team_a/team_b")
        if result.get("phase") not in allowed_phases:
            warnings.append(f"{match_id or index}: invalid phase {result.get('phase')}")
        if "source_status" not in result:
            warnings.append(f"{match_id or index}: missing source_status")
    for duplicate in _duplicates(match_ids):
        warnings.append(f"duplicate results match_id: {duplicate}")
    return warnings


def load_worldcup_2022_datasets(
    prematch_path: Path = PREMATCH_PATH,
    results_path: Path = RESULTS_PATH,
    config_path: Path = CONFIG_PATH,
    audit_path: Path = AUDIT_PATH,
) -> dict:
    warnings = []
    paths = {
        "prematch": prematch_path,
        "results": results_path,
        "config": config_path,
        "audit": audit_path,
    }
    missing_files = [name for name, path in paths.items() if not path.exists()]
    if missing_files:
        return {
            "datasets_ready": False,
            "prematch": {},
            "results": {},
            "config": {},
            "audit": {},
            "prematch_count": 0,
            "results_count": 0,
            "matched_pairs_count": 0,
            "missing_results": [],
            "missing_prematch": [],
            "warnings": [f"missing file: {name}" for name in missing_files],
        }

    prematch = _load_json(prematch_path)
    results = _load_json(results_path)
    config = _load_json(config_path)
    audit = _load_json(audit_path)
    warnings.extend(_validate_prematch(prematch, config))
    warnings.extend(_validate_results(results, config))

    prematch_ids = {match.get("match_id") for match in prematch.get("matches", []) if match.get("match_id")}
    result_ids = {result.get("match_id") for result in results.get("results", []) if result.get("match_id")}
    missing_results = sorted(prematch_ids - result_ids)
    missing_prematch = sorted(result_ids - prematch_ids)

    return {
        "datasets_ready": not warnings,
        "prematch": prematch,
        "results": results,
        "config": config,
        "audit": audit,
        "prematch_count": len(prematch_ids),
        "results_count": len(result_ids),
        "matched_pairs_count": len(prematch_ids & result_ids),
        "missing_results": missing_results,
        "missing_prematch": missing_prematch,
        "warnings": warnings,
    }
