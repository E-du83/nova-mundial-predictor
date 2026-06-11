from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from worldcup_2026_match_slot_engine import GROUPS, GROUP_STAGE_MATCHES


LAYER_ROOT = Path(__file__).resolve().parent
DATA_ROOT = LAYER_ROOT / "data"

INTAKE_PACKAGE_PATH = DATA_ROOT / "chatgpt_research_intake_package.json"
INTAKE_VALIDATION_REPORT_PATH = DATA_ROOT / "chatgpt_research_intake_validation_report.json"
MANUAL_FIXTURE_SNAPSHOT_PATH = DATA_ROOT / "worldcup_2026_official_fixture_snapshot_manual.json"
RESEARCH_BATCH_PATH = DATA_ROOT / "worldcup_2026_research_snapshots_batch.json"

PENDING_VALUES = {
    "",
    None,
    "pending_group_draw",
    "pending_manual_input",
    "pending_official_fixture",
    "pending_real_data",
    "pending_verification",
    "manual_review_required",
    "manual_snapshot_required",
    "not_available",
    "not_available_free",
}


def _now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _load_json(path: str | Path) -> dict:
    data_path = Path(path)
    if not data_path.exists():
        return {}
    return json.loads(data_path.read_text(encoding="utf-8"))


def _write_json_if_changed(path: str | Path, data: dict) -> None:
    data_path = Path(path)
    data_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if data_path.exists() and data_path.read_text(encoding="utf-8") == text:
        return
    data_path.write_text(text, encoding="utf-8")


def _is_pending(value) -> bool:
    if value in PENDING_VALUES:
        return True
    return isinstance(value, str) and value.strip().startswith("pending_")


def _valid_utc(value) -> bool:
    if _is_pending(value):
        return False
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return value.endswith("Z") or "+00:00" in value


def build_chatgpt_research_intake_template() -> dict:
    return {
        "package_name": "chatgpt_worldcup_2026_research_intake",
        "created_by": "ChatGPT",
        "source_mode": "chatgpt_curated_public_sources",
        "captured_at": "pending_manual_input",
        "source_policy": {
            "official_fixture_source_required": True,
            "public_sources_only": True,
            "no_scraping_by_codex": True,
            "no_unverified_claims": True,
        },
        "fixture": {
            "source": "FIFA official schedule",
            "source_url": "pending_manual_input",
            "source_status": "pending_manual_input",
            "matches": [],
        },
        "groups": {},
        "team_research": {},
        "match_research": {},
        "market_research": {},
        "missing_data_policy": {
            "confirmed_lineups": "pending_verification_allowed",
            "last_minute_injuries": "pending_verification_allowed",
            "odds": "optional_if_not_available",
            "weather": "optional_if_not_available",
        },
        "warnings": [
            "Template only. Fill fixture.matches with 72 official group-stage matches before running picks.",
        ],
    }


def ensure_chatgpt_research_intake_template(path: str | Path = INTAKE_PACKAGE_PATH) -> dict:
    template = build_chatgpt_research_intake_template()
    data_path = Path(path)
    if not data_path.exists():
        _write_json_if_changed(data_path, template)
        return template
    return _load_json(data_path)


def load_chatgpt_research_package(path: str | Path = INTAKE_PACKAGE_PATH) -> dict:
    package = _load_json(path)
    if not package:
        package = build_chatgpt_research_intake_template()
    return package


def _match_id_for(match: dict, group_counts: dict[str, int]) -> str:
    explicit = match.get("match_id") or match.get("slot_id")
    if explicit:
        return explicit
    group = match.get("group", "pending_verification")
    group_counts[group] = group_counts.get(group, 0) + 1
    return f"WG-{group}-{group_counts[group]:02d}"


