from itertools import combinations
from collections import Counter
import numpy as np

from match_simulator import calculate_expected_goals
from group_simulator import _empty_table, _apply_result, _rank_table

STAGES = ["R32", "R16", "QF", "SF", "FINAL", "CHAMPION"]


def _team_strength(team, teams):
    return float(teams[team].get("nova_strength_rating_v1", teams[team].get("elo", 1750)))


def _simulate_group_once(group_name, group_teams, teams, rng):
    table = _empty_table(group_teams)
    for team_a, team_b in combinations(group_teams, 2):
        la, lb = calculate_expected_goals(teams[team_a], teams[team_b])
        ga = int(rng.poisson(la))
        gb = int(rng.poisson(lb))
        _apply_result(table, team_a, team_b, ga, gb)

    ranked = _rank_table(table, rng)
    rows = []
    for idx, (team, stats) in enumerate(ranked, start=1):
        rows.append({
            "team": team,
            "group": group_name,
            "position": idx,
            "points": stats["points"],
            "gf": stats["gf"],
            "ga": stats["ga"],
            "gd": stats["gd"],
            "wins": stats["wins"],
        })
    return rows


def _rank_thirds(thirds, rng):
    return sorted(
        thirds,
        key=lambda row: (row["points"], row["gd"], row["gf"], row["wins"], rng.random()),
        reverse=True
    )


def simulate_group_stage_once(groups, teams, rng):
    direct = []
    thirds = []
    for group_name, group_teams in groups.items():
        rows = _simulate_group_once(group_name, group_teams, teams, rng)
        for row in rows:
            if row["position"] <= 2:
                row["qualified_as"] = str(row["position"])
                direct.append(row)
            elif row["position"] == 3:
                thirds.append(row)

    best_thirds = _rank_thirds(thirds, rng)[:8]
    for row in best_thirds:
        row["qualified_as"] = "3_best"

    return direct + best_thirds


def seed_qualifiers_generic(qualifiers, teams):
    """
    Bracket genérico MVP. No es todavía el bracket oficial FIFA 2026.
    Usa seeding por posición, puntos, diferencia de gol, goles y fuerza NOVA.
    """
    pos_weight = {1: 3, 2: 2, 3: 1}
    seeded = sorted(
        qualifiers,
        key=lambda row: (
            pos_weight.get(row["position"], 0),
            row["points"],
            row["gd"],
            row["gf"],
            _team_strength(row["team"], teams)
        ),
        reverse=True
    )
    for idx, row in enumerate(seeded, start=1):
        row["seed"] = idx
    return seeded


def build_generic_round_of_32(seeded):
    if len(seeded) != 32:
        raise ValueError("Se requieren exactamente 32 clasificados.")
    return [(seeded[i], seeded[-(i + 1)]) for i in range(16)]


def _penalty_winner(team_a, team_b, teams, rng):
    diff = _team_strength(team_a, teams) - _team_strength(team_b, teams)
    p_a = 0.50 + max(-0.15, min(0.15, diff / 2500))
    return team_a if rng.random() < p_a else team_b


def simulate_knockout_match(team_a, team_b, teams, rng):
    la, lb = calculate_expected_goals(teams[team_a], teams[team_b])
    ga90 = int(rng.poisson(la))
    gb90 = int(rng.poisson(lb))

    if ga90 > gb90:
        return {"winner": team_a, "method": "90", "score_90": f"{ga90}-{gb90}"}
    if gb90 > ga90:
        return {"winner": team_b, "method": "90", "score_90": f"{ga90}-{gb90}"}

    eta = int(rng.poisson(la * 0.27))
    etb = int(rng.poisson(lb * 0.27))
    if eta > etb:
        return {"winner": team_a, "method": "ET", "score_90": f"{ga90}-{gb90}"}
    if etb > eta:
        return {"winner": team_b, "method": "ET", "score_90": f"{ga90}-{gb90}"}

    return {"winner": _penalty_winner(team_a, team_b, teams, rng), "method": "PEN", "score_90": f"{ga90}-{gb90}"}


def _pair_in_order(teams_list):
    return [(teams_list[i], teams_list[i + 1]) for i in range(0, len(teams_list), 2)]


