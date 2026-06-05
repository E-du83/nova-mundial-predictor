def implied_probability(decimal_odds: float) -> float:
    if decimal_odds <= 1:
        raise ValueError("La cuota decimal debe ser mayor que 1.")
    return 1.0 / decimal_odds


def fair_odds(probability: float) -> float:
    if probability <= 0:
        return float("inf")
    return 1.0 / probability


def expected_value(model_probability: float, decimal_odds: float) -> float:
    return model_probability * decimal_odds - 1.0


def normalize_market_no_vig(odds: dict) -> dict:
    implied = {k: implied_probability(v) for k, v in odds.items() if v and v > 1}
    total = sum(implied.values())
    if total <= 0:
        return {}
    return {k: p / total for k, p in implied.items()}


def bookmaker_margin(odds: dict) -> float:
    return sum(implied_probability(v) for v in odds.values() if v and v > 1) - 1.0


def stake_profit(decimal_odds: float, stake: float) -> dict:
    total_return = stake * decimal_odds
    clean_profit = total_return - stake
    return {
        "stake": round(stake, 2),
        "total_return": round(total_return, 2),
        "clean_profit": round(clean_profit, 2)
    }


def fractional_kelly(model_probability: float, decimal_odds: float, fraction: float = 0.25) -> float:
    b = decimal_odds - 1
    p = model_probability
    q = 1 - p
    if b <= 0:
        return 0.0
    full_kelly = ((b * p) - q) / b
    return max(0.0, full_kelly * fraction)


def classify_value(ev):
    if ev is None:
        return "sin cuota"
    if ev >= 0.10:
        return "valor alto"
    if ev >= 0.03:
        return "valor positivo"
    if ev >= -0.02:
        return "sin ventaja clara"
    return "valor negativo"


def clear_decision(model_probability: float, current_odds):
    min_odds = fair_odds(model_probability)
    if current_odds is None:
        return {
            "decision": "Esperar cuota",
            "minimum_odds": round(min_odds, 2),
            "current_odds": None,
            "expected_value": None,
            "explanation": "Tenemos probabilidad del modelo, pero falta cuota real para decidir."
        }

    ev = expected_value(model_probability, current_odds)
    if ev >= 0.03:
        decision = "Sí jugar"
        explanation = "La cuota actual paga más de lo que el modelo considera justo."
    elif current_odds >= min_odds:
        decision = "Jugar solo bajo"
        explanation = "La cuota alcanza el mínimo justo, pero la ventaja es pequeña."
    else:
        decision = "No jugar"
        explanation = "La apuesta puede ocurrir, pero la cuota paga poco para el riesgo."

    return {
        "decision": decision,
        "minimum_odds": round(min_odds, 2),
        "current_odds": round(current_odds, 2),
        "expected_value": round(ev, 4),
        "explanation": explanation
    }


def evaluate_1x2_market(model_probs: dict, odds: dict, stake_example: float = 10000, bankroll=None) -> dict:
    labels = {"home": "Gana equipo A", "draw": "Empate", "away": "Gana equipo B"}
    no_vig = normalize_market_no_vig(odds)
    margin = bookmaker_margin(odds)
    evaluated = []

    for key in ["home", "draw", "away"]:
        p = model_probs.get(key)
        o = odds.get(key)
        decision = clear_decision(p, o)
        payout = stake_profit(o, stake_example) if o else None
        kelly = fractional_kelly(p, o, 0.25) if o else 0.0
        suggested_amount = bankroll * kelly if bankroll else None

        evaluated.append({
            "key": key,
            "label": labels[key],
            "model_probability": p,
            "market_probability_no_vig": no_vig.get(key),
            "current_odds": o,
            "minimum_odds": decision["minimum_odds"],
            "expected_value": decision["expected_value"],
            "value_class": classify_value(decision["expected_value"]),
            "decision": decision["decision"],
            "explanation": decision["explanation"],
            "payout_example": payout,
            "kelly_25_fraction": round(kelly, 4),
            "suggested_amount": round(suggested_amount, 2) if suggested_amount is not None else None,
        })

    playable = [x for x in evaluated if x["decision"] in ["Sí jugar", "Jugar solo bajo"]]
    if playable:
        best = sorted(playable, key=lambda x: (x["decision"] == "Sí jugar", x["expected_value"], x["model_probability"]), reverse=True)[0]
    else:
        best = sorted(evaluated, key=lambda x: x["model_probability"], reverse=True)[0]

    return {
        "market": "1X2",
        "bookmaker_margin": round(margin, 4),
        "bookmaker_margin_percent": round(margin * 100, 2),
        "evaluated": evaluated,
        "recommended": best,
        "market_probabilities_no_vig": no_vig,
    }


