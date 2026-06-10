from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from calibration_rules_engine import (
    SMALL_SAMPLE_WARNING,
    build_calibration_notes,
    compare_standard_final,
    evaluate_calibration_rules,
    minute_value,
    summarize_detected_patterns,
)
from prediction_history_engine import load_prediction_history
from result_review_engine import load_friendly_results
from scoring_rules import parse_score, result_key, result_label


PENDING = "pending_real_result"


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _without_generated_at(data: dict) -> dict:
    comparable = dict(data)
    comparable.pop("generated_at", None)
    return comparable


def _write_json_if_relevant_changed(path: str | Path, data: dict) -> dict:
    output_path = Path(path)
    if output_path.exists():
        existing = json.loads(output_path.read_text(encoding="utf-8"))
        if _without_generated_at(existing) == _without_generated_at(data):
            return existing
    output_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return data


def _match_key(match: str) -> str:
    return str(match).strip().lower()


def _safe_bool(value) -> bool | str:
    return value if isinstance(value, bool) else PENDING


def _score_error(predicted_score: str, real_score: str) -> int:
    pred_a, pred_b = parse_score(predicted_score)
    real_a, real_b = parse_score(real_score)
    return abs(pred_a - real_a) + abs(pred_b - real_b)


def _btts(score: str) -> bool:
    goals_a, goals_b = parse_score(score)
    return goals_a > 0 and goals_b > 0


def _pick_robustness(entry: dict) -> str:
    if entry.get("pick_robustness"):
        return entry["pick_robustness"]
    confidence = entry.get("confidence")
    if entry.get("data_quality_score", 100) < 25:
        return "fragil"
    if isinstance(confidence, (int, float)) and confidence < 45:
        return "cauteloso"
    return "medio"


def _missing_critical(entry: dict) -> list[str]:
    refresh = entry.get("research_refresh_status", {})
    fields = refresh.get("missing_critical_fields", [])
    if isinstance(fields, list) and fields:
        return fields
    missing = entry.get("datos_faltantes", [])
    if not isinstance(missing, list):
        return []
    critical_names = {
        "odds_1x2",
        "over_under",
        "probable_lineups",
        "formations",
        "player_ratings_key_players",
        "lineups",
    }
    return [item for item in missing if item in critical_names]


def _team_from_quinigol(quinigol: str, team_a: str, team_b: str) -> str:
    text = str(quinigol)
    if team_a in text:
        return team_a
    if team_b in text:
        return team_b
    if "No hay" in text:
        return "No hay"
    return PENDING


def _first_goal_minute(goals: dict, team: str) -> int | str:
    if not isinstance(goals, dict) or team not in goals:
        return PENDING
    minutes = [
        minute_value(goal.get("minute"))
        for goal in goals.get(team, [])
        if isinstance(goal, dict)
    ]
    values = [minute for minute in minutes if minute is not None]
    return min(values) if values else PENDING


def _halftime_fulltime_hit(entry: dict) -> bool | str:
    value = entry.get("acierto_descanso_final", PENDING)
    return value if isinstance(value, bool) else PENDING


def _alternative_result(score: str, predicted_score: str, real_score: str) -> dict:
    if not score or score == "none":
        return {
            "available": False,
            "score": "none",
            "exact_score_hit": False,
            "reduced_error": False,
        }
    alt_error = _score_error(score, real_score)
    pred_error = _score_error(predicted_score, real_score)
    return {
        "available": True,
        "score": score,
        "exact_score_hit": score == real_score,
        "result_hit": result_key(*parse_score(score)) == result_key(*parse_score(real_score)),
        "reduced_error": alt_error < pred_error,
        "goal_error": alt_error,
    }


