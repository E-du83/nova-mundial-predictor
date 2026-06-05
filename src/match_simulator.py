import json
import math
from collections import Counter
from pathlib import Path

import numpy as np


def implied_probability(decimal_odds: float) -> float:
    """Convert decimal odds into implied probability before bookmaker margin adjustment."""
    if decimal_odds <= 1:
        raise ValueError("La cuota decimal debe ser mayor que 1.")
    return 1 / decimal_odds


def fair_odds(probability: float) -> float:
    """Convert model probability into fair decimal odds."""
    if probability <= 0:
        return float("inf")
    return 1 / probability


def expected_value(probability: float, decimal_odds: float) -> float:
    """Expected value from model probability and decimal odds."""
    return probability * decimal_odds - 1


def calculate_expected_goals(team_a: dict, team_b: dict) -> tuple[float, float]:
    """
    Simplified expected goals formula.
    This is an MVP formula. Later versions should calibrate weights using historical backtesting.
    """

    # Elo difference adjustment. Small controlled effect to avoid overinflating favorites.
    elo_diff = team_a["elo"] - team_b["elo"]
    elo_factor_a = 1 + min(max(elo_diff / 1000, -0.30), 0.30)
    elo_factor_b = 1 + min(max(-elo_diff / 1000, -0.30), 0.30)

    lambda_a = (
        1.25
        * team_a["attack"]
        * team_b["defense"]
        * team_a["form"]
        * team_a.get("tactical_attack_adjustment", 1.0)
        * team_b.get("tactical_defense_adjustment", 1.0)
        * elo_factor_a
    )

    lambda_b = (
        1.25
        * team_b["attack"]
        * team_a["defense"]
        * team_b["form"]
        * team_b.get("tactical_attack_adjustment", 1.0)
        * team_a.get("tactical_defense_adjustment", 1.0)
        * elo_factor_b
    )

    # Keep values realistic for international football.
    lambda_a = max(0.15, min(lambda_a, 3.50))
    lambda_b = max(0.15, min(lambda_b, 3.50))

    return lambda_a, lambda_b


def simulate_match(team_a_name: str, team_b_name: str, teams: dict, simulations: int = 100_000, seed: int = 42) -> dict:
    if team_a_name not in teams:
        raise KeyError(f"No existe el equipo: {team_a_name}")
    if team_b_name not in teams:
        raise KeyError(f"No existe el equipo: {team_b_name}")

    rng = np.random.default_rng(seed)

    team_a = teams[team_a_name]
    team_b = teams[team_b_name]

    lambda_a, lambda_b = calculate_expected_goals(team_a, team_b)

    goals_a = rng.poisson(lambda_a, simulations)
    goals_b = rng.poisson(lambda_b, simulations)

    wins_a = int(np.sum(goals_a > goals_b))
    draws = int(np.sum(goals_a == goals_b))
    wins_b = int(np.sum(goals_a < goals_b))

    score_counter = Counter(zip(goals_a.tolist(), goals_b.tolist()))
    top_scores = score_counter.most_common(8)

    total_goals = goals_a + goals_b
    under_35 = float(np.mean(total_goals < 3.5))
    under_25 = float(np.mean(total_goals < 2.5))
    both_score = float(np.mean((goals_a > 0) & (goals_b > 0)))

    return {
        "team_a": team_a_name,
        "team_b": team_b_name,
        "simulations": simulations,
        "expected_goals": {
            team_a_name: round(lambda_a, 3),
            team_b_name: round(lambda_b, 3),
        },
        "probabilities": {
            f"{team_a_name}_win": wins_a / simulations,
            "draw": draws / simulations,
            f"{team_b_name}_win": wins_b / simulations,
            "under_3_5_goals": under_35,
            "under_2_5_goals": under_25,
            "both_teams_score_yes": both_score,
        },
        "top_scores": [
            {
                "score": f"{a}-{b}",
                "probability": count / simulations
            }
            for (a, b), count in top_scores
        ],
        "style_notes": {
            team_a_name: team_a.get("style_note", ""),
            team_b_name: team_b.get("style_note", ""),
        }
    }


