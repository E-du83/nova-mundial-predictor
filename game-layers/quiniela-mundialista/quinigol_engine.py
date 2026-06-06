import math

from strategy_engine import normalize_strategy


def _risk_from_probability(probability: float) -> str:
    if probability >= 0.70:
        return "bajo"
    if probability >= 0.50:
        return "medio"
    return "alto"


def _minute_range(minute: int, risk: str) -> str:
    margin = {"bajo": 8, "medio": 12, "alto": 16}[risk]
    start = max(1, minute - margin)
    end = min(90, minute + margin)
    return f"{start}-{end}"


def _clamp_minute(value: float) -> int:
    return int(max(8, min(85, round(value))))


def recommend_quinigol(match_result: dict, strategy: str = "balanceado") -> dict:
    """
    Recommend a Quinigol pick using Core expected goals.

    This layer treats Quinigol as a 90-minute regular-time game. "No hay" is
    retained as an explicit option when the total-goal profile is low.
    """
    strategy = normalize_strategy(strategy)
    team_a = match_result["team_a"]
    team_b = match_result["team_b"]
    expected = match_result["expected_goals"]
    lambda_a = float(expected[team_a])
    lambda_b = float(expected[team_b])
    total_lambda = max(0.01, lambda_a + lambda_b)

    team_a_scores_probability = 1 - math.exp(-lambda_a)
    team_b_scores_probability = 1 - math.exp(-lambda_b)
    no_goal_probability = math.exp(-total_lambda)

    scorer_options = [
        {
            "team": team_a,
            "probability": team_a_scores_probability,
            "lambda": lambda_a,
        },
        {
            "team": team_b,
            "probability": team_b_scores_probability,
            "lambda": lambda_b,
        },
    ]
    scorer_options.sort(key=lambda item: item["probability"], reverse=True)

    if strategy == "conservador" and no_goal_probability >= 0.30:
        selected = {
            "team": "No hay",
            "probability": no_goal_probability,
            "lambda": 0.0,
        }
    elif strategy == "agresivo" and scorer_options[1]["probability"] >= 0.38:
        selected = scorer_options[1]
    else:
        selected = scorer_options[0]

    if selected["team"] == "No hay":
        risk = _risk_from_probability(selected["probability"])
        return {
            "recommended": "No hay gol en 90 minutos",
            "team": "No hay",
            "minute": None,
            "minute_label": "No aplica",
            "minute_range": "Sin gol en 90 minutos",
            "risk": risk,
            "probability": round(selected["probability"] * 100, 2),
            "no_goal_option": {
                "label": "No hay",
                "probability": round(no_goal_probability * 100, 2),
            },
        }

    base_minute = 90 / total_lambda
    if strategy == "conservador":
        minute = _clamp_minute(base_minute + 6)
    elif strategy == "agresivo":
        minute = _clamp_minute(base_minute + 10)
    else:
        minute = _clamp_minute(base_minute)

    risk = _risk_from_probability(selected["probability"])

    return {
        "recommended": f"{selected['team']} anota",
        "team": selected["team"],
        "minute": minute,
        "minute_label": f"minuto {minute}",
        "minute_range": _minute_range(minute, risk),
        "risk": risk,
        "probability": round(selected["probability"] * 100, 2),
        "no_goal_option": {
            "label": "No hay",
            "probability": round(no_goal_probability * 100, 2),
        },
    }