def _play_round(matchups, teams, rng):
    winners = []
    for team_a, team_b in matchups:
        result = simulate_knockout_match(team_a, team_b, teams, rng)
        winners.append(result["winner"])
    return winners


def simulate_full_tournament_knockout(groups, teams, simulations=2000, seed=2026):
    rng = np.random.default_rng(seed)
    all_teams = [team for group in groups.values() for team in group]

    counts = {team: {stage: 0 for stage in STAGES} for team in all_teams}
    champion_counter = Counter()
    final_counter = Counter()
    semifinal_counter = Counter()

    for _ in range(simulations):
        qualifiers = simulate_group_stage_once(groups, teams, rng)

        for row in qualifiers:
            counts[row["team"]]["R32"] += 1

        seeded = seed_qualifiers_generic(qualifiers, teams)
        r32_pairs = build_generic_round_of_32(seeded)
        r32_matchups = [(a["team"], b["team"]) for a, b in r32_pairs]

        r16 = _play_round(r32_matchups, teams, rng)
        for t in r16:
            counts[t]["R16"] += 1

        qf = _play_round(_pair_in_order(r16), teams, rng)
        for t in qf:
            counts[t]["QF"] += 1

        sf = _play_round(_pair_in_order(qf), teams, rng)
        for t in sf:
            counts[t]["SF"] += 1
        semifinal_counter.update(sf)

        finalists = _play_round(_pair_in_order(sf), teams, rng)
        for t in finalists:
            counts[t]["FINAL"] += 1
        final_counter.update([tuple(sorted(finalists))])

        champion = _play_round(_pair_in_order(finalists), teams, rng)[0]
        counts[champion]["CHAMPION"] += 1
        champion_counter[champion] += 1

    probabilities = {
        team: {stage: counts[team][stage] / simulations for stage in STAGES}
        for team in all_teams
    }

    return {
        "simulations": simulations,
        "probabilities": probabilities,
        "champions": [{"team": t, "probability": c / simulations} for t, c in champion_counter.most_common()],
        "finals": [{"final": list(pair), "probability": c / simulations} for pair, c in final_counter.most_common(12)],
        "semifinalists": [{"team": t, "probability": c / simulations} for t, c in semifinal_counter.most_common(16)],
        "note": "Fase 4 MVP usa bracket genérico por seeding. Pendiente integrar bracket oficial FIFA 2026 y asignación exacta de terceros."
    }


def format_knockout_report(result, top_n=16):
    probs = result["probabilities"]
    lines = []
    lines.append("NOVA MUNDIAL PREDICTOR — FASE 4: ELIMINATORIAS + CAMPEÓN")
    lines.append(f"Simulaciones: {result['simulations']:,}")
    lines.append("")
    lines.append("DECISIÓN PARA QUINIELA — CAMPEÓN PRINCIPAL:")
    if result["champions"]:
        top = result["champions"][0]
        lines.append(f"{top['team']} — {round(top['probability'] * 100, 2)}%")
    lines.append("")
    lines.append("TOP CANDIDATOS A CAMPEÓN:")
    for item in result["champions"][:top_n]:
        lines.append(f"- {item['team']}: {round(item['probability'] * 100, 2)}%")
    lines.append("")
    lines.append("FINALES MÁS PROBABLES:")
    for item in result["finals"][:10]:
        lines.append(f"- {' vs '.join(item['final'])}: {round(item['probability'] * 100, 2)}%")
    lines.append("")
    lines.append("PROBABILIDAD POR FASE — TOP:")
    ordered = sorted(probs.items(), key=lambda item: item[1]["CHAMPION"], reverse=True)[:top_n]
    for team, p in ordered:
        lines.append(
            f"- {team}: R32 {round(p['R32']*100,1)}% | R16 {round(p['R16']*100,1)}% | "
            f"QF {round(p['QF']*100,1)}% | SF {round(p['SF']*100,1)}% | "
            f"Final {round(p['FINAL']*100,1)}% | Campeón {round(p['CHAMPION']*100,2)}%"
        )
    lines.append("")
    lines.append("NOTA NOVA:")
    lines.append(result["note"])
    lines.append("Lectura práctica: usar este módulo como primera ruta probabilística; no como bracket oficial final hasta integrar la asignación exacta FIFA.")
    return "\n".join(lines)