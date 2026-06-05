"""
Backtesting scaffold.

Purpose:
Measure whether the model is calibrated and useful before trusting it for betting decisions.

Metrics planned:
- Brier Score
- Log Loss
- ROI
- CLV
- calibration buckets
"""

import math


def brier_score(probability: float, outcome: int) -> float:
    return (probability - outcome) ** 2


def log_loss(probability: float, outcome: int, eps: float = 1e-15) -> float:
    p = max(eps, min(1 - eps, probability))
    return -(outcome * math.log(p) + (1 - outcome) * math.log(1 - p))


def simple_roi(total_return: float, total_staked: float) -> float:
    if total_staked == 0:
        return 0.0
    return (total_return - total_staked) / total_staked


def calibration_bucket(probability: float, bucket_size: float = 0.10) -> str:
    lower = int(probability / bucket_size) * bucket_size
    upper = lower + bucket_size
    return f"{lower:.1f}-{upper:.1f}"