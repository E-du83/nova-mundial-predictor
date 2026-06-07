"""
Friendly match context adjustments.

International friendlies are not official World Cup matches. This layer lowers
certainty and raises surprise risk because teams may rotate, test tactics and
play with lower competitive intensity.
"""


FRIENDLY_MATCH_TYPE = "international_friendly"


def build_friendly_context(match: dict) -> dict:
    return {
        "match_type": match.get("competition_type", FRIENDLY_MATCH_TYPE),
        "competitive_intensity": "menor_que_partido_oficial",
        "rotation_probability": "alta",
        "tactical_tests": "probables",
        "score_certainty_adjustment": -8.0,
        "surprise_risk_adjustment": "alto",
        "use_as_world_cup_official": False,
        "notes": [
            "Esto es prueba amistosa, no partido oficial del Mundial.",
            "La confianza se reduce por rotacion e intensidad competitiva menor.",
            "El marcador tiene mayor incertidumbre que un partido oficial.",
        ],
    }


def adjusted_confidence(base_confidence: float | int | str) -> float | str:
    if base_confidence == "pending_real_data":
        return base_confidence
    return round(max(5.0, float(base_confidence) - 8.0), 2)


def friendly_risk(base_risk: str) -> str:
    if base_risk == "alto":
        return "alto"
    if base_risk == "medio":
        return "medio_alto"
    return "medio"


def market_reading(odds_1x2) -> str:
    if odds_1x2 == "pending_manual_snapshot":
        return "Mercado pendiente: no hay cuotas verificadas en snapshot manual."
    if not odds_1x2:
        return "Mercado no disponible."
    return "Cuotas visibles en snapshot manual; revisar valor contra probabilidad del modelo."
