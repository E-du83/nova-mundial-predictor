from pathlib import Path

from match_simulator import load_teams
from group_simulator import simulate_group, format_group_report


ROOT = Path(__file__).resolve().parents[1]
teams = load_teams(ROOT / "data" / "sample_teams.json")

# Demo genérico. No representa un grupo oficial real del Mundial.
group_name = "Demo"
group_teams = ["Argentina", "Japón", "México", "Panamá"]

simulations = 100_000

result = simulate_group(group_name, group_teams, teams, simulations=simulations, seed=42)

print(format_group_report(result))