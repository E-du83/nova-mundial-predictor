from __future__ import annotations

import json
from pathlib import Path
from statistics import mean


LAYER_ROOT = Path(__file__).resolve().parent
RULES_PATH = LAYER_ROOT / "data" / "worldcup_2026_group_context_rules.json"

PENDING_VALUES = {
    "",
    None,
    "pending_real_data",
    "manual_snapshot_required",
    "pending_manual_input",
    "not_available_free",
    "pending_official_fixture",
    "pending_group_draw",
    "pending_verification",
}

PLACEHOLDER_WARNING = "Group context blocked because official group draw/fixture is not loaded."


DEFAULT_RULES = {
    "version": "group_context_rules_v1",
    "thresholds": {
        "elite_average_rating": 1880,
        "strong_average_rating": 1760,
        "weak_average_rating": 1520,
        "death_group_top3_spread": 150,
        "death_group_average_rating": 1760,
        "death_group_contender_rating": 1740,
        "balanced_group_spread": 220,
        "clear_favorite_gap": 180,
        "two_favorites_second_to_fourth_gap": 190,
        "unpredictable_group_spread": 120,
        "surprise_candidate_rating_ratio": 0.85,
        "good_form_threshold": 1.04,
        "good_rank_threshold": 45,
    },
    "minimum_data_quality_for_prediction_impact": "medium",
}


def _load_rules() -> dict:
    if not RULES_PATH.exists():
        return DEFAULT_RULES
    loaded = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    merged = dict(DEFAULT_RULES)
    merged.update(loaded)
    thresholds = dict(DEFAULT_RULES["thresholds"])
    thresholds.update(loaded.get("thresholds", {}))
    merged["thresholds"] = thresholds
    return merged


def _is_pending(value) -> bool:
    return value in PENDING_VALUES or str(value).startswith("pending_")


def _synthetic_mode(mode: str) -> bool:
    return str(mode).startswith("synthetic")


def _fixture_guard_status(mode: str) -> str:
    if _synthetic_mode(mode):
        return "synthetic_controlled"
    try:
        from worldcup_2026_fixture_guard import evaluate_group_stage_simulation_readiness
    except ImportError:
        return "fixture_guard_unavailable"
    return evaluate_group_stage_simulation_readiness().get("guard_status", "missing")


def _base_result(group_name: str, rules: dict) -> dict:
    return {
        "group": group_name,
        "context_status": "insufficient_data",
        "group_strength": {
            "average_rating": None,
            "strongest_team": None,
            "weakest_team": None,
            "rating_spread": None,
            "top_3_spread": None,
            "group_strength_bucket": "unknown",
            "ratings_used": [],
        },
        "competitive_balance": {
            "favorite_gap": None,
            "second_to_fourth_gap": None,
            "balance_bucket": "insufficient_data",
        },
        "death_group_analysis": {
            "is_death_group": False,
            "confidence": "low",
            "reason": "insufficient_data",
            "teams_considered": [],
            "thresholds_used": {
                "top3_spread": rules["thresholds"]["death_group_top3_spread"],
                "average_rating": rules["thresholds"]["death_group_average_rating"],
                "contender_rating": rules["thresholds"]["death_group_contender_rating"],
            },
        },
        "surprise_candidate_analysis": {
            "has_surprise_candidate": False,
            "surprise_team": None,
            "reason": "insufficient_data",
            "confidence": "low",
            "caution": "No future results or post-tournament narrative are used.",
        },
        "match_context": {},
        "jornada3_trap_analysis": {},
        "points_pressure": {},
        "draw_incentive": {},
        "flags": [],
        "warnings": [],
        "data_quality": "insufficient",
        "allowed_for_prediction": False,
        "leakage_guard": {
            "no_future_results": True,
            "no_final_table_before_match": True,
            "standings_required_for_jornada3_trap": True,
            "fixture_guard_status": "not_checked",
            "mode": "pre_tournament",
        },
    }


