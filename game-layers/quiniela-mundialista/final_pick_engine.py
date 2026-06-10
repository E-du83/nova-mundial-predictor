from pathlib import Path

from quiniela_engine import ROOT, load_teams, recommend_match
from scoring_rules import parse_score, result_key
from simulation_config import infer_simulation_mode, resolve_simulation_mode
from tournament_context_engine import (
    build_tournament_context,
    load_fixture_contexts,
)
from venue_climate_engine import (
    build_venue_climate_profile,
    climate_missing_data,
    load_venue_climate_profiles,
)


STRATEGIES = ("conservador", "balanceado", "agresivo")


def _percent(value: float) -> float:
    return round(value * 100, 2)


def _risk_value(risk: str) -> float:
    return {
        "bajo": 0.0,
        "medio": 0.35,
        "alto": 0.75,
    }.get(risk, 0.5)


def _most_probable_result_key(recommendation: dict) -> str:
    team_a = recommendation["team_a"]
    team_b = recommendation["team_b"]
    probabilities = recommendation["core"]["probabilities"]
    outcomes = [
        ("team_a_win", probabilities[f"{team_a}_win"]),
        ("draw", probabilities["draw"]),
        ("team_b_win", probabilities[f"{team_b}_win"]),
    ]
    return max(outcomes, key=lambda item: item[1])[0]


def _score_result_key(recommendation: dict) -> str:
    goals_a, goals_b = parse_score(recommendation["quiniela"]["recommended_score"])
    return result_key(goals_a, goals_b)


def _xg_consistency(recommendation: dict) -> float:
    team_a = recommendation["team_a"]
    team_b = recommendation["team_b"]
    goals_a, goals_b = parse_score(recommendation["quiniela"]["recommended_score"])
    expected = recommendation["core"]["expected_goals"]

    error = abs(goals_a - expected[team_a]) + abs(goals_b - expected[team_b])
    return max(0.0, 1 - error / 4)


def _quinigol_matches_score(recommendation: dict) -> bool:
    team_a = recommendation["team_a"]
    team_b = recommendation["team_b"]
    goals_a, goals_b = parse_score(recommendation["quiniela"]["recommended_score"])
    quinigol_team = recommendation["quinigol"]["team"]

    if quinigol_team == "No hay":
        return goals_a == 0 and goals_b == 0
    if quinigol_team == team_a:
        return goals_a > 0
    if quinigol_team == team_b:
        return goals_b > 0
    return False


def _potential_points(recommendation: dict) -> int:
    exact_score_points = 7
    quinigol_points = 2 if _quinigol_matches_score(recommendation) else 0
    return min(9, exact_score_points + quinigol_points)


def _context_adjustment(context: dict) -> float:
    if context["context_status"] == "pre_tournament_context":
        return 0.0
    adjustment = 0.0
    if context["pressure_estimate"] == "alta":
        adjustment -= 0.03
    if context["rotation_risk"] in ("medio_alto", "alto"):
        adjustment -= 0.04
    if context["goal_difference_importance"] == "alta":
        adjustment += 0.02
    return adjustment


def _climate_adjustment(climate: dict) -> float:
    if climate["data_status"] == "pending_real_data":
        return 0.0
    adjustment = 0.0
    if climate["heat_risk"] == "alto":
        adjustment -= 0.04
    if climate["adaptation_risk"] == "alto":
        adjustment -= 0.04
    return adjustment


def _evaluate_scenario(recommendation: dict, context: dict, climate: dict) -> dict:
    quiniela = recommendation["quiniela"]
    score_probability = quiniela["score_probability"]
    result_consistency = 1.0 if _score_result_key(recommendation) == _most_probable_result_key(recommendation) else 0.0
    xg_consistency = _xg_consistency(recommendation)
    potential_points = _potential_points(recommendation)
    aggressive_penalty = 0.0
    if recommendation["strategy"] == "agresivo":
        aggressive_penalty = _risk_value(quiniela["risk"]) * 0.09

    final_score = (
        score_probability * 0.34
        + (potential_points / 9) * 0.22
        + result_consistency * 0.16
        + xg_consistency * 0.14
        + (1 - _risk_value(quiniela["risk"])) * 0.08
        + _context_adjustment(context)
        + _climate_adjustment(climate)
        - aggressive_penalty
    )

    return {
        "strategy": recommendation["strategy"],
        "recommendation": recommendation,
        "evaluation_score": round(final_score, 4),
        "score_probability": _percent(score_probability),
        "potential_points": potential_points,
        "result_consistency": result_consistency == 1.0,
        "xg_consistency": round(xg_consistency, 3),
        "aggressive_penalty": round(aggressive_penalty, 3),
    }


