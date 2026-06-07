"""
Manual research intelligence for friendly-test snapshots.

This module converts public manual research into contextual risk/confidence
signals. It never replaces the Core pick; it only annotates and adjusts the
friendly-layer confidence/risk shown to the user.
"""


PENDING = "pending_manual_input"


def _confidence_delta(confidence_adjustment: str) -> float:
    if confidence_adjustment == "decrease":
        return -4.0
    if confidence_adjustment == "slight_decrease":
        return -2.0
    if confidence_adjustment == "increase":
        return 3.0
    if confidence_adjustment == "slight_increase":
        return 2.0
    if confidence_adjustment == "slight_increase_for_colombia_win_but_rotation_warning":
        return 1.5
    return 0.0


def _risk_level_value(risk: str) -> int:
    order = {
        "bajo": 0,
        "medio": 1,
        "medio_alto": 2,
        "alto": 3,
    }
    return order.get(risk, 1)


def _risk_value_level(value: int) -> str:
    levels = ["bajo", "medio", "medio_alto", "alto"]
    return levels[max(0, min(value, len(levels) - 1))]


def _risk_delta(risk_adjustment: str) -> int:
    if risk_adjustment == "increase":
        return 1
    if risk_adjustment == "moderate":
        return 0
    if risk_adjustment == "decrease":
        return -1
    return 0


def apply_research_confidence(base_confidence: float | int | str, impact: dict) -> float | str:
    if base_confidence == "pending_real_data":
        return base_confidence
    delta = _confidence_delta(str(impact.get("confidence_adjustment", PENDING)))
    return round(max(5.0, min(95.0, float(base_confidence) + delta)), 2)


def apply_research_risk(base_risk: str, impact: dict) -> str:
    delta = _risk_delta(str(impact.get("risk_adjustment", PENDING)))
    return _risk_value_level(_risk_level_value(base_risk) + delta)


def build_research_intelligence(
    snapshot: dict,
    snapshot_summary: dict,
    base_confidence: float | int | str,
    base_risk: str,
) -> dict:
    impact = snapshot_summary["manual_research_impact"]
    research_adjusted_confidence = apply_research_confidence(base_confidence, impact)
    research_adjusted_risk = apply_research_risk(base_risk, impact)
    has_research = snapshot_summary["snapshot_investigative"] == "si"

    if not has_research:
        market_reading = "Snapshot investigativo pendiente; no se aplica ajuste investigativo."
    elif impact["model_warning"] != PENDING:
        market_reading = impact["model_warning"]
    else:
        market_reading = "Snapshot investigativo disponible; usar como senal contextual, no como reemplazo del Core."

    return {
        "snapshot_investigative": snapshot_summary["snapshot_investigative"],
        "sources_used": snapshot_summary["sources_used"],
        "odds_visible": snapshot_summary["odds_visible"],
        "odds_decimal_visible": snapshot_summary["odds_decimal_visible"],
        "over_under_visible": snapshot_summary["over_under_visible"],
        "market_probabilities_visible": snapshot_summary["market_probabilities_visible"],
        "external_market_notes": snapshot_summary["external_market_notes"],
        "research_confidence": snapshot_summary["research_confidence"],
        "research_adjusted_confidence": research_adjusted_confidence,
        "research_adjusted_risk": research_adjusted_risk,
        "confidence_impact": impact["confidence_adjustment"],
        "risk_impact": impact["risk_adjustment"],
        "market_warning": market_reading,
        "venue_visible": snapshot_summary["venue_visible"],
        "data_status": snapshot.get("data_status", PENDING),
    }


def format_research_lines(research: dict) -> list[str]:
    sources = research["sources_used"] or [PENDING]
    notes = research["external_market_notes"] or [PENDING]
    return [
        f"Snapshot investigativo: {research['snapshot_investigative']}",
        "Fuentes usadas: " + "; ".join(sources),
        f"Sede/horario investigado: {research['venue_visible']}",
        f"Odds visibles: {research['odds_visible']}",
        f"Odds decimales referencia: {research['odds_decimal_visible']}",
        f"Over/Under visible: {research['over_under_visible']}",
        f"Probabilidades de mercado: {research['market_probabilities_visible']}",
        "Notas externas mercado: " + "; ".join(notes),
        (
            "Impacto investigativo en riesgo/confianza: "
            f"riesgo {research['risk_impact']} | confianza {research['confidence_impact']}"
        ),
        f"Confianza con investigacion: {research['research_adjusted_confidence']}",
        f"Riesgo con investigacion: {research['research_adjusted_risk']}",
        f"Advertencia mercado/Core: {research['market_warning']}",
    ]
