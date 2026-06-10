from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from data_leakage_guard import audit_prematch_dataset
from quinigol_timing_calibration_engine import build_quinigol_timing_report
from quiniela_engine import recommend_match
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


def _profile_for(profiles: dict, team: str) -> dict:
    return profiles.get("teams", {}).get(team, {})


def _profile_is_behavioral(profile: dict) -> bool:
    if not profile.get("valid_for_behavioral_backtest"):
        return False
    for field in ("attack", "defense", "form"):
        if not isinstance(profile.get(field), (int, float)):
            return False
    return isinstance(profile.get("elo"), (int, float))


def _profile_quality(profile_a: dict, profile_b: dict) -> str:
    qualities = {profile_a.get("data_quality"), profile_b.get("data_quality")}
    if "low" in qualities:
        return "low"
    if "medium" in qualities:
        return "medium"
    if "high" in qualities:
        return "high"
    return "unknown"


def _temporary_team(profile: dict) -> dict:
    return {
        "elo": float(profile.get("elo", 1500.0)),
        "nova_strength_rating_v1": float(profile.get("elo", 1500.0)),
        "world_football_elo": profile.get("elo_pre_tournament", "pending_verification"),
        "attack": float(profile["attack"]),
        "defense": float(profile["defense"]),
        "form": float(profile["form"]),
        "tactical_attack_adjustment": float(profile.get("tactical_attack_adjustment", 1.0)),
        "tactical_defense_adjustment": float(profile.get("tactical_defense_adjustment", 1.0)),
        "data_quality": {
            "status": profile.get("data_quality", "low"),
            "source_status": profile.get("source_status", "manual_snapshot_required"),
            "uses_neutral_defaults": profile.get("uses_neutral_defaults", False),
        },
        "style_notes": "World Cup 2022 prematch behavioral profile; not a 2026 baseline record.",
    }


def _range_hit(range_text, minute) -> bool | str:
    if minute in (None, "not_available") or not range_text:
        return "not_available"
    text = str(range_text).replace("min", "")
    if "-" not in text:
        return "not_available"
    left, right = text.split("-", maxsplit=1)
    left_digits = "".join(ch for ch in left if ch.isdigit())
    right_digits = "".join(ch for ch in right if ch.isdigit())
    if not left_digits or not right_digits:
        return "not_available"
    return int(left_digits) <= int(minute) <= int(right_digits)


def _real_score(result: dict) -> str:
    return f"{result['goals_a_90']}-{result['goals_b_90']}"