def _confidence_from_evaluation(evaluation: dict, recommendation: dict) -> float:
    result_probability = recommendation["quiniela"]["result_probability"]
    score_probability = recommendation["quiniela"]["score_probability"]
    confidence = result_probability * 0.70 + score_probability * 0.30
    confidence += min(0.05, evaluation["evaluation_score"] / 12)
    return round(confidence * 100, 2)


def _overall_risk(recommendation: dict, context: dict, climate: dict) -> str:
    risk_score = _risk_value(recommendation["quiniela"]["risk"])
    if recommendation["quinigol"]["risk"] == "alto":
        risk_score += 0.15
    if context["rotation_risk"] in ("medio_alto", "alto"):
        risk_score += 0.10
    if climate["heat_risk"] == "alto" or climate["adaptation_risk"] == "alto":
        risk_score += 0.10

    if risk_score <= 0.25:
        return "bajo"
    if risk_score <= 0.65:
        return "medio"
    return "alto"


def _why_score(evaluation: dict, recommendation: dict, context: dict, climate: dict) -> str:
    quiniela = recommendation["quiniela"]
    return (
        f"Se eligio {quiniela['recommended_score']} porque combina probabilidad de marcador "
        f"({evaluation['score_probability']}%), coherencia con el 1X2 principal "
        f"({quiniela['result']}) y ajuste razonable contra los xG del Core. "
        f"El contexto esta marcado como {context['context_status']} y la sede/clima como "
        f"{climate['data_status']}, por lo que esos factores no se inventan."
    )


def _why_quinigol(recommendation: dict) -> str:
    quinigol = recommendation["quinigol"]
    return (
        f"{quinigol['recommended']} se mantiene como gol recomendado unico. "
        f"El minuto es una referencia probabilistica ({quinigol['minute_label']}) "
        f"y el rango {quinigol['minute_range']} pesa mas que el minuto exacto. "
        f"Politica aplicada: {quinigol.get('policy_applied', 'normal')}."
    )


def _missing_data(context: dict, climate: dict) -> list[str]:
    missing = list(context.get("missing_data", []))
    missing.extend(f"venue_climate.{item}" for item in climate_missing_data(climate))
    if climate["data_status"] == "pending_real_data":
        missing.append("perfil climatico historico real de la sede")
    return sorted(set(missing))


