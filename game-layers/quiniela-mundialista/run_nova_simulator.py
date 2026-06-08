import argparse

from final_pick_engine import load_default_final_pick_inputs
from manual_snapshot_engine import load_manual_snapshots
from prediction_history_engine import record_prediction_history
from result_review_engine import find_real_result, load_friendly_results
from run_friendly_test_demo import (
    DATA_PATH,
    HISTORY_PATH,
    RESULTS_PATH,
    SNAPSHOTS_PATH,
    _build_friendly_recommendation,
    active_matches,
    load_friendly_matches,
)
from simulation_config import resolve_simulation_mode


def _yes_no(value: bool) -> str:
    return "si" if value else "no"


def _matches_for_scope(matches: list[dict], teams: dict, scope: str) -> list[dict]:
    active = active_matches(matches, teams)
    if scope == "friendly":
        return active
    return [
        match
        for match in active
        if match.get("test_scope") == "worldcup_only"
        or match.get("reason") == "active_worldcup_baseline_teams"
    ]


def _filter_matches(
    matches: list[dict],
    results_data: dict,
    requested_match: str | None,
) -> list[dict]:
    if requested_match:
        requested = requested_match.strip().lower()
        return [match for match in matches if match["match"].strip().lower() == requested]

    pending = []
    for match in matches:
        result = find_real_result(results_data, match["team_a"], match["team_b"])
        if result.get("status") != "final":
            pending.append(match)
    return pending


def _critical_alternative_text(recommendation: dict) -> str:
    alternatives = recommendation["critical_alternatives"]
    if alternatives["critical_alternative_active"] and alternatives["critical_alternative"]:
        return alternatives["critical_alternative"]["score"]
    return "none"


def _tempting_option_text(recommendation: dict) -> str:
    tempting = recommendation["critical_alternatives"]["tempting_option"]
    return tempting["score"] if tempting else "none"


def _print_compact_recommendation(
    recommendation: dict,
    scope: str,
    history_status: str,
) -> None:
    refresh = recommendation["research_refresh"]
    alarm = recommendation["match_alarm"]
    decision = recommendation["decision_weighting"]
    tactical = recommendation["research_weighting"]["tactical_weighting"]
    missing_critical = decision["missing_critical_data"] or refresh["missing_critical_fields"]

    print("NOVA SIMULATOR")
    print(f"Partido: {recommendation['match']}")
    print(f"Modo: {recommendation['simulation_mode']}")
    print(f"Simulaciones: {recommendation['simulations_used']}")
    print(f"Scope: {scope}")
    print(f"Kickoff UTC: {alarm['kickoff_time_utc']}")
    print(f"Minutos para inicio: {alarm['minutes_to_kickoff']}")
    print(f"Research refresh required: {_yes_no(refresh['research_refresh_required'])}")
    print(f"Recommended action: {refresh['recommended_action']}")
    print(f"Snapshot status: {refresh['source_status']}")
    print(f"Pick principal: {recommendation['critical_alternatives']['principal_pick']['score']}")
    print(f"Marcador: {recommendation['recommended_score']}")
    print(f"Alternativa critica: {_critical_alternative_text(recommendation)}")
    print(f"Opcion tentadora: {_tempting_option_text(recommendation)}")
    print(f"Quinigol: {recommendation['quinigol']}")
    print(f"Rango probable: {recommendation['quinigol_range']}")
    print(f"Minuto referencia: {recommendation['reference_minute']}")
    print(f"Descanso/final: {recommendation['half_time']['half_time_full_time']}")
    print(f"Confianza: {recommendation['adjusted_confidence']}")
    print(f"Riesgo: {recommendation['friendly_risk']}")
    print(f"Robustez: {recommendation['robustness']['pick_robustness']}")
    print(f"Alerta de empate: {_yes_no(recommendation['robustness']['draw_warning'])}")
    print(f"Tactical score: {tactical['tactical_score']}")
    print(
        "Datos faltantes criticos: "
        + ("; ".join(missing_critical) if missing_critical else "none")
    )
    print(f"Uso recomendado quiniela: {decision['recommended_use']['quiniela']}")
    print(f"Uso recomendado apuesta prepartido: {decision['recommended_use']['apuesta_prepartido']}")
    print(f"Prediction history updated: {history_status}")
    print(
        "Notas: "
        f"{refresh['recommended_action']}; "
        f"match_alarm={alarm['alarm_status']}; "
        f"pick_change={recommendation['pick_change_status']}"
    )


def build_nova_recommendations(
    mode: str,
    scope: str,
    requested_match: str | None,
) -> tuple[list[dict], str, int]:
    teams, _, _ = load_default_final_pick_inputs()
    matches = load_friendly_matches(DATA_PATH)
    snapshots_data = load_manual_snapshots(SNAPSHOTS_PATH)
    results_data = load_friendly_results(RESULTS_PATH)
    simulation_mode, simulations = resolve_simulation_mode(mode)
    scoped = _matches_for_scope(matches, teams, scope)
    selected = _filter_matches(scoped, results_data, requested_match)
    recommendations = [
        _build_friendly_recommendation(
            match,
            teams,
            snapshots_data,
            results_data,
            simulation_mode,
            simulations,
        )
        for match in selected
    ]
    return recommendations, simulation_mode, simulations


def run_nova_simulator(mode: str, scope: str, requested_match: str | None) -> None:
    recommendations, _, _ = build_nova_recommendations(mode, scope, requested_match)
    history_status = "not_run"
    if recommendations:
        history = record_prediction_history(recommendations, HISTORY_PATH)
        history_status = history.get("last_update_status", "unknown")

    if not recommendations:
        print("NOVA SIMULATOR")
        print("Partido: none")
        print(f"Modo: {mode}")
        print("Simulaciones: 0")
        print(f"Scope: {scope}")
        print("Notas: no hay partidos pending/upcoming para simular con los filtros actuales")
        return

    for index, recommendation in enumerate(recommendations):
        if index:
            print("")
            print("-" * 72)
            print("")
        _print_compact_recommendation(recommendation, scope, history_status)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ejecuta el pipeline NOVA de quiniela desde un solo comando."
    )
    parser.add_argument(
        "--mode",
        default="quick",
        choices=["quick", "standard", "final"],
        help="Modo de simulacion: quick=10000, standard=100000, final=1000000.",
    )
    parser.add_argument(
        "--scope",
        default="friendly",
        choices=["friendly", "worldcup_only"],
        help="Alcance de partidos a considerar.",
    )
    parser.add_argument(
        "--match",
        default=None,
        help='Partido exacto, por ejemplo "Netherlands vs Uzbekistan".',
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_nova_simulator(args.mode, args.scope, args.match)


if __name__ == "__main__":
    main()
