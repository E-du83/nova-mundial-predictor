import json
from pathlib import Path

from scoring_rules import parse_score


PENDING = "pending_real_result"


def load_friendly_results(path: str | Path) -> dict:
    result_path = Path(path)
    if not result_path.exists():
        return {
            "data_status": "real_results_missing",
            "results": [],
            "message": "friendly_test_results.json not found.",
        }
    try:
        return json.loads(result_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "data_status": "invalid_json",
            "results": [],
            "message": str(exc),
        }


def find_real_result(results_data: dict, team_a: str, team_b: str) -> dict:
    requested = {team_a.strip().lower(), team_b.strip().lower()}
    for result in results_data.get("results", []):
        current = {
            str(result.get("team_a", "")).strip().lower(),
            str(result.get("team_b", "")).strip().lower(),
        }
        if current == requested:
            return result
    return {
        "match": f"{team_a} vs {team_b}",
        "team_a": team_a,
        "team_b": team_b,
        "real_score": PENDING,
        "real_result": PENDING,
        "status": "pending",
        "learning_note": PENDING,
    }


def _result_key(score: str, team_a: str, team_b: str) -> str:
    goals_a, goals_b = parse_score(score)
    if goals_a > goals_b:
        return f"{team_a}_win"
    if goals_b > goals_a:
        return f"{team_b}_win"
    return "draw"


def _prediction_result_key(predicted_result: str, team_a: str, team_b: str) -> str:
    text = str(predicted_result).lower()
    if "empate" in text or text == "draw":
        return "draw"
    if team_a.lower() in text:
        return f"{team_a}_win"
    if team_b.lower() in text:
        return f"{team_b}_win"
    return "pending_prediction"


def _minute_value(value) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if not isinstance(value, str):
        return None
    text = value.strip().replace("'", "")
    if "+" in text:
        base, added = text.split("+", maxsplit=1)
        if base.strip().isdigit() and added.strip().isdigit():
            return int(base.strip()) + int(added.strip())
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else None


def _btts(score: str) -> bool:
    goals_a, goals_b = parse_score(score)
    return goals_a > 0 and goals_b > 0


def _late_goals(real_result: dict) -> list[dict]:
    goals = real_result.get("goals", {})
    if not isinstance(goals, dict):
        return []
    late = []
    for team, team_goals in goals.items():
        if not isinstance(team_goals, list):
            continue
        for goal in team_goals:
            minute = _minute_value(goal.get("minute"))
            if minute is not None and minute > 75:
                item = dict(goal)
                item["team"] = team
                item["normalized_minute"] = minute
                late.append(item)
    return late


def _red_card_context(real_result: dict) -> dict:
    red_cards = real_result.get("red_cards", {})
    if not isinstance(red_cards, dict) or not red_cards:
        return {
            "has_red_card": False,
            "cards": [],
            "summary": "none",
        }
    cards = []
    for team, team_cards in red_cards.items():
        if not isinstance(team_cards, list):
            continue
        for card in team_cards:
            item = dict(card)
            item["team"] = team
            item["normalized_minute"] = _minute_value(card.get("minute"))
            cards.append(item)
    summary = "; ".join(
        f"{card['team']}: {card.get('player', 'unknown')} {card.get('minute', 'unknown')}"
        for card in cards
    )
    return {
        "has_red_card": bool(cards),
        "cards": cards,
        "summary": summary or "none",
    }


def _score_distance(score: str, real_score: str) -> int:
    goals_a, goals_b = parse_score(score)
    real_goals_a, real_goals_b = parse_score(real_score)
    return abs(goals_a - real_goals_a) + abs(goals_b - real_goals_b)


def _critical_alternative_relevance(recommendation: dict, real_score: str) -> dict:
    alternatives = recommendation.get("critical_alternatives", {})
    critical = alternatives.get("critical_alternative")
    if not critical:
        return {
            "available": False,
            "score": "none",
            "exact_score_hit": False,
            "reduced_error": False,
        }
    critical_score = critical.get("score")
    predicted_score = recommendation["recommended_score"]
    return {
        "available": True,
        "score": critical_score,
        "exact_score_hit": critical_score == real_score,
        "reduced_error": _score_distance(critical_score, real_score)
        < _score_distance(predicted_score, real_score),
    }


