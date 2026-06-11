from __future__ import annotations

from copy import deepcopy


PENDING = "pending_manual_input"
PENDING_VERIFICATION = "pending_verification"
NOT_AVAILABLE = "not_available"

CONFIDENCE_VALUES = {"high", "medium", "low", "insufficient", PENDING_VERIFICATION}
SOURCE_STATUS_VALUES = {
    "manual_input",
    "ai_assisted",
    "official_verified",
    PENDING_VERIFICATION,
}
SNAPSHOT_TYPE_VALUES = {
    "manual_research",
    "ai_assisted_research",
    "official_snapshot",
}

REQUIRED_TOP_LEVEL_FIELDS = [
    "snapshot_id",
    "match",
    "team_a",
    "team_b",
    "competition",
    "phase",
    "kickoff_utc",
    "captured_at",
    "captured_by",
    "snapshot_type",
    "source_status",
    "overall_confidence",
    "sources",
    "odds_1x2",
    "over_under",
    "probable_lineups",
    "formations",
    "injuries_or_absences",
    "key_players",
    "player_ratings",
    "form_snapshot",
    "stats_snapshot",
    "tactical_notes",
    "data_quality_flags",
    "missing_data",
    "warnings",
    "valid_for_tactical_bridge",
    "valid_for_market_weighting",
    "valid_for_prediction_context",
]

RESEARCH_SNAPSHOT_SCHEMA = {
    "snapshot_id": "",
    "match": "",
    "team_a": "",
    "team_b": "",
    "competition": "",
    "phase": "",
    "kickoff_utc": "",
    "captured_at": "",
    "captured_by": "",
    "snapshot_type": "manual_research",
    "source_status": PENDING_VERIFICATION,
    "overall_confidence": "insufficient",
    "sources": [],
    "odds_1x2": {
        "home": "",
        "draw": "",
        "away": "",
        "source": "",
        "captured_at": "",
        "confidence": "",
    },
    "over_under": {},
    "probable_lineups": {
        "team_a": [],
        "team_b": [],
        "source": "",
        "confidence": "",
    },
    "formations": {
        "team_a": "",
        "team_b": "",
        "source": "",
        "confidence": "",
    },
    "injuries_or_absences": {
        "team_a": [],
        "team_b": [],
    },
    "key_players": {
        "team_a": [],
        "team_b": [],
    },
    "player_ratings": {
        "team_a": {},
        "team_b": {},
        "source": "",
        "confidence": "",
    },
    "form_snapshot": {
        "team_a": {},
        "team_b": {},
    },
    "stats_snapshot": {
        "btts": "",
        "over_2_5": "",
        "clean_sheet": "",
        "h2h": "",
        "corners": "",
        "cards": "",
    },
    "tactical_notes": {
        "team_a": "",
        "team_b": "",
        "matchup": "",
    },
    "data_quality_flags": [],
    "missing_data": [],
    "warnings": [],
    "valid_for_tactical_bridge": False,
    "valid_for_market_weighting": False,
    "valid_for_prediction_context": False,
}


def build_research_snapshot_template() -> dict:
    template = deepcopy(RESEARCH_SNAPSHOT_SCHEMA)
    template.update(
        {
            "snapshot_id": PENDING,
            "match": PENDING,
            "team_a": PENDING,
            "team_b": PENDING,
            "competition": PENDING,
            "phase": PENDING,
            "kickoff_utc": PENDING,
            "captured_at": PENDING,
            "captured_by": PENDING,
            "sources": [],
            "data_quality_flags": ["template_pending_manual_input"],
            "missing_data": REQUIRED_TOP_LEVEL_FIELDS,
            "warnings": [
                "Template only. Fill manually or with reviewed AI-assisted research before use.",
            ],
        }
    )
    for section in ("odds_1x2", "formations", "probable_lineups", "player_ratings"):
        for key in template[section]:
            if key not in ("team_a", "team_b"):
                template[section][key] = PENDING
    template["stats_snapshot"] = {key: PENDING for key in template["stats_snapshot"]}
    template["tactical_notes"] = {key: PENDING for key in template["tactical_notes"]}
    return template
