from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from chatgpt_research_intake_engine import (
    INTAKE_VALIDATION_REPORT_PATH,
    RESEARCH_BATCH_PATH,
)
from full_group_stage_picks_runner import run_full_group_stage_picks
from worldcup_2026_fixture_guard import evaluate_group_stage_simulation_readiness


LAYER_ROOT = Path(__file__).resolve().parent
DATA_ROOT = LAYER_ROOT / "data"
FILL_REPORT_PATH = DATA_ROOT / "worldcup_2026_quiniela_fill_report.json"
FILL_SUMMARY_CSV_PATH = DATA_ROOT / "worldcup_2026_quiniela_fill_summary.csv"
FILL_PRINTABLE_PATH = DATA_ROOT / "worldcup_2026_quiniela_fill_printable.md"

CSV_COLUMNS = [
    "group",
    "matchday",
    "match_id",
    "team_a",
    "team_b",
    "predicted_score",
    "pick_principal",
    "critical_alternative",
    "tempting_option",
    "quinigol_team",
    "quinigol_minute",
    "quinigol_range",
    "halftime_fulltime",
    "confidence",
    "risk",
    "robustness",
    "research_status",
    "missing_critical_data",
    "notes",
]


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


def _research_status() -> dict:
    validation = _load_json(INTAKE_VALIDATION_REPORT_PATH)
    batch = _load_json(RESEARCH_BATCH_PATH)
    if not validation and not batch:
        return {
            "research_package_status": "missing",
            "valid_for_prediction_context": False,
            "warnings": ["ChatGPT research intake has not been run yet."],
        }
    return {
        "research_package_status": validation.get(
            "validation_status",
            batch.get("fixture_validation_status", "missing"),
        ),
        "valid_for_prediction_context": batch.get("valid_for_prediction_context", False),
        "valid_for_tactical_bridge": batch.get("valid_for_tactical_bridge", False),
        "valid_for_market_weighting": batch.get("valid_for_market_weighting", False),
        "warnings": sorted(set(validation.get("warnings", []) + batch.get("warnings", []))),
    }


def _csv_row(pick: dict, research_status: str) -> dict:
    return {
        "group": pick.get("group", ""),
        "matchday": pick.get("matchday", ""),
        "match_id": pick.get("match_id", ""),
        "team_a": pick.get("team_a", ""),
        "team_b": pick.get("team_b", ""),
        "predicted_score": pick.get("predicted_score", ""),
        "pick_principal": pick.get("pick_principal", ""),
        "critical_alternative": pick.get("critical_alternative", ""),
        "tempting_option": pick.get("tempting_option", ""),
        "quinigol_team": pick.get("quinigol_team", ""),
        "quinigol_minute": pick.get("quinigol_minute", ""),
        "quinigol_range": pick.get("quinigol_range", ""),
        "halftime_fulltime": pick.get("halftime_fulltime", ""),
        "confidence": pick.get("confidence", ""),
        "risk": pick.get("risk", ""),
        "robustness": pick.get("robustness", ""),
        "research_status": research_status,
        "missing_critical_data": "; ".join(str(item) for item in pick.get("missing_critical_data", [])),
        "notes": pick.get("notes", ""),
    }


