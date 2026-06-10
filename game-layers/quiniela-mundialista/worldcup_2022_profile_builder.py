from __future__ import annotations

import json
from pathlib import Path

from worldcup_2022_dataset_loader import PREMATCH_PATH, PROFILES_PATH


PENDING = "pending_verification"


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _team_cutoffs(matches: list[dict]) -> dict[str, str]:
    cutoffs: dict[str, str] = {}
    for match in matches:
        cutoff = match.get("cutoff_datetime", "pending_verification")
        for team in (match.get("team_a"), match.get("team_b")):
            if not team:
                continue
            current = cutoffs.get(team)
            if current is None or str(cutoff) < current:
                cutoffs[team] = cutoff
    return cutoffs


def _neutral_profile(team: str, cutoff_datetime: str) -> dict:
    return {
        "team": team,
        "profile_type": "minimal_safe_behavioral_profile",
        "cutoff_datetime": cutoff_datetime,
        "fifa_rank_pre_tournament": PENDING,
        "elo_pre_tournament": PENDING,
        "elo": 1500.0,
        "attack": 1.0,
        "defense": 1.0,
        "form": 1.0,
        "tactical_attack_adjustment": 1.0,
        "tactical_defense_adjustment": 1.0,
        "data_quality": "low",
        "source_status": "manual_snapshot_required",
        "sources": [],
        "leakage_risk": "low",
        "uses_neutral_defaults": True,
        "valid_for_calibration": False,
        "valid_for_behavioral_backtest": True,
        "not_valid_for_true_prediction_accuracy": True,
        "not_valid_for_model_accuracy_claims": True,
        "source_year": 2022,
        "notes": (
            "Neutral defaults are allowed only for structural behavioral testing, "
            "not for predictive accuracy claims."
        ),
    }


def build_2022_prematch_profiles(
    prematch_dataset_path: str | Path = PREMATCH_PATH,
    output_path: str | Path = PROFILES_PATH,
    mode: str = "safe_behavioral_defaults",
) -> dict:
    prematch = _load_json(prematch_dataset_path)
    matches = prematch.get("matches", [])
    cutoffs = _team_cutoffs(matches)
    teams_found = sorted(cutoffs)
    profiles = {}
    warnings = []

    if mode != "safe_behavioral_defaults":
        warnings.append(f"Unsupported mode {mode}; only pending profiles were emitted.")

    for team in teams_found:
        if mode == "safe_behavioral_defaults":
            profiles[team] = _neutral_profile(team, cutoffs[team])
        else:
            profiles[team] = {
                "team": team,
                "profile_type": "pending_verification",
                "cutoff_datetime": cutoffs[team],
                "fifa_rank_pre_tournament": PENDING,
                "elo_pre_tournament": PENDING,
                "attack": PENDING,
                "defense": PENDING,
                "form": PENDING,
                "tactical_attack_adjustment": 1.0,
                "tactical_defense_adjustment": 1.0,
                "data_quality": "low",
                "source_status": "pending_verification",
                "sources": [],
                "leakage_risk": "low",
                "uses_neutral_defaults": False,
                "valid_for_calibration": False,
                "valid_for_behavioral_backtest": False,
                "not_valid_for_true_prediction_accuracy": True,
            }

    output = {
        "dataset_name": "worldcup_2022_team_profiles_prematch",
        "tournament": "FIFA World Cup",
        "year": 2022,
        "generated_after_event": True,
        "valid_for_behavioral_backtest": True,
        "not_valid_for_true_prediction_accuracy": True,
        "profile_policy": {
            "no_2026_baseline": True,
            "no_results_as_input": True,
            "cutoff_required": True,
            "sources_required": True,
            "neutral_defaults_only_for_structural_behavioral_testing": True,
        },
        "mode": mode,
        "teams": profiles,
    }
    Path(output_path).write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "teams_found": len(teams_found),
        "profiles_created": len(profiles),
        "profiles_pending_verification": len(profiles),
        "uses_neutral_defaults": sum(1 for profile in profiles.values() if profile.get("uses_neutral_defaults")),
        "warnings": warnings
        + [
            "Neutral defaults are allowed only for structural behavioral testing, not for predictive accuracy claims."
        ],
        "output_path": str(Path(output_path)),
    }
