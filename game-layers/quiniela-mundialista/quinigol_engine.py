import math

from quinigol_minute_policy import apply_quinigol_minute_policy
from scoring_rules import parse_score
from strategy_engine import normalize_strategy


def _risk_from_probability(probability: float) -> str:
    if probability >= 0.68:
        return "bajo"
    if probability >= 0.50:
        return "medio"
    return "alto"


def _minute_range(minute: int, risk: str, total_lambda: float) -> str:
    margin = {"bajo": 8, "medio": 12, "alto": 16}[risk]
    if total_lambda < 1.65:
        margin += 4
    start = max(1, minute - margin)
    end = min(90, minute + margin)
    return f"{start}-{end}"


def _clamp_minute(value: float) -> int:
    return int(max(8, min(85, round(value))))


def _probability_percent(probability: float) -> float:
    return round(probability * 100, 2)


def _simple_risk_explanation(risk: str) -> str:
    explanations = {
        "bajo": "riesgo bajo: el dato principal tiene respaldo fuerte del modelo.",
        "medio": "riesgo medio: hay una tendencia clara, pero el partido sigue abierto.",
        "alto": "riesgo alto: la jugada depende de un escenario menos estable.",
    }
    return explanations[risk]


def _outcome_probabilities_for_team(match_result: dict, team: str) -> dict:
    team_a = match_result["team_a"]
    team_b = match_result["team_b"]
    probabilities = match_result["probabilities"]

    if team == team_a:
        return {
            "win": probabilities[f"{team_a}_win"],
            "draw": probabilities["draw"],
            "loss": probabilities[f"{team_b}_win"],
        }

    return {
        "win": probabilities[f"{team_b}_win"],
        "draw": probabilities["draw"],
        "loss": probabilities[f"{team_a}_win"],
    }


def _recommended_goals_for_team(match_result: dict, team: str) -> int:
    score = match_result.get("recommended_score")
    if not score:
        context = match_result.get("quiniela_context", {})
        score = context.get("recommended_score")
    if not score:
        return 0

    goals_a, goals_b = parse_score(score)
    if team == match_result["team_a"]:
        return goals_a
    return goals_b


def _strength_edge_for_team(match_result: dict, team: str) -> float:
    difference = match_result.get("strength_difference")
    if isinstance(difference, dict):
        value = float(difference.get(team, 0.0))
    else:
        value = 0.0
    return max(-0.35, min(0.35, value / 350))


def _no_goal_threshold(strategy: str) -> float:
    thresholds = {
        "conservador": 0.22,
        "balanceado": 0.28,
        "agresivo": 0.34,
    }
    return thresholds[strategy]


def _build_team_option(match_result: dict, team: str, own_lambda: float, other_lambda: float) -> dict:
    goal_probability = 1 - math.exp(-own_lambda)
    outcome = _outcome_probabilities_for_team(match_result, team)
    recommended_goals = _recommended_goals_for_team(match_result, team)
    strength_edge = _strength_edge_for_team(match_result, team)

    selection_score = (
        goal_probability * 0.52
        + outcome["win"] * 0.24
        + max(0, recommended_goals) * 0.075
        + strength_edge * 0.08
        - outcome["loss"] * 0.05
    )

    return {
        "team": team,
        "probability": goal_probability,
        "lambda": own_lambda,
        "other_lambda": other_lambda,
        "outcome": outcome,
        "recommended_goals": recommended_goals,
        "strength_edge": strength_edge,
        "selection_score": selection_score,
    }


def _select_team_option(options: list[dict], strategy: str) -> dict:
    if strategy == "conservador":
        return max(
            options,
            key=lambda item: (
                item["selection_score"],
                item["probability"],
                -item["outcome"]["loss"],
            ),
        )

    if strategy == "agresivo":
        return max(
            options,
            key=lambda item: (
                item["selection_score"]
                + item["recommended_goals"] * 0.045
                + item["outcome"]["loss"] * 0.045,
                item["probability"],
            ),
        )

    return max(options, key=lambda item: (item["selection_score"], item["probability"]))


def _estimate_goal_minute(option: dict, strategy: str, total_lambda: float, draw_probability: float) -> int:
    base_minute = 90 / max(total_lambda + 0.15, 0.35)
    minute = base_minute
    minute -= (option["lambda"] - option["other_lambda"]) * 5.0
    minute -= (option["outcome"]["win"] - 0.33) * 10.0
    minute -= option["strength_edge"] * 8.0
    minute -= max(0, option["recommended_goals"] - 1) * 5.0

    if option["recommended_goals"] == 0:
        minute += 8.0
    if draw_probability >= 0.31:
        minute += 4.0

    if strategy == "conservador":
        minute += 3.0
    elif strategy == "agresivo":
        if option["outcome"]["loss"] > option["outcome"]["win"]:
            minute += 7.0
        else:
            minute -= 2.0

    risk = _risk_from_probability(option["probability"])
    if risk == "medio":
        minute += 2.0
    elif risk == "alto":
        minute += 6.0

    return _clamp_minute(minute)