def build_final_pick(
    team_a: str,
    team_b: str,
    teams: dict,
    fixtures_data: dict | None = None,
    climate_profiles: dict | None = None,
    simulations: int = 50_000,
    seed: int = 2026,
    simulation_mode: str | None = None,
) -> dict:
    if simulation_mode is not None:
        simulation_mode, simulations = resolve_simulation_mode(simulation_mode)
    else:
        simulation_mode = infer_simulation_mode(simulations)

    context = build_tournament_context(team_a, team_b, fixtures_data)
    climate = build_venue_climate_profile(context["venue"], climate_profiles)

    scenarios = [
        recommend_match(
            team_a,
            team_b,
            teams,
            strategy=strategy,
            simulations=simulations,
            seed=seed,
            simulation_mode=simulation_mode,
        )
        for strategy in STRATEGIES
    ]
    evaluations = [
        _evaluate_scenario(scenario, context, climate)
        for scenario in scenarios
    ]
    selected = max(
        evaluations,
        key=lambda item: (
            item["evaluation_score"],
            item["potential_points"],
            item["score_probability"],
        ),
    )
    recommendation = selected["recommendation"]
    quiniela = recommendation["quiniela"]
    quinigol = recommendation["quinigol"]

    safe = recommendation["quiniela"]["safe_alternative"]
    aggressive = recommendation["quiniela"]["aggressive_alternative"]
    rejected = [
        item
        for item in evaluations
        if item["strategy"] != selected["strategy"]
    ]
    rejected.sort(key=lambda item: item["evaluation_score"])

    return {
        "match": recommendation["match"],
        "phase": context["phase"],
        "group": context["group"],
        "matchday": context["matchday"],
        "match_order": context["match_order"],
        "venue": context["venue"],
        "simulation_mode": simulation_mode,
        "simulations_used": simulations,
        "final_quiniela_recommendation": quiniela["result"],
        "final_score": quiniela["recommended_score"],
        "final_quinigol": quinigol["recommended"],
        "quinigol_team": quinigol.get("team"),
        "quinigol_minute": quinigol.get("minute"),
        "quinigol_range": quinigol["minute_range"],
        "reference_minute": quinigol["minute_label"],
        "quinigol_policy_applied": quinigol.get("policy_applied", "normal"),
        "quinigol_policy_explanation": quinigol.get("policy_explanation", "normal"),
        "confidence": _confidence_from_evaluation(selected, recommendation),
        "risk": _overall_risk(recommendation, context, climate),
        "why_score": _why_score(selected, recommendation, context, climate),
        "why_quinigol": _why_quinigol(recommendation),
        "safe_alternative": f"{safe['result']} {safe['score']} ({safe['probability']}%)",
        "aggressive_alternative": f"{aggressive['result']} {aggressive['score']} ({aggressive['probability']}%)",
        "not_recommended": (
            f"No priorizar estrategia {rejected[0]['strategy']} como pick final "
            f"porque su evaluacion integrada fue menor."
        ) if rejected else "No aplica",
        "data_used": [
            "Core simulate_match",
            "expected_goals",
            "probabilidades 1X2",
            "top_scores",
            "reglas de puntuacion quiniela",
            "estrategias conservador/balanceado/agresivo",
            "fixtures_context.json",
            "venue_climate_profiles.json",
        ],
        "missing_data": _missing_data(context, climate),
        "notes": [
            "La quiniela real se llena una vez: esta salida contiene un pick final unico.",
            "Las alternativas segura y agresiva son informacion secundaria.",
            "No se genera cronologia de goles; Quinigol representa un gol recomendado del juego.",
            "No se usa clima del dia.",
        ],
        "selected_strategy": selected["strategy"],
        "scenario_evaluations": evaluations,
        "tournament_context": context,
        "venue_climate": climate,
    }


def format_final_pick(final_pick: dict) -> str:
    lines = [
        f"Partido: {final_pick['match']}",
        f"Fase: {final_pick['phase']}",
        f"Grupo: {final_pick['group']}",
        f"Jornada: {final_pick['matchday']}",
        f"Sede: {final_pick['venue']}",
        f"Modo de simulacion: {final_pick['simulation_mode']}",
        f"Simulaciones usadas: {final_pick['simulations_used']}",
        f"Recomendacion final quiniela: {final_pick['final_quiniela_recommendation']}",
        f"Marcador final recomendado: {final_pick['final_score']}",
        f"Quinigol final recomendado: {final_pick['final_quinigol']}",
        f"Equipo Quinigol: {final_pick.get('quinigol_team')}",
        f"Rango probable Quinigol: {final_pick['quinigol_range']}",
        f"Minuto referencia: {final_pick['reference_minute']}",
        f"Politica Quinigol: {final_pick.get('quinigol_policy_applied', 'normal')}",
        f"Confianza: {final_pick['confidence']}%",
        f"Riesgo: {final_pick['risk']}",
        f"Por que este marcador: {final_pick['why_score']}",
        f"Por que este Quinigol: {final_pick['why_quinigol']}",
        f"Alternativa segura: {final_pick['safe_alternative']}",
        f"Alternativa agresiva: {final_pick['aggressive_alternative']}",
        f"No recomendado: {final_pick['not_recommended']}",
        "Datos usados: " + "; ".join(final_pick["data_used"]),
        "Datos faltantes: " + "; ".join(final_pick["missing_data"]),
        "Notas: " + " ".join(final_pick["notes"]),
    ]
    return "\n".join(lines)


def load_default_final_pick_inputs() -> tuple[dict, dict, dict]:
    teams_path = ROOT / "data" / "worldcup_2026_real_teams_baseline_v1.json"
    fixtures_path = Path(__file__).resolve().parent / "data" / "fixtures_context.json"
    climate_path = Path(__file__).resolve().parent / "data" / "venue_climate_profiles.json"
    return (
        load_teams(teams_path),
        load_fixture_contexts(fixtures_path),
        load_venue_climate_profiles(climate_path),
    )
