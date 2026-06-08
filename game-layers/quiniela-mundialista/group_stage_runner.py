from __future__ import annotations

import json
from pathlib import Path

from critical_alternative_engine import build_critical_alternatives
from decision_weighting_engine import build_decision_weighting
from final_pick_engine import build_final_pick, load_default_final_pick_inputs
from half_time_engine import build_half_time_pick
from match_alarm_engine import build_match_alarm
from pick_robustness_engine import build_pick_robustness
from research_refresh_engine import build_research_refresh
from research_weighting_engine import build_research_weighting
from simulation_config import resolve_simulation_mode


PENDING_VALUES = {
    "",
    None,
    "pending_real_data",
    "manual_snapshot_required",
    "pending_manual_input",
    "not_available_free",
}

LAYER_ROOT = Path(__file__).resolve().parent
FIXTURE_PATH = LAYER_ROOT / "data" / "group_stage_fixture_context.json"
CALIBRATION_NOTES_PATH = LAYER_ROOT / "data" / "calibration_notes.json"


def _load_json(path: str | Path) -> dict:
    data_path = Path(path)
    if not data_path.exists():
        return {
            "data_status": "manual_snapshot_required",
            "matches": [],
            "message": f"{data_path} not found.",
        }
    return json.loads(data_path.read_text(encoding="utf-8"))


def load_group_stage_fixtures(path: str | Path = FIXTURE_PATH) -> dict:
    return _load_json(path)


def _is_pending(value) -> bool:
    return value in PENDING_VALUES or str(value).startswith("pending_")


def _pending_match(match: dict, reason: str, missing_data: list[str]) -> dict:
    return {
        "match_id": match.get("match_id", "manual_snapshot_required"),
        "group": match.get("group", "pending_real_data"),
        "match": f"{match.get('team_a', 'pending_real_data')} vs {match.get('team_b', 'pending_real_data')}",
        "data_status": "pending",
        "simulation_status": "not_run",
        "pending_reason": reason,
        "pick_principal": "pending_real_data",
        "marcador": "pending_real_data",
        "alternativa_critica": "pending_real_data",
        "opcion_tentadora": "pending_real_data",
        "quinigol": "pending_real_data",
        "quinigol_range": "pending_real_data",
        "reference_minute": "pending_real_data",
        "halftime_fulltime": "pending_real_data",
        "confidence": "pending_real_data",
        "risk": "pending_real_data",
        "robustez": "pending_real_data",
        "tactical_score": "pending_real_data",
        "research_refresh_required": "pending_real_data",
        "datos_faltantes": missing_data,
    }


def _match_missing_data(match: dict, teams: dict) -> list[str]:
    missing = []
    for field in ("team_a", "team_b", "venue", "date", "kickoff_time_utc"):
        if _is_pending(match.get(field)):
            missing.append(field)
    for field in ("team_a", "team_b"):
        team = match.get(field)
        if not _is_pending(team) and team not in teams:
            missing.append(f"baseline team missing: {team}")
    return missing


def _snapshot_for_fixture(match: dict) -> dict:
    return {
        "match": f"{match['team_a']} vs {match['team_b']}",
        "team_a": match["team_a"],
        "team_b": match["team_b"],
        "venue": match.get("venue", "pending_real_data"),
        "kickoff_time_utc": match.get("kickoff_time_utc", "pending_real_data"),
        "source_status": match.get("source_status", "manual_snapshot_required"),
        "data_status": match.get("data_status", "manual_snapshot_required"),
    }


