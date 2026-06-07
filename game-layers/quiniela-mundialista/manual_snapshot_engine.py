import json
from pathlib import Path


PENDING = "pending_manual_input"


def _as_list(value) -> list:
    if value in (None, "", PENDING):
        return [] if value in (None, "") else [PENDING]
    if isinstance(value, list):
        return value
    return [str(value)]


def load_manual_snapshots(path: str | Path) -> dict:
    snapshot_path = Path(path)
    if not snapshot_path.exists():
        return {
            "data_status": "manual_snapshot_required",
            "snapshots": [],
            "message": "manual_match_snapshots.json not found.",
        }

    try:
        return json.loads(snapshot_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "data_status": "invalid_json",
            "snapshots": [],
            "message": str(exc),
        }


def find_manual_snapshot(snapshots_data: dict, team_a: str, team_b: str) -> dict:
    requested = {team_a.strip().lower(), team_b.strip().lower()}
    for snapshot in snapshots_data.get("snapshots", []):
        current = {
            str(snapshot.get("team_a", "")).strip().lower(),
            str(snapshot.get("team_b", "")).strip().lower(),
        }
        if current == requested:
            return normalize_manual_snapshot(snapshot)
    return normalize_manual_snapshot(
        {
            "source": "365Scores",
            "source_status": "manual_snapshot",
            "match": f"{team_a} vs {team_b}",
            "team_a": team_a,
            "team_b": team_b,
            "data_status": "manual_snapshot_required",
        }
    )


def normalize_manual_snapshot(snapshot: dict) -> dict:
    odds = snapshot.get("odds_1x2") or {}
    lineups = snapshot.get("probable_lineups") or {}
    stats = snapshot.get("stats_snapshot") or {}
    over_under = snapshot.get("over_under") or {}
    decimal_reference = snapshot.get("odds_decimal_reference") or {}
    market_probabilities = snapshot.get("market_probabilities") or {}
    research_impact = snapshot.get("manual_research_impact") or {}
    return {
        "source": snapshot.get("source", "365Scores"),
        "source_status": snapshot.get("source_status", "manual_snapshot"),
        "captured_at": snapshot.get("captured_at", PENDING),
        "captured_by": snapshot.get("captured_by", PENDING),
        "sources_used": _as_list(snapshot.get("sources_used", [])),
        "match": snapshot.get("match", PENDING),
        "team_a": snapshot.get("team_a", PENDING),
        "team_b": snapshot.get("team_b", PENDING),
        "competition_type": snapshot.get("competition_type", PENDING),
        "kickoff_time_utc": snapshot.get("kickoff_time_utc", PENDING),
        "kickoff_time_local": snapshot.get("kickoff_time_local", PENDING),
        "venue": snapshot.get("venue", PENDING),
        "venue_status": snapshot.get("venue_status", PENDING),
        "odds_1x2": {
            "home": odds.get("home", PENDING),
            "draw": odds.get("draw", PENDING),
            "away": odds.get("away", PENDING),
            "home_american": odds.get("home_american", odds.get("home", PENDING)),
            "draw_american": odds.get("draw_american", odds.get("draw", PENDING)),
            "away_american": odds.get("away_american", odds.get("away", PENDING)),
            "source": odds.get("source", snapshot.get("source", PENDING)),
            "data_status": odds.get("data_status", snapshot.get("data_status", PENDING)),
        },
        "odds_decimal_reference": {
            "home": decimal_reference.get("home", PENDING),
            "draw": decimal_reference.get("draw", PENDING),
            "away": decimal_reference.get("away", PENDING),
            "source": decimal_reference.get("source", PENDING),
            "data_status": decimal_reference.get("data_status", PENDING),
        },
        "market_probabilities": {
            "home_win_percent": market_probabilities.get("home_win_percent", PENDING),
            "draw_percent": market_probabilities.get("draw_percent", PENDING),
            "away_win_percent": market_probabilities.get("away_win_percent", PENDING),
            "source": market_probabilities.get("source", PENDING),
            "data_status": market_probabilities.get("data_status", PENDING),
        },
        "over_under": {
            "line": over_under.get("line", PENDING),
            "over_american": over_under.get("over_american", PENDING),
            "under_american": over_under.get("under_american", PENDING),
            "source": over_under.get("source", PENDING),
            "data_status": over_under.get("data_status", PENDING),
        },
        "external_market_notes": _as_list(snapshot.get("external_market_notes", [])),
        "key_players": snapshot.get("key_players", {}),
        "team_context": snapshot.get("team_context", {}),
        "research_confidence": snapshot.get("research_confidence", PENDING),
        "manual_research_impact": {
            "risk_adjustment": research_impact.get("risk_adjustment", PENDING),
            "confidence_adjustment": research_impact.get("confidence_adjustment", PENDING),
            "model_warning": research_impact.get("model_warning", PENDING),
        },
        "probable_lineups": {
            "team_a_formation": lineups.get("team_a_formation", PENDING),
            "team_b_formation": lineups.get("team_b_formation", PENDING),
            "team_a_players": lineups.get(
                "team_a_players",
                lineups.get("team_a_players_text", PENDING),
            ),
            "team_b_players": lineups.get(
                "team_b_players",
                lineups.get("team_b_players_text", PENDING),
            ),
            "team_a_players_text": lineups.get(
                "team_a_players_text",
                lineups.get("team_a_players", PENDING),
            ),
            "team_b_players_text": lineups.get(
                "team_b_players_text",
                lineups.get("team_b_players", PENDING),
            ),
            "data_status": lineups.get("data_status", PENDING),
        },
        "stats_snapshot": {
            "both_teams_to_score_percent": stats.get("both_teams_to_score_percent", PENDING),
            "over_2_5_percent": stats.get("over_2_5_percent", PENDING),
            "avg_goals_for_team_a": stats.get("avg_goals_for_team_a", PENDING),
            "avg_goals_for_team_b": stats.get("avg_goals_for_team_b", PENDING),
            "avg_goals_against_team_a": stats.get("avg_goals_against_team_a", PENDING),
            "avg_goals_against_team_b": stats.get("avg_goals_against_team_b", PENDING),
            "h2h_notes": stats.get("h2h_notes", PENDING),
            "trends": _as_list(stats.get("trends", PENDING)),
            "data_status": stats.get("data_status", PENDING),
        },
        "data_status": snapshot.get("data_status", "manual_snapshot_required"),
    }


