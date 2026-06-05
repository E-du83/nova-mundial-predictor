from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]

print("NOVA MUNDIAL PREDICTOR — CORE SUMMARY")
print("")

files = [
    "src/match_simulator.py",
    "src/group_simulator.py",
    "src/tournament_simulator.py",
    "src/knockout_simulator.py",
    "src/odds_engine.py",
    "src/odds_history_engine.py",
    "src/official_bracket_2026.py",
    "src/storage/database.py",
    "src/backtesting/backtest_engine.py",
]

for file in files:
    path = ROOT / file
    print(f"{'OK' if path.exists() else 'MISSING'} - {file}")

print("")
print("Data files:")
for file in [
    "data/worldcup_2026_real_groups.json",
    "data/worldcup_2026_real_teams_baseline_v1.json",
    "data/source_manifest_v1.json"
]:
    path = ROOT / file
    print(f"{'OK' if path.exists() else 'MISSING'} - {file}")