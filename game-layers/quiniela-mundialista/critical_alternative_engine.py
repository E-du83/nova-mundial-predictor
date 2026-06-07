from scoring_rules import parse_score


def _score_result(score: str) -> str:
    goals_a, goals_b = parse_score(score)
    if goals_a > goals_b:
        return "team_a_win"
    if goals_b > goals_a:
        return "team_b_win"
    return "draw"


def _score_total_goals(score: str) -> int:
    goals_a, goals_b = parse_score(score)
    return goals_a + goals_b


def _format_option(option: dict | None) -> str:
    if not option:
        return "none"
    probability = round(option.get("probability", 0.0) * 100, 2)
    return f"{option['score']} ({probability}%)"


def _potential_points(score: str, recommended_result: str) -> int:
    result = _score_result(score)
    base = 7
    if "gana" in str(recommended_result).lower() and result == "draw":
        return 4
    return base + min(2, _score_total_goals(score) // 2)


def build_critical_alternatives(recommendation: dict) -> dict:
    top_scores = recommendation["robustness"].get("top_scores", [])
    primary = next(
        (item for item in top_scores if item.get("score") == recommendation["recommended_score"]),
        top_scores[0] if top_scores else None,
    )
    candidates = [item for item in top_scores if not primary or item["score"] != primary["score"]]
    critical = None
    if primary and candidates:
        sorted_candidates = sorted(
            candidates,
            key=lambda item: abs(float(primary["probability"]) - float(item["probability"])),
        )
        if abs(float(primary["probability"]) - float(sorted_candidates[0]["probability"])) <= 0.015:
            critical = sorted_candidates[0]

    draw_warning = bool(
        critical and _score_result(critical["score"]) == "draw"
        or recommendation["robustness"].get("draw_warning")
    )

    tempting_candidates = [
        item for item in top_scores
        if primary
        and item["score"] != primary["score"]
        and _potential_points(item["score"], recommendation["final_recommendation"])
        > _potential_points(primary["score"], recommendation["final_recommendation"])
    ]
    tempting = None
    if tempting_candidates:
        tempting = max(
            tempting_candidates,
            key=lambda item: (
                _potential_points(item["score"], recommendation["final_recommendation"]),
                item["probability"],
            ),
        )

    return {
        "principal_pick": {
            "result": recommendation["final_recommendation"],
            "score": recommendation["recommended_score"],
            "probability": primary.get("probability", "pending_real_data") if primary else "pending_real_data",
        },
        "critical_alternative": critical,
        "critical_alternative_active": critical is not None,
        "tempting_option": tempting,
        "draw_warning": draw_warning,
        "why_this_pick": (
            f"El pick principal mantiene el marcador {recommendation['recommended_score']} porque viene del Core "
            f"y queda contrastado por robustez {recommendation['robustness']['pick_robustness']}."
        ),
        "why_not_tempting": (
            "La opcion tentadora ofrece mayor recompensa/puntos potenciales, pero tiene menor probabilidad o mayor riesgo."
            if tempting
            else "No hay opcion tentadora clara dentro del top de marcadores."
        ),
    }


def format_critical_alternative_lines(alternatives: dict) -> list[str]:
    principal = alternatives["principal_pick"]
    return [
        f"Pick principal: {principal['result']} {principal['score']}",
        "Alternativa critica: "
        + (
            _format_option(alternatives["critical_alternative"])
            if alternatives["critical_alternative_active"]
            else "none"
        ),
        "Opcion tentadora: " + _format_option(alternatives["tempting_option"]),
        f"Draw warning decision layer: {'si' if alternatives['draw_warning'] else 'no'}",
        f"Por que este pick: {alternatives['why_this_pick']}",
        f"Por que no la opcion tentadora: {alternatives['why_not_tempting']}",
    ]