def _evaluate_recommendation(match: dict, result: dict, recommendation: dict, profile_a: dict, profile_b: dict) -> dict:
    predicted_score = recommendation["quiniela"]["recommended_score"]
    pred_a, pred_b = parse_score(predicted_score)
    real_score = _real_score(result)
    real_a, real_b = parse_score(real_score)
    predicted_result = result_key(pred_a, pred_b)
    real_result = result_key(real_a, real_b)
    quinigol = recommendation["quinigol"]
    predicted_quinigol_team = quinigol.get("team")
    predicted_quinigol_minute = quinigol.get("minute")
    predicted_quinigol_range = quinigol.get("minute_range")
    first_goal_team = result.get("first_goal_team")
    first_goal_minute = result.get("first_goal_minute")
    minute_error = (
        abs(int(predicted_quinigol_minute) - int(first_goal_minute))
        if isinstance(predicted_quinigol_minute, int) and isinstance(first_goal_minute, int)
        else "not_available"
    )
    signed_error = (
        int(predicted_quinigol_minute) - int(first_goal_minute)
        if isinstance(predicted_quinigol_minute, int) and isinstance(first_goal_minute, int)
        else None
    )
    used_neutral = bool(profile_a.get("uses_neutral_defaults") or profile_b.get("uses_neutral_defaults"))

    return {
        "match_id": match["match_id"],
        "match": f"{match['team_a']} vs {match['team_b']}",
        "phase": match.get("phase"),
        "generated_after_event": True,
        "behavioral_backtest_prediction": True,
        "not_valid_for_true_prediction_accuracy": True,
        "not_valid_for_model_accuracy_claims": True,
        "profile_quality": _profile_quality(profile_a, profile_b),
        "used_neutral_defaults": used_neutral,
        "predicted_score": predicted_score,
        "real_score": real_score,
        "result_hit": predicted_result == real_result,
        "exact_score_hit": predicted_score == real_score,
        "draw_hit": predicted_result == "draw" and real_result == "draw",
        "btts_predicted": pred_a > 0 and pred_b > 0,
        "btts_real": result.get("btts"),
        "btts_hit": (pred_a > 0 and pred_b > 0) == result.get("btts"),
        "goal_diff_error": abs((pred_a - pred_b) - result.get("goal_diff_90", real_a - real_b)),
        "total_goals_error": abs((pred_a + pred_b) - result.get("total_goals_90", real_a + real_b)),
        "clean_sheet_predicted": pred_a == 0 or pred_b == 0,
        "clean_sheet_real": real_a == 0 or real_b == 0,
        "clean_sheet_hit": (pred_a == 0 or pred_b == 0) == (real_a == 0 or real_b == 0),
        "favorite_fragility": recommendation["quiniela"].get("risk", "not_available"),
        "upset_risk": "not_available_neutral_defaults" if used_neutral else "pending",
        "upset_real": "not_available",
        "predicted_quinigol_team": predicted_quinigol_team,
        "predicted_quinigol_minute": predicted_quinigol_minute,
        "predicted_quinigol_range": predicted_quinigol_range,
        "quinigol_team_hit": predicted_quinigol_team == first_goal_team,
        "quinigol_minute_error": minute_error,
        "quinigol_range_hit": _range_hit(predicted_quinigol_range, first_goal_minute),
        "first_goal_team": first_goal_team,
        "first_goal_minute": first_goal_minute,
        "first_goal_team_hit": predicted_quinigol_team == first_goal_team,
        "first_goal_minute_error": minute_error,
        "quinigol_minute_bias": (
            "early" if signed_error is not None and signed_error < 0
            else "late" if signed_error is not None and signed_error > 0
            else "exact" if signed_error == 0
            else "not_available"
        ),
        "halftime_fulltime_hit": "not_available",
        "confidence_bucket": recommendation["quiniela"].get("confidence", "not_available"),
        "robustness_bucket": recommendation["quiniela"].get("risk", "not_available"),
        "notes": (
            "Generated after event with World Cup 2022 prematch profile defaults; "
            "validates pipeline behavior, not predictive strength."
        ),
    }


def _rate(evaluations: list[dict], field: str):
    if not evaluations:
        return "not_available"
    return round(sum(1 for item in evaluations if item.get(field) is True) / len(evaluations), 4)


def _average(evaluations: list[dict], field: str):
    values = [item[field] for item in evaluations if isinstance(item.get(field), (int, float))]
    return round(sum(values) / len(values), 4) if values else "not_available"


def _phase_counts(matches: list[dict], results: dict[str, dict], evaluations: list[dict]) -> dict:
    breakdown = {}
    for phase in PHASES:
        phase_matches = [match for match in matches if match.get("phase") == phase]
        phase_evaluations = [item for item in evaluations if item.get("phase") == phase]
        breakdown[phase] = {
            "prematch_count": len(phase_matches),
            "results_count": sum(1 for match in phase_matches if match.get("match_id") in results),
            "evaluated_count": len(phase_evaluations),
            "result_hit_rate": _rate(phase_evaluations, "result_hit"),
            "exact_score_hit_rate": _rate(phase_evaluations, "exact_score_hit"),
            "status": "evaluated_behavioral" if phase_evaluations else "structural_only",
        }
    return breakdown


