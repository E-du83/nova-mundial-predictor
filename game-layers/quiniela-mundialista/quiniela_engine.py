from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from match_simulator import load_teams, simulate_match  # noqa: E402
from quinigol_engine import recommend_quinigol  # noqa: E402
from simulation_config import infer_simulation_mode  # noqa: E402
from strategy_engine import choose_quiniela_strategy, normalize_strategy  # noqa: E402


def _team_strength(team_data: dict) -> float | None:
    for key in ("nova_strength_rating_v1", "elo", "world_football_elo"):
        value = team_data.get(key)
        if value is not None:
            return float(value)
    return None


def _attach_layer_context(core_result: dict, quiniela: dict, teams: dict) -> None:
    team_a = core_result["team_a"]
    team_b = core_result["team_b"]
    strength_a = _team_strength(teams[team_a])
    strength_b = _team_strength(teams[team_b])

    core_result["recommended_score"] = quiniela["recommended_score"]
    core_result["quiniela_context"] = {
        "recommended_score": quiniela["recommended_score"],
        "risk": quiniela["risk"],
        "score_probability": quiniela["score_probability"],
        "result_probability": quiniela["result_probability"],
        "strategy": quiniela["strategy"],
    }

    if strength_a is not None and strength_b is not None:
        difference = strength_a - strength_b
        core_result["strength_difference"] = {
            team_a: difference,
            team_b: -difference,
            "absolute": abs(difference),
        }


def recommend_match(
    team_a: str,
    team_b: str,
    teams: dict,
    strategy: str = "balanceado",
    simulations: int = 50_000,
    seed: int = 2026,
    simulation_mode: str | None = None,
) -> dict:
    """
    Build a Quiniela Mundialista recommendation from the Core match simulator.

    The Core remains responsible for probabilities and expected goals. This
    layer only translates those outputs into game picks and risk language.
    """
    strategy = normalize_strategy(strategy)
    core_result = simulate_match(
        team_a,
        team_b,
        teams,
        simulations=simulations,
        seed=seed,
    )
    quiniela = choose_quiniela_strategy(core_result, strategy=strategy)
    _attach_layer_context(core_result, quiniela, teams)
    quinigol = recommend_quinigol(core_result, strategy=strategy)

    return {
        "match": f"{team_a} vs {team_b}",
        "team_a": team_a,
        "team_b": team_b,
        "strategy": strategy,
        "quiniela": quiniela,
        "quinigol": quinigol,
        "core": {
            "simulations": core_result["simulations"],
            "simulation_mode": simulation_mode or infer_simulation_mode(core_result["simulations"]),
            "expected_goals": core_result["expected_goals"],
            "probabilities": core_result["probabilities"],
            "top_scores": core_result["top_scores"],
        },
        "game_definition": "90 minutos, incluye dos tiempos regulares.",
    }


def format_quiniela_recommendation(recommendation: dict) -> str:
    quiniela = recommendation["quiniela"]
    quinigol = recommendation["quinigol"]
    safe = quiniela["safe_alternative"]
    aggressive = quiniela["aggressive_alternative"]
    core = recommendation["core"]

    expected_goals = core["expected_goals"]
    team_a = recommendation["team_a"]
    team_b = recommendation["team_b"]

    justification = (
        f"El Core proyecto {expected_goals[team_a]} xG para {team_a} y "
        f"{expected_goals[team_b]} xG para {team_b}. La capa usa esos datos "
        "para ajustar marcador, riesgo y Quinigol sin duplicar el motor principal."
    )

    lines = [
        f"Partido: {recommendation['match']}",
        f"Prediccion quiniela: {quiniela['result']}",
        f"Marcador recomendado: {quiniela['recommended_score']}",
        f"Confianza: {quiniela['confidence']}%",
        f"Riesgo: {quiniela['risk']}",
        f"Estrategia: {recommendation['strategy']}",
        f"Modo de simulacion: {core['simulation_mode']}",
        f"Simulaciones usadas: {core['simulations']}",
        f"Quinigol recomendado: {quinigol['recommended']}",
        f"Minuto probable: {quinigol['minute_label']}",
        (
            "Alternativa segura: "
            f"{safe['result']} {safe['score']} ({safe['probability']}%)"
        ),
        (
            "Alternativa agresiva: "
            f"{aggressive['result']} {aggressive['score']} ({aggressive['probability']}%)"
        ),
        (
            "Detalle Quinigol: "
            f"rango probable {quinigol['minute_range']} | "
            f"riesgo {quinigol['risk']} | "
            f"opcion no hay {quinigol['no_goal_option']['probability']}%"
        ),
        f"Explicacion simple del minuto: {quinigol['minute_explanation']}",
        f"Riesgo simple: {quinigol['risk_explanation']}",
        f"Criterio estrategia: {quiniela['strategy_explanation']}",
        f"Justificacion breve: {justification}",
    ]
    return "\n".join(lines)


def recommend_many_matches(
    matches: list[tuple[str, str, str]],
    teams: dict,
    simulations: int = 50_000,
    seed: int = 2026,
    simulation_mode: str | None = None,
) -> list[dict]:
    recommendations = []
    for index, (team_a, team_b, strategy) in enumerate(matches):
        recommendations.append(
            recommend_match(
                team_a,
                team_b,
                teams,
                strategy=strategy,
                simulations=simulations,
                seed=seed + index,
                simulation_mode=simulation_mode,
            )
        )
    return recommendations
