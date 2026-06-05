from pathlib import Path
import json

from match_simulator import simulate_match
from odds_engine import evaluate_1x2_multi_bookmaker, format_multi_bookmaker_report

ROOT = Path(__file__).resolve().parents[1]
teams = json.loads((ROOT / "data" / "worldcup_2026_real_teams_baseline_v1.json").read_text(encoding="utf-8"))
odds_data = json.loads((ROOT / "data" / "sample_odds_multi_bookmaker.json").read_text(encoding="utf-8"))

simulations = 100_000

for match in odds_data["matches"]:
    home = match["home"]
    away = match["away"]
    sim = simulate_match(home, away, teams, simulations=simulations, seed=2026)

    model_probs = {
        "home": sim["probabilities"][f"{home}_win"],
        "draw": sim["probabilities"]["draw"],
        "away": sim["probabilities"][f"{away}_win"],
    }

    evaluation = evaluate_1x2_multi_bookmaker(
        model_probs=model_probs,
        bookmakers=match["bookmakers"],
        stake_example=10_000,
        bankroll=100_000
    )

    print("=" * 72)
    print(format_multi_bookmaker_report(f"{home} vs {away}", evaluation, stake_example=10_000))
    print("")