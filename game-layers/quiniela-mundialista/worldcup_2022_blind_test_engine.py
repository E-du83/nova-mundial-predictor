from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

from data_leakage_guard import audit_prematch_dataset
from scoring_rules import parse_score, result_key
from worldcup_2022_dataset_loader import (
    AUDIT_PATH,
    PREMATCH_PATH,
    REPORT_PATH,
    load_worldcup_2022_datasets,
)


PHASES = ("group_stage", "round_of_16", "quarter_final", "semi_final", "third_place", "final")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _has_historical_profile(match: dict) -> bool:
    profiles = [match.get("team_a_prematch_profile", {}), match.get("team_b_prematch_profile", {})]
    for profile in profiles:
        if profile.get("profile_status") == "insufficient_historical_team_profile":
            return False
        if profile.get("attack") in ("pending_real_data", "pending_verification", None):
            return False
        if profile.get("defense") in ("pending_real_data", "pending_verification", None):
            return False
    return True


def _phase_counts(matches: list[dict], results: dict[str, dict]) -> dict:
    breakdown = {}
    for phase in PHASES:
        phase_matches = [match for match in matches if match.get("phase") == phase]
        breakdown[phase] = {
            "prematch_count": len(phase_matches),
            "results_count": sum(1 for match in phase_matches if match.get("match_id") in results),
            "evaluated_count": 0,
            "status": "structural_only",
        }
    return breakdown


def _empty_rate_summary(status: str) -> dict:
    return {
        "status": status,
        "matches_evaluated": 0,
        "result_hit_rate": "not_available",
        "exact_score_hit_rate": "not_available",
    }


def _quinigol_timing_analysis(evaluations: list[dict]) -> dict:
    with_first_goal = [
        item for item in evaluations
        if item.get("first_goal_minute_error") not in (None, "not_available")
    ]
    errors = [item["first_goal_minute_error"] for item in with_first_goal]
    if not errors:
        return {
            "total_matches_with_first_goal_data": 0,
            "quinigol_team_hit_rate": "not_available",
            "average_minute_error": "not_available",
            "median_minute_error": "not_available",
            "early_bias_count": 0,
            "late_bias_count": 0,
            "range_hit_rate": "not_available",
            "no_goal_policy_cases": 0,
            "first_goal_team_miss_count": 0,
            "recommendation": "Quinigol team selection may be stronger than minute precision.",
            "status": "pending_predictions_or_quinigol_data",
        }
    team_hits = [item for item in with_first_goal if item.get("quinigol_team_hit") is True]
    range_hits = [item for item in with_first_goal if item.get("quinigol_range_hit") is True]
    return {
        "total_matches_with_first_goal_data": len(with_first_goal),
        "quinigol_team_hit_rate": round(len(team_hits) / len(with_first_goal), 4),
        "average_minute_error": round(sum(errors) / len(errors), 2),
        "median_minute_error": median(errors),
        "early_bias_count": sum(1 for item in with_first_goal if item.get("quinigol_minute_bias") == "early"),
        "late_bias_count": sum(1 for item in with_first_goal if item.get("quinigol_minute_bias") == "late"),
        "range_hit_rate": round(len(range_hits) / len(with_first_goal), 4),
        "no_goal_policy_cases": sum(1 for item in evaluations if item.get("no_goal_policy_case")),
        "first_goal_team_miss_count": sum(1 for item in with_first_goal if item.get("first_goal_team_hit") is False),
        "recommendation": "Quinigol team selection may be stronger than minute precision.",
        "status": "evaluated",
    }


