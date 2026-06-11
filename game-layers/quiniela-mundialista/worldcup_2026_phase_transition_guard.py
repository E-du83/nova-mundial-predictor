from __future__ import annotations

import json
from pathlib import Path


LAYER_ROOT = Path(__file__).resolve().parent
TRANSITION_GUARD_REPORT_PATH = LAYER_ROOT / "data" / "worldcup_2026_phase_transition_guard_report.json"


def _write_json_if_changed(path: Path, data: dict) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def evaluate_phase_transition_readiness(
    from_phase: str,
    to_phase: str,
    predictions_frozen: bool,
    results_status: dict,
    standings_status: dict,
    bracket_guard_status: dict | None = None,
    write_report: bool = False,
) -> dict:
    bracket_guard_status = bracket_guard_status or {}
    results_complete = bool(results_status.get("results_complete", False))
    standings_ready = standings_status.get("standings_status") == "ready"
    bracket_ready = bracket_guard_status.get("bracket_guard_status") == "ready_for_bracket_build"
    blocked = []
    warnings = []
    if not predictions_frozen:
        blocked.append("previous phase predictions are not frozen")
    if not results_complete:
        blocked.append("real results are not complete")
    if not standings_ready:
        blocked.append(f"standings not ready: {standings_status.get('standings_status', 'missing')}")
    if to_phase in ("round_of_32", "knockout") and not bracket_ready:
        blocked.append(
            f"bracket not ready: {bracket_guard_status.get('bracket_guard_status', 'missing')}"
        )
    if blocked:
        transition_status = "blocked"
    elif warnings:
        transition_status = "partial_ready"
    else:
        transition_status = "ready"
    report = {
        "transition_status": transition_status,
        "from_phase": from_phase,
        "to_phase": to_phase,
        "predictions_frozen": predictions_frozen,
        "results_complete": results_complete,
        "standings_ready": standings_ready,
        "bracket_ready": bracket_ready,
        "blocked_reasons": blocked,
        "warnings": warnings,
        "next_steps": [
            "Freeze previous phase predictions after real picks exist.",
            "Load verified real results with source_status, captured_at and review_status.",
            "Build standings only from final results.",
            "Re-run bracket guard before preparing the next phase.",
        ],
    }
    if write_report:
        _write_json_if_changed(TRANSITION_GUARD_REPORT_PATH, report)
    return report