def build_worldcup_2022_blind_test_report(write_report: bool = True) -> dict:
    audit = audit_prematch_dataset(PREMATCH_PATH, AUDIT_PATH, write_report=True)
    datasets = load_worldcup_2022_datasets()
    prematch = datasets.get("prematch", {})
    results_data = datasets.get("results", {})
    config = datasets.get("config", {})
    profiles = datasets.get("profiles", {})
    matches = prematch.get("matches", [])
    results = {
        item["match_id"]: item
        for item in results_data.get("results", [])
        if item.get("match_id")
    }

    blocked = set(audit.get("blocked_matches", []))
    evaluations = []
    missing_profiles = []
    neutral_default_evaluations = 0

    if audit.get("critical_leakage_count", 0) == 0:
        for index, match in enumerate(matches):
            match_id = match.get("match_id")
            if match_id in blocked or match_id not in results:
                continue
            profile_a = _profile_for(profiles, match["team_a"])
            profile_b = _profile_for(profiles, match["team_b"])
            if not (_profile_is_behavioral(profile_a) and _profile_is_behavioral(profile_b)):
                missing_profiles.append(match_id)
                continue
            teams = {
                match["team_a"]: _temporary_team(profile_a),
                match["team_b"]: _temporary_team(profile_b),
            }
            recommendation = recommend_match(
                match["team_a"],
                match["team_b"],
                teams,
                strategy="balanceado",
                simulations=10_000,
                seed=2022 + index,
                simulation_mode="quick",
                use_tactical_bridge=False,
            )
            evaluated = _evaluate_recommendation(match, results[match_id], recommendation, profile_a, profile_b)
            evaluations.append(evaluated)
            if evaluated["used_neutral_defaults"]:
                neutral_default_evaluations += 1

    if audit.get("critical_leakage_count", 0) > 0 and config.get("block_if_critical_leakage", True):
        engine_status = "blocked_by_critical_leakage"
    elif evaluations:
        engine_status = "evaluated_behavioral_backtest"
    else:
        engine_status = "foundation_partial_insufficient_historical_profiles"

    timing_report = build_quinigol_timing_report(evaluations, write_report=True)
    warnings = list(datasets.get("warnings", []))
    if missing_profiles:
        warnings.append("Some 2022 team profiles are insufficient; 2026 baseline was not used.")
    if neutral_default_evaluations:
        warnings.append("These results validate pipeline behavior, not predictive strength.")
    if config.get("generated_after_event"):
        warnings.append("generated_after_event=true; metrics are not valid for true historical prediction accuracy.")
    if timing_report["total_matches"] < 30:
        warnings.append("Quinigol timing sample too small; do not recalibrate.")

    structural_ready_count = len(matches) - len(blocked) - len(missing_profiles)
    phase_breakdown = _phase_counts(matches, results, evaluations)
    report = {
        "generated_at": _now(),
        "tournament": config.get("tournament", "FIFA World Cup"),
        "year": config.get("year", 2022),
        "test_mode": config.get("mode", "behavioral_backtest"),
        "generated_after_event": config.get("generated_after_event", True),
        "not_valid_for_true_prediction_accuracy": config.get("not_valid_for_true_prediction_accuracy", True),
        "valid_for_behavioral_backtest": config.get("valid_for_behavioral_backtest", True),
        "not_valid_for_model_accuracy_claims": neutral_default_evaluations > 0,
        "engine_status": engine_status,
        "total_matches_in_prematch": datasets.get("prematch_count", 0),
        "total_results_loaded": datasets.get("results_count", 0),
        "profiles_count": datasets.get("profiles_count", 0),
        "profiles_ready_count": datasets.get("profiles_ready_count", 0),
        "profiles_using_neutral_defaults": datasets.get("profiles_using_neutral_defaults", 0),
        "profiles_blocked": datasets.get("profiles_blocked", 0),
        "matches_evaluated": len(evaluations),
        "matches_evaluable_with_neutral_defaults": neutral_default_evaluations,
        "matches_blocked_by_leakage": len(blocked),
        "matches_missing_historical_profiles": len(missing_profiles),
        "blocked_match_ids": sorted(blocked),
        "missing_historical_profile_match_ids": missing_profiles,
        "true_prediction_metrics": {
            "status": "not_valid_generated_after_event",
            "matches_evaluated": 0,
            "reason": "Predictions generated after the tournament cannot prove historical predictive accuracy.",
        },
        "behavioral_backtest_metrics": {
            "status": engine_status,
            "matches_evaluated": len(evaluations),
            "result_hit_rate": _rate(evaluations, "result_hit"),
            "exact_score_hit_rate": _rate(evaluations, "exact_score_hit"),
            "btts_hit_rate": _rate(evaluations, "btts_hit"),
            "clean_sheet_hit_rate": _rate(evaluations, "clean_sheet_hit"),
            "average_goal_diff_error": _average(evaluations, "goal_diff_error"),
            "average_total_goals_error": _average(evaluations, "total_goals_error"),
        },
        "structural_flow_metrics": {
            "datasets_ready": datasets.get("datasets_ready", False),
            "prematch_count": datasets.get("prematch_count", 0),
            "results_count": datasets.get("results_count", 0),
            "matched_pairs_count": datasets.get("matched_pairs_count", 0),
            "structural_ready_count": structural_ready_count,
            "profiles_valid_for_behavioral_backtest": datasets.get("profiles_valid_for_behavioral_backtest", 0),
            "profiles_valid_for_true_prediction_accuracy": datasets.get("profiles_valid_for_true_prediction_accuracy", 0),
            "neutral_default_evaluations": neutral_default_evaluations,
            "missing_results": datasets.get("missing_results", []),
            "missing_prematch": datasets.get("missing_prematch", []),
            "historical_profiles_status": "ready_for_behavioral_with_neutral_defaults"
            if evaluations
            else "insufficient",
        },
        "structural_readiness_metrics": {
            "datasets_ready": datasets.get("datasets_ready", False),
            "prematch_count": datasets.get("prematch_count", 0),
            "results_count": datasets.get("results_count", 0),
            "matched_pairs_count": datasets.get("matched_pairs_count", 0),
            "structural_ready_count": structural_ready_count,
            "missing_results": datasets.get("missing_results", []),
            "missing_prematch": datasets.get("missing_prematch", []),
            "historical_profiles_status": "ready_for_behavioral_with_neutral_defaults"
            if evaluations
            else "insufficient",
        },
        "phase_breakdown": phase_breakdown,
        "group_stage_breakdown": phase_breakdown["group_stage"],
        "knockout_breakdown": {
            phase: phase_breakdown[phase]
            for phase in ("round_of_16", "quarter_final", "semi_final", "third_place", "final")
        },
        "upset_analysis": {"status": "neutral_defaults_behavioral_only", "matches_evaluated": len(evaluations)},
        "favorite_fragility_analysis": {"status": "neutral_defaults_behavioral_only", "matches_evaluated": len(evaluations)},
        "btts_analysis": {"matches_evaluated": len(evaluations), "btts_hit_rate": _rate(evaluations, "btts_hit")},
        "clean_sheet_analysis": {
            "matches_evaluated": len(evaluations),
            "clean_sheet_hit_rate": _rate(evaluations, "clean_sheet_hit"),
        },
        "quinigol_timing_analysis": timing_report,
        "exact_score_analysis": {
            "matches_evaluated": len(evaluations),
            "exact_score_hit_rate": _rate(evaluations, "exact_score_hit"),
        },
        "profile_quality_warning": (
            "Neutral defaults are low-quality profiles for structural behavioral testing only."
            if neutral_default_evaluations
            else "not_available"
        ),
        "leakage_audit_summary": {
            "audit_status": audit.get("audit_status"),
            "cleared_for_blind_test": audit.get("cleared_for_blind_test"),
            "critical_leakage_count": audit.get("critical_leakage_count"),
            "medium_leakage_count": audit.get("medium_leakage_count"),
            "low_leakage_count": audit.get("low_leakage_count"),
        },
        "profile_audit_summary": datasets.get("profile_audit", {}),
        "per_match_evaluations": evaluations,
        "warnings": warnings,
        "recommendations": [
            "Replace neutral defaults with verified 2022 Elo/FIFA/form/team-strength profiles before accuracy claims.",
            "Keep results separated from prematch data and rerun leakage guard after every dataset edit.",
            "Use Quinigol timing findings as monitoring only until sample size is larger.",
        ],
        "do_not_change_yet": [
            "No recalibrar Core todavia.",
            "No declarar precision predictiva real.",
            "No usar datos 2026 para 2022.",
            "No mezclar resultados en prematch.",
            "No recalibrar Quinigol desde muestra pequena o defaults neutrales.",
        ],
        "next_steps": [
            "Verify 2022 FIFA rank, Elo and form snapshots with cutoff per match.",
            "Add historical lineups/odds only if their prematch timestamp is auditable.",
            "Expand beyond 8 matches only after profile-source audit is stronger.",
        ],
    }
    if write_report:
        REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report
