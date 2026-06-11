from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from research_snapshot_validator import validate_research_snapshot


LAYER_ROOT = Path(__file__).resolve().parent
DATA_ROOT = LAYER_ROOT / "data"
TEMPLATE_PATH = DATA_ROOT / "research_snapshot_template.json"
REPORT_PATH = DATA_ROOT / "research_snapshot_validation_report.json"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_synthetic_valid_snapshot() -> dict:
    team_a_players = [f"Netherlands Player {index}" for index in range(1, 12)]
    team_b_players = [f"Uzbekistan Player {index}" for index in range(1, 12)]
    return {
        "snapshot_id": "synthetic_test_data_netherlands_uzbekistan",
        "match": "Netherlands vs Uzbekistan",
        "team_a": "Netherlands",
        "team_b": "Uzbekistan",
        "competition": "International Friendly",
        "phase": "friendly",
        "kickoff_utc": "2026-06-10T19:00:00Z",
        "captured_at": "2026-06-10T12:00:00Z",
        "captured_by": "synthetic_test_data",
        "snapshot_type": "manual_research",
        "source_status": "manual_input",
        "overall_confidence": "medium",
        "sources": [
            {"name": "Synthetic official lineup source", "url": "not_available", "source_status": "synthetic_test_data"},
            {"name": "Synthetic market source", "url": "not_available", "source_status": "synthetic_test_data"}
        ],
        "odds_1x2": {
            "home": 1.85,
            "draw": 3.45,
            "away": 4.2,
            "source": "synthetic_test_data",
            "captured_at": "2026-06-10T12:00:00Z",
            "confidence": "medium"
        },
        "over_under": {"line": 2.5, "over": 1.95, "under": 1.85, "source": "synthetic_test_data"},
        "probable_lineups": {
            "team_a": team_a_players,
            "team_b": team_b_players,
            "source": "synthetic_test_data",
            "confidence": "medium"
        },
        "formations": {
            "team_a": "4-3-3",
            "team_b": "5-4-1",
            "source": "synthetic_test_data",
            "confidence": "medium"
        },
        "injuries_or_absences": {
            "team_a": [{"player": "Synthetic A Absence", "impact": "medium", "source": "synthetic_test_data"}],
            "team_b": []
        },
        "key_players": {
            "team_a": ["Netherlands Player 9", "Netherlands Player 10"],
            "team_b": ["Uzbekistan Player 9"]
        },
        "player_ratings": {
            "team_a": {player: 82 + (index % 5) for index, player in enumerate(team_a_players)},
            "team_b": {player: 74 + (index % 5) for index, player in enumerate(team_b_players)},
            "source": "synthetic_test_data",
            "confidence": "medium"
        },
        "form_snapshot": {
            "team_a": {"form_multiplier": 1.03, "source": "synthetic_test_data"},
            "team_b": {"form_multiplier": 0.97, "source": "synthetic_test_data"}
        },
        "stats_snapshot": {
            "btts": "medium",
            "over_2_5": "medium",
            "clean_sheet": "low",
            "h2h": "not_available",
            "corners": "not_available",
            "cards": "not_available"
        },
        "tactical_notes": {
            "team_a": "Synthetic high press note.",
            "team_b": "Synthetic compact block note.",
            "matchup": "Synthetic matchup note."
        },
        "data_quality_flags": ["synthetic_test_data"],
        "missing_data": [],
        "warnings": ["Synthetic data for validation only. Do not use for picks."],
        "valid_for_tactical_bridge": True,
        "valid_for_market_weighting": True,
        "valid_for_prediction_context": True
    }


def _write_json_if_changed(path: Path, data: dict) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        comparable_existing = dict(existing)
        comparable_data = dict(data)
        comparable_existing.pop("generated_at", None)
        comparable_data.pop("generated_at", None)
        if comparable_existing == comparable_data:
            return
    path.write_text(text, encoding="utf-8")


def main() -> None:
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    template_validation = validate_research_snapshot(template)
    synthetic = build_synthetic_valid_snapshot()
    synthetic_validation = validate_research_snapshot(synthetic)
    report = {
        "data_status": "research_snapshot_validation_report_v1",
        "generated_at": _now(),
        "template_validation_status": template_validation["validation_status"],
        "synthetic_validation_status": synthetic_validation["validation_status"],
        "valid_for_tactical_bridge": synthetic_validation["valid_for_tactical_bridge"],
        "valid_for_market_weighting": synthetic_validation["valid_for_market_weighting"],
        "valid_for_prediction_context": synthetic_validation["valid_for_prediction_context"],
        "template_missing_data": template_validation["missing_data"],
        "synthetic_errors": synthetic_validation["errors"],
        "warnings": ["Synthetic snapshot is validation-only and was not saved as a real snapshot."],
    }
    _write_json_if_changed(REPORT_PATH, report)

    print("NOVA RESEARCH SNAPSHOT VALIDATION DEMO")
    print(f"- template validation_status: {template_validation['validation_status']}")
    print(f"- synthetic validation_status: {synthetic_validation['validation_status']}")
    print(f"- valid_for_tactical_bridge: {str(synthetic_validation['valid_for_tactical_bridge']).lower()}")
    print(f"- valid_for_market_weighting: {str(synthetic_validation['valid_for_market_weighting']).lower()}")
    print(f"- valid_for_prediction_context: {str(synthetic_validation['valid_for_prediction_context']).lower()}")
    print("- synthetic saved to real data: no")
    print(f"- report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
