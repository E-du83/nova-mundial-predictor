from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional

from odds_engine import expected_value, fair_odds, stake_profit


def sort_history(records: List[dict]) -> List[dict]:
    """Sort odds history records by timestamp string."""
    return sorted(records, key=lambda r: r["timestamp"])


def calculate_odds_movement(records: List[dict]) -> Dict[str, object]:
    """
    Calculate opening/current/closing movement for odds.

    Expected records:
    [
      {"timestamp": "2026-06-01T10:00:00-06:00", "odds": 1.90, "label": "open"},
      {"timestamp": "2026-06-02T12:00:00-06:00", "odds": 1.75, "label": "current"},
      {"timestamp": "2026-06-03T11:00:00-06:00", "odds": 1.62, "label": "close"}
    ]
    """
    if not records:
        return {
            "opening_odds": None,
            "current_odds": None,
            "closing_odds": None,
            "movement": None,
            "movement_direction": "sin datos",
        }

    ordered = sort_history(records)
    opening = ordered[0]["odds"]
    current = ordered[-1]["odds"]

    closing_records = [r for r in ordered if r.get("label") == "close"]
    closing = closing_records[-1]["odds"] if closing_records else None

    movement = current - opening

    if movement > 0:
        direction = "subió la cuota"
    elif movement < 0:
        direction = "bajó la cuota"
    else:
        direction = "sin cambio"

    return {
        "opening_odds": opening,
        "current_odds": current,
        "closing_odds": closing,
        "movement": round(movement, 4),
        "movement_direction": direction,
        "records": ordered,
    }


def calculate_clv(taken_odds: float, closing_odds: Optional[float]) -> Dict[str, object]:
    """
    Closing Line Value for decimal odds.
    If taken_odds is higher than closing_odds, the bettor beat the closing line.
    """
    if closing_odds is None:
        return {
            "clv": None,
            "clv_percent": None,
            "interpretation": "No hay cuota de cierre todavía."
        }

    clv = taken_odds / closing_odds - 1

    if clv > 0.02:
        interpretation = "Buena señal: agarraste mejor cuota que el cierre."
    elif clv > 0:
        interpretation = "Señal leve positiva: agarraste una cuota un poco mejor que el cierre."
    elif clv == 0:
        interpretation = "Neutral: agarraste la misma cuota que el cierre."
    else:
        interpretation = "Mala señal: agarraste peor cuota que el cierre."

    return {
        "clv": round(clv, 4),
        "clv_percent": round(clv * 100, 2),
        "interpretation": interpretation
    }


def evaluate_odds_timing(model_probability: float, records: List[dict], stake_example: float = 10000) -> Dict[str, object]:
    """
    Evaluate whether current/taken odds are worth playing based on model probability
    and odds movement.
    """
    movement = calculate_odds_movement(records)
    current_odds = movement["current_odds"]
    closing_odds = movement["closing_odds"]

    if current_odds is None:
        return {
            "decision": "Esperar cuota",
            "reason": "No hay cuota actual disponible.",
            "movement": movement,
        }

    min_odds = fair_odds(model_probability)
    ev = expected_value(model_probability, current_odds)
    clv = calculate_clv(current_odds, closing_odds)
    payout = stake_profit(current_odds, stake_example)

    if ev >= 0.03:
        decision = "Sí jugar ahora"
        reason = "La cuota actual todavía paga más de lo que el modelo considera justo."
    elif current_odds >= min_odds:
        decision = "Jugar solo bajo"
        reason = "La cuota alcanza el mínimo justo, pero la ventaja es pequeña."
    else:
        decision = "No jugar ahora"
        reason = "La cuota ya no compensa el riesgo según el modelo."

    if movement["movement_direction"] == "bajó la cuota" and current_odds < min_odds:
        decision = "Se pasó la oportunidad"
        reason = "La cuota bajó y ahora está por debajo de la cuota mínima del modelo."

    return {
        "decision": decision,
        "reason": reason,
        "model_probability": model_probability,
        "minimum_odds": round(min_odds, 2),
        "current_odds": current_odds,
        "expected_value": round(ev, 4),
        "movement": movement,
        "clv": clv,
        "payout_example": payout,
    }


def format_odds_history_report(match_name: str, market_name: str, evaluation: Dict[str, object], stake_example: float = 10000) -> str:
    lines = []
    lines.append(f"PARTIDO: {match_name}")
    lines.append(f"MERCADO: {market_name}")
    lines.append("")
    lines.append("DECISIÓN:")
    lines.append(evaluation["decision"])
    lines.append("")
    lines.append("CUOTA MÍNIMA DEL MODELO:")
    lines.append(str(evaluation["minimum_odds"]))
    lines.append("")
    lines.append("CUOTA ACTUAL:")
    lines.append(str(evaluation["current_odds"]))
    lines.append("")
    lines.append("VALOR ESPERADO:")
    lines.append(str(evaluation["expected_value"]))
    lines.append("")
    movement = evaluation["movement"]
    lines.append("MOVIMIENTO DE CUOTA:")
    lines.append(f"Apertura: {movement['opening_odds']}")
    lines.append(f"Actual: {movement['current_odds']}")
    if movement["closing_odds"] is not None:
        lines.append(f"Cierre: {movement['closing_odds']}")
    lines.append(f"Dirección: {movement['movement_direction']}")
    lines.append("")
    clv = evaluation["clv"]
    lines.append("CLOSING LINE VALUE:")
    if clv["clv"] is None:
        lines.append("Todavía no hay cierre para calcular CLV.")
    else:
        lines.append(f"{clv['clv_percent']}%")
        lines.append(clv["interpretation"])
    lines.append("")
    payout = evaluation["payout_example"]
    lines.append(f"SI APOSTÁS ₡{int(stake_example):,}:")
    lines.append(f"Cobrarías: ₡{payout['total_return']:,.0f}")
    lines.append(f"Ganancia limpia: ₡{payout['clean_profit']:,.0f}")
    lines.append("")
    lines.append("EXPLICACIÓN SIMPLE:")
    lines.append(evaluation["reason"])
    lines.append("")
    lines.append("LECTURA PRÁCTICA:")
    if evaluation["decision"] == "Sí jugar ahora":
        lines.append("La cuota sigue siendo jugable. Si vas a entrar, esta es una ventana razonable.")
    elif evaluation["decision"] == "Se pasó la oportunidad":
        lines.append("La cuota buena probablemente ya se fue. Mejor no perseguir una cuota peor.")
    elif evaluation["decision"] == "No jugar ahora":
        lines.append("Aunque el resultado pueda ocurrir, el precio ya no ayuda.")
    else:
        lines.append("Entrar solo con monto bajo o esperar mejor precio.")
    return "\n".join(lines)