def format_odds_report(match_name: str, evaluation: dict, stake_example: float = 10000) -> str:
    rec = evaluation["recommended"]
    lines = []
    lines.append(f"PARTIDO: {match_name}")
    lines.append("")
    lines.append("DECISIÓN PRINCIPAL:")
    lines.append(rec["decision"])
    lines.append("")
    lines.append("JUGADA:")
    lines.append(rec["label"])
    lines.append("")
    lines.append("CUOTA ACTUAL:")
    lines.append(str(rec["current_odds"]) if rec["current_odds"] else "No ingresada")
    lines.append("")
    lines.append("CUOTA MÍNIMA PARA QUE VALGA:")
    lines.append(str(rec["minimum_odds"]))
    lines.append("")
    lines.append("PROBABILIDAD DEL MODELO:")
    lines.append(f"{round(rec['model_probability'] * 100, 2)}%")
    lines.append("")
    if rec["market_probability_no_vig"] is not None:
        lines.append("PROBABILIDAD DEL MERCADO, SIN MARGEN:")
        lines.append(f"{round(rec['market_probability_no_vig'] * 100, 2)}%")
        lines.append("")
    lines.append("VALOR ESPERADO:")
    lines.append(str(rec["expected_value"]) if rec["expected_value"] is not None else "No calculado")
    lines.append("")
    lines.append("CLASIFICACIÓN:")
    lines.append(rec["value_class"])
    lines.append("")
    if rec["payout_example"]:
        p = rec["payout_example"]
        lines.append(f"SI APOSTÁS ₡{int(stake_example):,}:")
        lines.append(f"Cobrarías: ₡{p['total_return']:,.0f}")
        lines.append(f"Ganancia limpia: ₡{p['clean_profit']:,.0f}")
        lines.append("")
    lines.append("MARGEN ESTIMADO DE LA CASA:")
    lines.append(f"{evaluation['bookmaker_margin_percent']}%")
    lines.append("")
    lines.append("EXPLICACIÓN SIMPLE:")
    lines.append(rec["explanation"])
    lines.append("")
    lines.append("TODAS LAS OPCIONES:")
    for item in evaluation["evaluated"]:
        lines.append(
            f"- {item['label']}: modelo {round(item['model_probability']*100,2)}%, "
            f"cuota {item['current_odds']}, mínima {item['minimum_odds']}, "
            f"EV {item['expected_value']}, decisión: {item['decision']}"
        )
    return "\n".join(lines)

def best_odds_by_market(bookmakers: list[dict]) -> dict:
    """
    Find best available odds per market across multiple bookmakers.

    bookmakers format:
    [
      {
        "bookmaker": "Casa A",
        "odds": {"home": 1.70, "draw": 3.50, "away": 5.20}
      }
    ]
    """
    best = {}
    for book in bookmakers:
        name = book["bookmaker"]
        odds = book["odds"]
        for market, value in odds.items():
            if value is None:
                continue
            if market not in best or value > best[market]["odds"]:
                best[market] = {
                    "bookmaker": name,
                    "odds": value
                }
    return best


