from __future__ import annotations

import json
from pathlib import Path
from statistics import median

from scoring_rules import parse_score
from worldcup_2022_dataset_loader import QUINIGOL_TIMING_REPORT_PATH


def _parse_range(value) -> tuple[int, int] | None:
    if not value or value == "not_available":
        return None
    text = str(value).replace("min", "").strip()
    if "-" not in text:
        return None
    left, right = text.split("-", maxsplit=1)
    left_digits = "".join(ch for ch in left if ch.isdigit())
    right_digits = "".join(ch for ch in right if ch.isdigit())
    if not left_digits or not right_digits:
        return None
    return int(left_digits), int(right_digits)


def _recommendation(errors: list[int], team_hit_rate, total: int) -> str:
    if total < 12:
        return "needs_more_sample"
    if team_hit_rate != "not_available" and team_hit_rate >= 0.65 and errors and sum(errors) / len(errors) > 20:
        return "team_selection_stronger_than_timing"
    early = sum(1 for error in errors if error < 0)
    late = sum(1 for error in errors if error > 0)
    if early > late * 1.5:
        return "timing_tends_early"
    if late > early * 1.5:
        return "timing_tends_late"
    return "monitor"


def build_quinigol_timing_report(
    prediction_results: list[dict],
    output_path: str | Path = QUINIGOL_TIMING_REPORT_PATH,
    write_report: bool = True,
) -> dict:
    total = len(prediction_results)
    with_first_goal = []
    no_goal_policy_cases = 0
    no_goal_policy_hit = 0
    team_hits = 0
    team_misses = 0
    signed_errors = []
    abs_errors = []
    within_range = 0

    for item in prediction_results:
        real_score = item.get("real_score")
        predicted_team = item.get("predicted_quinigol_team")
        if real_score:
            goals_a, goals_b = parse_score(real_score)
            if goals_a == 0 and goals_b == 0 and predicted_team == "No hay":
                no_goal_policy_cases += 1
                no_goal_policy_hit += 1
                continue
        first_team = item.get("first_goal_team")
        first_minute = item.get("first_goal_minute")
        predicted_minute = item.get("predicted_quinigol_minute")
        if first_team in (None, "not_available") or first_minute in (None, "not_available"):
            continue
        with_first_goal.append(item)
        if predicted_team == first_team:
            team_hits += 1
        else:
            team_misses += 1
        if isinstance(predicted_minute, int):
            signed_error = predicted_minute - int(first_minute)
            signed_errors.append(signed_error)
            abs_errors.append(abs(signed_error))
            parsed_range = _parse_range(item.get("predicted_quinigol_range"))
            if parsed_range and parsed_range[0] <= int(first_minute) <= parsed_range[1]:
                within_range += 1

    team_hit_rate = (
        round(team_hits / len(with_first_goal), 4)
        if with_first_goal
        else "not_available"
    )
    report = {
        "total_matches": total,
        "matches_with_first_goal_data": len(with_first_goal),
        "no_goal_policy_cases": no_goal_policy_cases,
        "no_goal_policy_hit": no_goal_policy_hit,
        "quinigol_team_hit": team_hits,
        "quinigol_team_miss": team_misses,
        "quinigol_team_hit_rate": team_hit_rate,
        "minute_errors": abs_errors,
        "average_minute_error": round(sum(abs_errors) / len(abs_errors), 2) if abs_errors else "not_available",
        "median_minute_error": median(abs_errors) if abs_errors else "not_available",
        "early_bias_count": sum(1 for error in signed_errors if error < 0),
        "late_bias_count": sum(1 for error in signed_errors if error > 0),
        "within_range_count": within_range,
        "range_hit_rate": round(within_range / len(with_first_goal), 4) if with_first_goal else "not_available",
        "too_early_average": (
            round(sum(abs(error) for error in signed_errors if error < 0) / max(1, sum(1 for error in signed_errors if error < 0)), 2)
            if signed_errors
            else "not_available"
        ),
        "too_late_average": (
            round(sum(error for error in signed_errors if error > 0) / max(1, sum(1 for error in signed_errors if error > 0)), 2)
            if signed_errors
            else "not_available"
        ),
        "recommendation": _recommendation(signed_errors, team_hit_rate, total),
        "warning": "Sample size too small; do not recalibrate." if total < 30 else "No automatic recalibration.",
        "no_automatic_recalibration": True,
    }
    if write_report:
        Path(output_path).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report
