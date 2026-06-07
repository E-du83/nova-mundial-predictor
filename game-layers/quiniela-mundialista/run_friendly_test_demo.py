import argparse
import json
from pathlib import Path

from final_pick_engine import (
    build_final_pick,
    load_default_final_pick_inputs,
)
from friendly_context_engine import (
    adjusted_confidence,
    build_friendly_context,
    friendly_risk,
)
from manual_snapshot_engine import (
    find_manual_snapshot,
    load_manual_snapshots,
    summarize_manual_snapshot,
)
from half_time_engine import (  # noqa: E402
    build_half_time_pick,
    format_half_time_lines,
)
from pick_robustness_engine import (  # noqa: E402
    build_pick_robustness,
    format_robustness_lines,
)
from research_intelligence_engine import (  # noqa: E402
    build_research_intelligence,
    format_research_lines,
)
from result_review_engine import (  # noqa: E402
    build_result_review,
    find_real_result,
    format_result_review_lines,
    load_friendly_results,
)
from research_weighting_engine import (  # noqa: E402
    build_research_weighting,
    format_research_weighting_lines,
)
from simulation_config import resolve_simulation_mode


DATA_PATH = Path(__file__).resolve().parent / "data" / "friendly_test_matches.json"
SNAPSHOTS_PATH = Path(__file__).resolve().parent / "data" / "manual_match_snapshots.json"
RESULTS_PATH = Path(__file__).resolve().parent / "data" / "friendly_test_results.json"


def load_friendly_matches(path: Path = DATA_PATH) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["matches"]


def active_matches(matches: list[dict], teams: dict) -> list[dict]:
    active = []
    for match in matches:
        if match.get("excluded_from_current_test"):
            continue
        if match["team_a"] in teams and match["team_b"] in teams:
            active.append(match)
    return active


def excluded_matches(matches: list[dict], teams: dict) -> list[dict]:
    excluded = []
    for match in matches:
        missing_teams = [
            team
            for team in (match["team_a"], match["team_b"])
            if team not in teams
        ]
        if match.get("excluded_from_current_test") or missing_teams:
            item = dict(match)
            if missing_teams and not item.get("reason"):
                item["reason"] = "not_both_worldcup_baseline_teams"
            item["missing_teams"] = missing_teams
            excluded.append(item)
    return excluded


def _missing_team_response(match: dict, missing_teams: list[str], snapshot_summary: dict) -> dict:
    context = build_friendly_context(match)
    research = build_research_intelligence(
        snapshot={},
        snapshot_summary=snapshot_summary,
        base_confidence="pending_real_data",
        base_risk="alto",
    )
    weighting = build_research_weighting(match["team_a"], match["team_b"])
    return {
        "match": match["match"],
        "match_type": context["match_type"],
        "final_recommendation": "pending_real_data",
        "recommended_score": "pending_real_data",
        "quinigol": "pending_real_data",
        "quinigol_range": "pending_real_data",
        "reference_minute": "pending_real_data",
        "adjusted_confidence": "pending_real_data",
        "friendly_risk": "alto",
        "research_adjusted_confidence": research["research_adjusted_confidence"],
        "research_adjusted_risk": research["research_adjusted_risk"],
        "simulation_mode": "not_run",
        "simulations_used": 0,
        "odds_visible": snapshot_summary["odds_visible"],
        "over_under_visible": snapshot_summary["over_under_visible"],
        "market_probabilities_visible": snapshot_summary["market_probabilities_visible"],
        "lineups_visible": snapshot_summary["lineups_visible"],
        "stats_visible": snapshot_summary["stats_visible"],
        "market_reading": research["market_warning"],
        "research": research,
        "research_weighting": weighting,
        "pick_change_status": "no_simulation_run_due_missing_baseline_team",
        "data_used": [
            "friendly_test_matches.json",
            "manual_match_snapshots.json",
        ],
        "missing_data": [
            f"baseline team missing: {team}"
            for team in missing_teams
        ] + [
            "odds_1x2 manual snapshot",
            "kickoff_time_local verified",
            "venue",
            "lineups",
            "injuries",
        ],
        "note": "Esto es prueba amistosa y no partido oficial del Mundial. No se simula si falta un equipo en baseline.",
        "future_real_result": "pending_real_result",
    }