def evaluate_1x2_multi_bookmaker(model_probs: dict, bookmakers: list[dict], stake_example: float = 10000, bankroll=None) -> dict:
    """
    Evaluate 1X2 market across several bookmakers.
    Uses the best available odds per outcome.
    """
    best = best_odds_by_market(bookmakers)
    best_odds = {market: info["odds"] for market, info in best.items()}

    evaluation = evaluate_1x2_market(
        model_probs=model_probs,
        odds=best_odds,
        stake_example=stake_example,
        bankroll=bankroll
    )

    # Attach best bookmaker info to each evaluated option.
    for item in evaluation["evaluated"]:
        market = item["key"]
        if market in best:
            item["best_bookmaker"] = best[market]["bookmaker"]
        else:
            item["best_bookmaker"] = None

    rec_key = evaluation["recommended"]["key"]
    evaluation["recommended"]["best_bookmaker"] = best.get(rec_key, {}).get("bookmaker")

    # Add per-bookmaker margins.
    evaluation["bookmakers"] = []
    for book in bookmakers:
        margin = bookmaker_margin(book["odds"])
        evaluation["bookmakers"].append({
            "bookmaker": book["bookmaker"],
            "odds": book["odds"],
            "margin": round(margin, 4),
            "margin_percent": round(margin * 100, 2)
        })

    evaluation["best_odds"] = best
    return evaluation


def format_multi_bookmaker_report(match_name: str, evaluation: dict, stake_example: float = 10000) -> str:
    rec = evaluation["recommended"]
    lines = []
    lines.append(f"PARTIDO: {match_name}")
    lines.append("")
    lines.append("DECISIÓN PRINCIPAL:")
    lines.append(rec["decision"])
    lines.append("")
    lines.append("JUGADA:")
    lines.append(rec["label"])
    lines.append("")
    lines.append("MEJOR CASA PARA ESTA JUGADA:")
    lines.append(rec.get("best_bookmaker") or "No disponible")
    lines.append("")
    lines.append("MEJOR CUOTA ENCONTRADA:")
    lines.append(str(rec["current_odds"]) if rec["current_odds"] else "No ingresada")
    lines.append("")
    lines.append("CUOTA MÍNIMA PARA QUE VALGA:")
    lines.append(str(rec["minimum_odds"]))
    lines.append("")
    lines.append("PROBABILIDAD DEL MODELO:")
    lines.append(f"{round(rec['model_probability'] * 100, 2)}%")
    lines.append("")
    if rec["market_probability_no_vig"] is not None:
        lines.append("PROBABILIDAD DEL MERCADO, SIN MARGEN:")
        lines.append(f"{round(rec['market_probability_no_vig'] * 100, 2)}%")
        lines.append("")
    lines.append("VALOR ESPERADO:")
    lines.append(str(rec["expected_value"]) if rec["expected_value"] is not None else "No calculado")
    lines.append("")
    lines.append("CLASIFICACIÓN:")
    lines.append(rec["value_class"])
    lines.append("")
    if rec["payout_example"]:
        p = rec["payout_example"]
        lines.append(f"SI APOSTÁS ₡{int(stake_example):,}:")
        lines.append(f"Cobrarías: ₡{p['total_return']:,.0f}")
        lines.append(f"Ganancia limpia: ₡{p['clean_profit']:,.0f}")
        lines.append("")
    lines.append("EXPLICACIÓN SIMPLE:")
    lines.append(rec["explanation"])
    lines.append("")

    lines.append("MEJOR CUOTA POR RESULTADO:")
    labels = {"home": "Gana equipo A", "draw": "Empate", "away": "Gana equipo B"}
    for key in ["home", "draw", "away"]:
        info = evaluation["best_odds"].get(key)
        if info:
            lines.append(f"- {labels[key]}: {info['odds']} en {info['bookmaker']}")
    lines.append("")

    lines.append("COMPARACIÓN DE CASAS:")
    for book in evaluation["bookmakers"]:
        odds = book["odds"]
        lines.append(
            f"- {book['bookmaker']}: local {odds.get('home')}, empate {odds.get('draw')}, "
            f"visita {odds.get('away')} | margen estimado {book['margin_percent']}%"
        )
    lines.append("")

    lines.append("TODAS LAS OPCIONES EVALUADAS:")
    for item in evaluation["evaluated"]:
        lines.append(
            f"- {item['label']}: modelo {round(item['model_probability']*100,2)}%, "
            f"mejor cuota {item['current_odds']} en {item.get('best_bookmaker')}, "
            f"mínima {item['minimum_odds']}, EV {item['expected_value']}, decisión: {item['decision']}"
        )

    return "\n".join(lines)
