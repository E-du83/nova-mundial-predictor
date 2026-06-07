import argparse

from critical_alternative_engine import format_critical_alternative_lines
from decision_weighting_engine import format_decision_weighting_lines
from formation_tactical_engine import format_formation_tactical_lines
from run_friendly_test_demo import build_friendly_recommendations


def _print_decision(recommendation: dict) -> None:
    print(f"Partido: {recommendation['match']}")
    print(f"Modo de simulacion: {recommendation['simulation_mode']}")
    print(f"Simulaciones usadas: {recommendation['simulations_used']}")
    print(f"Quinigol: {recommendation['quinigol']}")
    print(f"Rango probable: {recommendation['quinigol_range']}")
    print(f"Minuto referencia: {recommendation['reference_minute']}")
    print(f"Confianza: {recommendation['adjusted_confidence']}")
    print(f"Riesgo: {recommendation['friendly_risk']}")
    print(f"Robustez: {recommendation['robustness']['pick_robustness']}")
    print(f"Alerta de empate: {'si' if recommendation['robustness']['draw_warning'] else 'no'}")
    print("")

    for line in format_critical_alternative_lines(recommendation["critical_alternatives"]):
        print(line)
    print("")

    for line in format_formation_tactical_lines(recommendation["research_weighting"]["tactical_weighting"]):
        print(line)
    print("")

    for line in format_decision_weighting_lines(recommendation["decision_weighting"]):
        print(line)
    print("")
    print("-" * 72)
    print("")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Corre Decision Weighting + Critical Alternative Layer v1."
    )
    parser.add_argument(
        "--mode",
        default="standard",
        choices=["quick", "standard", "final"],
        help="Modo de simulacion: quick=10000, standard=100000, final=1000000.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    recommendations, excluded, simulation_mode, simulations = build_friendly_recommendations(args.mode)

    print("NOVA DECISION WEIGHTING + CRITICAL ALTERNATIVE v1")
    print(f"Modo de simulacion: {simulation_mode}")
    print(f"Simulaciones usadas: {simulations}")
    print("")

    print("PARTIDOS ACTIVOS")
    for recommendation in recommendations:
        print(f"- {recommendation['match']}")
    print("")

    print("PARTIDOS EXCLUIDOS")
    for match in excluded:
        missing = ", ".join(match.get("missing_teams", [])) or "no aplica"
        print(f"- {match['match']} | razon: {match.get('reason')} | faltantes: {missing}")
    print("")

    for recommendation in recommendations:
        _print_decision(recommendation)


if __name__ == "__main__":
    main()
