from scoring_rules import parse_score, result_key, result_label


VALID_STRATEGIES = {"conservador", "balanceado", "agresivo"}


def normalize_strategy(strategy: str) -> str:
    normalized = strategy.strip().lower()
    if normalized not in VALID_STRATEGIES:
        raise ValueError(
            "Estrategia invalida. Usar: conservador, balanceado o agresivo."
        )
    return normalized


def _score_result(score_item: dict) -> str:
    goals_a, goals_b = parse_score(score_item["score"])
    return result_key(goals_a, goals_b)


def _score_total_goals(score_item: dict) -> int:
    goals_a, goals_b = parse_score(score_item["score"])
    return goals_a + goals_b


def _score_goal_difference(score_item: dict) -> int:
    goals_a, goals_b = parse_score(score_item["score"])
    return abs(goals_a - goals_b)


def _most_probable_result(match_result: dict) -> tuple[str, str, float]:
    team_a = match_result["team_a"]
    team_b = match_result["team_b"]
    probs = match_result["probabilities"]

    outcomes = [
        ("team_a_win", f"{team_a} gana", probs[f"{team_a}_win"]),
        ("draw", "Empate", probs["draw"]),
        ("team_b_win", f"{team_b} gana", probs[f"{team_b}_win"]),
    ]
    return max(outcomes, key=lambda item: item[2])


def _risk_from_score_probability(probability: float) -> str:
    if probability >= 0.11:
        return "bajo"
    if probability >= 0.07:
        return "medio"
    return "alto"


def _risk_explanation(risk: str, strategy: str) -> str:
    if risk == "bajo":
        return "Riesgo bajo: el marcador tiene buen respaldo dentro de los escenarios mas probables."
    if risk == "medio":
        return "Riesgo medio: el marcador es plausible, pero hay alternativas cercanas."
    if strategy == "agresivo":
        return "Riesgo alto: se acepta una opcion menos estable buscando mayor potencial de puntos."
    return "Riesgo alto: el marcador exacto tiene baja frecuencia aunque el resultado pueda ser razonable."


def _find_safe_score(top_scores: list[dict], target_result: str) -> dict:
    same_result = [item for item in top_scores if _score_result(item) == target_result]
    candidates = same_result or top_scores
    low_volatility = [
        item
        for item in candidates
        if _score_total_goals(item) <= 3 and _score_goal_difference(item) <= 2
    ]
    candidates = low_volatility or candidates
    return max(candidates, key=lambda item: (item["probability"], -_score_total_goals(item)))


def _find_aggressive_score(top_scores: list[dict], target_result: str) -> dict:
    same_result = [item for item in top_scores if _score_result(item) == target_result]
    candidates = same_result or top_scores
    return max(
        candidates,
        key=lambda item: (
            item["probability"] * 0.70
            + _score_total_goals(item) * 0.025
            + _score_goal_difference(item) * 0.01,
            _score_total_goals(item),
        ),
    )


def _find_balanced_score(top_scores: list[dict], target_result: str) -> dict:
    same_result = [item for item in top_scores if _score_result(item) == target_result]
    if same_result:
        return max(
            same_result,
            key=lambda item: (
                item["probability"] * 0.85
                + min(_score_total_goals(item), 3) * 0.01,
                item["probability"],
            ),
        )
    return top_scores[0]


def _strategy_explanation(strategy: str) -> str:
    explanations = {
        "conservador": (
            "Conservador: prioriza el marcador mas respaldado y evita goleadas "
            "cuando hay opciones probables de menor riesgo."
        ),
        "balanceado": (
            "Balanceado: combina probabilidad del marcador con un poco de "
            "potencial de puntos sin alejarse del resultado principal."
        ),
        "agresivo": (
            "Agresivo: acepta mas riesgo para buscar un marcador con mayor "
            "potencial, especialmente si suma goles dentro de los escenarios del Core."
        ),
    }
    return explanations[strategy]


def choose_quiniela_strategy(match_result: dict, strategy: str = "balanceado") -> dict:
    """
    Convert Core match probabilities into a quiniela recommendation.

    Conservador favors high-probability, low-volatility scores. Balanceado
    blends probability and point potential. Agresivo accepts more variance
    when a higher scoring Core candidate is still plausible.
    """
    strategy = normalize_strategy(strategy)
    top_scores = match_result["top_scores"]
    if not top_scores:
        raise ValueError("El resultado del Core no trae marcadores probables.")

    team_a = match_result["team_a"]
    team_b = match_result["team_b"]
    target_result_key, target_result_label, result_probability = _most_probable_result(match_result)

    safe_score = _find_safe_score(top_scores, target_result_key)
    balanced_score = _find_balanced_score(top_scores, target_result_key)
    aggressive_score = _find_aggressive_score(top_scores, target_result_key)

    if strategy == "conservador":
        selected_score = safe_score
    elif strategy == "agresivo":
        selected_score = aggressive_score
    else:
        selected_score = balanced_score

    goals_a, goals_b = parse_score(selected_score["score"])

    return {
        "strategy": strategy,
        "result": target_result_label,
        "result_probability": result_probability,
        "recommended_score": selected_score["score"],
        "recommended_goals": {
            team_a: goals_a,
            team_b: goals_b,
        },
        "score_probability": selected_score["probability"],
        "confidence": round(result_probability * 100, 2),
        "risk": _risk_from_score_probability(selected_score["probability"]),
        "strategy_explanation": _strategy_explanation(strategy),
        "risk_explanation": _risk_explanation(
            _risk_from_score_probability(selected_score["probability"]),
            strategy,
        ),
        "safe_alternative": {
            "score": safe_score["score"],
            "result": result_label(safe_score["score"], team_a, team_b),
            "probability": round(safe_score["probability"] * 100, 2),
        },
        "aggressive_alternative": {
            "score": aggressive_score["score"],
            "result": result_label(aggressive_score["score"], team_a, team_b),
            "probability": round(aggressive_score["probability"] * 100, 2),
        },
    }