def _simulate_match(match: dict, teams: dict, mode: str, simulations: int) -> dict:
    final_pick = build_final_pick(
        match["team_a"],
        match["team_b"],
        teams,
        fixtures_data=None,
        climate_profiles=None,
        simulations=simulations,
        simulation_mode=mode,
        seed=2026,
    )
    research_refresh = build_research_refresh(
        match["team_a"],
        match["team_b"],
        snapshots_data={"snapshots": [_snapshot_for_fixture(match)]},
        results_data={"results": []},
    )
    robustness = build_pick_robustness(
        final_pick,
        adjusted_confidence=final_pick["confidence"],
        friendly_risk=final_pick["risk"],
        match_type="world_cup_group_stage",
        missing_critical_fields=research_refresh["missing_critical_fields"],
        calibration_notes_path=CALIBRATION_NOTES_PATH,
    )
    recommendation = {
        "match": f"{match['team_a']} vs {match['team_b']}",
        "match_type": "world_cup_group_stage",
        "final_recommendation": final_pick["final_quiniela_recommendation"],
        "recommended_score": final_pick["final_score"],
        "quinigol": final_pick["final_quinigol"],
        "quinigol_range": final_pick["quinigol_range"],
        "reference_minute": final_pick["reference_minute"],
        "adjusted_confidence": final_pick["confidence"],
        "friendly_risk": final_pick["risk"],
        "simulation_mode": mode,
        "simulations_used": simulations,
        "research_refresh": research_refresh,
        "match_alarm": build_match_alarm(_snapshot_for_fixture(match)),
        "half_time": build_half_time_pick(final_pick, "world_cup_group_stage"),
        "robustness": robustness,
        "research_weighting": build_research_weighting(match["team_a"], match["team_b"]),
        "data_used": final_pick["data_used"] + ["group_stage_fixture_context.json"],
        "missing_data": sorted(set(final_pick["missing_data"] + research_refresh["missing_critical_fields"])),
        "raw_final_pick": final_pick,
    }
    recommendation["critical_alternatives"] = build_critical_alternatives(recommendation)
    recommendation["decision_weighting"] = build_decision_weighting(recommendation)

    alternatives = recommendation["critical_alternatives"]
    tactical = recommendation["research_weighting"]["tactical_weighting"]
    return {
        "match_id": match.get("match_id"),
        "group": match.get("group"),
        "match": recommendation["match"],
        "data_status": "simulated_with_available_baseline",
        "simulation_status": "simulated",
        "pick_principal": alternatives["principal_pick"]["score"],
        "marcador": recommendation["recommended_score"],
        "alternativa_critica": alternatives["critical_alternative"]["score"]
        if alternatives["critical_alternative"]
        else "none",
        "opcion_tentadora": alternatives["tempting_option"]["score"]
        if alternatives["tempting_option"]
        else "none",
        "quinigol": recommendation["quinigol"],
        "quinigol_range": recommendation["quinigol_range"],
        "reference_minute": recommendation["reference_minute"],
        "halftime_fulltime": recommendation["half_time"]["half_time_full_time"],
        "confidence": recommendation["adjusted_confidence"],
        "risk": recommendation["friendly_risk"],
        "robustez": robustness["pick_robustness"],
        "tactical_score": tactical["tactical_score"],
        "research_refresh_required": research_refresh["research_refresh_required"],
        "datos_faltantes": recommendation["missing_data"],
        "decision_weighting": recommendation["decision_weighting"],
        "data_quality_score": recommendation["research_weighting"]["data_quality_score"],
    }


def run_group_stage(mode: str = "quick", fixture_path: str | Path = FIXTURE_PATH) -> dict:
    teams, _, _ = load_default_final_pick_inputs()
    fixture_data = load_group_stage_fixtures(fixture_path)
    simulation_mode, simulations = resolve_simulation_mode(mode)
    results = []
    for match in fixture_data.get("matches", []):
        missing = _match_missing_data(match, teams)
        if missing:
            results.append(_pending_match(match, "insufficient_fixture_or_baseline_data", missing))
            continue
        results.append(_simulate_match(match, teams, simulation_mode, simulations))

    return {
        "data_status": fixture_data.get("data_status", "manual_snapshot_required"),
        "simulation_mode": simulation_mode,
        "simulations": simulations,
        "total_matches": len(results),
        "simulable_matches": sum(1 for item in results if item["simulation_status"] == "simulated"),
        "pending_matches": sum(1 for item in results if item["simulation_status"] != "simulated"),
        "fixture_warning": (
            "fixture incomplete; official group-stage matchups are not loaded"
            if fixture_data.get("data_status") != "ready_snapshot"
            else "none"
        ),
        "matches": results,
    }