def _write_csv(path: Path, picks: list[dict], research_status: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for pick in picks:
            writer.writerow(_csv_row(pick, research_status))


def _printable_blocked(report: dict) -> str:
    reasons = report.get("block_reasons") or ["Fixture oficial no cargado o no validado."]
    lines = [
        "# NO SE PUEDE GENERAR QUINIELA COMPLETA",
        "",
        "Razon:",
    ]
    lines.extend(f"- {reason}" for reason in reasons)
    lines.extend(
        [
            "",
            "Estado:",
            f"- Fixture: {report.get('fixture_status', 'missing')}",
            f"- Guard: {report.get('guard_status', 'missing')}",
            f"- Research: {report.get('research_package_status', 'missing')}",
            "- Picks generados: 0",
            "",
        ]
    )
    return "\n".join(lines)


def _printable_ready(report: dict) -> str:
    by_group: dict[str, list[dict]] = {}
    for pick in report.get("picks", []):
        by_group.setdefault(pick.get("group", "pending"), []).append(pick)
    lines = [
        "# NOVA Quiniela Mundial 2026 - Fase de Grupos",
        "",
        "Estado:",
        f"- Fixture: {report.get('fixture_status', 'missing')}",
        f"- Research: {report.get('research_package_status', 'missing')}",
        f"- Picks generados: {report.get('picks_generated', 0)}",
        "",
    ]
    for group in sorted(by_group):
        lines.append(f"## Grupo {group}")
        for index, pick in enumerate(by_group[group], start=1):
            lines.extend(
                [
                    f"{index}. {pick.get('team_a')} vs {pick.get('team_b')}",
                    f"   Marcador: {pick.get('predicted_score')}",
                    f"   Pick: {pick.get('pick_principal')}",
                    f"   Alternativa critica: {pick.get('critical_alternative')}",
                    f"   Quinigol: {pick.get('quinigol_team')} minuto {pick.get('quinigol_minute')}",
                    f"   Riesgo: {pick.get('risk')}",
                    "",
                ]
            )
    return "\n".join(lines)


def _write_markdown(path: Path, report: dict) -> None:
    text = _printable_ready(report) if report.get("ready_for_user_quiniela") else _printable_blocked(report)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    path.write_text(text, encoding="utf-8")


def _paths() -> dict:
    return {
        "json": str(FILL_REPORT_PATH),
        "csv": str(FILL_SUMMARY_CSV_PATH),
        "printable_md": str(FILL_PRINTABLE_PATH),
    }


def run_emergency_quiniela_fill(mode: str = "standard", write: bool = False) -> dict:
    guard = evaluate_group_stage_simulation_readiness()
    research = _research_status()
    paths = _paths()
    guard_status = guard.get("guard_status", "missing")
    warnings = sorted(set(guard.get("warnings", []) + research.get("warnings", [])))

    if guard_status != "ready":
        report = {
            "data_status": "worldcup_2026_quiniela_fill_v1",
            "generated_at": _now(),
            "mode": mode,
            "fixture_status": guard.get("fixture_type", "missing"),
            "guard_status": guard_status,
            "research_package_status": research["research_package_status"],
            "matches_detected": guard.get("confirmed_matches", 0) + guard.get("pending_matches", 0),
            "picks_generated": 0,
            "blocked_matches": guard.get("confirmed_matches", 0) + guard.get("pending_matches", 0),
            "ready_for_user_quiniela": False,
            "block_reasons": guard.get("block_reason", ["Fixture oficial no cargado o no validado."]),
            "warnings": warnings,
            "picks": [],
            "report_paths": paths,
            "next_steps": [
                "Load and validate ChatGPT research intake with 72 official fixture matches.",
                "Run fixture import dry-run, then apply only after review.",
                "Re-run emergency quiniela fill after Fixture Guard returns ready.",
            ],
        }
    else:
        picks_result = run_full_group_stage_picks(mode=mode, write_report=False)
        picks = picks_result.get("picks", [])
        report = {
            "data_status": "worldcup_2026_quiniela_fill_v1",
            "generated_at": _now(),
            "mode": picks_result.get("mode", mode),
            "fixture_status": guard.get("fixture_type", "missing"),
            "guard_status": guard_status,
            "research_package_status": research["research_package_status"],
            "matches_detected": picks_result.get("total_group_stage_slots", 0),
            "picks_generated": len(picks),
            "blocked_matches": picks_result.get("blocked_matches", 0),
            "ready_for_user_quiniela": len(picks) == 72,
            "block_reasons": picks_result.get("block_reasons", []),
            "warnings": sorted(set(warnings + picks_result.get("warnings", []))),
            "picks": picks,
            "report_paths": paths,
            "next_steps": [
                "Review printable report before user submission.",
                "Keep late lineups, injuries and odds as optional refresh data.",
                "Do not update prediction_history from this fill unless a future explicit flag is added.",
            ],
        }

    if write:
        _write_json_if_changed(FILL_REPORT_PATH, report)
        _write_csv(FILL_SUMMARY_CSV_PATH, report["picks"], research["research_package_status"])
        _write_markdown(FILL_PRINTABLE_PATH, report)
    return report
