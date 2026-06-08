from __future__ import annotations

import json
from pathlib import Path

from prediction_history_engine import load_prediction_history
from result_review_engine import load_friendly_results
from scoring_rules import parse_score, result_key, result_label


PENDING = "pending_real_result"


def _btts(score: str) -> bool:
    goals_a, goals_b = parse_score(score)
    return goals_a > 0 and goals_b > 0


def _result(score: str) -> str:
    return result_key(*parse_score(score))


def _latest_reviewed_entries(history: dict) -> dict[str, dict]:
    latest = {}
    for entry in history.get("entries", []):
        if entry.get("real_status") == "final" and entry.get("marcador_recomendado"):
            latest[entry["match"]] = entry
    return latest


def build_backtest_comparison(prediction: dict, real_result: dict) -> dict:
    predicted_score = prediction.get("marcador_recomendado", prediction.get("predicted_score"))
    real_score = real_result.get("real_score")
    pred_a, pred_b = parse_score(predicted_score)
    real_a, real_b = parse_score(real_score)
    predicted_result = result_label(predicted_score, real_result["team_a"], real_result["team_b"])
    real_label = real_result.get("real_result") or result_label(real_score, real_result["team_a"], real_result["team_b"])
    btts_predicted = _btts(predicted_score)
    btts_real = _btts(real_score)
    return {
        "match": real_result["match"],
        "predicted_score": predicted_score,
        "real_score": real_score,
        "predicted_result": predicted_result,
        "real_result": real_label,
        "exact_score_hit": predicted_score == real_score,
        "result_hit": _result(predicted_score) == _result(real_score),
        "btts_predicted": btts_predicted,
        "btts_real": btts_real,
        "btts_hit": btts_predicted == btts_real,
        "goal_diff_error": abs((pred_a - pred_b) - (real_a - real_b)),
        "total_goals_error": abs((pred_a + pred_b) - (real_a + real_b)),
        "quinigol_team_hit": prediction.get("acierto_quinigol_equipo", PENDING),
        "quinigol_minute_error": prediction.get("error_minuto_quinigol", PENDING),
        "halftime_fulltime_hit": prediction.get("acierto_descanso_final", PENDING),
        "brier_ready_fields": {
            "has_1x2_probabilities": False,
            "probability_source": "pending_probability_snapshot",
            "actual_result": _result(real_score),
        },
        "log_loss_ready_fields": {
            "has_class_probabilities": False,
            "probability_source": "pending_probability_snapshot",
            "actual_result": _result(real_score),
        },
        "notes": "Friendly demo comparison only; not a full historical World Cup backtest.",
    }


def build_friendly_backtest_demo(history_path: str | Path, results_path: str | Path) -> dict:
    history = load_prediction_history(history_path)
    results = load_friendly_results(results_path)
    latest = _latest_reviewed_entries(history)
    comparisons = []
    for result in results.get("results", []):
        prediction = latest.get(result.get("match"))
        if result.get("status") == "final" and prediction:
            comparisons.append(build_backtest_comparison(prediction, result))
    return {
        "data_status": "friendly_backtesting_demo_v1",
        "comparison_count": len(comparisons),
        "comparisons": comparisons,
        "notes": "Foundation only. World Cup 2022 requires blind test and data leakage guard before use.",
    }


def load_backtesting_manifest(path: str | Path) -> dict:
    manifest_path = Path(path)
    if not manifest_path.exists():
        return {
            "data_status": "manual_snapshot_required",
            "datasets": [],
            "message": "backtesting_manifest.json not found.",
        }
    return json.loads(manifest_path.read_text(encoding="utf-8"))
