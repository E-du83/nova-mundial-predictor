from itertools import combinations
from collections import defaultdict, Counter
import numpy as np

from match_simulator import calculate_expected_goals


def _simulate_single_score(team_a_name: str, team_b_name: str, teams: dict, rng) -> tuple[int, int]:
    """Simulate one football score using the same expected goals engine as match_simulator."""
    lambda_a, lambda_b = calculate_expected_goals(teams[team_a_name], teams[team_b_name])
    goals_a = int(rng.poisson(lambda_a))
    goals_b = int(rng.poisson(lambda_b))
    return goals_a, goals_b


def _empty_table(group_teams: list[str]) -> dict:
    return {
        team: {
            "played": 0,
            "points": 0,
            "gf": 0,
            "ga": 0,
            "gd": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
        }
        for team in group_teams
    }


def _apply_result(table: dict, team_a: str, team_b: str, goals_a: int, goals_b: int) -> None:
    table[team_a]["played"] += 1
    table[team_b]["played"] += 1

    table[team_a]["gf"] += goals_a
    table[team_a]["ga"] += goals_b
    table[team_b]["gf"] += goals_b
    table[team_b]["ga"] += goals_a

    table[team_a]["gd"] = table[team_a]["gf"] - table[team_a]["ga"]
    table[team_b]["gd"] = table[team_b]["gf"] - table[team_b]["ga"]

    if goals_a > goals_b:
        table[team_a]["points"] += 3
        table[team_a]["wins"] += 1
        table[team_b]["losses"] += 1
    elif goals_a < goals_b:
        table[team_b]["points"] += 3
        table[team_b]["wins"] += 1
        table[team_a]["losses"] += 1
    else:
        table[team_a]["points"] += 1
        table[team_b]["points"] += 1
        table[team_a]["draws"] += 1
        table[team_b]["draws"] += 1


def _rank_table(table: dict, rng) -> list[tuple[str, dict]]:
    """
    Rank group table.
    Simplified FIFA-like order:
    1. Points
    2. Goal difference
    3. Goals scored
    4. Wins
    5. Random tiny tiebreaker for unresolved ties in MVP

    Later versions should implement exact head-to-head and fair-play rules.
    """
    ranked = sorted(
        table.items(),
        key=lambda item: (
            item[1]["points"],
            item[1]["gd"],
            item[1]["gf"],
            item[1]["wins"],
            rng.random()
        ),
        reverse=True
    )
    return ranked


def simulate_group(
    group_name: str,
    group_teams: list[str],
    teams: dict,
    simulations: int = 100_000,
    seed: int = 42
) -> dict:
    """
    Simulate one 4-team group many times.

    Output:
    - probability of finishing 1st, 2nd, 3rd, 4th
    - probability of direct qualification, assuming 1st and 2nd qualify
    - probability of finishing 3rd
    - expected points, goal difference and goals for
    - most common final orders
    """

    if len(group_teams) != 4:
        raise ValueError("Este MVP de grupos espera exactamente 4 equipos.")

    for team in group_teams:
        if team not in teams:
            raise KeyError(f"No existe el equipo en la base de datos: {team}")

    rng = np.random.default_rng(seed)
    matches = list(combinations(group_teams, 2))

    finish_counts = {
        team: {
            "1st": 0,
            "2nd": 0,
            "3rd": 0,
            "4th": 0,
            "direct_qualify": 0,
            "third_place": 0,
        }
        for team in group_teams
    }

    totals = {
        team: {
            "points": 0,
            "gf": 0,
            "ga": 0,
            "gd": 0,
        }
        for team in group_teams
    }

    order_counter = Counter()

    for _ in range(simulations):
        table = _empty_table(group_teams)

        for team_a, team_b in matches:
            goals_a, goals_b = _simulate_single_score(team_a, team_b, teams, rng)
            _apply_result(table, team_a, team_b, goals_a, goals_b)

        ranked = _rank_table(table, rng)
        order = tuple(team for team, _stats in ranked)
        order_counter[order] += 1

        for idx, (team, stats) in enumerate(ranked):
            position = idx + 1
            finish_counts[team][f"{position}{'st' if position == 1 else 'nd' if position == 2 else 'rd' if position == 3 else 'th'}"] += 1

            if position <= 2:
                finish_counts[team]["direct_qualify"] += 1
            if position == 3:
                finish_counts[team]["third_place"] += 1

            totals[team]["points"] += stats["points"]
            totals[team]["gf"] += stats["gf"]
            totals[team]["ga"] += stats["ga"]
            totals[team]["gd"] += stats["gd"]

    teams_output = {}
    for team in group_teams:
        teams_output[team] = {
            "prob_1st": finish_counts[team]["1st"] / simulations,
            "prob_2nd": finish_counts[team]["2nd"] / simulations,
            "prob_3rd": finish_counts[team]["3rd"] / simulations,
            "prob_4th": finish_counts[team]["4th"] / simulations,
            "prob_direct_qualify": finish_counts[team]["direct_qualify"] / simulations,
            "prob_third_place": finish_counts[team]["third_place"] / simulations,
            # MVP note: actual best third qualification needs all 12 groups together.
            "expected_points": totals[team]["points"] / simulations,
            "expected_gf": totals[team]["gf"] / simulations,
            "expected_ga": totals[team]["ga"] / simulations,
            "expected_gd": totals[team]["gd"] / simulations,
        }

    common_orders = [
        {
            "order": list(order),
            "probability": count / simulations
        }
        for order, count in order_counter.most_common(8)
    ]

    return {
        "group_name": group_name,
        "teams": group_teams,
        "simulations": simulations,
        "team_probabilities": teams_output,
        "most_common_orders": common_orders,
        "note": "En este MVP, los dos primeros clasifican directo. La clasificación como mejor tercero requiere simular los 12 grupos juntos; se agregará en la siguiente fase."
    }