def _blocked_placeholder(group_name: str, rules: dict, guard_status: str, mode: str) -> dict:
    result = _base_result(group_name, rules)
    result["context_status"] = "placeholder_blocked"
    result["warnings"] = [PLACEHOLDER_WARNING]
    result["allowed_for_prediction"] = False
    result["leakage_guard"]["fixture_guard_status"] = guard_status
    result["leakage_guard"]["mode"] = mode
    return result


def _rating_for_team(team_name: str, teams_baseline: dict) -> dict:
    profile = teams_baseline.get(team_name, {})
    rating = None
    source = None
    for key in ("nova_strength_rating_v1", "elo", "world_football_elo"):
        value = profile.get(key)
        if isinstance(value, (int, float)):
            rating = float(value)
            source = key
            break
    return {
        "team": team_name,
        "rating": rating,
        "source": source,
        "fifa_rank": profile.get("fifa_rank"),
        "attack": profile.get("attack"),
        "defense": profile.get("defense"),
        "form": profile.get("form"),
    }


def _quality_for_ratings(group_teams: list[str], ratings: list[dict]) -> str:
    complete = sum(1 for item in ratings if item["rating"] is not None)
    if complete == len(group_teams) and complete >= 4:
        return "high"
    if complete >= 3:
        return "medium"
    if complete >= 2:
        return "low"
    return "insufficient"


def _strength_bucket(average_rating: float | None, rules: dict) -> str:
    if average_rating is None:
        return "unknown"
    thresholds = rules["thresholds"]
    if average_rating >= thresholds["elite_average_rating"]:
        return "elite"
    if average_rating >= thresholds["strong_average_rating"]:
        return "strong"
    if average_rating < thresholds["weak_average_rating"]:
        return "weak"
    return "balanced"


def _build_group_strength(ratings: list[dict], rules: dict) -> dict:
    valid = [item for item in ratings if item["rating"] is not None]
    ordered = sorted(valid, key=lambda item: item["rating"], reverse=True)
    average_rating = round(mean(item["rating"] for item in valid), 2) if valid else None
    rating_spread = round(ordered[0]["rating"] - ordered[-1]["rating"], 2) if len(ordered) >= 2 else None
    top_3_spread = round(ordered[0]["rating"] - ordered[2]["rating"], 2) if len(ordered) >= 3 else None
    return {
        "average_rating": average_rating,
        "strongest_team": ordered[0]["team"] if ordered else None,
        "weakest_team": ordered[-1]["team"] if ordered else None,
        "rating_spread": rating_spread,
        "top_3_spread": top_3_spread,
        "group_strength_bucket": _strength_bucket(average_rating, rules),
        "ratings_used": ordered,
    }


def _build_competitive_balance(group_strength: dict, rules: dict) -> dict:
    ratings = group_strength["ratings_used"]
    if len(ratings) < 4:
        return {
            "favorite_gap": None,
            "second_to_fourth_gap": None,
            "balance_bucket": "insufficient_data",
        }
    thresholds = rules["thresholds"]
    favorite_gap = round(ratings[0]["rating"] - ratings[1]["rating"], 2)
    second_to_fourth_gap = round(ratings[1]["rating"] - ratings[3]["rating"], 2)
    spread = group_strength["rating_spread"]
    if favorite_gap >= thresholds["clear_favorite_gap"]:
        bucket = "clear_favorite_group"
    elif second_to_fourth_gap >= thresholds["two_favorites_second_to_fourth_gap"]:
        bucket = "two_clear_favorites"
    elif spread is not None and spread <= thresholds["unpredictable_group_spread"]:
        bucket = "unpredictable_group"
    elif spread is not None and spread <= thresholds["balanced_group_spread"]:
        bucket = "balanced_group"
    else:
        bucket = "mixed_group"
    return {
        "favorite_gap": favorite_gap,
        "second_to_fourth_gap": second_to_fourth_gap,
        "balance_bucket": bucket,
    }


