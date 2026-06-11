from __future__ import annotations

from research_snapshot_validator import validate_research_snapshot


PENDING = "pending_manual_input"


def _players_text(players: list) -> str:
    if not players:
        return PENDING
    names = []
    for item in players:
        if isinstance(item, dict):
            names.append(str(item.get("name", item.get("player", PENDING))))
        else:
            names.append(str(item))
    return ", ".join(names)


def _ratings_list(ratings: dict) -> list[dict]:
    return [
        {
            "player_name": player,
            "overall_rating": value,
            "rating_type": "research_snapshot",
        }
        for player, value in ratings.items()
    ]


def normalize_research_snapshot(snapshot: dict) -> dict:
    validation = validate_research_snapshot(snapshot)
    odds = snapshot.get("odds_1x2", {})
    lineups = snapshot.get("probable_lineups", {})
    formations = snapshot.get("formations", {})
    ratings = snapshot.get("player_ratings", {})
    stats = snapshot.get("stats_snapshot", {})
    form = snapshot.get("form_snapshot", {})
    tactical = snapshot.get("tactical_notes", {})
    return {
        "source": "research_automation",
        "source_status": snapshot.get("source_status", "pending_verification"),
        "captured_at": snapshot.get("captured_at", PENDING),
        "captured_by": snapshot.get("captured_by", PENDING),
        "sources_used": snapshot.get("sources", []),
        "match": snapshot.get("match", PENDING),
        "team_a": snapshot.get("team_a", PENDING),
        "team_b": snapshot.get("team_b", PENDING),
        "competition_type": snapshot.get("competition", PENDING),
        "phase": snapshot.get("phase", PENDING),
        "kickoff_time_utc": snapshot.get("kickoff_utc", PENDING),
        "odds_1x2": {
            "home": odds.get("home", PENDING),
            "draw": odds.get("draw", PENDING),
            "away": odds.get("away", PENDING),
            "source": odds.get("source", PENDING),
            "captured_at": odds.get("captured_at", snapshot.get("captured_at", PENDING)),
            "confidence": odds.get("confidence", PENDING),
            "data_status": snapshot.get("source_status", "pending_verification"),
        },
        "over_under": snapshot.get("over_under", {}),
        "probable_lineups": {
            "team_a_formation": formations.get("team_a", PENDING),
            "team_b_formation": formations.get("team_b", PENDING),
            "team_a_players": lineups.get("team_a", []),
            "team_b_players": lineups.get("team_b", []),
            "team_a_players_text": _players_text(lineups.get("team_a", [])),
            "team_b_players_text": _players_text(lineups.get("team_b", [])),
            "source": lineups.get("source", PENDING),
            "confidence": lineups.get("confidence", PENDING),
            "data_status": snapshot.get("source_status", "pending_verification"),
        },
        "formations": formations,
        "injuries_or_absences": snapshot.get("injuries_or_absences", {"team_a": [], "team_b": []}),
        "key_players": snapshot.get("key_players", {"team_a": [], "team_b": []}),
        "player_ratings": {
            "team_a": _ratings_list(ratings.get("team_a", {})),
            "team_b": _ratings_list(ratings.get("team_b", {})),
            "source": ratings.get("source", PENDING),
            "confidence": ratings.get("confidence", PENDING),
        },
        "form": form,
        "stats_snapshot": stats,
        "tactical_notes": tactical,
        "research_confidence": snapshot.get("overall_confidence", "insufficient"),
        "data_quality_score": validation["data_quality_score"],
        "research_automation_validation": validation,
        "valid_for_tactical_bridge": validation["valid_for_tactical_bridge"],
        "valid_for_market_weighting": validation["valid_for_market_weighting"],
        "valid_for_prediction_context": validation["valid_for_prediction_context"],
        "data_status": "research_snapshot_normalized",
    }
