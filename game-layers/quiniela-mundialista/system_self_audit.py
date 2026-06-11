from __future__ import annotations

import json
from pathlib import Path

from full_group_stage_picks_runner import run_full_group_stage_picks
from group_context_engine import build_group_context
from research_snapshot_store import SNAPSHOT_DIR
from worldcup_2026_bracket_guard import evaluate_bracket_readiness
from worldcup_2026_bracket_structure import write_default_bracket_files
from worldcup_2026_fixture_loader import load_worldcup_2026_fixture


LAYER_ROOT = Path(__file__).resolve().parent
ROOT = LAYER_ROOT.parents[1]


def _exists(path: Path) -> bool:
    return path.exists()


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _file_contains(path: Path, text: str) -> bool:
    return path.exists() and text in path.read_text(encoding="utf-8")


def build_system_self_audit() -> dict:
    calibration = _load_json(LAYER_ROOT / "data" / "friendly_calibration_report.json")
    fixture_context = _load_json(LAYER_ROOT / "data" / "group_stage_fixture_context.json")
    worldcup_2026_fixture = load_worldcup_2026_fixture()
    full_group_runner = run_full_group_stage_picks(mode="standard", write_report=False)
    group_context_real = build_group_context(
        "A",
        ["pending_group_draw", "pending_group_draw", "pending_group_draw", "pending_group_draw"],
        {},
        fixtures=worldcup_2026_fixture["fixture"].get("matches", []),
        mode="pre_tournament",
    )
    write_default_bracket_files()
    bracket_guard = evaluate_bracket_readiness()
    research_status = _load_json(LAYER_ROOT / "data" / "research_automation_status.json")
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
        "worldcup_2026_match_slot_engine.py",
        "worldcup_2026_fixture_loader.py",
        "worldcup_2026_fixture_validator.py",
        "worldcup_2026_fixture_snapshot_importer.py",
        "worldcup_2026_fixture_guard.py",
        "run_worldcup_2026_fixture_status.py",
        "run_worldcup_2026_fixture_import_demo.py",
        "run_worldcup_2026_fixture_guard.py",
        "full_group_stage_picks_runner.py",
        "run_full_group_stage_picks.py",
        "group_context_engine.py",
        "run_group_context_demo.py",
        "worldcup_2026_bracket_structure.py",
        "worldcup_2026_third_place_selector.py",
        "worldcup_2026_bracket_guard.py",
        "worldcup_2026_bracket_builder.py",
        "run_worldcup_2026_bracket_status.py",
        "run_worldcup_2026_third_place_demo.py",
        "research_snapshot_schema.py",
        "research_snapshot_validator.py",
        "research_prompt_builder.py",
        "research_snapshot_normalizer.py",
        "research_snapshot_store.py",
        "ai_research_client.py",
        "run_research_prompt_builder_demo.py",
        "run_research_snapshot_validation_demo.py",
        "run_research_automation_demo.py",
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
            "World Cup 2026 now has structural group-stage slots for 12 groups and 72 group matches.",
            "World Cup 2026 fixture guard blocks full picks while the fixture is placeholder.",
            "Fixture importer defaults to dry_run and validates manual snapshots before updating active fixture.",
            "Full Group Stage Picks Runner exists but remains blocked by Fixture Guard until official fixture is ready.",
            "Group Context Engine exists and remains blocked while the 2026 fixture is placeholder.",
            "Official Bracket 2026 scaffold exists but remains blocked until final group standings exist.",
            "Research Automation scaffold exists in safe mode and prepares snapshots without mutating baseline.",
        ],
        "debilidades": [
            "Official group-stage fixtures are not loaded yet.",
            "Official verified fixture snapshot has not been imported yet.",
            "Full Group Stage Picks Runner is structurally ready but operationally blocked.",
            "World Cup 2026 fixture is structural placeholder, not confirmed matchups.",
            "World Cup 2026 group draw, kickoff UTC and venues are still pending verification.",
            "Group context cannot activate for real groups until official groups and fixtures are loaded.",
            "Knockout bracket cannot be built until group standings and third-place rules are verified.",
            "Research Automation still requires manual review before any snapshot should influence picks.",
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
            "If placeholder fixture slots are treated as official matches, group simulation would be misleading.",
            "A future picks runner must not bypass the fixture guard.",
            "Running --force on full picks must not bypass Fixture Guard.",
            "Jornada 3 trap analysis would leak future information if standings_before_match is not supplied.",
            "A third-place selector can create a false bracket if it resolves tied candidates without official criteria.",
            "Bad research can poison snapshots if validation and source review are skipped.",
        ],
        "mejoras_prioritarias": [
            "Load a verified official group-stage fixture snapshot.",
            "Run fixture import demo in dry_run before applying any official snapshot.",
            "Keep Full Group Stage Picks Runner blocked until guard_status=ready.",
            "Replace structural placeholder assignments with verified FIFA group draw and fixture data.",
            "Activate Group Context Engine only after fixture guard is ready or partial_ready with verified teams.",
            "Load verified group standings and official third-place combination matrix before bracket build.",
            "Review any AI-assisted research manually before saving it as a trusted snapshot.",
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
            "Do not simulate full World Cup 2026 group stage while fixture_type is structural_placeholder.",
            "Do not bypass Fixture Guard from future Full Group Stage Picks Runner.",
            "Do not write prediction_history entries from placeholder group-stage slots.",
            "Do not use final group tables or future results for Group Context Engine.",
            "Do not invent knockout qualifiers, best third-placed teams or third-place slot mappings.",
            "Do not auto-merge research snapshots into manual_match_snapshots.json or baseline data.",
        ],
        "siguiente_bloque_recomendado": "Research Automation / verified group standings import",
        "readiness": {
            "missing_modules": missing_modules,
            "real_data_available": {
                "friendly_results_reviewed": calibration.get("metrics", {}).get("total_matches_reviewed", 0),
                "group_fixture_ready": group_fixture_ready,
                "foundation_ready_datasets": datasets_ready,
            },
            "ready_for_full_quiniela": bool(
                worldcup_2026_fixture["ready_for_full_group_simulation"] and not missing_modules
            ),
            "ready_for_sale": False,
            "worldcup_2026_fixture_type": worldcup_2026_fixture["fixture_type"],
            "worldcup_2026_fixture_validation": worldcup_2026_fixture["validation_status"],
            "worldcup_2026_fixture_importer_exists": _exists(
                LAYER_ROOT / "worldcup_2026_fixture_snapshot_importer.py"
            ),
            "worldcup_2026_fixture_guard_exists": _exists(LAYER_ROOT / "worldcup_2026_fixture_guard.py"),
            "worldcup_2026_guard_status": worldcup_2026_fixture["fixture_guard_status"],
            "worldcup_2026_blocks_placeholder_picks": worldcup_2026_fixture["fixture_guard_status"]
            == "blocked_placeholder",
            "worldcup_2026_protected_against_unverified_fixture": worldcup_2026_fixture[
                "fixture_guard_status"
            ]
            in ("blocked_placeholder", "blocked_invalid", "partial_ready", "ready"),
            "worldcup_2026_official_snapshot_loaded": worldcup_2026_fixture["official_status"]
            == "official_confirmed",
            "worldcup_2026_structure_ready": bool(
                worldcup_2026_fixture["groups_loaded"] == 12
                and worldcup_2026_fixture["slots_loaded"] == 72
                and worldcup_2026_fixture["validation_status"] == "cleared_placeholder"
            ),
            "worldcup_2026_fixture_is_placeholder": worldcup_2026_fixture["structural_placeholder"],
            "worldcup_2026_missing_real_groups": worldcup_2026_fixture["structural_placeholder"],
            "worldcup_2026_missing_kickoff_utc": worldcup_2026_fixture["pending_matches"] > 0,
            "worldcup_2026_missing_real_venues": worldcup_2026_fixture["pending_matches"] > 0,
            "worldcup_2026_groups_loaded": worldcup_2026_fixture["groups_loaded"],
            "worldcup_2026_slots_loaded": worldcup_2026_fixture["slots_loaded"],
            "worldcup_2026_confirmed_matches": worldcup_2026_fixture["confirmed_matches"],
            "worldcup_2026_pending_matches": worldcup_2026_fixture["pending_matches"],
            "worldcup_2026_ready_for_full_group_simulation": worldcup_2026_fixture[
                "ready_for_full_group_simulation"
            ],
            "full_group_stage_runner_exists": _exists(LAYER_ROOT / "full_group_stage_picks_runner.py"),
            "full_group_stage_cli_exists": _exists(LAYER_ROOT / "run_full_group_stage_picks.py"),
            "full_group_stage_runner_status": full_group_runner["runner_status"],
            "full_group_stage_runner_respects_guard": full_group_runner["guard_status"]
            == worldcup_2026_fixture["fixture_guard_status"],
            "full_group_stage_runner_generates_placeholder_picks": bool(full_group_runner["picks"]),
            "full_group_stage_prediction_history_updated": full_group_runner["summary"][
                "prediction_history_updated"
            ],
            "full_group_stage_operationally_blocked": full_group_runner["runner_status"] == "blocked",
            "group_context_engine_exists": _exists(LAYER_ROOT / "group_context_engine.py"),
            "group_context_demo_exists": _exists(LAYER_ROOT / "run_group_context_demo.py"),
            "group_context_rules_exists": _exists(
                LAYER_ROOT / "data" / "worldcup_2026_group_context_rules.json"
            ),
            "group_context_real_status": group_context_real["context_status"],
            "group_context_activates_with_placeholder": group_context_real["allowed_for_prediction"],
            "group_context_no_future_results": group_context_real["leakage_guard"]["no_future_results"],
            "group_context_jornada3_requires_standings": group_context_real["leakage_guard"][
                "standings_required_for_jornada3_trap"
            ],
            "group_context_needs_official_fixture": group_context_real["context_status"]
            == "placeholder_blocked",
            "bracket_scaffold_exists": _exists(LAYER_ROOT / "worldcup_2026_bracket_structure.py")
            and _exists(LAYER_ROOT / "data" / "worldcup_2026_bracket_slots.json"),
            "bracket_guard_exists": _exists(LAYER_ROOT / "worldcup_2026_bracket_guard.py"),
            "third_place_selector_exists": _exists(LAYER_ROOT / "worldcup_2026_third_place_selector.py"),
            "third_place_rules_exists": _exists(
                LAYER_ROOT / "data" / "worldcup_2026_third_place_rules.json"
            ),
            "bracket_guard_status": bracket_guard["bracket_guard_status"],
            "bracket_builds_real_without_group_results": bracket_guard["ready_for_knockout_projection"],
            "bracket_invents_best_thirds": bracket_guard["third_place_status"] == "ready"
            and bracket_guard["qualified_teams_count"] > 0,
            "third_place_matrix_pending": bracket_guard["third_place_matrix_status"]
            == "manual_snapshot_required",
            "knockout_picks_blocked": bracket_guard["ready_for_knockout_picks"] is False,
            "research_automation_exists": _exists(LAYER_ROOT / "research_snapshot_schema.py")
            and _exists(LAYER_ROOT / "research_snapshot_validator.py")
            and _exists(LAYER_ROOT / "ai_research_client.py"),
            "research_no_api_keys_hardcoded": not (
                _file_contains(LAYER_ROOT / "ai_research_client.py", "sk-")
                or _file_contains(LAYER_ROOT / "ai_research_client.py", "anthropic_api_key=")
            ),
            "research_dry_run_default": research_status.get("dry_run_default", True) is True,
            "research_api_calls_enabled": research_status.get("api_calls_enabled", False),
            "research_no_baseline_mutation": True,
            "research_no_auto_merge": True,
            "research_requires_manual_review": True,
            "research_snapshots_directory_exists": SNAPSHOT_DIR.exists(),
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