def _build_death_group(group_strength: dict, rules: dict) -> dict:
    ratings = group_strength["ratings_used"]
    thresholds = rules["thresholds"]
    teams_considered = [item["team"] for item in ratings]
    if len(ratings) < 4:
        return {
            "is_death_group": False,
            "confidence": "low",
            "reason": "insufficient_data",
            "teams_considered": teams_considered,
            "thresholds_used": {
                "top3_spread": thresholds["death_group_top3_spread"],
                "average_rating": thresholds["death_group_average_rating"],
                "contender_rating": thresholds["death_group_contender_rating"],
            },
        }
    contenders = [item for item in ratings if item["rating"] >= thresholds["death_group_contender_rating"]]
    top3_ok = group_strength["top_3_spread"] <= thresholds["death_group_top3_spread"]
    average_ok = group_strength["average_rating"] >= thresholds["death_group_average_rating"]
    is_death_group = bool(top3_ok and average_ok and len(contenders) >= 3)
    reason = (
        "top three teams are close and group average is high"
        if is_death_group
        else "death group thresholds not fully met"
    )
    return {
        "is_death_group": is_death_group,
        "confidence": "medium" if is_death_group else "low",
        "reason": reason,
        "teams_considered": teams_considered,
        "thresholds_used": {
            "top3_spread": thresholds["death_group_top3_spread"],
            "average_rating": thresholds["death_group_average_rating"],
            "contender_rating": thresholds["death_group_contender_rating"],
        },
    }


def _build_surprise_candidate(group_strength: dict, rules: dict) -> dict:
    ratings = group_strength["ratings_used"]
    if len(ratings) < 4 or group_strength["average_rating"] is None:
        return {
            "has_surprise_candidate": False,
            "surprise_team": None,
            "reason": "insufficient_data",
            "confidence": "low",
            "caution": "No future results or post-tournament narrative are used.",
        }
    thresholds = rules["thresholds"]
    average_rating = group_strength["average_rating"]
    candidates = []
    for item in ratings[2:]:
        rating_ratio = item["rating"] / average_rating
        form = item.get("form")
        rank = item.get("fifa_rank")
        good_form = isinstance(form, (int, float)) and form >= thresholds["good_form_threshold"]
        good_rank = isinstance(rank, int) and rank <= thresholds["good_rank_threshold"]
        if rating_ratio >= thresholds["surprise_candidate_rating_ratio"] and (good_form or good_rank):
            candidates.append((rating_ratio, item))
    if not candidates:
        return {
            "has_surprise_candidate": False,
            "surprise_team": None,
            "reason": "no lower-seed team met controlled prematch surprise criteria",
            "confidence": "low",
            "caution": "No future results or post-tournament narrative are used.",
        }
    _, candidate = sorted(candidates, key=lambda pair: pair[0], reverse=True)[0]
    return {
        "has_surprise_candidate": True,
        "surprise_team": candidate["team"],
        "reason": "lower-seed rating remains near group average with positive prematch form or ranking",
        "confidence": "medium",
        "caution": "Candidate flag is contextual only and must not override insufficient fixture data.",
    }


def _team_points(standings: dict | None, team: str) -> int | None:
    if not standings or team not in standings:
        return None
    row = standings.get(team, {})
    points = row.get("points")
    return points if isinstance(points, int) else None


