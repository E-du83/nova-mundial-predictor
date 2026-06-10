from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from worldcup_2022_dataset_loader import PROFILE_AUDIT_PATH, PROFILES_PATH


RESULT_FIELDS = {
    "goals_a_90",
    "goals_b_90",
    "goals_a_final",
    "goals_b_final",
    "real_score",
    "winner_90",
    "winner_final",
    "first_goal_team",
    "first_goal_minute",
    "goals_timeline",
    "btts",
}

FORBIDDEN_TEXT = (
    "champion",
    "campeon",
    "finalist",
    "finalista",
    "eliminated",
    "eliminado",
    "post_match",
    "post tournament",
    "surprise",
    "sorpresa",
    "worldcup_2026_real_teams_baseline",
    "2026 baseline",
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _text_blob(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(f"{key} {_text_blob(item)}" for key, item in value.items())
    if isinstance(value, list):
        return " ".join(_text_blob(item) for item in value)
    return str(value)


def validate_2022_profiles(
    profiles_path: str | Path = PROFILES_PATH,
    audit_path: str | Path = PROFILE_AUDIT_PATH,
    write_report: bool = True,
) -> dict:
    profiles_data = _load_json(profiles_path)
    teams = profiles_data.get("teams", {})
    source_warnings = []
    cutoff_warnings = []
    leakage_warnings = []
    blocked_profiles = []
    neutral_defaults = []
    verified = []
    pending = []

    for team, profile in teams.items():
        profile_warnings = []
        result_fields = sorted(field for field in RESULT_FIELDS if field in profile)
        if result_fields:
            profile_warnings.append(f"{team}: result fields inside profile: {', '.join(result_fields)}")
        searchable = _text_blob(profile).lower()
        for forbidden in FORBIDDEN_TEXT:
            if forbidden in searchable:
                profile_warnings.append(f"{team}: forbidden leakage marker '{forbidden}'")
        source_year = profile.get("source_year")
        if isinstance(source_year, int) and source_year > 2022:
            profile_warnings.append(f"{team}: source_year > 2022")
        if profile.get("use_2026_baseline") is True:
            profile_warnings.append(f"{team}: use_2026_baseline=true")
        if not profile.get("cutoff_datetime"):
            cutoff_warnings.append(f"{team}: missing cutoff_datetime")
        if not profile.get("source_status"):
            source_warnings.append(f"{team}: missing source_status")
        if not profile.get("data_quality"):
            source_warnings.append(f"{team}: missing data_quality")
        for field in ("attack", "defense", "form"):
            if field not in profile:
                source_warnings.append(f"{team}: missing {field}")
        if profile.get("uses_neutral_defaults") and profile.get("profile_type") != "minimal_safe_behavioral_profile":
            profile_warnings.append(f"{team}: neutral defaults not marked as minimal_safe_behavioral_profile")
        if profile.get("uses_neutral_defaults"):
            neutral_defaults.append(team)
        if profile.get("source_status") == "verified_public_source":
            verified.append(team)
        else:
            pending.append(team)
        if profile_warnings:
            leakage_warnings.extend(profile_warnings)
            blocked_profiles.append(team)

    audit_status = "blocked" if blocked_profiles else "warning" if neutral_defaults or pending else "verified"
    audit = {
        "teams_checked": len(teams),
        "profiles_verified": len(verified),
        "profiles_pending_verification": len(pending),
        "profiles_using_neutral_defaults": len(neutral_defaults),
        "profiles_blocked": len(set(blocked_profiles)),
        "source_warnings": source_warnings,
        "cutoff_warnings": cutoff_warnings,
        "leakage_warnings": leakage_warnings,
        "generated_after_event_warning": (
            "Profiles generated after event are valid for behavioral flow only, not true prediction accuracy."
        ),
        "neutral_defaults_warning": (
            "Neutral defaults are allowed only for structural behavioral testing, not for predictive accuracy claims."
        ),
        "blocked_profiles": sorted(set(blocked_profiles)),
        "neutral_default_teams": neutral_defaults,
        "generated_at": _now(),
        "audit_status": audit_status,
    }
    if write_report:
        Path(audit_path).write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return audit
