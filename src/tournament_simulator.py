from itertools import combinations
from collections import Counter
import numpy as np

from match_simulator import calculate_expected_goals
from group_simulator import _empty_table, _apply_result, _rank_table


def _simulate_group_once(group_teams: list[str], teams: dict, rng) -> tuple[list[tuple[str, dict]], dict]:
    table = _empty_table(group_teams)
    for team_a, team_b in combinations(group_teams, 2):
        lambda_a, lambda_b = calculate_expected_goals(teams[team_a], teams[team_b])
        goals_a = int(rng.poisson(lambda_a))
        goals_b = int(rng.poisson(lambda_b))
        _apply_result(table, team_a, team_b, goals_a, goals_b)
    ranked = _rank_table(table, rng)
    return ranked, table


def _rank_third_placed(thirds: list[dict], rng) -> list[dict]:
    return sorted(
        thirds,
        key=lambda t: (t["points"], t["gd"], t["gf"], t["wins"], rng.random()),
        reverse=True
    )


def simulate_tournament_groups(groups: dict[str, list[str]], teams: dict, simulations: int = 100_000, seed: int = 42) -> dict:
    if len(groups) != 12:
        raise ValueError("Para el formato 2026 se esperan 12 grupos.")

    for group_name, group_teams in groups.items():
        if len(group_teams) != 4:
            raise ValueError(f"El grupo {group_name} debe tener exactamente 4 equipos.")
        for team in group_teams:
            if team not in teams:
                raise KeyError(f"No existe el equipo en la base de datos: {team}")

    rng = np.random.default_rng(seed)
    all_teams = [team for group_teams in groups.values() for team in group_teams]

    counts = {
        team: {
            "1st": 0,
            "2nd": 0,
            "3rd_qualified": 0,
            "3rd_eliminated": 0,
            "4th": 0,
            "total_qualified": 0,
            "direct_qualified": 0,
            "third_total": 0,
        }
        for team in all_teams
    }

    totals = {team: {"points": 0, "gf": 0, "ga": 0, "gd": 0} for team in all_teams}
    group_order_counter = {group_name: Counter() for group_name in groups}

    for _ in range(simulations):
        third_candidates = []

        for group_name, group_teams in groups.items():
            ranked, table = _simulate_group_once(group_teams, teams, rng)
            order = tuple(team for team, _stats in ranked)
            group_order_counter[group_name][order] += 1

            for idx, (team, stats) in enumerate(ranked):
                position = idx + 1
                totals[team]["points"] += stats["points"]
                totals[team]["gf"] += stats["gf"]
                totals[team]["ga"] += stats["ga"]
                totals[team]["gd"] += stats["gd"]

                if position == 1:
                    counts[team]["1st"] += 1
                    counts[team]["direct_qualified"] += 1
                    counts[team]["total_qualified"] += 1
                elif position == 2:
                    counts[team]["2nd"] += 1
                    counts[team]["direct_qualified"] += 1
                    counts[team]["total_qualified"] += 1
                elif position == 3:
                    counts[team]["third_total"] += 1
                    third_candidates.append({
                        "team": team,
                        "group": group_name,
                        "points": stats["points"],
                        "gf": stats["gf"],
                        "ga": stats["ga"],
                        "gd": stats["gd"],
                        "wins": stats["wins"],
                    })
                else:
                    counts[team]["4th"] += 1

        ranked_thirds = _rank_third_placed(third_candidates, rng)
        qualified_thirds = set(t["team"] for t in ranked_thirds[:8])
        eliminated_thirds = set(t["team"] for t in ranked_thirds[8:])

        for team in qualified_thirds:
            counts[team]["3rd_qualified"] += 1
            counts[team]["total_qualified"] += 1
        for team in eliminated_thirds:
            counts[team]["3rd_eliminated"] += 1

    team_output = {}
    for team in all_teams:
        team_output[team] = {
            "prob_1st": counts[team]["1st"] / simulations,
            "prob_2nd": counts[team]["2nd"] / simulations,
            "prob_3rd_qualified": counts[team]["3rd_qualified"] / simulations,
            "prob_3rd_eliminated": counts[team]["3rd_eliminated"] / simulations,
            "prob_4th": counts[team]["4th"] / simulations,
            "prob_direct_qualified": counts[team]["direct_qualified"] / simulations,
            "prob_total_qualified": counts[team]["total_qualified"] / simulations,
            "prob_third_total": counts[team]["third_total"] / simulations,
            "expected_points": totals[team]["points"] / simulations,
            "expected_gf": totals[team]["gf"] / simulations,
            "expected_ga": totals[team]["ga"] / simulations,
            "expected_gd": totals[team]["gd"] / simulations,
        }

    group_outputs = {}
    for group_name, counter in group_order_counter.items():
        group_outputs[group_name] = [
            {"order": list(order), "probability": count / simulations}
            for order, count in counter.most_common(5)
        ]

    return {
        "simulations": simulations,
        "groups": groups,
        "team_probabilities": team_output,
        "group_common_orders": group_outputs,
        "note": "MVP Fase 3: simula grupos y mejores terceros. Todavía no construye automáticamente el bracket de ronda de 32."
    }


