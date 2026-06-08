from __future__ import annotations

from datetime import datetime, timezone


PENDING_VALUES = {
    None,
    "",
    "pending_manual_input",
    "pending_real_data",
    "pending_real_result",
    "manual_research_required",
}


def _parse_utc(value) -> datetime | None:
    if value in PENDING_VALUES:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    if text.endswith(" UTC"):
        text = text[:-4] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def build_match_alarm(
    snapshot_or_match: dict,
    current_time_utc: str | datetime | None = None,
    refresh_window_minutes: int = 60,
) -> dict:
    kickoff_raw = snapshot_or_match.get("kickoff_time_utc")
    kickoff = _parse_utc(kickoff_raw)
    if kickoff is None:
        return {
            "kickoff_time_utc": kickoff_raw or "pending_manual_input",
            "current_time_utc": "pending_runtime_clock",
            "minutes_to_kickoff": "unknown",
            "refresh_window_minutes": refresh_window_minutes,
            "final_refresh_due": False,
            "match_status": "unknown",
            "alarm_status": "needs_kickoff_time",
            "recommended_action": "needs_kickoff_time",
        }

    if isinstance(current_time_utc, datetime):
        current = current_time_utc.astimezone(timezone.utc)
    else:
        current = _parse_utc(current_time_utc) if current_time_utc else datetime.now(timezone.utc)

    minutes_to_kickoff = int((kickoff - current).total_seconds() // 60)
    if minutes_to_kickoff > refresh_window_minutes:
        match_status = "upcoming"
    elif 0 <= minutes_to_kickoff <= refresh_window_minutes:
        match_status = "near_kickoff"
    elif -130 <= minutes_to_kickoff < 0:
        match_status = "live"
    else:
        match_status = "final"

    final_refresh_due = 0 <= minutes_to_kickoff <= refresh_window_minutes
    alarm_status = "final_refresh_due" if final_refresh_due else match_status
    recommended_action = (
        "refresh_before_final_pick"
        if final_refresh_due
        else "monitor_result_status" if match_status in {"live", "final"} else "no_alarm"
    )

    return {
        "kickoff_time_utc": kickoff.isoformat().replace("+00:00", "Z"),
        "current_time_utc": current.isoformat().replace("+00:00", "Z"),
        "minutes_to_kickoff": minutes_to_kickoff,
        "refresh_window_minutes": refresh_window_minutes,
        "final_refresh_due": final_refresh_due,
        "match_status": match_status,
        "alarm_status": alarm_status,
        "recommended_action": recommended_action,
    }