def validate_chatgpt_research_package(package: dict) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    missing_data: list[str] = []
    fixture = package.get("fixture", {}) if isinstance(package, dict) else {}
    matches = fixture.get("matches", []) if isinstance(fixture, dict) else []
    groups = package.get("groups", {}) if isinstance(package, dict) else {}
    team_research = package.get("team_research", {}) if isinstance(package, dict) else {}
    match_research = package.get("match_research", {}) if isinstance(package, dict) else {}
    market_research = package.get("market_research", {}) if isinstance(package, dict) else {}
    source_status = fixture.get("source_status", "missing")
    source_name = fixture.get("source")
    source_url = fixture.get("source_url")

    if not isinstance(package, dict) or not package:
        return {
            "validation_status": "missing_or_template",
            "fixture_ready": False,
            "research_ready": False,
            "matches_detected": 0,
            "groups_detected": 0,
            "teams_detected": 0,
            "errors": ["chatgpt research intake package is missing or unreadable"],
            "warnings": [],
            "missing_data": ["falta llenar fixture.matches con 72 partidos"],
        }

    if not isinstance(matches, list):
        errors.append("fixture.matches must be a list")
        matches = []

    teams = set()
    group_set = set()
    seen_ids = set()
    group_counts: dict[str, int] = {}
    placeholder_matches = []
    invalid_match_count = 0

    for index, match in enumerate(matches, start=1):
        if not isinstance(match, dict):
            invalid_match_count += 1
            errors.append(f"fixture.matches[{index}] must be an object")
            continue
        match_id = _match_id_for(match, group_counts)
        if match_id in seen_ids:
            errors.append(f"duplicate match_id or slot_id: {match_id}")
        seen_ids.add(match_id)
        group = match.get("group")
        if group in GROUPS:
            group_set.add(group)
        else:
            invalid_match_count += 1
            errors.append(f"{match_id}: invalid or missing group")
        if _is_pending(match.get("matchday")):
            missing_data.append(f"{match_id}: matchday")
        for field in ("team_a", "team_b"):
            value = match.get(field)
            if _is_pending(value):
                placeholder_matches.append(match_id)
                missing_data.append(f"{match_id}: {field}")
            else:
                teams.add(str(value))

    if not source_name:
        missing_data.append("fixture.source")
    if _is_pending(source_url):
        warnings.append("fixture.source_url is pending; keep source name explicit until URL is supplied")

    if not matches:
        missing_data.append("falta llenar fixture.matches con 72 partidos")
    elif len(matches) != GROUP_STAGE_MATCHES:
        missing_data.append(f"fixture.matches must contain 72 matches; found {len(matches)}")

    if source_status == "official_verified":
        if len(matches) != GROUP_STAGE_MATCHES:
            errors.append("official_verified fixture requires exactly 72 matches")
        if placeholder_matches:
            errors.append("official_verified fixture cannot contain pending teams")
        if invalid_match_count:
            errors.append("official_verified fixture contains invalid match records")
    elif matches:
        warnings.append("fixture is not official_verified; Codex will not import it as official")

    research_ready = bool(team_research or match_research or market_research)
    fixture_ready = bool(source_status == "official_verified" and len(matches) == GROUP_STAGE_MATCHES and not errors)
    if not matches:
        validation_status = "missing_or_template"
    elif errors:
        validation_status = "invalid"
    elif fixture_ready:
        validation_status = "valid"
    else:
        validation_status = "partial"

    if not research_ready:
        warnings.append("research is empty or partial; this does not block fixture import")

    return {
        "validation_status": validation_status,
        "fixture_ready": fixture_ready,
        "research_ready": research_ready,
        "matches_detected": len(matches),
        "groups_detected": len(group_set) or (len(groups) if isinstance(groups, dict) else 0),
        "teams_detected": len(teams),
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings + list(package.get("warnings", [])))),
        "missing_data": sorted(set(missing_data)),
    }


def _fixture_match_to_snapshot(match: dict, fixture: dict, validation: dict, group_counts: dict[str, int]) -> dict:
    match_id = _match_id_for(match, group_counts)
    warnings = []
    kickoff_utc = match.get("kickoff_utc")
    if _valid_utc(kickoff_utc):
        normalized_kickoff = kickoff_utc
    elif match.get("kickoff_local"):
        normalized_kickoff = "pending_verification"
        warnings.append("kickoff_local supplied without kickoff_utc; kickoff_utc kept pending_verification")
    else:
        normalized_kickoff = "pending_verification"
        warnings.append("kickoff_utc missing; kept pending_verification")

    venue = match.get("venue") or "pending_verification"
    if _is_pending(venue):
        warnings.append("venue missing or pending; kept pending_verification")

    return {
        "slot_id": match_id,
        "phase": "group_stage",
        "group": match.get("group", "pending_verification"),
        "matchday": match.get("matchday", "pending_verification"),
        "team_a": match.get("team_a", "pending_verification"),
        "team_b": match.get("team_b", "pending_verification"),
        "kickoff_utc": normalized_kickoff,
        "venue": venue,
        "city": match.get("city", "pending_verification"),
        "country": match.get("country", "pending_verification"),
        "source": match.get("source", fixture.get("source", "FIFA official schedule")),
        "source_status": "official_confirmed" if validation.get("fixture_ready") else "pending_manual_input",
        "verification_status": "official_confirmed" if validation.get("fixture_ready") else "pending_verification",
        "warnings": warnings,
    }


