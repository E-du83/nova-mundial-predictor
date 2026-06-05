from pathlib import Path
import json

from match_simulator import load_teams
from tournament_simulator import simulate_tournament_groups, format_tournament_group_report


ROOT = Path(__file__).resolve().parents[1]
teams = load_teams(ROOT / "data" / "sample_teams.json")
groups = json.loads((ROOT / "data" / "sample_tournament_groups.json").read_text(encoding="utf-8"))

# Para prueba rápida: 10_000
# Para análisis serio: 100_000
# Para análisis avanzado: 1_000_000
simulations = 10_000

result = simulate_tournament_groups(groups, teams, simulations=simulations, seed=42)

print(format_tournament_group_report(result))