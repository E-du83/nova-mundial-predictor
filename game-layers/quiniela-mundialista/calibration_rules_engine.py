from __future__ import annotations

from scoring_rules import parse_score, result_key


SMALL_SAMPLE_WARNING = (
    "Sample size is very small. Do not recalibrate aggressively from only three friendlies."
)


def minute_value(value) -> int | None:
    """Convert minutes like 75 or '90+2' into comparable match minutes."""
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if not isinstance(value, str):
        return None
    text = value.strip().replace("'", "")
    if "+" in text:
        base, added = text.split("+", maxsplit=1)
        if base.strip().isdigit() and added.strip().isdigit():
            return int(base.strip()) + int(added.strip())
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else None


def _score_result(score: str) -> str:
    goals_a, goals_b = parse_score(score)
    return result_key(goals_a, goals_b)


def _is_clean_sheet_pick(score: str) -> bool:
    goals_a, goals_b = parse_score(score)
    return (goals_a > goals_b and goals_b == 0) or (goals_b > goals_a and goals_a == 0)


def _favorite_won_by_one(predicted_score: str, real_score: str) -> bool:
    predicted_goals_a, predicted_goals_b = parse_score(predicted_score)
    real_goals_a, real_goals_b = parse_score(real_score)
    predicted_key = result_key(predicted_goals_a, predicted_goals_b)
    real_key = result_key(real_goals_a, real_goals_b)
    return predicted_key == real_key and abs(real_goals_a - real_goals_b) == 1


def _opponent_late_goal(review: dict) -> bool:
    predicted_score = review["predicted_score"]
    predicted_goals_a, predicted_goals_b = parse_score(predicted_score)
    if predicted_goals_a > predicted_goals_b:
        opponent = review["team_b"]
    elif predicted_goals_b > predicted_goals_a:
        opponent = review["team_a"]
    else:
        return False

    goals = review.get("goals", {})
    if not isinstance(goals, dict):
        return False
    for goal in goals.get(opponent, []):
        minute = minute_value(goal.get("minute"))
        if minute is not None and minute > 75:
            return True
    return False


def _first_goal_outside_range(review: dict) -> bool:
    if not review.get("quinigol_team_hit"):
        return False
    first_goal = review.get("quinigol_real_first_goal_minute")
    if not isinstance(first_goal, int):
        return False
    probable_range = str(review.get("quinigol_range", ""))
    if "-" not in probable_range:
        return False
    left, right = probable_range.split("-", maxsplit=1)
    if not left.strip().isdigit() or not right.strip().isdigit():
        return False
    return first_goal < int(left.strip()) or first_goal > int(right.strip())


def _confidence_bucket(confidence) -> str:
    if not isinstance(confidence, (int, float)):
        return "unknown"
    if confidence < 45:
        return "low_medium"
    if confidence < 55:
        return "medium"
    return "high"


def compare_standard_final(match_reviews: list[dict]) -> dict:
    by_mode = {review.get("mode"): review for review in match_reviews}
    standard = by_mode.get("standard")
    final = by_mode.get("final")
    if not standard or not final:
        return {
            "available": False,
            "final_improved": "not_available",
            "winner": "not_available",
        }

    standard_error = standard["goal_diff_error"] + standard["total_goals_error"]
    final_error = final["goal_diff_error"] + final["total_goals_error"]
    if final_error < standard_error:
        winner = "final"
    elif standard_error < final_error:
        winner = "standard"
    else:
        winner = "tie"
    return {
        "available": True,
        "standard_error": standard_error,
        "final_error": final_error,
        "final_improved": final_error < standard_error,
        "winner": winner,
    }


def evaluate_calibration_rules(review: dict, mode_comparison: dict | None = None) -> dict:
    predicted_score = review["predicted_score"]
    real_score = review["real_score"]
    real_key = _score_result(real_score)
    critical = review.get("critical_alternative", "none")
    critical_is_draw = critical != "none" and _score_result(critical) == "draw"
    close_draw = bool(review.get("critical_alternative_helped") and critical_is_draw)
    confidence_bucket = _confidence_bucket(review.get("confidence"))
    fragile = review.get("pick_robustness") in ("fragil", "cauteloso")

    draw_underestimation = bool(
        review.get("match_type") == "international_friendly"
        and confidence_bucket in ("low_medium", "medium")
        and close_draw
        and real_key == "draw"
    )
    late_opponent_goal = bool(
        _favorite_won_by_one(predicted_score, real_score)
        and _is_clean_sheet_pick(predicted_score)
        and _opponent_late_goal(review)
    )
    quinigol_timing = _first_goal_outside_range(review)
    fragility_validated = bool(fragile and not review.get("exact_score_hit"))

    return {
        "draw_underestimation_pattern": draw_underestimation,
        "late_opponent_goal_pattern": late_opponent_goal,
        "quinigol_timing_miscalibration": quinigol_timing,
        "fragility_warning_validated": fragility_validated,
        "clean_sheet_risk_warning": bool(
            review.get("match_type") == "international_friendly"
            and _is_clean_sheet_pick(predicted_score)
            and fragile
            and review.get("missing_critical_data")
        ),
        "final_mode_validation": mode_comparison or {
            "available": False,
            "final_improved": "not_available",
            "winner": "not_available",
        },
    }


def summarize_detected_patterns(match_reviews: list[dict]) -> dict:
    pattern_keys = [
        "draw_underestimation_pattern",
        "late_opponent_goal_pattern",
        "quinigol_timing_miscalibration",
        "fragility_warning_validated",
        "clean_sheet_risk_warning",
    ]
    summary = {key: 0 for key in pattern_keys}
    for review in match_reviews:
        patterns = review.get("patterns", {})
        for key in pattern_keys:
            if patterns.get(key):
                summary[key] += 1
    summary["sample_size_warning"] = SMALL_SAMPLE_WARNING
    return summary


def build_calibration_notes(match_reviews: list[dict]) -> dict:
    patterns = summarize_detected_patterns(match_reviews)
    final_modes = [
        review["patterns"]["final_mode_validation"]
        for review in match_reviews
        if review.get("mode") == "final"
        and review.get("patterns", {}).get("final_mode_validation", {}).get("available")
    ]
    return {
        "data_status": "friendly_calibration_notes_v1",
        "notes": "Evaluative calibration notes only. No automatic training or pick mutation.",
        "draw_underestimation_pattern": patterns["draw_underestimation_pattern"],
        "late_opponent_goal_pattern": patterns["late_opponent_goal_pattern"],
        "quinigol_timing_miscalibration": patterns["quinigol_timing_miscalibration"],
        "clean_sheet_risk_warning": patterns["clean_sheet_risk_warning"],
        "fragility_warning_validated": patterns["fragility_warning_validated"],
        "final_mode_validation": final_modes,
        "sample_size_warning": SMALL_SAMPLE_WARNING,
        "recommended_use": (
            "Use as audit evidence for future backtesting. Do not recalibrate aggressively "
            "from this sample."
        ),
    }
