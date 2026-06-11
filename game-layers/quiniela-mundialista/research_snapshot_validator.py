from __future__ import annotations

from research_snapshot_schema import (
    CONFIDENCE_VALUES,
    REQUIRED_TOP_LEVEL_FIELDS,
    SOURCE_STATUS_VALUES,
    SNAPSHOT_TYPE_VALUES,
)


PENDING_VALUES = {
    None,
    "",
    "pending_manual_input",
    "pending_verification",
    "pending_real_data",
    "not_available",
    "not_available_free",
}


def _is_pending(value) -> bool:
    if isinstance(value, list):
        return not value or all(_is_pending(item) for item in value)
    if isinstance(value, dict):
        return not value or all(_is_pending(item) for item in value.values())
    if value in PENDING_VALUES:
        return True
    if isinstance(value, str):
        stripped = value.strip()
        return stripped in PENDING_VALUES or stripped.startswith("pending_")
    return False


def _is_number(value) -> bool:
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        try:
            float(value)
            return True
        except ValueError:
            return False
    return False


def _valid_lineups(lineups: dict) -> bool:
    return (
        isinstance(lineups, dict)
        and isinstance(lineups.get("team_a"), list)
        and isinstance(lineups.get("team_b"), list)
        and len(lineups.get("team_a", [])) >= 7
        and len(lineups.get("team_b", [])) >= 7
    )


def _valid_formations(formations: dict) -> bool:
    return (
        isinstance(formations, dict)
        and isinstance(formations.get("team_a"), str)
        and isinstance(formations.get("team_b"), str)
        and not _is_pending(formations.get("team_a"))
        and not _is_pending(formations.get("team_b"))
    )


def _valid_ratings(player_ratings: dict) -> bool:
    if not isinstance(player_ratings, dict):
        return False
    for side in ("team_a", "team_b"):
        ratings = player_ratings.get(side, {})
        if not isinstance(ratings, dict) or len(ratings) < 7:
            return False
        if not all(_is_number(value) for value in ratings.values()):
            return False
    return True


def _valid_odds(odds: dict) -> bool:
    return (
        isinstance(odds, dict)
        and all(_is_number(odds.get(key)) for key in ("home", "draw", "away"))
        and not _is_pending(odds.get("source"))
    )


def _valid_injuries(injuries: dict) -> list[str]:
    warnings = []
    if not isinstance(injuries, dict):
        return ["injuries_or_absences must be an object"]
    for side in ("team_a", "team_b"):
        for item in injuries.get(side, []):
            if isinstance(item, dict) and _is_pending(item.get("impact")):
                warnings.append(f"{side} injury/absence missing impact: {item.get('player', 'unknown')}")
    return warnings


def validate_research_snapshot(snapshot: dict) -> dict:
    errors = []
    warnings = []
    missing_data = []

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in snapshot:
            errors.append(f"missing top-level field: {field}")

    for field in ("snapshot_id", "match", "team_a", "team_b", "captured_at"):
        if _is_pending(snapshot.get(field)):
            missing_data.append(field)

    sources = snapshot.get("sources", [])
    if not isinstance(sources, list) or not sources:
        missing_data.append("sources")
        warnings.append("sources are required for prediction context")

    source_status = snapshot.get("source_status")
    if source_status not in SOURCE_STATUS_VALUES:
        errors.append(f"invalid source_status: {source_status}")
    if source_status == "official_verified" and not sources:
        errors.append("official_verified source_status requires at least one source")

    snapshot_type = snapshot.get("snapshot_type")
    if snapshot_type not in SNAPSHOT_TYPE_VALUES:
        errors.append(f"invalid snapshot_type: {snapshot_type}")

    confidence = snapshot.get("overall_confidence")
    if confidence not in CONFIDENCE_VALUES:
        errors.append(f"invalid overall_confidence: {confidence}")

    odds = snapshot.get("odds_1x2", {})
    lineups = snapshot.get("probable_lineups", {})
    formations = snapshot.get("formations", {})
    player_ratings = snapshot.get("player_ratings", {})

    if any(not _is_pending(odds.get(key)) for key in ("home", "draw", "away")) and not _valid_odds(odds):
        errors.append("odds_1x2 must be numeric and complete when provided")
    if not isinstance(lineups.get("team_a", []), list) or not isinstance(lineups.get("team_b", []), list):
        errors.append("probable_lineups.team_a and team_b must be lists")
    if formations and not isinstance(formations.get("team_a", ""), str):
        errors.append("formations.team_a must be a string")
    if formations and not isinstance(formations.get("team_b", ""), str):
        errors.append("formations.team_b must be a string")
    warnings.extend(_valid_injuries(snapshot.get("injuries_or_absences", {})))

    tactical_ready = _valid_lineups(lineups) and _valid_formations(formations) and _valid_ratings(player_ratings)
    market_ready = _valid_odds(odds)
    context_ready = len(sources) >= 2 and source_status in {"manual_input", "ai_assisted", "official_verified"}

    if snapshot.get("valid_for_tactical_bridge") and not tactical_ready:
        errors.append("valid_for_tactical_bridge cannot be true without lineups, formations and ratings")
    if snapshot.get("valid_for_market_weighting") and not market_ready:
        errors.append("valid_for_market_weighting cannot be true without complete numeric odds")
    if snapshot.get("valid_for_prediction_context") and not context_ready:
        errors.append("valid_for_prediction_context cannot be true without enough sources")

    score_parts = [
        not _is_pending(snapshot.get("match")),
        not _is_pending(snapshot.get("captured_at")),
        bool(sources),
        tactical_ready,
        market_ready,
        context_ready,
        not errors,
    ]
    data_quality_score = round(sum(1 for item in score_parts if item) / len(score_parts), 2)
    if errors:
        validation_status = "invalid"
    elif missing_data or warnings or data_quality_score < 0.85:
        validation_status = "partial"
    else:
        validation_status = "valid"
    return {
        "validation_status": validation_status,
        "valid_for_tactical_bridge": tactical_ready and not errors,
        "valid_for_market_weighting": market_ready and not errors,
        "valid_for_prediction_context": context_ready and not errors,
        "errors": errors,
        "warnings": warnings,
        "missing_data": sorted(set(missing_data)),
        "data_quality_score": data_quality_score,
    }