def build_result_review(
    recommendation: dict,
    real_result: dict,
    robustness: dict | None = None,
) -> dict:
    if real_result.get("status") != "final":
        return {
            "status": real_result.get("status", "pending"),
            "real_score": real_result.get("real_score", PENDING),
            "real_result": real_result.get("real_result", PENDING),
            "review_available": False,
            "summary": "Resultado real pendiente; revision post-partido aun no disponible.",
            "learning_note": real_result.get("learning_note", PENDING),
        }

    team_a = recommendation["raw_final_pick"]["match"].split(" vs ", 1)[0]
    team_b = recommendation["raw_final_pick"]["match"].split(" vs ", 1)[1]
    predicted_score = recommendation["recommended_score"]
    real_score = real_result["real_score"]
    predicted_goals_a, predicted_goals_b = parse_score(predicted_score)
    real_goals_a, real_goals_b = parse_score(real_score)
    predicted_key = _prediction_result_key(recommendation["final_recommendation"], team_a, team_b)
    real_key = _result_key(real_score, team_a, team_b)
    winner_hit = predicted_key == real_key
    draw_detected = predicted_key == "draw"
    real_draw = real_key == "draw"
    goal_difference_error = abs(
        (predicted_goals_a - predicted_goals_b) - (real_goals_a - real_goals_b)
    )
    total_goals_error = abs(
        (predicted_goals_a + predicted_goals_b) - (real_goals_a + real_goals_b)
    )
    exact_score_hit = predicted_score == real_score
    result_hit = winner_hit
    close_score_hit = _score_distance(predicted_score, real_score) <= 1
    btts_predicted = _btts(predicted_score)
    btts_real = _btts(real_score)
    btts_miss = btts_predicted != btts_real
    late_goals = _late_goals(real_result)
    red_card_context = _red_card_context(real_result)
    late_goal_impact = {
        "has_late_goal": bool(late_goals),
        "late_goals": late_goals,
        "changed_exact_score": bool(late_goals and not exact_score_hit),
        "summary": (
            "Gol tardio impacto marcador exacto o BTTS."
            if late_goals and not exact_score_hit
            else "none"
        ),
    }
    critical_relevance = _critical_alternative_relevance(recommendation, real_score)
    closed_match_detected = (
        recommendation.get("friendly_risk") in ("medio", "medio_alto", "alto")
        or (robustness or {}).get("pick_robustness") in ("cauteloso", "fragil")
    )

    if exact_score_hit:
        qualitative_error = "Acierto exacto."
    elif real_draw and not draw_detected:
        qualitative_error = "El modelo proyecto partido cerrado, pero subestimo el empate."
    elif winner_hit:
        qualitative_error = "Ganador correcto, marcador exacto incorrecto."
    else:
        qualitative_error = "Resultado 1X2 incorrecto; revisar probabilidad de empate y gol rival."

    structured_learning_note = {
        "winner_direction": "hit" if winner_hit else "miss",
        "exact_score": "hit" if exact_score_hit else "miss",
        "btts": "hit" if not btts_miss else "miss",
        "late_goal_impact": late_goal_impact["summary"],
        "red_card_context": red_card_context["summary"],
        "human_note": real_result.get("learning_note", PENDING),
    }

    return {
        "status": real_result["status"],
        "review_available": True,
        "predicted_result": recommendation["final_recommendation"],
        "predicted_score": predicted_score,
        "real_score": real_score,
        "real_result": real_result["real_result"],
        "winner_hit": winner_hit,
        "result_hit": result_hit,
        "exact_score_hit": exact_score_hit,
        "close_score_hit": close_score_hit,
        "draw_detected": draw_detected,
        "real_draw": real_draw,
        "goal_difference_error": goal_difference_error,
        "total_goals_error": total_goals_error,
        "btts_predicted": btts_predicted,
        "btts_real": btts_real,
        "btts_hit": not btts_miss,
        "btts_miss": btts_miss,
        "late_goal_impact": late_goal_impact,
        "red_card_context": red_card_context,
        "critical_alternative_relevance": critical_relevance,
        "closed_match_detected": closed_match_detected,
        "qualitative_error": qualitative_error,
        "learning_note": real_result.get("learning_note", PENDING),
        "structured_learning_note": structured_learning_note,
        "goals": real_result.get("goals", {}),
        "summary": (
            f"Prediccion {recommendation['final_recommendation']} {predicted_score}; "
            f"resultado real {real_score}. {qualitative_error}"
        ),
    }


def format_result_review_lines(review: dict) -> list[str]:
    lines = [
        f"Resultado real: {review['real_score']} | estado: {review['status']}",
        f"Revision disponible: {'si' if review['review_available'] else 'no'}",
        f"Revision resumen: {review['summary']}",
    ]
    if review["review_available"]:
        lines.extend(
            [
                f"Ganador acertado: {'si' if review['winner_hit'] else 'no'}",
                f"Marcador exacto acertado: {'si' if review['exact_score_hit'] else 'no'}",
                f"Empate detectado por pick: {'si' if review['draw_detected'] else 'no'}",
                f"Partido cerrado detectado: {'si' if review['closed_match_detected'] else 'no'}",
                f"Error diferencia de goles: {review['goal_difference_error']}",
                f"Error total de goles: {review['total_goals_error']}",
                f"BTTS predicho/real: {'si' if review['btts_predicted'] else 'no'} / {'si' if review['btts_real'] else 'no'}",
                f"BTTS miss: {'si' if review['btts_miss'] else 'no'}",
                f"Impacto gol tardio: {review['late_goal_impact']['summary']}",
                f"Contexto roja: {review['red_card_context']['summary']}",
                (
                    "Alternativa critica relevante: "
                    f"{'si' if review['critical_alternative_relevance']['exact_score_hit'] or review['critical_alternative_relevance']['reduced_error'] else 'no'}"
                ),
                f"Lectura cualitativa error: {review['qualitative_error']}",
                f"Learning note: {review['learning_note']}",
            ]
        )
    return lines
