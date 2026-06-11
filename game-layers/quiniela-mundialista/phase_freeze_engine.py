from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from prediction_history_engine import load_prediction_history


PENDING_VALUES = {
    None,
    "",
    "pending_real_data",
    "pending_real_result",
    "pending_group_draw",
    "pending_official_fixture",
    "manual_snapshot_required",
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_json_if_changed(path: Path, data: dict) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _is_placeholder_prediction(entry: dict) -> bool:
    values = [
        entry.get("match"),
        entry.get("match_id"),
        entry.get("pick_principal"),
        entry.get("marcador_recomendado"),
        entry.get("prediction_previous"),
    ]
    return any(value in PENDING_VALUES or str(value).startswith("pending_") for value in values)


def _phase_for_entry(entry: dict) -> str:
    phase = entry.get("phase") or entry.get("competition_phase")
    if phase:
        return str(phase)
    match_id = str(entry.get("match_id", ""))
    if match_id.startswith("WG-"):
        return "group_stage"
    return "unknown"


def freeze_phase_predictions(
    phase: str,
    prediction_history_path: str,
    output_log_path: str,
    dry_run: bool = True,
) -> dict:
    history = load_prediction_history(prediction_history_path)
    entries = history.get("entries", [])
    phase_entries = [entry for entry in entries if _phase_for_entry(entry) == phase]
    placeholders = [entry for entry in phase_entries if _is_placeholder_prediction(entry)]
    real_predictions = [entry for entry in phase_entries if entry not in placeholders]
    warnings = []
    if not phase_entries:
        freeze_status = "blocked_no_predictions"
        warnings.append("No predictions found for requested phase.")
    elif not real_predictions:
        freeze_status = "blocked_placeholder_only"
        warnings.append("Only placeholder predictions were found; nothing was frozen.")
    elif dry_run:
        freeze_status = "dry_run_ok"
    else:
        freeze_status = "frozen"

    summary = {
        "freeze_status": freeze_status,
        "phase": phase,
        "predictions_found": len(phase_entries),
        "predictions_frozen": len(real_predictions) if freeze_status == "frozen" else 0,
        "placeholders_ignored": len(placeholders),
        "dry_run": dry_run,
        "warnings": warnings,
        "next_steps": [
            "Load verified real results for the completed phase.",
            "Run inter-phase update after predictions are frozen and results are validated.",
        ],
    }
    if not dry_run and real_predictions:
        log_path = Path(output_log_path)
        existing = {}
        if log_path.exists():
            existing = json.loads(log_path.read_text(encoding="utf-8"))
        freezes = existing.setdefault("freezes", [])
        known = {item.get("phase") for item in freezes}
        if phase not in known:
            freezes.append(
                {
                    "phase": phase,
                    "frozen_at": _now(),
                    "prediction_count": len(real_predictions),
                    "source_history": str(prediction_history_path),
                }
            )
        existing.update(
            {
                "data_status": "worldcup_2026_phase_freeze_log_v1",
                "last_freeze_status": freeze_status,
                "last_phase": phase,
            }
        )
        _write_json_if_changed(log_path, existing)
    return summary
