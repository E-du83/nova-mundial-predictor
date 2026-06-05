from pathlib import Path
import json

from odds_history_engine import evaluate_odds_timing, format_odds_history_report

ROOT = Path(__file__).resolve().parents[1]
history = json.loads((ROOT / "data" / "sample_odds_history.json").read_text(encoding="utf-8"))

for item in history["markets"]:
    evaluation = evaluate_odds_timing(
        model_probability=item["model_probability"],
        records=item["records"],
        stake_example=10_000
    )

    print("=" * 72)
    print(format_odds_history_report(
        match_name=item["match"],
        market_name=item["market"],
        evaluation=evaluation,
        stake_example=10_000
    ))
    print("")