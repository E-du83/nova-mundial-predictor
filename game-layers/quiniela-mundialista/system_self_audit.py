from __future__ import annotations

import json
from pathlib import Path


LAYER_ROOT = Path(__file__).resolve().parent
ROOT = LAYER_ROOT.parents[1]


def _exists(path: Path) -> bool:
    return path.exists()


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_system_self_audit() -> dict:
    calibration = _load_json(LAYER_ROOT / "data" / "friendly_calibration_report.json")
    fixture_context = _load_json(LAYER_ROOT / "data" / "group_stage_fixture_context.json")
    manifest = _load_json(LAYER_ROOT / "data" / "backtesting_manifest.json")
    required_modules = [
        "final_pick_engine.py",
        "run_nova_simulator.py",
        "friendly_calibration_engine.py",
        "group_stage_runner.py",
        "report_builder.py",
        "backtesting_engine.py",
        "system_self_audit.py",
    ]
    missing_modules = [
        module for module in required_modules if not _exists(LAYER_ROOT / module)
    ]
    group_fixture_ready = fixture_context.get("data_status") == "ready_snapshot"
    datasets_ready = [
        item["dataset"]
        for item in manifest.get("datasets", [])
        if item.get("integration_status") == "foundation_ready"
    ]
    return {
        "data_status": "system_self_audit_v1",
        "fortalezas": [
            "Core remains centralized in src and the quiniela layer wraps it instead of duplicating it.",
            "Friendly calibration now records auditable learning without automatic training.",
            "Simulation modes are explicit and heavy final runs are opt-in.",
            "Data source clients are offline-first and avoid paid API dependencies.",
        ],
        "debilidades": [
            "Official group-stage fixtures are not loaded yet.",
            "Lineups, formations, odds and player ratings remain partial or manual.",
            "Brier/log-loss fields are prepared but class probabilities are not persisted for every pick.",
            "Some layers explain risk more than they change decisions, so impact needs future validation.",
        ],
        "riesgos": [
            "Small sample overfitting from only three friendlies.",
            "Data leakage if historical backtests use information collected after match kickoff.",
            "Core dominance can hide weak external-data layers if missing data is not surfaced.",
            "Decorative variables can accumulate if a field has no measurable downstream impact.",
        ],
        "mejoras_prioritarias": [
            "Load a verified official group-stage fixture snapshot.",
            "Add cutoff-date rules before World Cup 2022 blind testing.",
            "Persist probability vectors for Brier/log-loss evaluation.",
            "Complete manual snapshots for odds, lineups and formations before final picks.",
        ],
        "mejoras_opcionales": [
            "Add richer report exports once fixture data is verified.",
            "Add source freshness checks for Elo and fixtures.",
            "Add per-group dashboard summaries after fixtures exist.",
        ],
        "no_hacer_todavia": [
            "Do not recalibrate weights with only three friendlies.",
            "Do not use World Cup 2022 without blind test and data leakage guard.",
            "Do not sell or present this as production betting software.",
            "Do not auto-change Core weights from calibration_notes.json.",
        ],
        "siguiente_bloque_recomendado": "Historical Blind Backtesting v1 with leakage guard",
        "readiness": {
            "missing_modules": missing_modules,
            "real_data_available": {
                "friendly_results_reviewed": calibration.get("metrics", {}).get("total_matches_reviewed", 0),
                "group_fixture_ready": group_fixture_ready,
                "foundation_ready_datasets": datasets_ready,
            },
            "ready_for_full_quiniela": bool(group_fixture_ready and not missing_modules),
            "ready_for_sale": False,
            "worldcup_2022_requires_blind_test": True,
        },
    }
