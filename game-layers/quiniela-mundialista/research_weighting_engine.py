from pathlib import Path

from lineup_strength_engine import (
    DEFAULT_RATINGS_PATH,
    DEFAULT_SNAPSHOTS_PATH,
    build_match_lineup_strength,
)
from manual_snapshot_engine import (
    find_manual_snapshot,
    load_manual_snapshots,
    summarize_manual_snapshot,
)
from research_intelligence_engine import (
    build_research_intelligence,
)
from tactical_weighting_engine import build_tactical_weighting


PENDING = "pending_manual_input"


def _numeric(value, default: float = 0.0) -> float:
    return float(value) if isinstance(value, (int, float)) else default


def _quality_from_snapshot(snapshot: dict) -> float:
    score = 0
    total = 6
    if snapshot.get("source_status") == "manual_researched_snapshot":
        score += 1
    if snapshot.get("venue") != PENDING:
        score += 1
    if snapshot.get("kickoff_time_utc") != PENDING:
        score += 1
    if snapshot.get("over_under", {}).get("line") != PENDING:
        score += 1
    if snapshot.get("odds_1x2", {}).get("home_american") != PENDING:
        score += 1
    if snapshot.get("market_probabilities", {}).get("home_win_percent") != PENDING:
        score += 1
    return round((score / total) * 100, 2)


def _lineup_adjustment_delta(lineup_strength: dict, team_key: str) -> float:
    team = lineup_strength[team_key]
    return _numeric(team.get("confidence_adjustment"))


def _market_alignment(snapshot: dict, research: dict) -> str:
    warning = str(research.get("market_warning", "")).lower()
    if "fragile" in warning or "balanced" in warning:
        return "market_weakens_core_pick"
    if "aligned" in warning or "favoritism" in warning:
        return "market_supports_core_direction"
    if snapshot.get("odds_1x2", {}).get("home_american") != PENDING:
        return "market_available_needs_manual_review"
    return "market_pending"


def _model_fragility(lineup_strength: dict, tactical: dict, market_alignment: str) -> str:
    if market_alignment == "market_weakens_core_pick":
        if lineup_strength["lineup_weighting_status"] == "replacement_estimate":
            return "high_replacement_ratings_and_market_disagreement"
        return "high_market_disagreement"
    if lineup_strength["lineup_weighting_status"] == "incomplete":
        return "high_missing_player_ratings"
    if lineup_strength["lineup_weighting_status"] == "replacement_estimate":
        return "medium_replacement_ratings"
    if tactical["adjustment_status"] == "qualitative_only":
        return "medium_tactical_data_incomplete"
    return "low"


def _layer(
    data_found: bool,
    data_quality: float,
    evidence_level: str,
    impact_type: str,
    numeric_adjustment,
    qualitative_adjustment: str,
    explanation: str,
) -> dict:
    return {
        "data_found": data_found,
        "data_quality": data_quality,
        "evidence_level": evidence_level,
        "impact_type": impact_type,
        "numeric_adjustment": numeric_adjustment,
        "qualitative_adjustment": qualitative_adjustment,
        "explanation": explanation,
    }


