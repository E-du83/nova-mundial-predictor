import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from data_ingestion.free_sources_registry import (  # noqa: E402
    get_free_sources,
    get_sources_requiring_api_key,
)
from final_pick_engine import load_default_final_pick_inputs  # noqa: E402
from manual_snapshot_engine import find_manual_snapshot, load_manual_snapshots  # noqa: E402
from match_alarm_engine import build_match_alarm  # noqa: E402
from run_friendly_test_demo import active_matches, excluded_matches  # noqa: E402
from prediction_history_engine import load_prediction_history, summarize_prediction_history  # noqa: E402
from research_refresh_engine import build_research_refresh  # noqa: E402
from result_review_engine import find_real_result, load_friendly_results  # noqa: E402
from simulation_config import SIMULATION_MODES  # noqa: E402
from tactical_input_bridge import build_adjusted_match_inputs  # noqa: E402
from full_group_stage_picks_runner import run_full_group_stage_picks  # noqa: E402
from group_context_engine import build_group_context  # noqa: E402
from inter_phase_update_engine import run_inter_phase_update  # noqa: E402
from research_snapshot_store import SNAPSHOT_DIR  # noqa: E402
from worldcup_2026_bracket_guard import evaluate_bracket_readiness  # noqa: E402
from worldcup_2026_bracket_structure import write_default_bracket_files  # noqa: E402
from worldcup_2026_fixture_loader import load_worldcup_2026_fixture  # noqa: E402
from worldcup_2022_dataset_loader import load_worldcup_2022_datasets  # noqa: E402


LAYER_ROOT = Path(__file__).resolve().parent


def _load_friendly_matches() -> list[dict]:
    path = LAYER_ROOT / "data" / "friendly_test_matches.json"
    return json.loads(path.read_text(encoding="utf-8"))["matches"]


def _exists(path: Path) -> str:
    return "OK" if path.exists() else "PENDIENTE"


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _dataset_status(data: dict, missing_value: str = "missing") -> str:
    status = data.get("data_status")
    if not status:
        return missing_value
    if str(status).startswith("partial"):
        return "partial"
    if status in ("complete", "ready", "foundation_ready"):
        return "OK"
    return str(status)


def _profile_dataset_status(worldcup_2022: dict) -> str:
    if worldcup_2022.get("profiles_count", 0) > 0:
        return "OK"
    return _dataset_status(worldcup_2022.get("profiles", {}))