def _build_friendly_recommendation(
    match: dict,
    teams: dict,
    snapshots_data: dict,
    results_data: dict,
    simulation_mode: str,
    simulations: int,
) -> dict:
    context = build_friendly_context(match)
    snapshot = find_manual_snapshot(snapshots_data, match["team_a"], match["team_b"])
    snapshot_summary = summarize_manual_snapshot(snapshot)
    missing_teams = [
        team
        for team in (match["team_a"], match["team_b"])
        if team not in teams
    ]
    if missing_teams:
        return _missing_team_response(match, missing_teams, snapshot_summary)

    final_pick = build_final_pick(
        match["team_a"],
        match["team_b"],
        teams,
        fixtures_data=None,
        climate_profiles=None,
        simulations=simulations,
        simulation_mode=simulation_mode,
        seed=2026,
    )
    base_confidence = adjusted_confidence(final_pick["confidence"])
    base_risk = friendly_risk(final_pick["risk"])
    research = build_research_intelligence(
        snapshot=snapshot,
        snapshot_summary=snapshot_summary,
        base_confidence=base_confidence,
        base_risk=base_risk,
    )
    weighting = build_research_weighting(
        match["team_a"],
        match["team_b"],
        base_confidence=base_confidence,
        base_risk=base_risk,
    )
    half_time = build_half_time_pick(final_pick, context["match_type"])
    robustness = build_pick_robustness(
        final_pick,
        adjusted_confidence=base_confidence,
        friendly_risk=base_risk,
        match_type=context["match_type"],
    )
    real_result = find_real_result(results_data, match["team_a"], match["team_b"])
    result_review = build_result_review(
        recommendation={
            "raw_final_pick": final_pick,
            "recommended_score": final_pick["final_score"],
            "final_recommendation": final_pick["final_quiniela_recommendation"],
            "friendly_risk": base_risk,
        },
        real_result=real_result,
        robustness=robustness,
    )

    return {
        "match": match["match"],
        "match_type": context["match_type"],
        "final_recommendation": final_pick["final_quiniela_recommendation"],
        "recommended_score": final_pick["final_score"],
        "quinigol": final_pick["final_quinigol"],
        "quinigol_range": final_pick["quinigol_range"],
        "reference_minute": final_pick["reference_minute"],
        "adjusted_confidence": base_confidence,
        "friendly_risk": base_risk,
        "research_adjusted_confidence": research["research_adjusted_confidence"],
        "research_adjusted_risk": research["research_adjusted_risk"],
        "simulation_mode": final_pick["simulation_mode"],
        "simulations_used": final_pick["simulations_used"],
        "odds_visible": snapshot_summary["odds_visible"],
        "over_under_visible": snapshot_summary["over_under_visible"],
        "market_probabilities_visible": snapshot_summary["market_probabilities_visible"],
        "lineups_visible": snapshot_summary["lineups_visible"],
        "stats_visible": snapshot_summary["stats_visible"],
        "market_reading": research["market_warning"],
        "research": research,
        "research_weighting": weighting,
        "half_time": half_time,
        "robustness": robustness,
        "real_result": real_result,
        "result_review": result_review,
        "pick_change_status": (
            "no cambio marcador recomendado; research/lineup/tactica solo ajustan confianza, riesgo y contexto"
        ),
        "data_used": final_pick["data_used"] + [
            "friendly_test_matches.json",
            "manual_match_snapshots.json",
            "research_intelligence_engine",
            "friendly_context_engine",
        ],
        "missing_data": sorted(
            set(
                final_pick["missing_data"]
                + [
                    "lineups",
                    "injuries",
                ]
            )
        ),
        "note": (
            "Esto es prueba amistosa, no partido oficial del Mundial. "
            "Confianza ajustada por rotacion, pruebas tacticas e intensidad menor. "
            "El minuto referencia es el punto mas representativo dentro del rango probable, no una promesa exacta."
        ),
        "future_real_result": "pending_real_result",
        "raw_final_pick": final_pick,
    }