def choose_recommendation(result: dict, odds: dict | None = None, stake_example: int = 10_000) -> dict:
    """
    Convert probabilities into a clear decision.
    odds example:
    {
      "team_a_win": 1.80,
      "draw": 3.40,
      "team_b_win": 4.80,
      "under_3_5_goals": 1.45,
      "under_2_5_goals": 1.90,
      "both_teams_score_yes": 1.95
    }
    """
    odds = odds or {}

    team_a = result["team_a"]
    team_b = result["team_b"]
    probs = result["probabilities"]

    markets = []

    mapping = {
        "team_a_win": (f"{team_a} gana", probs[f"{team_a}_win"]),
        "draw": ("Empate", probs["draw"]),
        "team_b_win": (f"{team_b} gana", probs[f"{team_b}_win"]),
        "under_3_5_goals": ("Menos de 3.5 goles", probs["under_3_5_goals"]),
        "under_2_5_goals": ("Menos de 2.5 goles", probs["under_2_5_goals"]),
        "both_teams_score_yes": ("Ambos equipos anotan: Sí", probs["both_teams_score_yes"]),
    }

    for key, (label, prob) in mapping.items():
        min_odds = fair_odds(prob)
        current_odds = odds.get(key)
        ev = expected_value(prob, current_odds) if current_odds else None

        markets.append({
            "key": key,
            "label": label,
            "probability": prob,
            "min_odds": min_odds,
            "current_odds": current_odds,
            "ev": ev
        })

    # Most probable market
    most_probable = max(markets, key=lambda m: m["probability"])

    # Best value among markets with available odds
    value_markets = [m for m in markets if m["current_odds"] is not None]
    positive_value = [m for m in value_markets if m["ev"] is not None and m["ev"] > 0.03]

    if positive_value:
        best_value = max(positive_value, key=lambda m: m["ev"])
        decision = "Sí jugar"
        main_pick = best_value
        decision_reason = "La cuota actual paga más de lo que el modelo considera justo."
    else:
        best_value = None
        main_pick = most_probable
        if main_pick["probability"] >= 0.70:
            decision = "Solo jugar si la cuota alcanza la mínima"
            decision_reason = "Es una jugada probable, pero la cuota disponible debe compensar el riesgo."
        else:
            decision = "Solo quiniela o esperar mejor cuota"
            decision_reason = "No hay suficiente valor confirmado con las cuotas actuales."

    top_score = result["top_scores"][0]["score"]
    second_score = result["top_scores"][1]["score"] if len(result["top_scores"]) > 1 else None

    current_odds = main_pick.get("current_odds")
    min_odds = main_pick["min_odds"]

    payout_info = None
    if current_odds:
        total_return = stake_example * current_odds
        clean_profit = total_return - stake_example
        payout_info = {
            "stake_example": stake_example,
            "total_return_if_win": round(total_return, 2),
            "clean_profit_if_win": round(clean_profit, 2)
        }

    # Stake guidance
    p = main_pick["probability"]
    if decision == "Sí jugar":
        if p >= 0.70:
            stake = "Medio"
        elif p >= 0.58:
            stake = "Bajo-medio"
        else:
            stake = "Bajo"
    else:
        stake = "No apostar todavía"

    # Avoid aggressive bet based on score spread
    avoid = "Marcadores de goleada o apuestas agresivas sin cuota clara"

    return {
        "decision": decision,
        "recommended_play": main_pick["label"],
        "type": "Valor" if best_value else "Conservadora / Quiniela",
        "model_probability": round(main_pick["probability"] * 100, 2),
        "minimum_odds_to_play": round(min_odds, 2),
        "current_odds": current_odds,
        "expected_value": round(main_pick["ev"], 4) if main_pick["ev"] is not None else None,
        "payout_example": payout_info,
        "stake": stake,
        "quiniela_score": top_score,
        "second_score": second_score,
        "avoid": avoid,
        "simple_reason": decision_reason,
        "top_scores": result["top_scores"],
    }


def format_report(result: dict, recommendation: dict) -> str:
    team_a = result["team_a"]
    team_b = result["team_b"]
    probs = result["probabilities"]

    lines = []
    lines.append(f"PARTIDO: {team_a} vs {team_b}")
    lines.append("")
    lines.append("DECISIÓN:")
    lines.append(f"{recommendation['decision']}")
    lines.append("")
    lines.append("JUGADA RECOMENDADA:")
    lines.append(f"{recommendation['recommended_play']}")
    lines.append("")
    lines.append("PROBABILIDAD DEL MODELO:")
    lines.append(f"{recommendation['model_probability']}%")
    lines.append("")
    lines.append("CUOTA MÍNIMA PARA QUE VALGA:")
    lines.append(f"{recommendation['minimum_odds_to_play']}")
    lines.append("Lectura: si la casa paga menos que esa cuota, mejor no jugar esa apuesta.")
    lines.append("")

    if recommendation["current_odds"]:
        lines.append("CUOTA ACTUAL INGRESADA:")
        lines.append(str(recommendation["current_odds"]))
        lines.append("")
        if recommendation["payout_example"]:
            p = recommendation["payout_example"]
            lines.append(f"SI APOSTÁS ₡{p['stake_example']:,}:")
            lines.append(f"Cobrarías: ₡{p['total_return_if_win']:,.0f}")
            lines.append(f"Ganancia limpia: ₡{p['clean_profit_if_win']:,.0f}")
            lines.append("")

    lines.append("MONTO SUGERIDO:")
    lines.append(recommendation["stake"])
    lines.append("")
    lines.append("QUINIELA:")
    lines.append(f"Marcador principal: {recommendation['quiniela_score']}")
    if recommendation["second_score"]:
        lines.append(f"Segunda opción: {recommendation['second_score']}")
    lines.append("")
    lines.append("EVITAR:")
    lines.append(recommendation["avoid"])
    lines.append("")
    lines.append("PROBABILIDADES 1X2:")
    lines.append(f"{team_a} gana: {round(probs[f'{team_a}_win'] * 100, 2)}%")
    lines.append(f"Empate: {round(probs['draw'] * 100, 2)}%")
    lines.append(f"{team_b} gana: {round(probs[f'{team_b}_win'] * 100, 2)}%")
    lines.append("")
    lines.append("GOLES ESPERADOS:")
    lines.append(f"{team_a}: {result['expected_goals'][team_a]}")
    lines.append(f"{team_b}: {result['expected_goals'][team_b]}")
    lines.append("")
    lines.append("EXPLICACIÓN SIMPLE:")
    lines.append(recommendation["simple_reason"])
    lines.append(f"{team_a}: {result['style_notes'][team_a]}")
    lines.append(f"{team_b}: {result['style_notes'][team_b]}")
    lines.append("")
    lines.append("MARCADORES MÁS PROBABLES:")
    for item in result["top_scores"][:5]:
        lines.append(f"- {item['score']}: {round(item['probability'] * 100, 2)}%")

    return "\n".join(lines)


def load_teams(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))