def _git_tracked(path: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return "unknown_git_unavailable"
    return "TRACKED" if result.returncode == 0 else "not_tracked"


def _gitignore_has_hardening_rules() -> bool:
    path = ROOT / ".gitignore"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    required = [
        "__pycache__/",
        "**/__pycache__/",
        "*.pyc",
        "*.sqlite3",
        ".env",
        "*.log",
    ]
    return all(item in text for item in required)


def _history_has_probabilities(history: dict) -> bool:
    for entry in history.get("entries", []):
        probabilities = entry.get("probabilities_1x2")
        if isinstance(probabilities, dict) and probabilities:
            return True
    return False


def _file_contains(path: Path, text: str) -> bool:
    return path.exists() and text in path.read_text(encoding="utf-8")


def _synthetic_bridge_validation(teams: dict) -> bool:
    if "Netherlands" not in teams or "Uzbekistan" not in teams:
        return False
    test_teams = {
        "Bridge A": dict(teams["Netherlands"]),
        "Bridge B": dict(teams["Uzbekistan"]),
    }
    original = json.dumps(test_teams, sort_keys=True)
    players = [
        {"player_name": f"P{index}", "position": "attack", "overall_rating": 84, "rating_type": "real"}
        for index in range(7)
    ]
    snapshot = {
        "team_a": "Bridge A",
        "team_b": "Bridge B",
        "formations": {"Bridge A": "4-3-3", "Bridge B": "5-4-1"},
        "player_ratings": {"Bridge A": players, "Bridge B": players},
        "form": {"Bridge A": 1.03, "Bridge B": 0.97},
        "research_confidence": "high",
    }
    result = build_adjusted_match_inputs("Bridge A", "Bridge B", test_teams, snapshot)
    changed = result["team_a_adjusted"]["attack"] != test_teams["Bridge A"]["attack"]
    not_mutated = json.dumps(test_teams, sort_keys=True) == original
    return changed and not_mutated and not result["adjustment_report"]["baseline_mutated"]


def main() -> None:
    teams, _, _ = load_default_final_pick_inputs()
    matches = _load_friendly_matches()
    active = active_matches(matches, teams)
    excluded = excluded_matches(matches, teams)
    snapshots = load_manual_snapshots(LAYER_ROOT / "data" / "manual_match_snapshots.json")
    results = load_friendly_results(LAYER_ROOT / "data" / "friendly_test_results.json")
    history = load_prediction_history(LAYER_ROOT / "data" / "prediction_history.json")
    history_summary = summarize_prediction_history(history)
    calibration_report = _load_json(LAYER_ROOT / "data" / "friendly_calibration_report.json")
    calibration_notes = _load_json(LAYER_ROOT / "data" / "calibration_notes.json")
    group_fixture_context = _load_json(LAYER_ROOT / "data" / "group_stage_fixture_context.json")
    worldcup_2026_fixture = load_worldcup_2026_fixture()
    full_group_stage_runner = run_full_group_stage_picks(mode="standard", write_report=False)
    group_context_real = build_group_context(
        "A",
        ["pending_group_draw", "pending_group_draw", "pending_group_draw", "pending_group_draw"],
        {},
        fixtures=worldcup_2026_fixture["fixture"].get("matches", []),
        mode="pre_tournament",
    )
    group_context_report = _load_json(LAYER_ROOT / "data" / "worldcup_2026_group_context_report.json")
    group_context_guard_report = _load_json(
        LAYER_ROOT / "data" / "worldcup_2026_group_context_guard_report.json"
    )
    write_default_bracket_files()
    bracket_guard = evaluate_bracket_readiness()
    research_automation_status = _load_json(LAYER_ROOT / "data" / "research_automation_status.json")
    inter_phase_update = run_inter_phase_update(dry_run=True, write_report=False)
    backtesting_manifest = _load_json(LAYER_ROOT / "data" / "backtesting_manifest.json")
    worldcup_2022 = load_worldcup_2022_datasets()
    worldcup_2022_report = _load_json(
        LAYER_ROOT
        / "historical_blind_tests"
        / "worldcup_2022"
        / "worldcup_2022_blind_test_report.json"
    )
    refresh_reports = [
        build_research_refresh(
            match["team_a"],
            match["team_b"],
            snapshots_data=snapshots,
            results_data=results,
        )
        for match in active
    ]
    alarm_reports = {
        report["match"]: build_match_alarm(find_manual_snapshot(snapshots, report["team_a"], report["team_b"]))
        for report in refresh_reports
    }

    print("NOVA PROJECT STATUS REPORT - QUINIELA MUNDIALISTA")
    print("")

    sqlite_status = _git_tracked(Path("nova_mundial_predictor.sqlite3"))
    hardening_checks = {
        ".gitignore actualizado": _gitignore_has_hardening_rules(),
        "tests presentes": (ROOT / "tests" / "test_scoring_rules.py").exists(),
        "Quinigol policy presente": (LAYER_ROOT / "quinigol_minute_policy.py").exists(),
        "prediction_history probabilities_1x2": _history_has_probabilities(history),
        "SQLite no trackeado": sqlite_status == "not_tracked",
    }
    hardening_status = "OK" if all(hardening_checks.values()) else "partial"
    print("HARDENING FOUNDATION v1")
    print(f"- estado bloque: {hardening_status}")
    for label, ok in hardening_checks.items():
        print(f"- {label}: {'OK' if ok else 'partial'}")
    print(f"- SQLite tracking status: {sqlite_status}")
    print("- siguiente bloque recomendado: Quinigol Timing Calibration / World Cup 2022 Blind Test")
    print("")

    print("MODULOS FUNCIONAN / PRESENTES")
    modules = [
        "final_pick_engine.py",
        "friendly_context_engine.py",
        "manual_snapshot_engine.py",
        "half_time_engine.py",
        "result_review_engine.py",
        "pick_robustness_engine.py",
        "decision_weighting_engine.py",
        "critical_alternative_engine.py",
        "player_rating_engine.py",
        "lineup_strength_engine.py",
        "formation_tactical_engine.py",
        "tactical_weighting_engine.py",
        "prediction_history_engine.py",
        "friendly_calibration_engine.py",
        "calibration_rules_engine.py",
        "group_stage_runner.py",
        "report_builder.py",
        "backtesting_engine.py",
        "system_self_audit.py",
        "research_intelligence_engine.py",
        "research_weighting_engine.py",
        "research_refresh_engine.py",
        "match_alarm_engine.py",
        "tournament_context_engine.py",
        "venue_climate_engine.py",
        "simulation_config.py",
        "quinigol_minute_policy.py",
        "tactical_input_bridge.py",
        "data_leakage_guard.py",
        "worldcup_2022_dataset_loader.py",
        "worldcup_2022_blind_test_engine.py",
        "worldcup_2022_profile_builder.py",
        "worldcup_2022_profile_validator.py",
        "quinigol_timing_calibration_engine.py",
        "worldcup_2026_match_slot_engine.py",
        "worldcup_2026_fixture_loader.py",
        "worldcup_2026_fixture_validator.py",
        "worldcup_2026_fixture_snapshot_importer.py",
        "worldcup_2026_fixture_guard.py",
        "full_group_stage_picks_runner.py",
        "group_context_engine.py",
        "worldcup_2026_bracket_structure.py",
        "worldcup_2026_third_place_selector.py",
        "worldcup_2026_bracket_guard.py",
        "worldcup_2026_bracket_builder.py",
        "research_snapshot_schema.py",
        "research_snapshot_validator.py",
        "research_prompt_builder.py",
        "research_snapshot_normalizer.py",
        "research_snapshot_store.py",
        "ai_research_client.py",
        "phase_freeze_engine.py",
        "worldcup_2026_results_loader.py",
        "worldcup_2026_standings_engine.py",
        "worldcup_2026_phase_transition_guard.py",
        "inter_phase_update_engine.py",
        "chatgpt_research_intake_engine.py",
        "emergency_quiniela_fill_engine.py",
    ]
    for module in modules:
        print(f"- {module}: {_exists(LAYER_ROOT / module)}")
    print("")

    print("DEMOS DISPONIBLES")
    demos = [
        "run_data_sources_demo.py",
        "run_lineup_weighting_demo.py",
        "run_decision_weighting_demo.py",
        "run_match_intelligence_demo.py",
        "run_research_snapshot_demo.py",
        "run_research_refresh_demo.py",
        "run_friendly_test_demo.py",
        "run_project_status_report.py",
        "run_friendly_calibration_report.py",
        "run_tactical_input_bridge_demo.py",
        "run_group_stage_report_demo.py",
        "run_backtesting_foundation_demo.py",
        "run_system_self_audit.py",
        "run_final_pick_demo.py",
        "run_quiniela_demo.py",
        "run_group_quiniela_demo.py",
        "run_worldcup_2022_blind_test.py",
        "run_worldcup_2022_profile_validation.py",
        "run_quinigol_timing_calibration.py",
        "run_worldcup_2026_fixture_status.py",
        "run_worldcup_2026_fixture_import_demo.py",
        "run_worldcup_2026_fixture_guard.py",
        "run_full_group_stage_picks.py",
        "run_group_context_demo.py",
        "run_worldcup_2026_bracket_status.py",
        "run_worldcup_2026_third_place_demo.py",
        "run_research_prompt_builder_demo.py",
        "run_research_snapshot_validation_demo.py",
        "run_research_automation_demo.py",
        "run_phase_freeze_demo.py",
        "run_worldcup_2026_standings_demo.py",
        "run_inter_phase_update_demo.py",
        "run_chatgpt_research_intake.py",
        "run_emergency_quiniela_fill.py",
    ]
    for demo in demos:
        print(f"- {demo}: {_exists(LAYER_ROOT / demo)}")
    print("")

    print("FUENTES GRATIS SIN API KEY")
    for source in get_free_sources():
        print(f"- {source['source_id']}: {source['name']} ({source['status']})")
    print("")

    print("FUENTES CON API KEY / OPCIONALES")
    for source in get_sources_requiring_api_key():
        print(f"- {source['source_id']}: {source['name']} ({source['status']})")
    print("")

    print("DATOS ACTIVOS")
    print("- baseline equipos Mundial 2026: OK")
    print("- friendly_test_matches activos: " + ", ".join(match["match"] for match in active))
    print("- manual_match_snapshots.json: " + _exists(LAYER_ROOT / "data" / "manual_match_snapshots.json"))
    print("- player_ratings_seed.json: " + _exists(LAYER_ROOT / "data" / "player_ratings_seed.json"))
    print("- friendly_test_results.json: " + _exists(LAYER_ROOT / "data" / "friendly_test_results.json"))
    print("- prediction_history.json: " + _exists(LAYER_ROOT / "data" / "prediction_history.json"))
    print("- friendly_calibration_report.json: " + _exists(LAYER_ROOT / "data" / "friendly_calibration_report.json"))
    print("- calibration_notes.json: " + _exists(LAYER_ROOT / "data" / "calibration_notes.json"))
    print("- group_stage_fixture_context.json: " + _exists(LAYER_ROOT / "data" / "group_stage_fixture_context.json"))
    print("- worldcup_2026_group_structure.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_group_structure.json"))
    print("- worldcup_2026_match_slots.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_match_slots.json"))
    print("- worldcup_2026_group_stage_fixture.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_group_stage_fixture.json"))
    print("- worldcup_2026_fixture_validation_report.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_fixture_validation_report.json"))
    print("- worldcup_2026_official_fixture_snapshot_template.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_official_fixture_snapshot_template.json"))
    print("- worldcup_2026_fixture_import_report.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_fixture_import_report.json"))
    print("- worldcup_2026_fixture_guard_report.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_fixture_guard_report.json"))
    print("- worldcup_2026_group_stage_picks_report.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_group_stage_picks_report.json"))
    print("- worldcup_2026_group_stage_picks_summary.csv: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_group_stage_picks_summary.csv"))
    print("- worldcup_2026_group_stage_picks_guard_report.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_group_stage_picks_guard_report.json"))
    print("- worldcup_2026_group_context_rules.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_group_context_rules.json"))
    print("- worldcup_2026_group_context_report.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_group_context_report.json"))
    print("- worldcup_2026_group_context_guard_report.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_group_context_guard_report.json"))
    print("- worldcup_2026_knockout_structure.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_knockout_structure.json"))
    print("- worldcup_2026_bracket_slots.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_bracket_slots.json"))
    print("- worldcup_2026_third_place_rules.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_third_place_rules.json"))
    print("- worldcup_2026_bracket_guard_report.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_bracket_guard_report.json"))
    print("- worldcup_2026_bracket_projection_report.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_bracket_projection_report.json"))
    print("- research_snapshot_template.json: " + _exists(LAYER_ROOT / "data" / "research_snapshot_template.json"))
    print("- research_snapshot_validation_report.json: " + _exists(LAYER_ROOT / "data" / "research_snapshot_validation_report.json"))
    print("- research_prompt_template.md: " + _exists(LAYER_ROOT / "data" / "research_prompt_template.md"))
    print("- research_automation_status.json: " + _exists(LAYER_ROOT / "data" / "research_automation_status.json"))
    print("- worldcup_2026_results_template.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_results_template.json"))
    print("- worldcup_2026_phase_freeze_log.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_phase_freeze_log.json"))
    print("- worldcup_2026_standings_snapshot.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_standings_snapshot.json"))
    print("- worldcup_2026_inter_phase_update_report.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_inter_phase_update_report.json"))
    print("- worldcup_2026_phase_transition_guard_report.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_phase_transition_guard_report.json"))
    print("- chatgpt_research_intake_package.json: " + _exists(LAYER_ROOT / "data" / "chatgpt_research_intake_package.json"))
    print("- chatgpt_research_intake_validation_report.json: " + _exists(LAYER_ROOT / "data" / "chatgpt_research_intake_validation_report.json"))
    print("- worldcup_2026_official_fixture_snapshot_manual.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_official_fixture_snapshot_manual.json"))
    print("- worldcup_2026_research_snapshots_batch.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_research_snapshots_batch.json"))
    print("- worldcup_2026_quiniela_fill_report.json: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_quiniela_fill_report.json"))
    print("- worldcup_2026_quiniela_fill_summary.csv: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_quiniela_fill_summary.csv"))
    print("- worldcup_2026_quiniela_fill_printable.md: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_quiniela_fill_printable.md"))
    print("- backtesting_manifest.json: " + _exists(LAYER_ROOT / "data" / "backtesting_manifest.json"))
    print("- world_elo_snapshot_template.csv: " + _exists(LAYER_ROOT / "data" / "world_elo_snapshot_template.csv"))
    print("- worldcup_venues_seed.json: " + _exists(LAYER_ROOT / "data" / "worldcup_venues_seed.json"))
    print("- venue_climate_profiles.json: " + _exists(LAYER_ROOT / "data" / "venue_climate_profiles.json"))
    print("")

    print("DATOS PENDIENTES")
    print("- cuotas manuales 365Scores: pending_manual_input")
    print("- alineaciones/formaciones: pending_manual_input")
    print("- ratings reales de jugadores: parcial; replacement_level_estimate donde falta dato")
    print("- resultado real post-partido: finalizados para amistosos revisados")
    print("- Morocco vs Norway resultado real: registrado 1-1")
    print("- Colombia vs Jordan resultado real: registrado 2-0")
    print("- Netherlands vs Uzbekistan resultado real: registrado 2-1")
    print("- sedes/coordenadas verificadas: pending_real_data")
    print("- World Elo CSV verificado: manual_snapshot_required")
    print("- openfootball JSON local: manual_snapshot_required")
    print("")

    print("FALTA PARA PRUEBA REAL COMPLETA")
    print("- completar horarios y sedes de amistosos")
    print("- copiar cuotas visibles si el usuario decide usarlas")
    print("- copiar alineaciones o formaciones verificadas")
    print("- mantener resultados reales trazables para comparar y backtesting")
    print("- verificar coordenadas si se activa clima historico")
    print("")

    print("AMISTOSOS ACTIVOS")
    for match in active:
        print(f"- {match['match']}")
    print("")

    print("RESEARCH REFRESH / MATCH ALARM")
    requiring_refresh = [report for report in refresh_reports if report["research_refresh_required"]]
    near_kickoff = [
        report for report in refresh_reports
        if alarm_reports[report["match"]]["match_status"] == "near_kickoff"
    ]
    partial_snapshots = [
        report for report in refresh_reports
        if report["partial_snapshot_ok_for_final_pick"] and report["research_refresh_required"]
    ]
    print(
        "- partidos que requieren refresh: "
        + (", ".join(report["match"] for report in requiring_refresh) or "none")
    )
    print(
        "- near kickoff: "
        + (", ".join(report["match"] for report in near_kickoff) or "none")
    )
    print(
        "- snapshots parciales: "
        + (", ".join(report["match"] for report in partial_snapshots) or "none")
    )
    print(
        "- pending result: "
        + (
            ", ".join(
                match["match"]
                for match in active
                if find_real_result(results, match["team_a"], match["team_b"]).get("status") != "final"
            )
            or "none"
        )
    )
    print(
        "- reviewed result: "
        + (
            ", ".join(
                match["match"]
                for match in active
                if find_real_result(results, match["team_a"], match["team_b"]).get("status") == "final"
            )
            or "none"
        )
    )
    print("")

    print("AMISTOSOS EXCLUIDOS")
    for match in excluded:
        missing = ", ".join(match.get("missing_teams", [])) or "no aplica"
        print(f"- {match['match']} | razon: {match.get('reason')} | faltantes: {missing}")
    print("")

    print("MODOS DE SIMULACION DISPONIBLES")
    for mode, simulations in SIMULATION_MODES.items():
        print(f"- {mode}: {simulations}")
    print("")

    print("HISTORIAL DE PREDICCIONES")
    print(f"- partidos con prediccion guardada: {history_summary['prediction_saved_count']}")
    print(f"- partidos con resultado real: {history_summary['real_result_count']}")
    print(f"- partidos revisados: {history_summary['reviewed_count']}")
    print(f"- partidos pendientes de resultado: {history_summary['pending_result_count']}")
    print(f"- aprendizajes registrados: {history_summary['learning_count']}")
    print(f"- entradas historicas guardadas: {history_summary['history_entry_count']}")
    print("- uso: evidencia para backtesting/calibracion futura; no entrenamiento automatico")
    print("")

    print("TACTICAL INPUT BRIDGE v1")
    print(f"- archivo presente: {_exists(LAYER_ROOT / 'tactical_input_bridge.py')}")
    print(
        "- integrado en quiniela_engine: "
        + (
            "OK"
            if _file_contains(LAYER_ROOT / "quiniela_engine.py", "build_adjusted_match_inputs")
            else "PENDIENTE"
        )
    )
    print(
        "- integrado en run_nova_simulator: "
        + (
            "OK"
            if _file_contains(LAYER_ROOT / "run_nova_simulator.py", "Tactical/Input Bridge")
            else "PENDIENTE"
        )
    )
    print(f"- demo presente: {_exists(LAYER_ROOT / 'run_tactical_input_bridge_demo.py')}")
    print(
        "- baseline mutation protection: "
        + (
            "OK"
            if _file_contains(LAYER_ROOT / "tactical_input_bridge.py", "copy.deepcopy")
            else "PENDIENTE"
        )
    )
    print(f"- synthetic bridge validation: {'OK' if _synthetic_bridge_validation(teams) else 'pendiente'}")
    print("- siguiente bloque recomendado: Quinigol Timing Calibration / World Cup 2022 Blind Test")
    print("")

    print("WORLD CUP 2026 GROUP STAGE STRUCTURE")
    print(f"- groups configured: {worldcup_2026_fixture['groups_loaded']}")
    print("- total group stage matches: 72")
    print(f"- fixture slots loaded: {worldcup_2026_fixture['slots_loaded']}")
    print(f"- confirmed fixture matches: {worldcup_2026_fixture['confirmed_matches']}")
    print(f"- pending fixture matches: {worldcup_2026_fixture['pending_matches']}")
    print(f"- fixture type: {worldcup_2026_fixture['fixture_type']}")
    print(
        "- fixture snapshot template: "
        + _exists(LAYER_ROOT / "data" / "worldcup_2026_official_fixture_snapshot_template.json")
    )
    print(f"- fixture importer: {_exists(LAYER_ROOT / 'worldcup_2026_fixture_snapshot_importer.py')}")
    print(f"- fixture guard: {_exists(LAYER_ROOT / 'worldcup_2026_fixture_guard.py')}")
    print(f"- import demo: {_exists(LAYER_ROOT / 'run_worldcup_2026_fixture_import_demo.py')}")
    print(f"- fixture validation: {worldcup_2026_fixture['validation_status']}")
    print(f"- guard status: {worldcup_2026_fixture['fixture_guard_status']}")
    runner_status = "placeholder_waiting_official_fixture"
    if worldcup_2026_fixture["fixture_ready"]:
        runner_status = "ready_for_full_group_simulation"
    elif worldcup_2026_fixture["fixture_partial"]:
        runner_status = "partial_fixture_only_confirmed_matches"
    print(f"- group stage runner status: {runner_status}")
    print(
        "- ready_for_partial_simulation: "
        f"{str(worldcup_2026_fixture['ready_for_partial_simulation']).lower()}"
    )
    print(
        "- ready_for_full_group_simulation: "
        f"{str(worldcup_2026_fixture['ready_for_full_group_simulation']).lower()}"
    )
    print("- next block recommended: Full Group Stage Picks Runner v1 after verified fixture import")
    print("")

    print("FULL GROUP STAGE PICKS RUNNER v1")
    print(f"- runner file: {_exists(LAYER_ROOT / 'full_group_stage_picks_runner.py')}")
    print(f"- CLI runner: {_exists(LAYER_ROOT / 'run_full_group_stage_picks.py')}")
    print(
        "- guard integrated: "
        f"{'OK' if full_group_stage_runner['guard_status'] != 'missing' else 'PENDIENTE'}"
    )
    print(f"- current runner status: {full_group_stage_runner['runner_status']}")
    print(
        "- full simulation blocked: "
        f"{'yes' if not full_group_stage_runner['ready_for_full_group_simulation'] else 'no'}"
    )
    print(f"- confirmed matches: {full_group_stage_runner['confirmed_matches']}")
    print(f"- pending matches: {full_group_stage_runner['pending_matches']}")
    print(f"- picks generated: {full_group_stage_runner['summary']['picks_generated']}")
    print("- report JSON status: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_group_stage_picks_report.json"))
    print("- report CSV status: " + _exists(LAYER_ROOT / "data" / "worldcup_2026_group_stage_picks_summary.csv"))
    print("- next block recommended: Group Context Engine v1 / official fixture import required")
    print("")

    print("GROUP CONTEXT ENGINE v1")
    print(f"- engine file: {_exists(LAYER_ROOT / 'group_context_engine.py')}")
    print(
        "- rules file: "
        + _exists(LAYER_ROOT / "data" / "worldcup_2026_group_context_rules.json")
    )
    print(f"- demo file: {_exists(LAYER_ROOT / 'run_group_context_demo.py')}")
    print(f"- real fixture context status: {group_context_real['context_status']}")
    print(
        "- placeholder guard: "
        + ("OK" if group_context_real["context_status"] == "placeholder_blocked" else "partial")
    )
    synthetic_validation = group_context_guard_report.get("synthetic_validation_ok")
    if synthetic_validation is None:
        synthetic_validation = group_context_report.get("validation", {}).get("synthetic_jornada3_trap_confirmed")
    print("- synthetic validation: " + ("OK" if synthetic_validation else "pending"))
    prediction_impact = (
        "conditional"
        if group_context_real.get("allowed_for_prediction")
        else "false"
    )
    print(f"- prediction impact enabled: {prediction_impact}")
    print("- next block recommended: Official Bracket 2026 / Research Automation")
    print("")

    print("WORLD CUP 2026 OFFICIAL BRACKET v1")
    print(
        "- knockout structure: "
        + _exists(LAYER_ROOT / "data" / "worldcup_2026_knockout_structure.json")
    )
    print(
        "- bracket slots: "
        + _exists(LAYER_ROOT / "data" / "worldcup_2026_bracket_slots.json")
    )
    print(
        "- third-place rules: "
        + _exists(LAYER_ROOT / "data" / "worldcup_2026_third_place_rules.json")
    )
    print(f"- third-place selector: {_exists(LAYER_ROOT / 'worldcup_2026_third_place_selector.py')}")
    print(f"- bracket guard: {_exists(LAYER_ROOT / 'worldcup_2026_bracket_guard.py')}")
    print(f"- bracket guard status: {bracket_guard['bracket_guard_status']}")
    print(
        "- ready for knockout projection: "
        f"{str(bracket_guard['ready_for_knockout_projection']).lower()}"
    )
    print(
        "- ready for knockout picks: "
        f"{str(bracket_guard['ready_for_knockout_picks']).lower()}"
    )
    print(f"- third-place matrix status: {bracket_guard['third_place_matrix_status']}")
    print("- next block recommended: Research Automation / verified group standings import")
    print("")

    print("RESEARCH AUTOMATION v1")
    print(f"- prompt builder: {_exists(LAYER_ROOT / 'research_prompt_builder.py')}")
    print(f"- snapshot schema: {_exists(LAYER_ROOT / 'research_snapshot_schema.py')}")
    print(f"- snapshot validator: {_exists(LAYER_ROOT / 'research_snapshot_validator.py')}")
    print(f"- snapshot normalizer: {_exists(LAYER_ROOT / 'research_snapshot_normalizer.py')}")
    print(f"- snapshot store: {_exists(LAYER_ROOT / 'research_snapshot_store.py')}")
    print(f"- ai client safe mode: {_exists(LAYER_ROOT / 'ai_research_client.py')}")
    print(f"- API calls enabled: {str(research_automation_status.get('api_calls_enabled', False)).lower()}")
    print(f"- dry run default: {str(research_automation_status.get('dry_run_default', True)).lower()}")
    print("- snapshots directory: " + ("OK" if SNAPSHOT_DIR.exists() else "missing"))
    print("- next block recommended: Manual research snapshot review / optional API connector")
    print("")

    print("INTER PHASE UPDATER v1")
    print(f"- phase freeze engine: {_exists(LAYER_ROOT / 'phase_freeze_engine.py')}")
    print(f"- results loader: {_exists(LAYER_ROOT / 'worldcup_2026_results_loader.py')}")
    print(f"- standings engine: {_exists(LAYER_ROOT / 'worldcup_2026_standings_engine.py')}")
    print(f"- transition guard: {_exists(LAYER_ROOT / 'worldcup_2026_phase_transition_guard.py')}")
    print(f"- inter phase updater: {_exists(LAYER_ROOT / 'inter_phase_update_engine.py')}")
    print(f"- current update status: {inter_phase_update['update_status']}")
    print(
        "- predictions frozen: "
        f"{str(inter_phase_update['transition_guard']['predictions_frozen']).lower()}"
    )
    print(
        "- results complete: "
        f"{str(inter_phase_update['transition_guard']['results_complete']).lower()}"
    )
    print(
        "- standings ready: "
        f"{str(inter_phase_update['transition_guard']['standings_ready']).lower()}"
    )
    print(
        "- bracket ready: "
        f"{str(inter_phase_update['transition_guard']['bracket_ready']).lower()}"
    )
    print(
        "- ready for next phase: "
        f"{str(inter_phase_update['transition_guard']['transition_status'] == 'ready').lower()}"
    )
    print("- next block recommended: Verified results import / phase review workflow")
    print("")

    intake_validation = _load_json(LAYER_ROOT / "data" / "chatgpt_research_intake_validation_report.json")
    fill_report = _load_json(LAYER_ROOT / "data" / "worldcup_2026_quiniela_fill_report.json")
    intake_status = intake_validation.get("validation_status", "missing")
    package_status = "missing"
    if (LAYER_ROOT / "data" / "chatgpt_research_intake_package.json").exists():
        package_status = "template" if intake_status == "missing_or_template" else "OK"
    printable_status = _exists(LAYER_ROOT / "data" / "worldcup_2026_quiniela_fill_printable.md")
    next_action = "fill chatgpt_research_intake_package.json with 72 verified fixture matches"
    if intake_validation.get("fixture_ready"):
        next_action = "run chatgpt intake dry-run, review importer, then apply fixture import"
    if fill_report.get("ready_for_user_quiniela"):
        next_action = "review printable quiniela before user submission"
    print("CHATGPT RESEARCH INTAKE + EMERGENCY QUINIELA FILL")
    print(f"- intake package: {package_status}")
    print(f"- fixture package status: {intake_status}")
    print(f"- research package status: {fill_report.get('research_package_status', intake_status)}")
    print(f"- fixture ready: {str(intake_validation.get('fixture_ready', False)).lower()}")
    print(f"- guard status: {worldcup_2026_fixture['fixture_guard_status']}")
    print(f"- picks generated: {fill_report.get('picks_generated', 0)}")
    print(f"- printable report: {printable_status}")
    print(f"- ready for user quiniela: {str(fill_report.get('ready_for_user_quiniela', False)).lower()}")
    print(f"- next action: {next_action}")
    print("")

    print("WORLD CUP 2022 HISTORICAL BLIND TEST v1")
    print(f"- prematch dataset: {_dataset_status(worldcup_2022.get('prematch', {}))}")
    print(f"- results dataset: {_dataset_status(worldcup_2022.get('results', {}))}")
    print(f"- profile dataset: {_profile_dataset_status(worldcup_2022)}")
    print(f"- profile audit: {worldcup_2022.get('profile_audit', {}).get('audit_status', 'pending')}")
    print(f"- profiles using neutral defaults: {worldcup_2022.get('profiles_using_neutral_defaults', 0)}")
    audit_status = worldcup_2022.get("audit", {}).get("audit_status", "pending")
    print(f"- data leakage guard: {audit_status}")
    print(f"- blind test report: {worldcup_2022_report.get('engine_status', 'missing')}")
    quinigol_timing_report = _load_json(
        LAYER_ROOT
        / "historical_blind_tests"
        / "worldcup_2022"
        / "worldcup_2022_quinigol_timing_report.json"
    )
    print(
        "- Quinigol timing report: "
        + ("OK" if quinigol_timing_report.get("total_matches") else "partial")
    )
    print(f"- generated_after_event: {str(worldcup_2022_report.get('generated_after_event', True)).lower()}")
    print(
        "- valid_for_behavioral_backtest: "
        f"{str(worldcup_2022_report.get('valid_for_behavioral_backtest', True)).lower()}"
    )
    print(
        "- valid_for_true_prediction_accuracy: "
        f"{str(not worldcup_2022_report.get('not_valid_for_true_prediction_accuracy', True)).lower()}"
    )
    print(f"- matches evaluated: {worldcup_2022_report.get('matches_evaluated', 0)}")
    print(
        "- matches evaluable with neutral defaults: "
        f"{worldcup_2022_report.get('matches_evaluable_with_neutral_defaults', 0)}"
    )
    print(f"- matches blocked by leakage: {worldcup_2022_report.get('matches_blocked_by_leakage', 0)}")
    print(
        "- not valid for model accuracy claims: "
        f"{str(worldcup_2022_report.get('not_valid_for_model_accuracy_claims', True)).lower()}"
    )
    print(
        "- historical profiles status: "
        + worldcup_2022_report.get("structural_flow_metrics", worldcup_2022_report.get("structural_readiness_metrics", {})).get(
            "historical_profiles_status",
            "not_available",
        )
    )
    print("- next block recommended: verified 2022 prematch profiles / Quinigol Timing Calibration")
    print("")

    print("CALIBRACION AMISTOSOS")
    reviewed = calibration_report.get("matches_reviewed", [])
    print(f"- amistosos finalizados revisados: {len(reviewed)}")
    print(f"- prediction_history status: {history.get('last_update_status', 'not_available')}")
    print(f"- calibration report status: {calibration_report.get('data_status', 'not_available')}")
    patterns = calibration_report.get("patterns") or calibration_notes
    pattern_items = [
        "draw_underestimation_pattern",
        "late_opponent_goal_pattern",
        "quinigol_timing_miscalibration",
        "clean_sheet_risk_warning",
        "fragility_warning_validated",
    ]
    for item in pattern_items:
        print(f"- {item}: {patterns.get(item, 'not_available')}")
    print(
        "- sample size warning: "
        + calibration_notes.get(
            "sample_size_warning",
            "Sample size is very small. Do not recalibrate aggressively from only three friendlies.",
        )
    )
    print("- proximo bloque recomendado: Quinigol Timing Calibration / World Cup 2022 Blind Test")
    print("")

    print("DATA COMPLETION + BACKTESTING FOUNDATION v1")
    print("- estado bloque: foundation_ready")
    print("- estado Elo snapshot: " + _exists(LAYER_ROOT / "data" / "world_elo_snapshot_template.csv"))
    print(
        "- estado venues/climate: "
        f"venues={_exists(LAYER_ROOT / 'data' / 'worldcup_venues_seed.json')} | "
        f"climate={_exists(LAYER_ROOT / 'data' / 'venue_climate_profiles.json')}"
    )
    print(
        "- estado group stage fixtures: "
        + group_fixture_context.get("data_status", "manual_snapshot_required")
    )
    print("- estado report builder: " + _exists(LAYER_ROOT / "report_builder.py"))
    print(
        "- estado backtesting foundation: "
        + backtesting_manifest.get("data_status", "manual_snapshot_required")
    )
    print("- estado self audit: " + _exists(LAYER_ROOT / "system_self_audit.py"))
    print("- siguiente bloque recomendado: verified 2022 prematch profiles / Quinigol Timing Calibration")


if __name__ == "__main__":
    main()
