from pathlib import Path

from quiniela_engine import (
    ROOT,
    format_quiniela_recommendation,
    load_teams,
    recommend_many_matches,
)
from scoring_rules import score_game
from simulation_config import resolve_simulation_mode


def run_validation() -> None:
    exact_with_quinigol = score_game("2-1", "2-1", "Argentina", "Argentina")
    winner_one_goal = score_game("2-0", "2-1")
    result_only = score_game("1-1", "0-0")

    assert exact_with_quinigol["total_points"] == 9
    assert winner_one_goal["match_points"] == 5
    assert result_only["match_points"] == 3


def main() -> None:
    teams_path = ROOT / "data" / "worldcup_2026_real_teams_baseline_v1.json"
    teams = load_teams(teams_path)
    simulation_mode, simulations = resolve_simulation_mode("quick")

    matches = [
        ("Mexico", "South Africa", "conservador"),
        ("Brazil", "Morocco", "balanceado"),
        ("Argentina", "Austria", "agresivo"),
    ]

    recommendations = recommend_many_matches(
        matches,
        teams,
        simulations=simulations,
        simulation_mode=simulation_mode,
        seed=2026,
    )

    print("NOVA QUINIELA MUNDIALISTA - DEMO")
    print("Juego: 90 minutos, incluye dos tiempos regulares.")
    print("")

    for recommendation in recommendations:
        print(format_quiniela_recommendation(recommendation))
        print("")
        print("-" * 72)
        print("")

    run_validation()
    print("VALIDACION SIMPLE: OK")
    print(f"Datos usados: {Path(teams_path).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
