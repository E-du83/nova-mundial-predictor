from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from phase_freeze_engine import freeze_phase_predictions
from worldcup_2026_bracket_guard import evaluate_bracket_readiness
from worldcup_2026_phase_transition_guard import evaluate_phase_transition_readiness
from worldcup_2026_results_loader import (
    RESULTS_TEMPLATE_PATH,
    ensure_results_template,
    validate_worldcup_2026_results,
)
from worldcup_2026_standings_engine import build_group_standings


LAYER_ROOT = Path(__file__).resolve().parent
DATA_ROOT = LAYER_ROOT / "data"
PREDICTION_HISTORY_PATH = DATA_ROOT / "prediction_history.json"
FREEZE_LOG_PATH = DATA_ROOT / "worldcup_2026_phase_freeze_log.json"
UPDATE_REPORT_PATH = DATA_ROOT / "worldcup_2026_inter_phase_update_report.json"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _update_status(transition_guard: dict, dry_run: bool) -> str:
    if transition_guard["transition_status"] == "ready":
        return "dry_run_ok" if dry_run else "ready"
    if transition_guard["transition_status"] == "partial_ready":
        return "partial_ready"
    return "blocked"


def run_inter_phase_update(
    from_phase="group_stage",
    to_phase="round_of_32",
    dry_run=True,
    write_report=False,
) -> dict:
    freeze_summary = freeze_phase_predictions(
        from_phase,
        str(PREDICTION_HISTORY_PATH),
        str(FREEZE_LOG_PATH),
        dry_run=True,
    )
    results = ensure_results_template(RESULTS_TEMPLATE_PATH)
    results_summary = validate_worldcup_2026_results(results)
    standings_summary = build_group_standings(results, write=False)
    bracket_guard = evaluate_bracket_readiness(group_standings_path=standings_summary)
    transition_guard = evaluate_phase_transition_readiness(
        from_phase,
        to_phase,
        predictions_frozen=freeze_summary["freeze_status"] == "frozen",
        results_status=results_summary,
        standings_status=standings_summary,
        bracket_guard_status=bracket_guard,
        write_report=write_report,
    )
    report = {
        "data_status": "worldcup_2026_inter_phase_update_v1",
        "generated_at": _now(),
        "update_status": _update_status(transition_guard, dry_run),
        "from_phase": from_phase,
        "to_phase": to_phase,
        "dry_run": dry_run,
        "freeze_summary": freeze_summary,
        "results_summary": results_summary,
        "standings_summary": {
            "standings_status": standings_summary.get("standings_status"),
            "groups_calculated": standings_summary.get("groups_calculated", 0),
            "warnings": standings_summary.get("warnings", []),
        },
        "transition_guard": transition_guard,
        "recalibration_applied": False,
        "baseline_modified": False,
        "prediction_history_modified": False,
        "warnings": sorted(
            set(
                freeze_summary.get("warnings", [])
                + results_summary.get("warnings", [])
                + standings_summary.get("warnings", [])
                + transition_guard.get("warnings", [])
            )
        ),
        "next_steps": transition_guard.get("next_steps", []),
    }
    if write_report:
        _write_json_if_changed(UPDATE_REPORT_PATH, report)
    return report
