from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def _field(item: dict, key: str, default="pending_real_data"):
    return item.get(key, default)


def build_prediction_report(matches: list[dict], metadata: dict | None = None) -> dict:
    report_matches = []
    for item in matches:
        decision = item.get("decision_weighting", {})
        recommended_use = decision.get("recommended_use", {}) if isinstance(decision, dict) else {}
        report_matches.append(
            {
                "match_id": _field(item, "match_id"),
                "group": _field(item, "group"),
                "match": _field(item, "match"),
                "pick_principal": _field(item, "pick_principal"),
                "predicted_score": _field(item, "marcador"),
                "critical_alternative": _field(item, "alternativa_critica"),
                "tempting_option": _field(item, "opcion_tentadora"),
                "quinigol": _field(item, "quinigol"),
                "quinigol_policy_applied": _field(item, "quinigol_policy_applied", "not_available"),
                "quinigol_range": _field(item, "quinigol_range"),
                "quinigol_minute_reference": _field(item, "reference_minute"),
                "halftime_fulltime": _field(item, "halftime_fulltime"),
                "confidence": _field(item, "confidence"),
                "risk": _field(item, "risk"),
                "robustness": _field(item, "robustez"),
                "tactical_score": _field(item, "tactical_score"),
                "data_quality_score": _field(item, "data_quality_score"),
                "missing_critical_data": _field(item, "datos_faltantes", []),
                "quiniela_recommendation": recommended_use.get("quiniela", "pending_real_data"),
                "pre_match_betting_recommendation": recommended_use.get("apuesta_prepartido", "pending_real_data"),
                "notes": _field(item, "pending_reason", "none"),
            }
        )
    return {
        "data_status": "prediction_report_v1",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "metadata": metadata or {},
        "matches": report_matches,
    }


def _without_generated_at(report: dict) -> dict:
    comparable = dict(report)
    comparable.pop("generated_at", None)
    return comparable


def save_prediction_report(report: dict, output_path: str | Path) -> dict:
    path = Path(output_path)
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if _without_generated_at(existing) == _without_generated_at(report):
            return existing
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report
