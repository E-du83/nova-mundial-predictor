from scoring_rules import parse_score


def _clamp_minute(value: float) -> int:
    return int(max(8, min(85, round(value))))


def _probability_key_for_team(probabilities: dict, team: str) -> str | None:
    key = f"{team}_win"
    return key if key in probabilities else None


def _favorite_1x2(match_result: dict) -> str:
    team_a = match_result["team_a"]
    team_b = match_result["team_b"]
    probabilities = match_result.get("probabilities", {})
    candidates = []
    for team in (team_a, team_b):
        key = _probability_key_for_team(probabilities, team)
        if key:
            candidates.append((team, float(probabilities[key])))
    if not candidates:
        return team_a
    return max(candidates, key=lambda item: item[1])[0]


def _first_goal_probability(match_result: dict, team: str) -> float | None:
    probabilities = match_result.get("first_goal_probabilities")
    if not isinstance(probabilities, dict):
        probabilities = match_result.get("first_goal_probability")
    if not isinstance(probabilities, dict):
        return None
    value = probabilities.get(team)
    return float(value) if value is not None else None


def _preferred_team_for_goal(match_result: dict, goals_a: int, goals_b: int) -> str:
    team_a = match_result["team_a"]
    team_b = match_result["team_b"]
    if goals_a > 0 and goals_b == 0:
        return team_a
    if goals_b > 0 and goals_a == 0:
        return team_b

    expected = match_result.get("expected_goals", {})
    lambda_a = float(expected.get(team_a, 0.0))
    lambda_b = float(expected.get(team_b, 0.0))
    if lambda_a > lambda_b:
        return team_a
    if lambda_b > lambda_a:
        return team_b

    first_a = _first_goal_probability(match_result, team_a)
    first_b = _first_goal_probability(match_result, team_b)
    if first_a is not None and first_b is not None and first_a != first_b:
        return team_a if first_a > first_b else team_b

    return _favorite_1x2(match_result)


def _fallback_minute(match_result: dict, team: str) -> int:
    team_a = match_result["team_a"]
    team_b = match_result["team_b"]
    expected = match_result.get("expected_goals", {})
    team_lambda = float(expected.get(team, 0.0))
    other_team = team_b if team == team_a else team_a
    other_lambda = float(expected.get(other_team, 0.0))
    total_lambda = max(0.35, team_lambda + other_lambda)
    minute = 90 / (total_lambda + 0.15)
    minute -= (team_lambda - other_lambda) * 5.0
    return _clamp_minute(minute)


def _fallback_range(minute: int) -> str:
    return f"{max(1, minute - 12)}-{min(90, minute + 12)}"


def apply_quinigol_minute_policy(
    match_result: dict,
    quinigol: dict,
    predicted_score: str | tuple[int, int] | None = None,
) -> dict:
    """
    Enforce the final Quinigol policy against the predicted score.

    The engine can estimate a scenario, but the registered pick must remain
    coherent with the final score: 0-0 means no goal, any scored match needs a
    concrete team and minute.
    """
    normalized = dict(quinigol)
    score = predicted_score or match_result.get("recommended_score")
    goals_a, goals_b = parse_score(score)

    if goals_a == 0 and goals_b == 0:
        normalized.update(
            {
                "recommended": "No hay gol en 90 minutos",
                "team": "No hay",
                "minute": None,
                "minute_label": "No hay gol",
                "minute_range": "No aplica",
                "policy_applied": "score_0_0_no_goal",
                "policy_explanation": "Marcador predicho 0-0: Quinigol se registra como No hay gol.",
            }
        )
        return normalized

    expected_team = _preferred_team_for_goal(match_result, goals_a, goals_b)
    current_team = normalized.get("team")
    current_minute = normalized.get("minute")
    current_label = str(normalized.get("minute_label", ""))
    team_has_predicted_goal = (
        (current_team == match_result["team_a"] and goals_a > 0)
        or (current_team == match_result["team_b"] and goals_b > 0)
    )

    correction_needed = (
        current_team in (None, "No hay", "No hay gol")
        or current_minute is None
        or current_label.lower() in ("no aplica", "no hay gol")
        or (goals_a > 0 and goals_b > 0 and current_team != expected_team)
        or not team_has_predicted_goal
    )

    if not correction_needed:
        normalized["policy_applied"] = "normal"
        normalized.setdefault(
            "policy_explanation",
            "Quinigol coherente con marcador predicho y minuto registrado.",
        )
        return normalized

    minute = current_minute if isinstance(current_minute, int) else _fallback_minute(match_result, expected_team)
    minute_range = normalized.get("minute_range")
    if not minute_range or str(minute_range).lower() in ("no aplica", "sin gol en 90 minutos"):
        minute_range = _fallback_range(minute)

    normalized.update(
        {
            "recommended": f"{expected_team} anota gol recomendado",
            "team": expected_team,
            "minute": minute,
            "minute_label": f"minuto {minute}",
            "minute_range": minute_range,
            "policy_applied": "minute_forced_by_predicted_goals",
            "policy_explanation": (
                "Marcador predicho con goles: la politica fuerza equipo y minuto "
                "concretos para el Quinigol registrado."
            ),
        }
    )
    return normalized
