from pathlib import Path

from match_simulator import load_teams, simulate_match, choose_recommendation, format_report


ROOT = Path(__file__).resolve().parents[1]
teams = load_teams(ROOT / "data" / "sample_teams.json")

# Demo inicial. Cambiar equipos aquí:
team_a = "Argentina"
team_b = "Japón"

# Cambiar cantidad de simulaciones.
# Para prueba rápida: 10_000
# Para análisis serio: 100_000
# Para análisis avanzado: 1_000_000
simulations = 100_000

# Cuotas de ejemplo. En una versión futura esto vendrá por API.
# Si no conocés una cuota, podés quitarla o dejarla en None.
odds = {
    "team_a_win": 1.55,
    "draw": 3.90,
    "team_b_win": 6.20,
    "under_3_5_goals": 1.42,
    "under_2_5_goals": 1.90,
    "both_teams_score_yes": 1.95,
}

result = simulate_match(team_a, team_b, teams, simulations=simulations, seed=42)
recommendation = choose_recommendation(result, odds=odds, stake_example=10_000)

print(format_report(result, recommendation))