def _evaluate_prediction(prediction: dict, result: dict) -> dict:
    predicted_score = prediction.get("predicted_score")
    if not predicted_score:
        return {}
    goals_a, goals_b = parse_score(predicted_score)
    predicted_result = result_key(goals_a, goals_b)
    real_score = f"{result['goals_a_90']}-{result['goals_b_90']}"
    real_a, real_b = parse_score(real_score)
    real_result = result_key(real_a, real_b)
    btts_predicted = goals_a > 0 and goals_b > 0
    clean_sheet_predicted = goals_a == 0 or goals_b == 0
    clean_sheet_real = real_a == 0 or real_b == 0
    return {
        "match_id": result["match_id"],
        "result_hit": predicted_result == real_result,
        "exact_score_hit": predicted_score == real_score,
        "draw_hit": predicted_result == "draw" and real_result == "draw",
        "btts_predicted": btts_predicted,
        "btts_real": result.get("btts"),
        "btts_hit": btts_predicted == result.get("btts"),
        "goal_diff_error": abs((goals_a - goals_b) - result.get("goal_diff_90", real_a - real_b)),
        "total_goals_error": abs((goals_a + goals_b) - result.get("total_goals_90", real_a + real_b)),
        "clean_sheet_predicted": clean_sheet_predicted,
        "clean_sheet_real": clean_sheet_real,
        "clean_sheet_hit": clean_sheet_predicted == clean_sheet_real,
        "favorite_fragility": prediction.get("favorite_fragility", "not_available"),
        "upset_risk": prediction.get("upset_risk", "not_available"),
        "upset_real": "not_available",
        "quinigol_team_hit": "not_available",
        "quinigol_minute_error": "not_available",
        "quinigol_range_hit": "not_available",
        "first_goal_team_hit": "not_available",
        "first_goal_minute_error": "not_available",
        "halftime_fulltime_hit": "not_available",
        "confidence_bucket": prediction.get("confidence_bucket", "not_available"),
        "robustness_bucket": prediction.get("robustness_bucket", "not_available"),
        "notes": "Behavioral metric from existing historical prediction row, if supplied.",
    }