def summarize_manual_snapshot(snapshot: dict) -> dict:
    odds = snapshot["odds_1x2"]
    lineups = snapshot["probable_lineups"]
    stats = snapshot["stats_snapshot"]
    return {
        "odds_visible": (
            f"home {odds['home_american']} | draw {odds['draw_american']} | "
            f"away {odds['away_american']} | source {odds['source']}"
        ),
        "odds_decimal_visible": (
            f"home {snapshot['odds_decimal_reference']['home']} | "
            f"draw {snapshot['odds_decimal_reference']['draw']} | "
            f"away {snapshot['odds_decimal_reference']['away']} | "
            f"source {snapshot['odds_decimal_reference']['source']}"
        ),
        "over_under_visible": (
            f"line {snapshot['over_under']['line']} | "
            f"over {snapshot['over_under']['over_american']} | "
            f"under {snapshot['over_under']['under_american']} | "
            f"source {snapshot['over_under']['source']}"
        ),
        "market_probabilities_visible": (
            f"home {snapshot['market_probabilities']['home_win_percent']}% | "
            f"draw {snapshot['market_probabilities']['draw_percent']}% | "
            f"away {snapshot['market_probabilities']['away_win_percent']}% | "
            f"source {snapshot['market_probabilities']['source']}"
        ),
        "lineups_visible": (
            f"{snapshot['team_a']} {lineups['team_a_formation']} | "
            f"{snapshot['team_b']} {lineups['team_b_formation']}"
        ),
        "stats_visible": (
            f"BTTS {stats['both_teams_to_score_percent']} | "
            f"Over 2.5 {stats['over_2_5_percent']} | "
            f"H2H {stats['h2h_notes']}"
        ),
        "snapshot_investigative": (
            "si"
            if snapshot["source_status"] == "manual_researched_snapshot"
            or snapshot["data_status"] == "manual_researched_public_snapshot"
            else "no"
        ),
        "sources_used": snapshot["sources_used"],
        "external_market_notes": snapshot["external_market_notes"],
        "manual_research_impact": snapshot["manual_research_impact"],
        "research_confidence": snapshot["research_confidence"],
        "venue_visible": f"{snapshot['venue']} | {snapshot['kickoff_time_utc']}",
        "data_status": snapshot["data_status"],
    }
