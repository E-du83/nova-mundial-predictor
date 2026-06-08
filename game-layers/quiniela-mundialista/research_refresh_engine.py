from __future__ import annotations

import json
from pathlib import Path

from manual_snapshot_engine import find_manual_snapshot, load_manual_snapshots


PENDING_VALUES = {
    None,
    "",
    "pending_manual_input",
    "pending_real_data",
    "pending_real_result",
    "pending_manual_snapshot",
    "manual_research_required",
    "not_available_free",
}

CRITICAL_FIELDS = [
    "venue",
    "kickoff_time_utc",
    "odds_1x2",
    "over_under",
    "probable_lineups",
    "formations",
    "player_ratings_key_players",
    "result_status",
]

OPTIONAL_FIELDS = [
    "visible_stats",
    "injuries_or_absences",
    "tactical_notes",
    "market_notes",
]


def _is_pending(value) -> bool:
    if isinstance(value, list):
        return not value or all(_is_pending(item) for item in value)
    if isinstance(value, dict):
        return not value or all(_is_pending(item) for item in value.values())
    if value in PENDING_VALUES:
        return True
    if isinstance(value, str):
        return value.strip() in PENDING_VALUES or value.strip().startswith("pending_")
    return False


def _load_json(path: str | Path) -> dict:
    data_path = Path(path)
    if not data_path.exists():
        return {}
    return json.loads(data_path.read_text(encoding="utf-8"))


def _raw_snapshot(snapshots_data: dict, team_a: str, team_b: str) -> dict:
    requested = {team_a.strip().lower(), team_b.strip().lower()}
    for snapshot in snapshots_data.get("snapshots", []):
        current = {
            str(snapshot.get("team_a", "")).strip().lower(),
            str(snapshot.get("team_b", "")).strip().lower(),
        }
        if current == requested:
            return snapshot
    return {}


def _real_result_status(results_data: dict, team_a: str, team_b: str) -> str:
    requested = {team_a.strip().lower(), team_b.strip().lower()}
    for result in results_data.get("results", []):
        current = {
            str(result.get("team_a", "")).strip().lower(),
            str(result.get("team_b", "")).strip().lower(),
        }
        if current == requested:
            return result.get("status", result.get("real_score", "pending_real_result"))
    return "pending_real_result"


def _has_partial_snapshot(snapshot: dict) -> bool:
    sources = snapshot.get("cross_checked_with") or snapshot.get("primary_sources") or snapshot.get("sources_used")
    stats = snapshot.get("stats_snapshot") or {}
    trends = stats.get("trends", [])
    has_context = bool(snapshot.get("tactical_notes")) or bool(snapshot.get("team_context"))
    has_rankings_or_form = bool(stats.get("fifa_rankings_visible")) or any(
        "FIFA" in str(item) or "form" in str(item).lower()
        for item in (trends if isinstance(trends, list) else [trends])
    )
    return (
        not _is_pending(snapshot.get("venue"))
        and not _is_pending(snapshot.get("kickoff_time_utc"))
        and has_context
        and has_rankings_or_form
        and isinstance(sources, list)
        and len([source for source in sources if not _is_pending(source)]) >= 3
    )


def build_research_refresh(
    team_a: str,
    team_b: str,
    snapshots_data: dict | None = None,
    results_data: dict | None = None,
    snapshots_path: str | Path | None = None,
    results_path: str | Path | None = None,
) -> dict:
    if snapshots_data is None:
        snapshots_data = load_manual_snapshots(snapshots_path) if snapshots_path else {"snapshots": []}
    if results_data is None:
        results_data = _load_json(results_path) if results_path else {"results": []}

    snapshot = _raw_snapshot(snapshots_data, team_a, team_b)
    normalized = find_manual_snapshot(snapshots_data, team_a, team_b)
    result_status = _real_result_status(results_data, team_a, team_b)

    missing_critical = []
    if _is_pending(normalized.get("venue")):
        missing_critical.append("venue")
    if _is_pending(normalized.get("kickoff_time_utc")):
        missing_critical.append("kickoff_time_utc")
    if _is_pending(normalized.get("odds_1x2")):
        missing_critical.append("odds_1x2")
    if _is_pending(normalized.get("over_under")):
        missing_critical.append("over_under")
    if _is_pending(normalized.get("probable_lineups")):
        missing_critical.append("probable_lineups")

    formations = snapshot.get("formations") or {
        team_a: normalized["probable_lineups"].get("team_a_formation"),
        team_b: normalized["probable_lineups"].get("team_b_formation"),
    }
    if _is_pending(formations):
        missing_critical.append("formations")
    if _is_pending(normalized.get("key_players")):
        missing_critical.append("player_ratings_key_players")
    if result_status != "final":
        missing_critical.append("result_status")

    missing_optional = []
    stats = snapshot.get("stats_snapshot") or normalized.get("stats_snapshot", {})
    if _is_pending(stats) or _is_pending(stats.get("data_status")):
        missing_optional.append("visible_stats")
    injuries = snapshot.get("injuries_or_absences")
    if _is_pending(injuries):
        missing_optional.append("injuries_or_absences")
    tactical_notes = snapshot.get("tactical_notes")
    if _is_pending(tactical_notes) or any(_is_pending(value) for value in (tactical_notes or {}).values()):
        missing_optional.append("complete_tactical_notes")
    if _is_pending(snapshot.get("market_notes")) and _is_pending(normalized.get("external_market_notes")):
        missing_optional.append("market_notes")

    partial_snapshot_ok = _has_partial_snapshot(snapshot)
    refresh_required = len(missing_critical) >= 3 and result_status != "final"
    if not refresh_required:
        priority = "low"
        recommended_action = "final_pick_can_run"
    elif partial_snapshot_ok:
        priority = "high"
        recommended_action = "final_pick_can_run_with_partial_snapshot_warning"
    else:
        priority = "urgent"
        recommended_action = "refresh_required_before_final_pick"

    return {
        "match": f"{team_a} vs {team_b}",
        "team_a": team_a,
        "team_b": team_b,
        "source_status": snapshot.get("source_status", "manual_research_required"),
        "venue": normalized.get("venue"),
        "kickoff_time_utc": normalized.get("kickoff_time_utc"),
        "research_refresh_required": refresh_required,
        "missing_critical_fields": missing_critical,
        "missing_optional_fields": missing_optional,
        "critical_missing_count": len(missing_critical),
        "optional_missing_count": len(missing_optional),
        "research_priority": priority,
        "recommended_action": recommended_action,
        "partial_snapshot_ok_for_final_pick": partial_snapshot_ok,
        "snapshot_sources": snapshot.get("primary_sources")
        or snapshot.get("sources_used")
        or normalized.get("sources_used", []),
        "cross_checked_with": snapshot.get("cross_checked_with", []),
        "result_status": result_status,
    }