def format_group_report(group_result: dict) -> str:
    group_name = group_result["group_name"]
    simulations = group_result["simulations"]
    probs = group_result["team_probabilities"]

    lines = []
    lines.append(f"GRUPO {group_name}")
    lines.append(f"Simulaciones: {simulations:,}")
    lines.append("")

    # Recommended order by expected points, then direct qualification
    ordered = sorted(
        probs.items(),
        key=lambda item: (
            item[1]["expected_points"],
            item[1]["prob_direct_qualify"],
            item[1]["prob_1st"]
        ),
        reverse=True
    )

    lines.append("DECISIÓN RECOMENDADA PARA QUINIELA:")
    for idx, (team, _data) in enumerate(ordered, start=1):
        lines.append(f"{idx}. {team}")
    lines.append("")

    lines.append("QUÉ HACER:")
    first = ordered[0][0]
    second = ordered[1][0]
    third = ordered[2][0]
    lines.append(f"Poner a {first} como 1.º del grupo.")
    lines.append(f"Poner a {second} como 2.º del grupo.")
    lines.append(f"Marcar a {third} como candidato a 3.º con opción, pero pendiente de comparación contra otros grupos.")
    lines.append("")

    lines.append("PROBABILIDADES POR EQUIPO:")
    for team, data in ordered:
        lines.append("")
        lines.append(f"{team}:")
        lines.append(f"- 1.º: {round(data['prob_1st'] * 100, 2)}%")
        lines.append(f"- 2.º: {round(data['prob_2nd'] * 100, 2)}%")
        lines.append(f"- 3.º: {round(data['prob_3rd'] * 100, 2)}%")
        lines.append(f"- 4.º: {round(data['prob_4th'] * 100, 2)}%")
        lines.append(f"- Clasifica directo, 1.º o 2.º: {round(data['prob_direct_qualify'] * 100, 2)}%")
        lines.append(f"- Puntos esperados: {round(data['expected_points'], 2)}")
        lines.append(f"- Diferencia de gol esperada: {round(data['expected_gd'], 2)}")

    lines.append("")
    lines.append("ÓRDENES MÁS REPETIDOS EN LA SIMULACIÓN:")
    for item in group_result["most_common_orders"][:5]:
        order = " / ".join(item["order"])
        lines.append(f"- {order}: {round(item['probability'] * 100, 2)}%")

    lines.append("")
    lines.append("NOTA NOVA:")
    lines.append(group_result["note"])
    lines.append("La siguiente fase agregará comparación real de mejores terceros entre todos los grupos.")

    return "\n".join(lines)