def format_friendly_recommendation(recommendation: dict) -> str:
    lines = [
        f"Partido: {recommendation['match']}",
        f"Tipo de partido: {recommendation['match_type']}",
        f"Recomendacion final: {recommendation['final_recommendation']}",
        f"Marcador recomendado: {recommendation['recommended_score']}",
        f"Quinigol recomendado: {recommendation['quinigol']}",
        f"Rango probable: {recommendation['quinigol_range']}",
        f"Minuto referencia: {recommendation['reference_minute']}",
        f"Modo de simulacion: {recommendation['simulation_mode']}",
        f"Simulaciones usadas: {recommendation['simulations_used']}",
        f"Confianza ajustada: {recommendation['adjusted_confidence']}",
        f"Riesgo amistoso: {recommendation['friendly_risk']}",
        f"Confianza ajustada con investigacion: {recommendation.get('research_adjusted_confidence')}",
        f"Riesgo ajustado con investigacion: {recommendation.get('research_adjusted_risk')}",
        f"Cuotas visibles si existen: {recommendation['odds_visible']}",
        f"Over/Under visible: {recommendation['over_under_visible']}",
        f"Probabilidades mercado si existen: {recommendation['market_probabilities_visible']}",
        f"Alineaciones/formaciones visibles: {recommendation['lineups_visible']}",
        f"Stats snapshot visibles: {recommendation['stats_visible']}",
        f"Lectura del mercado: {recommendation['market_reading']}",
        f"Player rating impact: {recommendation['research_weighting']['player_rating_alignment']}",
        (
            "Ratings reales/replacement/criticos faltantes: "
            f"{recommendation['research_weighting']['lineup_strength']['known_rating_count']}/"
            f"{recommendation['research_weighting']['lineup_strength']['replacement_rating_count']}/"
            f"{len(recommendation['research_weighting']['lineup_strength']['critical_missing_ratings'])}"
        ),
        (
            "Rating coverage: "
            f"{recommendation['research_weighting']['lineup_strength']['rating_coverage']}% total | "
            f"{recommendation['research_weighting']['lineup_strength']['real_rating_coverage']}% real"
        ),
        (
            "Source confidence weighted score: "
            f"{recommendation['research_weighting']['lineup_strength']['source_confidence_weighted_score']}%"
        ),
        (
            "Lineup strength: "
            f"{recommendation['research_weighting']['lineup_strength']['team_a']['team']} "
            f"GK {recommendation['research_weighting']['lineup_strength']['team_a']['goalkeeper_strength']} / "
            f"DEF {recommendation['research_weighting']['lineup_strength']['team_a']['defense_strength']} / "
            f"MID {recommendation['research_weighting']['lineup_strength']['team_a']['midfield_strength']} / "
            f"ATT {recommendation['research_weighting']['lineup_strength']['team_a']['attack_strength']} | "
            f"{recommendation['research_weighting']['lineup_strength']['team_b']['team']} "
            f"GK {recommendation['research_weighting']['lineup_strength']['team_b']['goalkeeper_strength']} / "
            f"DEF {recommendation['research_weighting']['lineup_strength']['team_b']['defense_strength']} / "
            f"MID {recommendation['research_weighting']['lineup_strength']['team_b']['midfield_strength']} / "
            f"ATT {recommendation['research_weighting']['lineup_strength']['team_b']['attack_strength']}"
        ),
        (
            "Lineup strength status: "
            f"{recommendation['research_weighting']['lineup_strength']['lineup_weighting_status']}"
        ),
        (
            "Replacement ratings usados: "
            + (
                ", ".join(recommendation["research_weighting"]["lineup_strength"]["critical_missing_ratings"])
                if recommendation["research_weighting"]["lineup_strength"]["critical_missing_ratings"]
                else "none"
            )
        ),
        f"Tactical weighting impact: {recommendation['research_weighting']['tactical_alignment']}",
        (
            "Research weighting impact: "
            f"confidence {recommendation['research_weighting']['total_confidence_adjustment']} | "
            f"risk {recommendation['research_weighting']['total_risk_adjustment']}"
        ),
        (
            "Datos que cambiaron confianza/riesgo: "
            f"mercado={recommendation['research_weighting']['market_alignment']}; "
            f"ratings={recommendation['research_weighting']['player_rating_alignment']}; "
            f"tactica={recommendation['research_weighting']['tactical_alignment']}"
        ),
        f"Market alignment: {recommendation['research_weighting']['market_alignment']}",
        f"Model fragility: {recommendation['research_weighting']['model_fragility']}",
        f"Descanso recomendado: {recommendation['half_time']['half_time_score']}",
        f"Descanso/final recomendado: {recommendation['half_time']['half_time_full_time']}",
        f"Robustez del pick: {recommendation['robustness']['pick_robustness']}",
        f"Alerta de empate: {'si' if recommendation['robustness']['draw_warning'] else 'no'}",
        f"Motivo alerta empate: {recommendation['robustness']['draw_warning_reason']}",
        f"Resultado real registrado: {recommendation['result_review']['real_score']}",
        f"Revision resultado: {recommendation['result_review']['summary']}",
        f"Cambio de pick: {recommendation['pick_change_status']}",
        f"Comparacion futura resultado real: {recommendation['future_real_result']}",
        "Datos usados: " + "; ".join(recommendation["data_used"]),
        "Datos faltantes: " + "; ".join(recommendation["missing_data"]),
        f"Nota: {recommendation['note']}",
    ]
    lines.extend(format_research_lines(recommendation["research"]))
    lines.extend(format_research_weighting_lines(recommendation["research_weighting"]))
    lines.extend(format_half_time_lines(recommendation["half_time"]))
    lines.extend(format_robustness_lines(recommendation["robustness"]))
    lines.extend(format_result_review_lines(recommendation["result_review"]))
    return "\n".join(lines)


