import argparse

from half_time_engine import format_half_time_lines
from pick_robustness_engine import format_robustness_lines
from result_review_engine import format_result_review_lines
from run_friendly_test_demo import build_friendly_recommendations


def _print_match_intelligence(recommendation: dict) -> None:
    print(f"Partido: {recommendation['match']}")
    print(f"Modo de simulacion: {recommendation['simulation_mode']}")
    print(f"Simulaciones usadas: {recommendation['simulations_used']}")
    print(f"Prediccion actual: {recommendation['final_recommendation']}")
    print(f"Marcador recomendado: {recommendation['recommended_score']}")
    print(f"Quinigol recomendado: {recommendation['quinigol']}")
    print(f"Rango probable: {recommendation['quinigol_range']}")
    print(f"Minuto referencia: {recommendation['reference_minute']}")
    print(f"Confianza ajustada: {recommendation['adjusted_confidence']}")
    print(f"Riesgo amistoso: {recommendation['friendly_risk']}")
    print("")

    for line in format_half_time_lines(recommendation["half_time"]):
        print(line)
    print("")

    for line in format_robustness_lines(recommendation["robustness"]):
        print(line)
    print("")

    print(f"Market alignment: {recommendation['research_weighting']['market_alignment']}")
    print(f"Model fragility: {recommendation['research_weighting']['model_fragility']}")
    print(
        "Missing critical data: "
        + (
            "; ".join(recommendation["research_weighting"]["missing_critical_data"])
            if recommendation["research_weighting"]["missing_critical_data"]
            else "none"
        )
    )
    print("")

    for line in format_result_review_lines(recommendation["result_review"]):
        print(line)
    print("")
    print("-" * 72)
    print("")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Corre Match Intelligence Final Test v1 para amistosos activos."
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
    print("NOVA MATCH INTELLIGENCE FINAL TEST v1")
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
        _print_match_intelligence(recommendation)


if __name__ == "__main__":
    main()
