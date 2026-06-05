from pathlib import Path
import json
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
teams = json.loads((ROOT / "data" / "worldcup_2026_real_teams_baseline_v1.json").read_text(encoding="utf-8"))

counter = Counter()
for team, data in teams.items():
    for key, value in data["data_quality"].items():
        counter[f"{key}: {value}"] += 1

print("NOVA DATA QUALITY SUMMARY")
print("")
for k, v in counter.most_common():
    print(f"{k}: {v}")