def _minute_explanation(option: dict, minute: int, minute_range: str) -> str:
    return (
        f"El minuto {minute} es una estimacion probabilistica basada en xG, "
        f"probabilidades 1X2, fuerza relativa y marcador recomendado; el rango "
        f"{minute_range} es mas importante que el minuto exacto."
    )


def recommend_quinigol(match_result: dict, strategy: str = "balanceado") -> dict:
    """
    Recommend one Quinigol pick using Core expected goals and local strategy context.

    Quinigol is not a full scoring timeline. It is the recommended goal event
    for this specific match, or "No hay" when the goal profile is too low.
    """
    strategy = normalize_strategy(strategy)
    team_a = match_result["team_a"]
    team_b = match_result["team_b"]
    expected = match_result["expected_goals"]
    lambda_a = float(expected[team_a])
    lambda_b = float(expected[team_b])
    total_lambda = max(0.01, lambda_a + lambda_b)

    no_goal_probability = math.exp(-total_lambda)
    context = match_result.get("quiniela_context", {})
    recommended_score = match_result.get("recommended_score") or context.get("recommended_score")
    draw_probability = match_result["probabilities"]["draw"]

    scorer_options = [
        _build_team_option(match_result, team_a, lambda_a, lambda_b),
        _build_team_option(match_result, team_b, lambda_b, lambda_a),
    ]
    selected = _select_team_option(scorer_options, strategy)

    recommended_score_is_no_goal = recommended_score == "0-0"
    if (
        no_goal_probability >= _no_goal_threshold(strategy)
        or (strategy != "agresivo" and recommended_score_is_no_goal)
    ):
        selected = {
            "team": "No hay",
            "probability": no_goal_probability,
            "lambda": 0.0,
            "outcome": {"win": 0.0, "draw": draw_probability, "loss": 0.0},
        }

    if selected["team"] == "No hay":
        risk = _risk_from_probability(selected["probability"])
        return apply_quinigol_minute_policy(match_result, {
            "recommended": "No hay gol en 90 minutos",
            "team": "No hay",
            "minute": None,
            "minute_label": "No aplica",
            "minute_range": "Sin gol en 90 minutos",
            "risk": risk,
            "risk_explanation": _simple_risk_explanation(risk),
            "probability": _probability_percent(selected["probability"]),
            "goal_probability": _probability_percent(selected["probability"]),
            "outcome_probability": _probability_percent(draw_probability),
            "no_goal_option": {
                "label": "No hay",
                "probability": _probability_percent(no_goal_probability),
                "is_recommended": True,
            },
            "range_priority_note": "Para Quinigol importa mas el escenario que un minuto exacto.",
            "minute_explanation": (
                "La opcion 'No hay' aparece porque la probabilidad de gol es baja "
                "para este perfil de partido."
            ),
        }, recommended_score)

    minute = _estimate_goal_minute(selected, strategy, total_lambda, draw_probability)
    risk = _risk_from_probability(selected["probability"])
    minute_range = _minute_range(minute, risk, total_lambda)

    return apply_quinigol_minute_policy(match_result, {
        "recommended": f"{selected['team']} anota gol recomendado",
        "team": selected["team"],
        "minute": minute,
        "minute_label": f"minuto {minute}",
        "minute_range": minute_range,
        "risk": risk,
        "risk_explanation": _simple_risk_explanation(risk),
        "probability": _probability_percent(selected["probability"]),
        "goal_probability": _probability_percent(selected["probability"]),
        "outcome_probability": _probability_percent(selected["outcome"]["win"]),
        "no_goal_option": {
            "label": "No hay",
            "probability": _probability_percent(no_goal_probability),
            "is_recommended": False,
        },
        "range_priority_note": "El rango probable pesa mas que el minuto exacto.",
        "minute_explanation": _minute_explanation(selected, minute, minute_range),
        "inputs_used": {
            "expected_goals": {
                selected["team"]: selected["lambda"],
            },
            "win_probability": _probability_percent(selected["outcome"]["win"]),
            "draw_probability": _probability_percent(selected["outcome"]["draw"]),
            "loss_probability": _probability_percent(selected["outcome"]["loss"]),
            "recommended_score": recommended_score,
            "strategy": strategy,
        },
    }, recommended_score)