def build_friendly_recommendations(mode: str = "quick") -> tuple[list[dict], list[dict], str, int]:
    teams, _, _ = load_default_final_pick_inputs()
    matches = load_friendly_matches()
    snapshots_data = load_manual_snapshots(SNAPSHOTS_PATH)
    results_data = load_friendly_results(RESULTS_PATH)
    simulation_mode, simulations = resolve_simulation_mode(mode)
    active = active_matches(matches, teams)
    excluded = excluded_matches(matches, teams)
    recommendations = [
        _build_friendly_recommendation(
            match,
            teams,
            snapshots_data,
            results_data,
            simulation_mode,
            simulations,
        )
        for match in active
    ]
    return recommendations, excluded, simulation_mode, simulations


def run_friendly_test(mode: str = "quick") -> None:
    recommendations, excluded, simulation_mode, simulations = build_friendly_recommendations(mode)

    print("NOVA FRIENDLY TEST DEMO - DOMINGO")
    print("Esto es una prueba amistosa, no una prediccion oficial del Mundial.")
    print("Solo se simulan partidos activos con ambos equipos mundialistas en baseline.")
    print(f"Modo de simulacion: {simulation_mode}")
    print(f"Simulaciones usadas: {simulations}")
    print("")

    print("PARTIDOS ACTIVOS PARA PRUEBA")
    for recommendation in recommendations:
        print(f"- {recommendation['match']}")
    print("")

    print("PARTIDOS EXCLUIDOS")
    for match in excluded:
        missing = ", ".join(match.get("missing_teams", [])) or "no aplica"
        print(f"- {match['match']} | razon: {match.get('reason')} | faltantes: {missing}")
    print("")

    for recommendation in recommendations:
        print(format_friendly_recommendation(recommendation))
        print("")
        print("-" * 72)
        print("")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Corre la prueba amistosa con modo de simulacion configurable."
    )
    parser.add_argument(
        "--mode",
        default="quick",
        choices=["quick", "standard", "final"],
        help="Modo de simulacion: quick=10000, standard=100000, final=1000000.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_friendly_test(args.mode)


if __name__ == "__main__":
    main()