def build_research_weighting(
    team_a: str,
    team_b: str,
    base_confidence: float | int | str = 50.0,
    base_risk: str = "medio",
    snapshots_path: str | Path = DEFAULT_SNAPSHOTS_PATH,
    ratings_path: str | Path = DEFAULT_RATINGS_PATH,
) -> dict:
    snapshots_data = load_manual_snapshots(snapshots_path)
    snapshot = find_manual_snapshot(snapshots_data, team_a, team_b)
    snapshot_summary = summarize_manual_snapshot(snapshot)
    research = build_research_intelligence(snapshot, snapshot_summary, base_confidence, base_risk)
    lineup_strength = build_match_lineup_strength(team_a, team_b, snapshots_path, ratings_path)
    tactical = build_tactical_weighting(team_a, team_b, snapshots_path, ratings_path)

    market_alignment = _market_alignment(snapshot, research)
    tactical_alignment = tactical["adjustment_status"]
    player_rating_alignment = lineup_strength["lineup_weighting_status"]
    model_fragility = _model_fragility(lineup_strength, tactical, market_alignment)

    lineup_confidence_delta = (
        _lineup_adjustment_delta(lineup_strength, "team_a")
        - _lineup_adjustment_delta(lineup_strength, "team_b")
    )
    research_confidence_delta = (
        _numeric(research["research_adjusted_confidence"]) - _numeric(base_confidence)
        if isinstance(base_confidence, (int, float))
        else 0.0
    )
    tactical_confidence_delta = 0.0 if tactical["adjustment_status"] == "qualitative_only" else 1.0
    total_confidence_adjustment = round(
        research_confidence_delta + lineup_confidence_delta + tactical_confidence_delta,
        2,
    )

    xg_adjustment_team_a = round(
        _numeric(lineup_strength["team_a"]["attack_xg_adjustment"])
        + _numeric(tactical["tactical_attack_adjustment"]),
        3,
    )
    xg_adjustment_team_b = round(
        _numeric(lineup_strength["team_b"]["attack_xg_adjustment"])
        + _numeric(tactical["tactical_attack_adjustment"]),
        3,
    )
    data_quality_score = round(
        (
            _quality_from_snapshot(snapshot)
            + lineup_strength["lineup_data_quality"]
            + (0 if tactical["formation_missing"] else 100)
        )
        / 3,
        2,
    )

    missing_critical_data = []
    if lineup_strength["critical_missing_ratings"]:
        missing_critical_data.append("real player ratings: " + ", ".join(lineup_strength["critical_missing_ratings"]))
    if tactical["formation_missing"]:
        missing_critical_data.append("confirmed/probable formations")
    if snapshot.get("probable_lineups", {}).get("data_status") == PENDING:
        missing_critical_data.append("confirmed probable lineups")
    if snapshot.get("odds_1x2", {}).get("draw_american") == PENDING:
        missing_critical_data.append("complete 1X2 market")

    layers = {
        "real_strength": _layer(
            True,
            100.0,
            "core_baseline_available",
            "numeric",
            0.0,
            "Core strength remains primary.",
            "Fuerza real viene del Core; esta capa no la reemplaza.",
        ),
        "match_context": _layer(
            True,
            _quality_from_snapshot(snapshot),
            snapshot.get("source_status", PENDING),
            "qualitative",
            0.0,
            "Friendly context reduces certainty.",
            "El partido amistoso eleva riesgo por rotacion e intensidad menor.",
        ),
        "tactical_information": _layer(
            not tactical["formation_missing"],
            0.0 if tactical["formation_missing"] else 100.0,
            "formation_missing" if tactical["formation_missing"] else "formation_available",
            tactical["adjustment_status"],
            0.0 if tactical["adjustment_status"] == "qualitative_only" else tactical["tactical_attack_adjustment"],
            tactical["explanation"],
            "La tactica no aplica peso fuerte sin formaciones y ratings suficientes.",
        ),
        "external_context": _layer(
            research["snapshot_investigative"] == "si",
            _quality_from_snapshot(snapshot),
            snapshot.get("source_status", PENDING),
            "qualitative",
            research_confidence_delta,
            research["market_warning"],
            "La investigacion externa ajusta confianza/riesgo, no el pick.",
        ),
        "market": _layer(
            market_alignment != "market_pending",
            _quality_from_snapshot(snapshot),
            snapshot.get("odds_1x2", {}).get("data_status", PENDING),
            "mixed",
            research_confidence_delta,
            market_alignment,
            "El mercado se usa como contraste contextual contra Core.",
        ),
        "advanced_signals": _layer(
            lineup_strength["lineup_weighting_status"] in ("active", "replacement_estimate"),
            lineup_strength["lineup_data_quality"],
            "player_rating_seed",
            lineup_strength["lineup_weighting_status"],
            lineup_confidence_delta,
            (
                "Replacement ratings used; numeric effect is conservative and fragility is raised."
                if lineup_strength["lineup_weighting_status"] == "replacement_estimate"
                else "Player ratings pending; strong numeric effect blocked."
                if lineup_strength["lineup_weighting_status"] == "incomplete"
                else "Lineup ratings sufficient for numeric adjustment."
            ),
            "Dato -> variable -> peso -> ajuste; replacement level reduce el peso matematico.",
        ),
    }

    return {
        "match": snapshot["match"],
        "layers": layers,
        "lineup_strength": lineup_strength,
        "tactical_weighting": tactical,
        "research_intelligence": research,
        "total_confidence_adjustment": total_confidence_adjustment,
        "total_risk_adjustment": model_fragility,
        "xg_adjustment_team_a": xg_adjustment_team_a,
        "xg_adjustment_team_b": xg_adjustment_team_b,
        "market_alignment": market_alignment,
        "tactical_alignment": tactical_alignment,
        "player_rating_alignment": player_rating_alignment,
        "model_fragility": model_fragility,
        "data_quality_score": data_quality_score,
        "missing_critical_data": missing_critical_data,
        "rating_coverage": lineup_strength["rating_coverage"],
        "real_rating_coverage": lineup_strength["real_rating_coverage"],
        "replacement_rating_count": lineup_strength["replacement_rating_count"],
        "real_rating_count": lineup_strength["known_rating_count"],
        "source_confidence_weighted_score": lineup_strength["source_confidence_weighted_score"],
    }


def format_research_weighting_lines(weighting: dict) -> list[str]:
    lines = [
        "Seis capas de weighting:",
    ]
    for name, layer in weighting["layers"].items():
        lines.append(
            f"- {name}: data_found={layer['data_found']} | quality={layer['data_quality']} | "
            f"evidence={layer['evidence_level']} | impact={layer['impact_type']} | "
            f"numeric={layer['numeric_adjustment']} | qualitative={layer['qualitative_adjustment']}"
        )
    lines.extend(
        [
            f"Player rating impact: {weighting['player_rating_alignment']}",
            f"Rating coverage: {weighting['rating_coverage']}% total | {weighting['real_rating_coverage']}% real",
            f"Source confidence weighted score: {weighting['source_confidence_weighted_score']}%",
            f"Ratings reales/replacement: {weighting['real_rating_count']}/{weighting['replacement_rating_count']}",
            f"Lineup strength impact: {weighting['lineup_strength']['lineup_weighting_status']}",
            f"Tactical impact: {weighting['tactical_alignment']}",
            f"Market alignment: {weighting['market_alignment']}",
            f"Model fragility: {weighting['model_fragility']}",
            f"Data quality score: {weighting['data_quality_score']}",
            "Missing critical data: "
            + (
                "; ".join(weighting["missing_critical_data"])
                if weighting["missing_critical_data"]
                else "none"
            ),
            f"Total confidence adjustment: {weighting['total_confidence_adjustment']}",
            f"Total risk adjustment: {weighting['total_risk_adjustment']}",
            f"xG adjustment team A: {weighting['xg_adjustment_team_a']}",
            f"xG adjustment team B: {weighting['xg_adjustment_team_b']}",
        ]
    )
    return lines
