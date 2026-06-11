from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from group_stage_runner import run_group_stage
from simulation_config import resolve_simulation_mode
from worldcup_2026_fixture_guard import evaluate_group_stage_simulation_readiness


LAYER_ROOT = Path(__file__).resolve().parent
DATA_ROOT = LAYER_ROOT / "data"
PICKS_REPORT_PATH = DATA_ROOT / "worldcup_2026_group_stage_picks_report.json"
PICKS_SUMMARY_CSV_PATH = DATA_ROOT / "worldcup_2026_group_stage_picks_summary.csv"
PICKS_GUARD_REPORT_PATH = DATA_ROOT / "worldcup_2026_group_stage_picks_guard_report.json"

CSV_COLUMNS = [
    "match_id",
    "group",
    "matchday",
    "team_a",
    "team_b",
    "kickoff_utc",
    "venue",
    "pick_principal",
    "predicted_score",
    "critical_alternative",
    "quinigol_team",
    "quinigol_minute",
    "halftime_fulltime",
    "confidence",
    "risk",
    "robustness",
    "data_quality_score",
    "notes",
]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_json_if_changed(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        comparable_existing = dict(existing)
        comparable_data = dict(data)
        comparable_existing.pop("generated_at", None)
        comparable_data.pop("generated_at", None)
        if comparable_existing == comparable_data:
            return
    path.write_text(text, encoding="utf-8")


def _write_csv(path: Path, picks: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [{column: pick.get(column, "") for column in CSV_COLUMNS} for pick in picks]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _empty_groups() -> dict:
    return {group: {"picks_generated": 0, "matches": []} for group in "ABCDEFGHIJKL"}


def _split_match_label(label: str) -> tuple[str, str]:
    if " vs " not in str(label):
        return "pending_group_draw", "pending_group_draw"
    left, right = str(label).split(" vs ", maxsplit=1)
    return left, right


def _pick_from_group_result(item: dict) -> dict:
    team_a, team_b = _split_match_label(item.get("match", "pending_group_draw vs pending_group_draw"))
    decision = item.get("decision_weighting", {})
    recommended_use = decision.get("recommended_use", {}) if isinstance(decision, dict) else {}
    return {
        "match_id": item.get("match_id", "pending_verification"),
        "group": item.get("group", "pending_verification"),
        "matchday": item.get("matchday", "pending_verification"),
        "team_a": team_a,
        "team_b": team_b,
        "kickoff_utc": item.get("kickoff_utc", "pending_official_fixture"),
        "venue": item.get("venue", "pending_official_fixture"),
        "pick_principal": item.get("pick_principal", "pending_real_data"),
        "predicted_score": item.get("marcador", "pending_real_data"),
        "critical_alternative": item.get("alternativa_critica", "pending_real_data"),
        "tempting_option": item.get("opcion_tentadora", "pending_real_data"),
        "quinigol_team": item.get("quinigol", "pending_real_data"),
        "quinigol_minute": item.get("reference_minute", "pending_real_data"),
        "quinigol_range": item.get("quinigol_range", "pending_real_data"),
        "quinigol_policy_applied": item.get("quinigol_policy_applied", "not_available"),
        "halftime_fulltime": item.get("halftime_fulltime", "pending_real_data"),
        "confidence": item.get("confidence", "pending_real_data"),
        "risk": item.get("risk", "pending_real_data"),
        "robustness": item.get("robustez", "pending_real_data"),
        "tactical_input_bridge_status": item.get("tactical_input_bridge_status", "not_available"),
        "lineup_adjustment_applied": item.get("lineup_adjustment_applied", False),
        "tactical_adjustment_applied": item.get("tactical_adjustment_applied", False),
        "form_adjustment_applied": item.get("form_adjustment_applied", False),
        "data_quality_score": item.get("data_quality_score", "pending_real_data"),
        "missing_critical_data": item.get("datos_faltantes", []),
        "quiniela_recommendation": recommended_use.get("quiniela", "pending_real_data"),
        "betting_note": recommended_use.get("apuesta_prepartido", "pending_real_data"),
        "notes": item.get("pending_reason", "none"),
    }


def _group_summary(picks: list[dict]) -> dict:
    groups = _empty_groups()
    for pick in picks:
        group = pick.get("group", "pending_verification")
        groups.setdefault(group, {"picks_generated": 0, "matches": []})
        groups[group]["picks_generated"] += 1
        groups[group]["matches"].append(pick.get("match_id"))
    return groups


def _blocked_result(mode: str, guard: dict, warnings: list[str], report_paths: dict) -> dict:
    confirmed = guard.get("confirmed_matches", 0)
    pending = guard.get("pending_matches", 72)
    return {
        "runner_status": "blocked",
        "mode": mode,
        "guard_status": guard.get("guard_status", "missing"),
        "ready_for_full_group_simulation": guard.get("ready_for_full_group_simulation", False),
        "ready_for_partial_simulation": guard.get("ready_for_partial_simulation", False),
        "total_group_stage_slots": confirmed + pending,
        "confirmed_matches": confirmed,
        "pending_matches": pending,
        "simulated_matches": 0,
        "blocked_matches": confirmed + pending,
        "block_reasons": guard.get("block_reason", []),
        "warnings": warnings,
        "picks": [],
        "summary": {
            "groups": _empty_groups(),
            "picks_generated": 0,
            "prediction_history_updated": False,
            "prediction_history_status": "not_updated_runner_blocked",
        },
        "report_paths": report_paths,
    }


def _report_payload(result: dict) -> dict:
    return {
        "data_status": "worldcup_2026_group_stage_picks_v1",
        "runner_status": result["runner_status"],
        "generated_at": _now(),
        "mode": result["mode"],
        "guard_status": result["guard_status"],
        "total_slots": result["total_group_stage_slots"],
        "confirmed_matches": result["confirmed_matches"],
        "pending_matches": result["pending_matches"],
        "simulated_matches": result["simulated_matches"],
        "blocked_matches": result["blocked_matches"],
        "ready_for_full_group_simulation": result["ready_for_full_group_simulation"],
        "ready_for_partial_simulation": result["ready_for_partial_simulation"],
        "picks": result["picks"],
        "groups": result["summary"].get("groups", {}),
        "warnings": result["warnings"],
        "block_reasons": result["block_reasons"],
        "next_steps": [
            "Load verified official World Cup 2026 group-stage fixture snapshot.",
            "Run fixture importer in dry_run, then import real fixture only after validation passes.",
            "Run this full picks runner only after fixture guard returns ready.",
        ],
    }


def _write_outputs(result: dict, guard: dict) -> None:
    _write_json_if_changed(PICKS_REPORT_PATH, _report_payload(result))
    guard_payload = {
        "generated_at": _now(),
        "guard_status": guard.get("guard_status", "missing"),
        "block_reasons": guard.get("block_reason", []),
        "warnings": guard.get("warnings", []),
        "ready_for_full_group_simulation": guard.get("ready_for_full_group_simulation", False),
        "ready_for_partial_simulation": guard.get("ready_for_partial_simulation", False),
        "confirmed_matches": guard.get("confirmed_matches", 0),
        "pending_matches": guard.get("pending_matches", 72),
    }
    _write_json_if_changed(PICKS_GUARD_REPORT_PATH, guard_payload)
    _write_csv(PICKS_SUMMARY_CSV_PATH, result["picks"])


def run_full_group_stage_picks(
    mode: str = "standard",
    write_report: bool = False,
    allow_partial: bool = False,
    force: bool = False,
) -> dict:
    simulation_mode, _ = resolve_simulation_mode(mode)
    guard = evaluate_group_stage_simulation_readiness()
    report_paths = {
        "json": str(PICKS_REPORT_PATH),
        "csv": str(PICKS_SUMMARY_CSV_PATH),
        "guard": str(PICKS_GUARD_REPORT_PATH),
    }
    warnings = list(guard.get("warnings", []))
    if force:
        warnings.append("force=true only allows report rewriting; it does not bypass Fixture Guard.")

    guard_status = guard.get("guard_status", "missing")
    if guard_status != "ready":
        if guard_status == "partial_ready" and allow_partial:
            runner_status = "partial_ready"
        else:
            result = _blocked_result(simulation_mode, guard, warnings, report_paths)
            if guard_status == "partial_ready" and not allow_partial:
                result["block_reasons"] = sorted(
                    set(result["block_reasons"] + ["partial fixture requires allow_partial=True"])
                )
            if write_report:
                _write_outputs(result, guard)
            return result
    else:
        runner_status = "completed"

    stage_result = run_group_stage(mode=simulation_mode)
    simulated = [item for item in stage_result.get("matches", []) if item.get("simulation_status") == "simulated"]
    picks = [_pick_from_group_result(item) for item in simulated]
    groups = _group_summary(picks)
    result = {
        "runner_status": runner_status,
        "mode": simulation_mode,
        "guard_status": guard_status,
        "ready_for_full_group_simulation": guard.get("ready_for_full_group_simulation", False),
        "ready_for_partial_simulation": guard.get("ready_for_partial_simulation", False),
        "total_group_stage_slots": guard.get("confirmed_matches", 0) + guard.get("pending_matches", 0),
        "confirmed_matches": guard.get("confirmed_matches", 0),
        "pending_matches": guard.get("pending_matches", 0),
        "simulated_matches": len(picks),
        "blocked_matches": max(0, guard.get("confirmed_matches", 0) + guard.get("pending_matches", 0) - len(picks)),
        "block_reasons": [],
        "warnings": warnings + stage_result.get("warnings", []),
        "picks": picks,
        "summary": {
            "groups": groups,
            "picks_generated": len(picks),
            "prediction_history_updated": False,
            "prediction_history_status": "not_updated_by_runner_v1",
        },
        "report_paths": report_paths,
    }
    if write_report:
        _write_outputs(result, guard)
    return result
