from __future__ import annotations

import json
from pathlib import Path

from worldcup_2026_fixture_guard import GUARD_REPORT_PATH, evaluate_group_stage_simulation_readiness
from worldcup_2026_fixture_snapshot_importer import (
    IMPORT_REPORT_PATH,
    SNAPSHOT_TEMPLATE_PATH,
    ensure_official_fixture_snapshot_template,
)
from worldcup_2026_fixture_validator import VALIDATION_REPORT_PATH, validate_worldcup_2026_fixture
from worldcup_2026_match_slot_engine import (
    FIXTURE_STATUS_PATH,
    GROUP_STAGE_FIXTURE_PATH,
    GROUP_STRUCTURE_PATH,
    MATCH_SLOTS_PATH,
    write_default_fixture_files,
)


def _load_json(path: str | Path) -> dict:
    data_path = Path(path)
    if not data_path.exists():
        return {}
    return json.loads(data_path.read_text(encoding="utf-8"))


def ensure_worldcup_2026_fixture_files() -> dict:
    required = [
        GROUP_STRUCTURE_PATH,
        FIXTURE_STATUS_PATH,
        GROUP_STAGE_FIXTURE_PATH,
        MATCH_SLOTS_PATH,
    ]
    if not all(path.exists() for path in required):
        write_default_fixture_files()
    ensure_official_fixture_snapshot_template(SNAPSHOT_TEMPLATE_PATH)
    validation = validate_worldcup_2026_fixture(write_report=True)
    guard = evaluate_group_stage_simulation_readiness()
    return {
        "files_ready": all(path.exists() for path in required) and VALIDATION_REPORT_PATH.exists(),
        "validation": validation,
        "guard": guard,
    }


def load_worldcup_2026_fixture() -> dict:
    ensure_worldcup_2026_fixture_files()
    group_structure = _load_json(GROUP_STRUCTURE_PATH)
    fixture_status = _load_json(FIXTURE_STATUS_PATH)
    fixture = _load_json(GROUP_STAGE_FIXTURE_PATH)
    slots = _load_json(MATCH_SLOTS_PATH)
    validation = _load_json(VALIDATION_REPORT_PATH)
    snapshot_template = _load_json(SNAPSHOT_TEMPLATE_PATH)
    import_report = _load_json(IMPORT_REPORT_PATH)
    guard_report = _load_json(GUARD_REPORT_PATH)

    fixture_type = fixture.get("fixture_type", "missing")
    confirmed = fixture.get("matches_confirmed", 0)
    pending = fixture.get("matches_pending", 0)
    total = fixture.get("total_matches", len(slots.get("matches", [])))
    structural_placeholder = fixture_type == "structural_placeholder"
    fixture_ready = bool(
        validation.get("audit_status") in ("cleared", "cleared_placeholder")
        and confirmed == total
        and total == 72
        and not structural_placeholder
    )
    fixture_partial = bool(0 < confirmed < total)

    warnings = []
    warnings.extend(fixture.get("warnings", []))
    warnings.extend(validation.get("warnings", []))
    if structural_placeholder:
        warnings.append("Fixture loader detected placeholder fixture; simulation must wait for official draw.")

    return {
        "fixture_ready": fixture_ready,
        "fixture_partial": fixture_partial,
        "structural_placeholder": structural_placeholder,
        "groups_loaded": len(group_structure.get("groups", [])),
        "slots_loaded": len(slots.get("matches", [])),
        "confirmed_matches": confirmed,
        "pending_matches": pending,
        "fixture_type": fixture_type,
        "official_status": fixture.get("official_status", "missing"),
        "validation_status": validation.get("audit_status", "missing"),
        "fixture_import_ready": import_report.get("import_status") in ("dry_run_ok", "imported"),
        "fixture_guard_status": guard_report.get("guard_status", "missing"),
        "ready_for_full_group_simulation": guard_report.get(
            "ready_for_full_group_simulation",
            validation.get("ready_for_full_group_simulation", False),
        ),
        "ready_for_partial_simulation": guard_report.get("ready_for_partial_simulation", False),
        "group_structure": group_structure,
        "fixture_status": fixture_status,
        "fixture": fixture,
        "slots": slots,
        "snapshot_template": snapshot_template,
        "import_report": import_report,
        "guard_report": guard_report,
        "validation_report": validation,
        "warnings": sorted(set(warnings)),
    }