def calculate_points_pressure(team_a, team_b, standings_before_match, matchday):
    if standings_before_match is None:
        return {
            "status": "pending_real_standings",
            "must_win_team_a": False,
            "must_win_team_b": False,
            "draw_enough_team_a": False,
            "draw_enough_team_b": False,
            "already_qualified": [],
            "likely_eliminated": [],
            "pressure_bucket": "pending",
        }
    points_a = _team_points(standings_before_match, team_a)
    points_b = _team_points(standings_before_match, team_b)
    if points_a is None or points_b is None:
        return {
            "status": "insufficient_standings",
            "must_win_team_a": False,
            "must_win_team_b": False,
            "draw_enough_team_a": False,
            "draw_enough_team_b": False,
            "already_qualified": [],
            "likely_eliminated": [],
            "pressure_bucket": "insufficient",
        }
    matchday = int(matchday or 0)
    must_win_team_a = bool(matchday == 3 and points_a <= 2)
    must_win_team_b = bool(matchday == 3 and points_b <= 2)
    draw_enough_team_a = bool(matchday == 3 and points_a >= 4)
    draw_enough_team_b = bool(matchday == 3 and points_b >= 4)
    already_qualified = [team for team, points in ((team_a, points_a), (team_b, points_b)) if points >= 6]
    likely_eliminated = [
        team for team, points in ((team_a, points_a), (team_b, points_b)) if matchday == 3 and points == 0
    ]
    if must_win_team_a or must_win_team_b:
        bucket = "high"
    elif draw_enough_team_a or draw_enough_team_b:
        bucket = "medium"
    else:
        bucket = "low"
    return {
        "status": "ready",
        "must_win_team_a": must_win_team_a,
        "must_win_team_b": must_win_team_b,
        "draw_enough_team_a": draw_enough_team_a,
        "draw_enough_team_b": draw_enough_team_b,
        "already_qualified": already_qualified,
        "likely_eliminated": likely_eliminated,
        "pressure_bucket": bucket,
        "points_team_a": points_a,
        "points_team_b": points_b,
    }


def detect_jornada3_trap(team_a: str, team_b: str, standings_before_match: dict | None, matchday: int | None = 3):
    if matchday != 3:
        return {
            "trap_status": "not_applicable",
            "trap_confirmed": False,
            "draw_incentive": "not_applicable",
            "points_team_a": None,
            "points_team_b": None,
            "explanation": "Jornada 3 trap only applies to matchday 3.",
        }
    if standings_before_match is None:
        return {
            "trap_status": "pending_standings",
            "trap_confirmed": False,
            "draw_incentive": "pending",
            "points_team_a": None,
            "points_team_b": None,
            "explanation": "Standings before the match are required.",
        }
    points_a = _team_points(standings_before_match, team_a)
    points_b = _team_points(standings_before_match, team_b)
    if points_a is None or points_b is None:
        return {
            "trap_status": "insufficient_standings",
            "trap_confirmed": False,
            "draw_incentive": "pending",
            "points_team_a": points_a,
            "points_team_b": points_b,
            "explanation": "One or both teams are missing from standings_before_match.",
        }
    if points_a >= 4 and points_b >= 4:
        return {
            "trap_status": "confirmed",
            "trap_confirmed": True,
            "draw_incentive": "high",
            "points_team_a": points_a,
            "points_team_b": points_b,
            "explanation": "Both teams can reasonably protect qualification with a draw from the prior table.",
        }
    if points_a <= 2 or points_b <= 2:
        incentive = "low"
        explanation = "At least one team likely needs a win from the prior table."
    else:
        incentive = "medium"
        explanation = "Draw incentive exists for one side but is not mutual."
    return {
        "trap_status": "not_confirmed",
        "trap_confirmed": False,
        "draw_incentive": incentive,
        "points_team_a": points_a,
        "points_team_b": points_b,
        "explanation": explanation,
    }


def build_match_group_context(match: dict, group_context: dict, standings_before_match: dict | None = None) -> dict:
    team_a = match.get("team_a")
    team_b = match.get("team_b")
    matchday = match.get("matchday", match.get("slot_number"))
    if isinstance(matchday, str) and matchday.isdigit():
        matchday = int(matchday)
    flags = []
    warnings = []
    if standings_before_match is None:
        flags.append("points_context_pending")
        warnings.append("standings_before_match is required for points pressure after jornada 1.")
    pressure = calculate_points_pressure(team_a, team_b, standings_before_match, matchday)
    trap = detect_jornada3_trap(team_a, team_b, standings_before_match, matchday=matchday)
    if trap["trap_status"] == "pending_standings":
        flags.append("jornada3_trap_pending")
    if trap["trap_confirmed"]:
        flags.extend(["jornada3_trap_confirmed", "mutual_draw_incentive"])
    if pressure.get("must_win_team_a") or pressure.get("must_win_team_b"):
        flags.append("must_win_pressure")
    surprise = group_context.get("surprise_candidate_analysis", {}).get("surprise_team")
    if surprise and surprise in (team_a, team_b):
        flags.extend(["surprise_candidate_in_match", "underdog_upset_spot"])
    return {
        "matchday": matchday,
        "favorite_pressure": pressure.get("pressure_bucket", "pending"),
        "underdog_upset_potential": "contextual" if "underdog_upset_spot" in flags else "not_flagged",
        "draw_risk_context": trap.get("draw_incentive", "pending"),
        "qualification_pressure": pressure,
        "elimination_pressure": {
            "likely_eliminated": pressure.get("likely_eliminated", []),
        },
        "jornada3_trap_analysis": trap,
        "flags": sorted(set(flags)),
        "warnings": warnings,
    }