def format_tournament_group_report(result: dict) -> str:
    groups = result["groups"]
    probs = result["team_probabilities"]
    simulations = result["simulations"]

    lines = []
    lines.append("NOVA MUNDIAL PREDICTOR — FASE DE GRUPOS + MEJORES TERCEROS")
    lines.append(f"Simulaciones: {simulations:,}")
    lines.append("")

    for group_name, group_teams in groups.items():
        ordered = sorted(
            group_teams,
            key=lambda team: (
                probs[team]["prob_total_qualified"],
                probs[team]["prob_direct_qualified"],
                probs[team]["expected_points"]
            ),
            reverse=True
        )

        lines.append(f"GRUPO {group_name}")
        lines.append("DECISIÓN RECOMENDADA:")
        for idx, team in enumerate(ordered, start=1):
            lines.append(f"{idx}. {team}")

        first, second, third = ordered[0], ordered[1], ordered[2]
        lines.append("QUÉ HACER:")
        lines.append(f"- Poner a {first} como 1.º.")
        lines.append(f"- Poner a {second} como 2.º.")
        if probs[third]["prob_3rd_qualified"] >= 0.45:
            lines.append(f"- Marcar a {third} como buen candidato a mejor 3.º.")
        elif probs[third]["prob_3rd_qualified"] >= 0.25:
            lines.append(f"- Marcar a {third} como 3.º posible, pero no seguro.")
        else:
            lines.append(f"- No confiar demasiado en {third} como mejor 3.º.")

        lines.append("PROBABILIDADES CLAVE:")
        for team in ordered:
            data = probs[team]
            lines.append(
                f"- {team}: clasifica total {round(data['prob_total_qualified']*100,2)}% | "
                f"1.º {round(data['prob_1st']*100,2)}% | "
                f"2.º {round(data['prob_2nd']*100,2)}% | "
                f"3.º clasificado {round(data['prob_3rd_qualified']*100,2)}% | "
                f"3.º eliminado {round(data['prob_3rd_eliminated']*100,2)}% | "
                f"4.º {round(data['prob_4th']*100,2)}%"
            )
        lines.append("")

    third_candidates = sorted(probs.items(), key=lambda item: item[1]["prob_3rd_qualified"], reverse=True)[:12]
    lines.append("MEJORES CANDIDATOS A 3.º CLASIFICADO:")
    for team, data in third_candidates:
        if data["prob_3rd_qualified"] > 0:
            lines.append(f"- {team}: {round(data['prob_3rd_qualified']*100,2)}%")

    lines.append("")
    lines.append("NOTA NOVA:")
    lines.append(result["note"])
    lines.append("La siguiente fase debe construir la ruta de ronda de 32, octavos, cuartos, semifinales y final.")
    return "\n".join(lines)