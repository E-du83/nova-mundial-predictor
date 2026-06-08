import json
from pathlib import Path

from scoring_rules import parse_score


def _score_result(score: str) -> str:
    goals_a, goals_b = parse_score(score)
    if goals_a > goals_b:
        return "team_a_win"
    if goals_b > goals_a:
        return "team_b_win"
    return "draw"


def _selected_core(final_pick: dict) -> dict:
    selected = next(
        item for item in final_pick["scenario_evaluations"]
        if item["strategy"] == final_pick["selected_strategy"]
    )
    return selected["recommendation"]["core"]


def _top_score_probability(top_scores: list[dict], score: str) -> float | None:
    for item in top_scores:
        if item.get("score") == score:
            return float(item.get("probability", 0.0))
    return None


def _closest_draw_score(top_scores: list[dict]) -> dict | None:
    draws = [item for item in top_scores if _score_result(item["score"]) == "draw"]
    if not draws:
        return None
    return max(draws, key=lambda item: item.get("probability", 0.0))


def build_pick_robustness(
    final_pick: dict,
    adjusted_confidence: float | int | str,
    friendly_risk: str,
    match_type: str = "international_friendly",
    missing_critical_fields: list[str] | None = None,
    calibration_notes_path: str | Path | None = None,
) -> dict:
    core = _selected_core(final_pick)
    top_scores = core.get("top_scores", [])[:5]
    top_1 = top_scores[0] if top_scores else {}
    top_2 = top_scores[1] if len(top_scores) > 1 else {}
    probability_gap = round(
        float(top_1.get("probability", 0.0)) - float(top_2.get("probability", 0.0)),
        4,
    ) if top_1 and top_2 else "pending_real_data"
    draw_score = _closest_draw_score(top_scores)
    recommended_score = final_pick["final_score"]
    recommended_probability = _top_score_probability(top_scores, recommended_score)
    draw_probability = float(draw_score.get("probability", 0.0)) if draw_score else None
    confidence = float(adjusted_confidence) if isinstance(adjusted_confidence, (int, float)) else 0.0
    friendly = match_type == "international_friendly"
    close_draw = (
        draw_probability is not None
        and recommended_probability is not None
        and abs(recommended_probability - draw_probability) <= 0.015
    )
    one_zero_vs_one_one = recommended_score in ("1-0", "0-1") and draw_score and draw_score["score"] == "1-1"
    draw_warning = bool(
        friendly
        and confidence < 45
        and friendly_risk in ("medio", "medio_alto", "alto")
        and draw_score
        and (close_draw or one_zero_vs_one_one)
    )

    if draw_warning:
        robustness = "cauteloso"
    elif isinstance(probability_gap, float) and probability_gap < 0.012:
        robustness = "fragil"
    elif confidence < 45 and friendly_risk in ("medio", "medio_alto", "alto"):
        robustness = "cauteloso"
    elif isinstance(probability_gap, float) and probability_gap < 0.025:
        robustness = "medio"
    else:
        robustness = "estable"

    if draw_warning:
        draw_reason = (
            f"Amistoso con confianza {confidence}% y riesgo {friendly_risk}; "
            f"empate {draw_score['score']} cerca del pick {recommended_score}."
        )
    elif draw_score:
        draw_reason = f"Empate candidato {draw_score['score']} existe, pero no supera umbral de alerta."
    else:
        draw_reason = "No hay empate dentro del top 5 disponible."

    warnings = []
    if confidence < 45:
        warnings.append("Confianza ajustada baja/media.")
    if draw_warning:
        warnings.append("Alerta de empate activada.")
    if one_zero_vs_one_one:
        warnings.append("1-0 y 1-1 aparecen como marcadores sensibles.")
    missing_critical_fields = missing_critical_fields or []
    clean_sheet_score = recommended_score in ("1-0", "2-0", "0-1", "0-2")
    critical_missing_for_clean_sheet = any(
        field in missing_critical_fields
        for field in ("probable_lineups", "formations", "odds_1x2", "over_under", "lineups")
    )
    clean_sheet_risk_warning = bool(
        friendly
        and clean_sheet_score
        and robustness in ("fragil", "cauteloso")
        and critical_missing_for_clean_sheet
    )
    if clean_sheet_risk_warning:
        warnings.append(
            "clean_sheet_risk_warning: amistoso con pick de porteria a cero, robustez baja y datos criticos faltantes."
        )

    late_goal_history_warning = False
    if calibration_notes_path:
        notes_path = Path(calibration_notes_path)
        if notes_path.exists():
            try:
                notes = json.loads(notes_path.read_text(encoding="utf-8"))
                late_goal_history_warning = notes.get("late_opponent_goal_pattern", 0) > 0
            except json.JSONDecodeError:
                late_goal_history_warning = False
    if late_goal_history_warning:
        warnings.append(
            "Cuidado: el sistema ha subestimado goles tardios del rival en amistosos."
        )

    return {
        "top_scores": top_scores,
        "top_1_score": top_1.get("score", "pending_real_data"),
        "top_2_score": top_2.get("score", "pending_real_data"),
        "top_1_probability": top_1.get("probability", "pending_real_data"),
        "top_2_probability": top_2.get("probability", "pending_real_data"),
        "top_probability_gap": probability_gap,
        "pick_robustness": robustness,
        "draw_warning": draw_warning,
        "draw_warning_reason": draw_reason,
        "closest_draw_score": draw_score or "pending_real_data",
        "clean_sheet_risk_warning": clean_sheet_risk_warning,
        "late_goal_history_warning": late_goal_history_warning,
        "warnings": warnings,
    }


def format_robustness_lines(robustness: dict) -> list[str]:
    top_scores_text = "; ".join(
        f"{item['score']} ({round(item['probability'] * 100, 2)}%)"
        for item in robustness["top_scores"]
    ) or "pending_real_data"
    return [
        f"Top 5 marcadores probables: {top_scores_text}",
        f"Diferencia pick #1 vs #2: {robustness['top_probability_gap']}",
        f"Robustez del pick: {robustness['pick_robustness']}",
        f"Alerta de empate: {'si' if robustness['draw_warning'] else 'no'}",
        f"Motivo alerta empate: {robustness['draw_warning_reason']}",
        "Warnings robustez: " + ("; ".join(robustness["warnings"]) if robustness["warnings"] else "none"),
    ]
