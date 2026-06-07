from scoring_rules import parse_score


def _result_label(goals_a: int, goals_b: int, team_a: str, team_b: str) -> str:
    if goals_a > goals_b:
        return team_a
    if goals_b > goals_a:
        return team_b
    return "Empate"


def _minute_number(minute_label: str) -> int | None:
    digits = "".join(ch for ch in str(minute_label) if ch.isdigit())
    return int(digits) if digits else None


def _half_time_score(final_score: str, reference_minute: str, total_xg: float) -> str:
    goals_a, goals_b = parse_score(final_score)
    ref_minute = _minute_number(reference_minute)

    if total_xg < 1.8:
        return "0-0"
    if ref_minute is not None and ref_minute <= 25:
        if goals_a > goals_b and goals_a > 0:
            return "1-0"
        if goals_b > goals_a and goals_b > 0:
            return "0-1"
    if goals_a + goals_b >= 3:
        if goals_a > goals_b:
            return "1-0"
        if goals_b > goals_a:
            return "0-1"
    return "0-0"


def build_half_time_pick(final_pick: dict, match_type: str = "international_friendly") -> dict:
    team_a, team_b = [part.strip() for part in final_pick["match"].split(" vs ", 1)]
    final_goals_a, final_goals_b = parse_score(final_pick["final_score"])
    selected = next(
        item for item in final_pick["scenario_evaluations"]
        if item["strategy"] == final_pick["selected_strategy"]
    )
    core = selected["recommendation"]["core"]
    expected = core["expected_goals"]
    total_xg = float(expected[team_a]) + float(expected[team_b])
    ht_score = _half_time_score(
        final_pick["final_score"],
        final_pick["reference_minute"],
        total_xg,
    )
    ht_goals_a, ht_goals_b = parse_score(ht_score)
    ht_result = _result_label(ht_goals_a, ht_goals_b, team_a, team_b)
    ft_result = _result_label(final_goals_a, final_goals_b, team_a, team_b)
    friendly = match_type == "international_friendly"
    risk = "medio" if friendly or final_pick["risk"] == "medio" else final_pick["risk"]

    if friendly and ht_score == "0-0":
        explanation = "Amistoso con incertidumbre alta: se prioriza descanso prudente 0-0 aunque el pick final tenga ganador."
    elif _minute_number(final_pick["reference_minute"]) is not None:
        explanation = "Partido proyectado con gol temprano/moderado segun Quinigol, minuto referencia y xG."
    else:
        explanation = "Descanso estimado desde marcador final recomendado y xG Core."

    return {
        "half_time_score": ht_score,
        "half_time_result": ht_result,
        "half_time_full_time": f"{ht_result}/{ft_result}",
        "half_time_risk": risk,
        "explanation": explanation,
        "total_xg": round(total_xg, 2),
    }


def format_half_time_lines(half_time: dict) -> list[str]:
    return [
        f"Descanso recomendado: {half_time['half_time_score']}",
        f"Resultado probable al descanso: {half_time['half_time_result']}",
        f"Descanso/final recomendado: {half_time['half_time_full_time']}",
        f"Riesgo descanso: {half_time['half_time_risk']}",
        f"Explicacion descanso: {half_time['explanation']}",
    ]
