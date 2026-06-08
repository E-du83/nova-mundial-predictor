import json
from pathlib import Path
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
    backtesting_manifest = _load_json(LAYER_ROOT / "data" / "backtesting_manifest.json")
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
        "run_group_stage_report_demo.py",
        "run_backtesting_foundation_demo.py",
        "run_system_self_audit.py",
        "run_final_pick_demo.py",
        "run_quiniela_demo.py",
        "run_group_quiniela_demo.py",
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
    print("- proximo bloque recomendado: Data Completion + Backtesting Foundation v1")
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
    print("- siguiente bloque recomendado: Historical Blind Backtesting v1 with leakage guard")


if __name__ == "__main__":
    main()
