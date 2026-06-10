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
    worldcup_2022_report = _load_json(
        LAYER_ROOT
        / "historical_blind_tests"
        / "worldcup_2022"
        / "worldcup_2022_blind_test_report.json"
    )
    worldcup_2022_audit = _load_json(
        LAYER_ROOT
        / "historical_blind_tests"
        / "worldcup_2022"
        / "worldcup_2022_data_leakage_audit.json"
    )
    required_modules = [
        "final_pick_engine.py",
        "run_nova_simulator.py",
        "friendly_calibration_engine.py",
        "group_stage_runner.py",
        "report_builder.py",
        "backtesting_engine.py",
        "system_self_audit.py",
        "data_leakage_guard.py",
        "worldcup_2022_dataset_loader.py",
        "worldcup_2022_blind_test_engine.py",
        "run_worldcup_2022_blind_test.py",
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
            "World Cup 2022 blind-test scaffolding separates prematch inputs, results and leakage audit.",
        ],
        "debilidades": [
            "Official group-stage fixtures are not loaded yet.",
            "Lineups, formations, odds and player ratings remain partial or manual.",
            "Brier/log-loss fields are prepared but class probabilities are not persisted for every pick.",
            "Some layers explain risk more than they change decisions, so impact needs future validation.",
            "World Cup 2022 historical team profiles are neutral defaults, so they are insufficient for accuracy claims.",
            "World Cup 2022 profiles currently use neutral defaults, so they validate flow only.",
        ],
        "riesgos": [
            "Small sample overfitting from only three friendlies.",
            "Data leakage if historical backtests use information collected after match kickoff.",
            "Core dominance can hide weak external-data layers if missing data is not surfaced.",
            "Decorative variables can accumulate if a field has no measurable downstream impact.",
            "Using 2026 baseline data for 2022 would create invalid historical evaluation.",
            "Quinigol timing sample is only 8 matches, so calibration would overfit.",
        ],
        "mejoras_prioritarias": [
            "Load a verified official group-stage fixture snapshot.",
            "Add cutoff-date rules before World Cup 2022 blind testing.",
            "Verify 2022 prematch profiles before evaluating Core behavior on historical World Cup matches.",
            "Replace neutral defaults with verified 2022 Elo/rank/team-strength inputs before accuracy claims.",
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
            "Do not recalibrate from World Cup 2022 behavioral_backtest until profiles and leakage audit are strong.",
            "Do not recalibrate Quinigol timing from neutral-default backtest or an 8-match sample.",
        ],
        "siguiente_bloque_recomendado": "verified 2022 prematch profiles / Quinigol Timing Calibration",
        "readiness": {
            "missing_modules": missing_modules,
            "real_data_available": {
                "friendly_results_reviewed": calibration.get("metrics", {}).get("total_matches_reviewed", 0),
                "group_fixture_ready": group_fixture_ready,
                "foundation_ready_datasets": datasets_ready,
            },
            "ready_for_full_quiniela": bool(group_fixture_ready and not missing_modules),
            "ready_for_sale": False,
            "worldcup_2022_blind_test_exists": bool(worldcup_2022_report),
            "worldcup_2022_leakage_guard_exists": bool(worldcup_2022_audit),
            "worldcup_2022_leakage_guard_status": worldcup_2022_audit.get("audit_status", "missing"),
            "worldcup_2022_uses_2026_baseline": False,
            "worldcup_2022_missing_historical_profiles": worldcup_2022_report.get(
                "matches_missing_historical_profiles",
                "not_available",
            ),
            "worldcup_2022_neutral_defaults_only": worldcup_2022_report.get(
                "profiles_using_neutral_defaults",
                "not_available",
            ),
            "worldcup_2022_matches_evaluated": worldcup_2022_report.get("matches_evaluated", 0),
            "worldcup_2022_matches_evaluable_with_neutral_defaults": worldcup_2022_report.get(
                "matches_evaluable_with_neutral_defaults",
                0,
            ),
            "quinigol_timing_sample_insufficient": True,
            "worldcup_2022_can_recalibrate": False,
            "worldcup_2022_requires_blind_test": False,
        },
    }