def _review_from_entry(entry: dict, result: dict) -> dict:
    match = result["match"]
    team_a = result["team_a"]
    team_b = result["team_b"]
    predicted_score = entry.get("marcador_recomendado") or entry.get("pick_principal")
    real_score = result["real_score"]
    pred_a, pred_b = parse_score(predicted_score)
    real_a, real_b = parse_score(real_score)
    predicted_key = result_key(pred_a, pred_b)
    real_key = result_key(real_a, real_b)
    critical = entry.get("alternativa_critica", "none")
    tempting = entry.get("opcion_tentadora", "none")
    critical_result = _alternative_result(critical, predicted_score, real_score)
    tempting_result = _alternative_result(tempting, predicted_score, real_score)
    quinigol_team = _team_from_quinigol(entry.get("quinigol", ""), team_a, team_b)
    real_first_goal = _first_goal_minute(result.get("goals", {}), quinigol_team)
    predicted_minute = minute_value(entry.get("minuto_referencia"))
    minute_error = (
        abs(predicted_minute - real_first_goal)
        if isinstance(predicted_minute, int) and isinstance(real_first_goal, int)
        else entry.get("error_minuto_quinigol", PENDING)
    )

    review = {
        "match": match,
        "team_a": team_a,
        "team_b": team_b,
        "match_type": "international_friendly",
        "pre_match_prediction": entry.get("prediction_previous", PENDING),
        "predicted_score": predicted_score,
        "real_score": real_score,
        "predicted_result": result_label(predicted_score, team_a, team_b),
        "real_result": result.get("real_result", result_label(real_score, team_a, team_b)),
        "mode": entry.get("simulation_mode", entry.get("mode", PENDING)),
        "simulations": entry.get("simulations_used", entry.get("simulations", PENDING)),
        "pick_principal": entry.get("pick_principal", predicted_score),
        "critical_alternative": critical,
        "tempting_option": tempting,
        "quinigol": entry.get("quinigol", PENDING),
        "quinigol_range": entry.get("rango_probable", PENDING),
        "halftime_fulltime": entry.get("descanso_final", PENDING),
        "tactical_score": entry.get("tactical_score", PENDING),
        "research_refresh_status": entry.get("research_refresh_status", {}),
        "model_fragility": entry.get("model_fragility", _pick_robustness(entry)),
        "pick_robustness": _pick_robustness(entry),
        "data_quality_score": entry.get("data_quality_score", PENDING),
        "confidence": entry.get("confidence", PENDING),
        "risk": entry.get("risk", PENDING),
        "missing_critical_data": _missing_critical(entry),
        "result_hit": predicted_key == real_key,
        "exact_score_hit": predicted_score == real_score,
        "goal_diff_error": abs((pred_a - pred_b) - (real_a - real_b)),
        "total_goals_error": abs((pred_a + pred_b) - (real_a + real_b)),
        "btts_predicted": _btts(predicted_score),
        "btts_real": _btts(real_score),
        "btts_hit": _btts(predicted_score) == _btts(real_score),
        "quinigol_team_hit": _safe_bool(entry.get("acierto_quinigol_equipo")),
        "quinigol_minute_error": minute_error,
        "quinigol_real_first_goal_minute": real_first_goal,
        "halftime_fulltime_hit": _halftime_fulltime_hit(entry),
        "critical_alternative_helped": bool(
            critical_result["available"]
            and (critical_result["exact_score_hit"] or critical_result["reduced_error"])
        ),
        "critical_alternative_result": critical_result,
        "tempting_option_result": tempting_result,
        "goals": result.get("goals", {}),
        "red_cards": result.get("red_cards", {}),
        "learning_note": result.get("learning_note", entry.get("learning_note", PENDING)),
        "review_status": "reviewed",
        "history_signature": entry.get("signature", PENDING),
    }
    review["patterns"] = evaluate_calibration_rules(review)
    return review


def _entries_by_match(history: dict) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for entry in history.get("entries", []):
        grouped.setdefault(_match_key(entry.get("match", "")), []).append(entry)
    return grouped


def _best_entry(entries: list[dict]) -> dict | None:
    if not entries:
        return None
    priorities = [
        lambda item: item.get("history_status") == "reviewed" and item.get("simulation_mode") == "final",
        lambda item: item.get("simulation_mode") == "final",
        lambda item: item.get("history_status") == "reviewed",
    ]
    for predicate in priorities:
        matches = [entry for entry in entries if predicate(entry)]
        if matches:
            return matches[-1]
    return entries[-1]


def _mode_reviews(entries: list[dict], result: dict) -> list[dict]:
    reviews = []
    seen_modes = set()
    for entry in reversed(entries):
        mode = entry.get("simulation_mode", entry.get("mode", PENDING))
        if mode in seen_modes:
            continue
        if not entry.get("marcador_recomendado"):
            continue
        reviews.append(_review_from_entry(entry, result))
        seen_modes.add(mode)
    return list(reversed(reviews))


