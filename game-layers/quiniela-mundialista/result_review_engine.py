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
    exact_score_hit = predicted_score == real_score
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

    return {
        "status": real_result["status"],
        "review_available": True,
        "predicted_result": recommendation["final_recommendation"],
        "predicted_score": predicted_score,
        "real_score": real_score,
        "real_result": real_result["real_result"],
        "winner_hit": winner_hit,
        "exact_score_hit": exact_score_hit,
        "draw_detected": draw_detected,
        "real_draw": real_draw,
        "goal_difference_error": goal_difference_error,
        "closed_match_detected": closed_match_detected,
        "qualitative_error": qualitative_error,
        "learning_note": real_result.get("learning_note", PENDING),
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
                f"Lectura cualitativa error: {review['qualitative_error']}",
                f"Learning note: {review['learning_note']}",
            ]
        )
    return lines