def build_manual_fixture_snapshot(package: dict, validation: dict) -> dict:
    fixture = package.get("fixture", {})
    group_counts: dict[str, int] = {}
    matches = [
        _fixture_match_to_snapshot(match, fixture, validation, group_counts)
        for match in fixture.get("matches", [])
        if isinstance(match, dict)
    ]
    return {
        "snapshot_name": "worldcup_2026_official_fixture_snapshot_manual",
        "tournament": "FIFA World Cup 2026",
        "snapshot_type": "chatgpt_research_intake_fixture_snapshot",
        "source_status": "official_confirmed" if validation.get("fixture_ready") else "pending_manual_input",
        "source": fixture.get("source", "FIFA official schedule"),
        "source_url": fixture.get("source_url", "pending_manual_input"),
        "captured_at": package.get("captured_at", "pending_manual_input"),
        "captured_by": package.get("created_by", "ChatGPT"),
        "timezone_policy": "kickoff_utc_required_when_available",
        "total_group_stage_matches_expected": GROUP_STAGE_MATCHES,
        "groups_expected": len(GROUPS),
        "teams_per_group_expected": 4,
        "matches": matches,
        "warnings": sorted(
            set(
                validation.get("warnings", [])
                + [
                    warning
                    for item in matches
                    for warning in item.get("warnings", [])
                ]
            )
        ),
    }


def build_research_snapshots_batch(package: dict, validation: dict) -> dict:
    team_research = package.get("team_research", {})
    match_research = package.get("match_research", {})
    market_research = package.get("market_research", {})
    research_present = bool(team_research or match_research or market_research)
    market_complete = bool(market_research) and not any(_is_pending(value) for value in market_research.values())
    tactical_ready = False
    return {
        "data_status": "chatgpt_research_snapshots_batch_v1",
        "generated_at": _now(),
        "source": package.get("source_mode", "chatgpt_curated_public_sources"),
        "captured_at": package.get("captured_at", "pending_manual_input"),
        "captured_by": package.get("created_by", "ChatGPT"),
        "confidence": "partial" if validation.get("validation_status") in ("partial", "missing_or_template") else "reviewed",
        "fixture_validation_status": validation.get("validation_status", "missing_or_template"),
        "valid_for_prediction_context": bool(validation.get("validation_status") != "invalid" and research_present),
        "valid_for_tactical_bridge": tactical_ready,
        "valid_for_market_weighting": market_complete,
        "team_research": team_research,
        "match_research": match_research,
        "market_research": market_research,
        "missing_data": validation.get("missing_data", []),
        "warnings": validation.get("warnings", []),
    }


def split_chatgpt_package_to_fixture_and_research(package: dict) -> dict:
    validation = validate_chatgpt_research_package(package)
    return {
        "validation": validation,
        "fixture_snapshot": build_manual_fixture_snapshot(package, validation),
        "research_batch": build_research_snapshots_batch(package, validation),
    }


def write_intake_artifacts(package: dict, validation: dict, split: dict) -> dict:
    _write_json_if_changed(INTAKE_VALIDATION_REPORT_PATH, validation)
    _write_json_if_changed(MANUAL_FIXTURE_SNAPSHOT_PATH, split["fixture_snapshot"])
    _write_json_if_changed(RESEARCH_BATCH_PATH, split["research_batch"])
    return {
        "validation_report": str(INTAKE_VALIDATION_REPORT_PATH),
        "fixture_snapshot": str(MANUAL_FIXTURE_SNAPSHOT_PATH),
        "research_batch": str(RESEARCH_BATCH_PATH),
    }