def build_friendly_calibration(
    results_path: str | Path,
    history_path: str | Path,
) -> dict:
    results = load_friendly_results(results_path)
    history = load_prediction_history(history_path)
    entries = _entries_by_match(history)
    matches_reviewed = []
    mode_review_groups: dict[str, list[dict]] = {}

    for result in results.get("results", []):
        if result.get("status") != "final":
            continue
        match_entries = entries.get(_match_key(result.get("match", "")), [])
        selected = _best_entry(match_entries)
        if not selected:
            continue
        mode_reviews = _mode_reviews(match_entries, result)
        mode_review_groups[result["match"]] = mode_reviews
        review = _review_from_entry(selected, result)
        review["patterns"] = evaluate_calibration_rules(
            review,
            compare_standard_final(mode_reviews),
        )
        matches_reviewed.append(review)

    metrics = _build_metrics(matches_reviewed)
    patterns = summarize_detected_patterns(matches_reviewed)
    recommended_adjustments = _recommended_adjustments(patterns)
    report = {
        "data_status": "friendly_results_calibration_v1",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "matches_reviewed": matches_reviewed,
        "metrics": metrics,
        "patterns": patterns,
        "recommended_adjustments": recommended_adjustments,
        "do_not_change_yet": [
            "No automatic training.",
            "No aggressive recalibration from only three friendlies.",
            "Do not mutate Core probabilities or baseline data from this sample.",
            "Do not auto-change clean sheet picks; warnings only.",
        ],
        "next_steps": [
            "Data Completion + Backtesting Foundation v1",
            "Collect more finalized matches before changing model weights.",
            "Track late opponent goals, draw alternatives and Quinigol timing over a larger sample.",
        ],
        "sample_size_warning": SMALL_SAMPLE_WARNING,
        "mode_review_groups": mode_review_groups,
    }
    return report


def _rate(items: list[dict], key: str) -> float:
    valid = [item for item in items if isinstance(item.get(key), bool)]
    if not valid:
        return 0.0
    return round(sum(1 for item in valid if item[key]) / len(valid), 4)


def _average(items: list[int | float]) -> float:
    return round(sum(items) / len(items), 4) if items else 0.0


def _build_metrics(matches: list[dict]) -> dict:
    return {
        "total_matches_reviewed": len(matches),
        "result_hit_rate": _rate(matches, "result_hit"),
        "exact_score_hit_rate": _rate(matches, "exact_score_hit"),
        "btts_hit_rate": _rate(matches, "btts_hit"),
        "quinigol_team_hit_rate": _rate(matches, "quinigol_team_hit"),
        "average_goal_diff_error": _average([item["goal_diff_error"] for item in matches]),
        "average_total_goals_error": _average([item["total_goals_error"] for item in matches]),
        "fragile_pick_count": sum(
            1 for item in matches if item.get("pick_robustness") in ("fragil", "cauteloso")
        ),
        "critical_alternative_was_relevant_count": sum(
            1 for item in matches if item.get("critical_alternative_helped")
        ),
        "late_goal_error_count": sum(
            1 for item in matches if item.get("patterns", {}).get("late_opponent_goal_pattern")
        ),
        "draw_underestimation_count": sum(
            1 for item in matches if item.get("patterns", {}).get("draw_underestimation_pattern")
        ),
    }


def _recommended_adjustments(patterns: dict) -> list[str]:
    adjustments = []
    if patterns.get("draw_underestimation_pattern"):
        adjustments.append(
            "When a friendly has low/medium confidence and a near draw alternative, surface draw risk more clearly."
        )
    if patterns.get("late_opponent_goal_pattern"):
        adjustments.append(
            "Add clean-sheet caution for fragile friendly favorites when missing lineups, formations or market data."
        )
    if patterns.get("quinigol_timing_miscalibration"):
        adjustments.append(
            "Track Quinigol timing separately; current team selection is stronger than minute precision."
        )
    if not adjustments:
        adjustments.append("Keep collecting evidence before changing calibration rules.")
    return adjustments


def build_and_save_calibration_outputs(
    results_path: str | Path,
    history_path: str | Path,
    report_path: str | Path,
    notes_path: str | Path,
) -> tuple[dict, dict]:
    report = build_friendly_calibration(results_path, history_path)
    notes = build_calibration_notes(report["matches_reviewed"])
    saved_report = _write_json_if_relevant_changed(report_path, report)
    saved_notes = _write_json_if_relevant_changed(notes_path, notes)
    return saved_report, saved_notes