def build_group_context(
    group_name: str,
    group_teams: list[str],
    teams_baseline: dict,
    fixtures: list[dict] | None = None,
    standings_before_match: dict | None = None,
    match: dict | None = None,
    mode: str = "pre_tournament",
) -> dict:
    rules = _load_rules()
    guard_status = _fixture_guard_status(mode)
    if any(_is_pending(team) for team in group_teams) or guard_status == "blocked_placeholder":
        return _blocked_placeholder(group_name, rules, guard_status, mode)

    result = _base_result(group_name, rules)
    result["leakage_guard"]["fixture_guard_status"] = guard_status
    result["leakage_guard"]["mode"] = mode

    ratings = [_rating_for_team(team, teams_baseline) for team in group_teams]
    data_quality = _quality_for_ratings(group_teams, ratings)
    result["data_quality"] = data_quality
    result["group_strength"] = _build_group_strength(ratings, rules)
    result["competitive_balance"] = _build_competitive_balance(result["group_strength"], rules)
    result["death_group_analysis"] = _build_death_group(result["group_strength"], rules)
    result["surprise_candidate_analysis"] = _build_surprise_candidate(result["group_strength"], rules)

    if data_quality == "insufficient":
        result["context_status"] = "insufficient_data"
        result["warnings"].append("insufficient_group_data")
        result["flags"].append("insufficient_group_data")
    elif data_quality == "low":
        result["context_status"] = "partial"
        result["warnings"].append("ratings are incomplete; prediction impact should stay disabled")
    else:
        result["context_status"] = "ready"

    balance_bucket = result["competitive_balance"]["balance_bucket"]
    if result["death_group_analysis"]["is_death_group"]:
        result["flags"].append("death_group")
    if balance_bucket in ("balanced_group", "unpredictable_group"):
        result["flags"].append("balanced_group")
    if balance_bucket == "clear_favorite_group":
        result["flags"].append("clear_favorite_group")
    if result["surprise_candidate_analysis"]["has_surprise_candidate"]:
        result["flags"].append("surprise_candidate_in_group")

    if match:
        match_context = build_match_group_context(match, result, standings_before_match)
        result["match_context"] = match_context
        result["jornada3_trap_analysis"] = match_context["jornada3_trap_analysis"]
        result["points_pressure"] = match_context["qualification_pressure"]
        result["draw_incentive"] = {
            "draw_incentive": match_context["jornada3_trap_analysis"].get("draw_incentive", "pending")
        }
        result["flags"].extend(match_context["flags"])
        result["warnings"].extend(match_context["warnings"])
    else:
        result["jornada3_trap_analysis"] = detect_jornada3_trap("", "", None, matchday=None)
        result["points_pressure"] = calculate_points_pressure("", "", None, None)
        result["draw_incentive"] = {"draw_incentive": "pending_match_context"}

    result["flags"] = sorted(set(result["flags"]))
    result["warnings"] = sorted(set(result["warnings"]))
    result["allowed_for_prediction"] = bool(
        result["context_status"] in ("ready", "partial")
        and data_quality in ("high", "medium")
        and guard_status in ("ready", "partial_ready", "synthetic_controlled")
    )
    if not fixtures and not _synthetic_mode(mode):
        result["allowed_for_prediction"] = False
    return result
