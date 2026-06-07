import json
from pathlib import Path


PENDING = "pending_manual_input"


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
    return {
        "source": snapshot.get("source", "365Scores"),
        "source_status": snapshot.get("source_status", "manual_snapshot"),
        "captured_at": snapshot.get("captured_at", PENDING),
        "captured_by": snapshot.get("captured_by", PENDING),
        "match": snapshot.get("match", PENDING),
        "team_a": snapshot.get("team_a", PENDING),
        "team_b": snapshot.get("team_b", PENDING),
        "odds_1x2": {
            "home": odds.get("home", PENDING),
            "draw": odds.get("draw", PENDING),
            "away": odds.get("away", PENDING),
        },
        "probable_lineups": {
            "team_a_formation": lineups.get("team_a_formation", PENDING),
            "team_b_formation": lineups.get("team_b_formation", PENDING),
            "team_a_players": lineups.get("team_a_players", PENDING),
            "team_b_players": lineups.get("team_b_players", PENDING),
        },
        "stats_snapshot": {
            "both_teams_to_score_percent": stats.get("both_teams_to_score_percent", PENDING),
            "over_2_5_percent": stats.get("over_2_5_percent", PENDING),
            "avg_goals_for_team_a": stats.get("avg_goals_for_team_a", PENDING),
            "avg_goals_for_team_b": stats.get("avg_goals_for_team_b", PENDING),
            "avg_goals_against_team_a": stats.get("avg_goals_against_team_a", PENDING),
            "avg_goals_against_team_b": stats.get("avg_goals_against_team_b", PENDING),
            "h2h_notes": stats.get("h2h_notes", PENDING),
            "trends": stats.get("trends", PENDING),
        },
        "data_status": snapshot.get("data_status", "manual_snapshot_required"),
    }


def summarize_manual_snapshot(snapshot: dict) -> dict:
    odds = snapshot["odds_1x2"]
    lineups = snapshot["probable_lineups"]
    stats = snapshot["stats_snapshot"]
    return {
        "odds_visible": (
            f"home {odds['home']} | draw {odds['draw']} | away {odds['away']}"
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
        "data_status": snapshot["data_status"],
    }
