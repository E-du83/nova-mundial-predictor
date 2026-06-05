from pathlib import Path
import json

from knockout_simulator import simulate_full_tournament_knockout, format_knockout_report

ROOT = Path(__file__).resolve().parents[1]
teams = json.loads((ROOT / "data" / "worldcup_2026_real_teams_baseline_v1.json").read_text(encoding="utf-8"))
groups = json.loads((ROOT / "data" / "worldcup_2026_real_groups.json").read_text(encoding="utf-8"))

# Para prueba rápida: 2_000
# Para análisis medio: 10_000
# Para análisis serio: 100_000
simulations = 2_000

result = simulate_full_tournament_knockout(groups, teams, simulations=simulations, seed=2026)

print(format_knockout_report(result))