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
from run_friendly_test_demo import active_matches, excluded_matches  # noqa: E402
from simulation_config import SIMULATION_MODES  # noqa: E402


LAYER_ROOT = Path(__file__).resolve().parent


def _load_friendly_matches() -> list[dict]:
    path = LAYER_ROOT / "data" / "friendly_test_matches.json"
    return json.loads(path.read_text(encoding="utf-8"))["matches"]


def _exists(path: Path) -> str:
    return "OK" if path.exists() else "PENDIENTE"


def main() -> None:
    teams, _, _ = load_default_final_pick_inputs()
    matches = _load_friendly_matches()
    active = active_matches(matches, teams)
    excluded = excluded_matches(matches, teams)

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
        "research_intelligence_engine.py",
        "research_weighting_engine.py",
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
        "run_friendly_test_demo.py",
        "run_project_status_report.py",
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
    print("")

    print("DATOS PENDIENTES")
    print("- cuotas manuales 365Scores: pending_manual_input")
    print("- alineaciones/formaciones: pending_manual_input")
    print("- ratings reales de jugadores: parcial; replacement_level_estimate donde falta dato")
    print("- resultado real post-partido: pending_real_result")
    print("- Morocco vs Norway resultado real: registrado 1-1")
    print("- Colombia vs Jordan resultado real: pending_real_result")
    print("- sedes/coordenadas verificadas: pending_real_data")
    print("- World Elo CSV verificado: manual_snapshot_required")
    print("- openfootball JSON local: manual_snapshot_required")
    print("")

    print("FALTA PARA PRUEBA REAL COMPLETA")
    print("- completar horarios y sedes de amistosos")
    print("- copiar cuotas visibles si el usuario decide usarlas")
    print("- copiar alineaciones o formaciones verificadas")
    print("- llenar resultado real despues del partido para comparar")
    print("- verificar coordenadas si se activa clima historico")
    print("")

    print("AMISTOSOS ACTIVOS")
    for match in active:
        print(f"- {match['match']}")
    print("")

    print("AMISTOSOS EXCLUIDOS")
    for match in excluded:
        missing = ", ".join(match.get("missing_teams", [])) or "no aplica"
        print(f"- {match['match']} | razon: {match.get('reason')} | faltantes: {missing}")
    print("")

    print("MODOS DE SIMULACION DISPONIBLES")
    for mode, simulations in SIMULATION_MODES.items():
        print(f"- {mode}: {simulations}")


if __name__ == "__main__":
    main()