def build_worldcup_2022_blind_test_report(write_report: bool = True) -> dict:
    audit = audit_prematch_dataset(PREMATCH_PATH, AUDIT_PATH, write_report=True)
    datasets = load_worldcup_2022_datasets()
    prematch = datasets.get("prematch", {})
    results_data = datasets.get("results", {})
    config = datasets.get("config", {})
    matches = prematch.get("matches", [])
    results = {
        item["match_id"]: item
        for item in results_data.get("results", [])
        if item.get("match_id")
    }

    blocked = set(audit.get("blocked_matches", []))
    missing_profiles = [
        match["match_id"]
        for match in matches
        if match.get("match_id") not in blocked and not _has_historical_profile(match)
    ]
    historical_predictions = {
        item.get("match_id"): item
        for item in prematch.get("historical_predictions", [])
        if item.get("match_id")
    }
    evaluations = []
    for match in matches:
        match_id = match.get("match_id")
        if match_id in blocked or match_id in missing_profiles:
            continue
        prediction = historical_predictions.get(match_id)
        result = results.get(match_id)
        if prediction and result:
            evaluated = _evaluate_prediction(prediction, result)
            if evaluated:
                evaluations.append(evaluated)

    if audit.get("critical_leakage_count", 0) > 0 and config.get("block_if_critical_leakage", True):
        engine_status = "blocked_by_critical_leakage"
    elif not evaluations:
        engine_status = "foundation_partial_insufficient_historical_profiles"
    else:
        engine_status = "evaluated_behavioral_backtest"

    warnings = list(datasets.get("warnings", []))
    if missing_profiles:
        warnings.append("Historical 2022 team profiles are insufficient; 2026 baseline was not used.")
    if not evaluations:
        warnings.append("No matches evaluated because no valid historical prediction/profile pair is available.")
    if config.get("generated_after_event"):
        warnings.append("generated_after_event=true; metrics are not valid for true historical prediction accuracy.")

    structural_ready_count = len(matches) - len(blocked) - len(missing_profiles)
    phase_breakdown = _phase_counts(matches, results)
    report = {
        "generated_at": _now(),
        "tournament": config.get("tournament", "FIFA World Cup"),
        "year": config.get("year", 2022),
        "test_mode": config.get("mode", "behavioral_backtest"),
        "generated_after_event": config.get("generated_after_event", True),
        "not_valid_for_true_prediction_accuracy": config.get("not_valid_for_true_prediction_accuracy", True),
        "valid_for_behavioral_backtest": config.get("valid_for_behavioral_backtest", True),
        "engine_status": engine_status,
        "total_matches_in_prematch": datasets.get("prematch_count", 0),
        "total_results_loaded": datasets.get("results_count", 0),
        "matches_evaluated": len(evaluations),
        "matches_blocked_by_leakage": len(blocked),
        "matches_missing_historical_profiles": len(missing_profiles),
        "blocked_match_ids": sorted(blocked),
        "missing_historical_profile_match_ids": missing_profiles,
        "true_prediction_metrics": {
            "status": "not_valid_generated_after_event",
            "matches_evaluated": 0,
            "reason": "Predictions generated after the tournament cannot prove historical predictive accuracy.",
        },
        "behavioral_backtest_metrics": _empty_rate_summary(engine_status)
        if not evaluations
        else {
            "status": "evaluated",
            "matches_evaluated": len(evaluations),
            "result_hit_rate": round(sum(1 for item in evaluations if item["result_hit"]) / len(evaluations), 4),
            "exact_score_hit_rate": round(sum(1 for item in evaluations if item["exact_score_hit"]) / len(evaluations), 4),
        },
        "structural_readiness_metrics": {
            "datasets_ready": datasets.get("datasets_ready", False),
            "prematch_count": datasets.get("prematch_count", 0),
            "results_count": datasets.get("results_count", 0),
            "matched_pairs_count": datasets.get("matched_pairs_count", 0),
            "structural_ready_count": structural_ready_count,
            "missing_results": datasets.get("missing_results", []),
            "missing_prematch": datasets.get("missing_prematch", []),
            "historical_profiles_status": "insufficient" if missing_profiles else "ready",
        },
        "phase_breakdown": phase_breakdown,
        "group_stage_breakdown": {
            "prematch_count": phase_breakdown["group_stage"]["prematch_count"],
            "results_count": phase_breakdown["group_stage"]["results_count"],
            "evaluated_count": 0,
        },
        "knockout_breakdown": {
            phase: phase_breakdown[phase]
            for phase in ("round_of_16", "quarter_final", "semi_final", "third_place", "final")
        },
        "upset_analysis": {"status": "pending_predictions", "matches_evaluated": len(evaluations)},
        "favorite_fragility_analysis": {"status": "pending_predictions", "matches_evaluated": len(evaluations)},
        "btts_analysis": {"status": "pending_predictions", "matches_evaluated": len(evaluations)},
        "clean_sheet_analysis": {"status": "pending_predictions", "matches_evaluated": len(evaluations)},
        "quinigol_timing_analysis": _quinigol_timing_analysis(evaluations),
        "exact_score_analysis": {"status": "pending_predictions", "matches_evaluated": len(evaluations)},
        "leakage_audit_summary": {
            "audit_status": audit.get("audit_status"),
            "cleared_for_blind_test": audit.get("cleared_for_blind_test"),
            "critical_leakage_count": audit.get("critical_leakage_count"),
            "medium_leakage_count": audit.get("medium_leakage_count"),
            "low_leakage_count": audit.get("low_leakage_count"),
        },
        "per_match_evaluations": evaluations,
        "warnings": warnings,
        "recommendations": [
            "Load verified 2022 prematch team profiles before running Core-based simulations.",
            "Keep results separated from prematch data and rerun leakage guard after every dataset edit.",
            "Use this report as behavioral_backtest foundation only until true prematch predictions exist.",
        ],
        "do_not_change_yet": [
            "No recalibrar Core todavia.",
            "No declarar precision predictiva real.",
            "No usar datos 2026 para 2022.",
            "No mezclar resultados en prematch.",
            "No ampliar a 2018/2014 hasta validar 2022.",
        ],
        "next_steps": [
            "Verify every partial result row against an official public source manually.",
            "Create verified 2022 prematch team profiles with cutoff dates.",
            "Add historical prediction rows only if their source and timestamp are auditable.",
        ],
    }
    if write_report:
        REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report
