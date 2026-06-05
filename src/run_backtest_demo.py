from backtesting.backtest_engine import brier_score, log_loss, simple_roi, calibration_bucket

# Demo only.
examples = [
    {"probability": 0.62, "outcome": 1},
    {"probability": 0.55, "outcome": 0},
    {"probability": 0.78, "outcome": 1},
]

print("NOVA BACKTEST DEMO")
for row in examples:
    p = row["probability"]
    y = row["outcome"]
    print({
        "probability": p,
        "outcome": y,
        "brier": round(brier_score(p, y), 4),
        "log_loss": round(log_loss(p, y), 4),
        "bucket": calibration_bucket(p)
    })

print("ROI demo:", round(simple_roi(total_return=115000, total_staked=100000) * 100, 2), "%")