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
    market_reading,
)
from manual_snapshot_engine import (
    find_manual_snapshot,
    load_manual_snapshots,
    summarize_manual_snapshot,
)
from simulation_config import resolve_simulation_mode


DATA_PATH = Path(__file__).resolve().parent / "data" / "friendly_test_matches.json"
SNAPSHOTS_PATH = Path(__file__).resolve().parent / "data" / "manual_match_snapshots.json"


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
        "simulation_mode": "not_run",
        "simulations_used": 0,
        "odds_visible": snapshot_summary["odds_visible"],
        "lineups_visible": snapshot_summary["lineups_visible"],
        "stats_visible": snapshot_summary["stats_visible"],
        "market_reading": market_reading(match["odds_1x2"]),
        "data_used": [
            "friendly_test_matches.json",
            "365Scores screenshot/manual",
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

    return {
        "match": match["match"],
        "match_type": context["match_type"],
        "final_recommendation": final_pick["final_quiniela_recommendation"],
        "recommended_score": final_pick["final_score"],
        "quinigol": final_pick["final_quinigol"],
        "quinigol_range": final_pick["quinigol_range"],
        "reference_minute": final_pick["reference_minute"],
        "adjusted_confidence": adjusted_confidence(final_pick["confidence"]),
        "friendly_risk": friendly_risk(final_pick["risk"]),
        "simulation_mode": final_pick["simulation_mode"],
        "simulations_used": final_pick["simulations_used"],
        "odds_visible": snapshot_summary["odds_visible"],
        "lineups_visible": snapshot_summary["lineups_visible"],
        "stats_visible": snapshot_summary["stats_visible"],
        "market_reading": market_reading(match["odds_1x2"]),
        "data_used": final_pick["data_used"] + [
            "friendly_test_matches.json",
            "friendly_context_engine",
        ],
        "missing_data": sorted(
            set(
                final_pick["missing_data"]
                + [
                    "odds_1x2 manual snapshot",
                    "kickoff_time_local verified",
                    "friendly venue",
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
        f"Cuotas visibles si existen: {recommendation['odds_visible']}",
        f"Alineaciones/formaciones visibles: {recommendation['lineups_visible']}",
        f"Stats snapshot visibles: {recommendation['stats_visible']}",
        f"Lectura del mercado: {recommendation['market_reading']}",
        f"Comparacion futura resultado real: {recommendation['future_real_result']}",
        "Datos usados: " + "; ".join(recommendation["data_used"]),
        "Datos faltantes: " + "; ".join(recommendation["missing_data"]),
        f"Nota: {recommendation['note']}",
    ]
    return "\n".join(lines)


def run_friendly_test(mode: str = "quick") -> None:
    teams, _, _ = load_default_final_pick_inputs()
    matches = load_friendly_matches()
    snapshots_data = load_manual_snapshots(SNAPSHOTS_PATH)
    simulation_mode, simulations = resolve_simulation_mode(mode)
    active = active_matches(matches, teams)
    excluded = excluded_matches(matches, teams)

    print("NOVA FRIENDLY TEST DEMO - DOMINGO")
    print("Esto es una prueba amistosa, no una prediccion oficial del Mundial.")
    print("Solo se simulan partidos activos con ambos equipos mundialistas en baseline.")
    print(f"Modo de simulacion: {simulation_mode}")
    print(f"Simulaciones usadas: {simulations}")
    print("")

    print("PARTIDOS ACTIVOS PARA PRUEBA")
    for match in active:
        print(f"- {match['match']}")
    print("")

    print("PARTIDOS EXCLUIDOS")
    for match in excluded:
        missing = ", ".join(match.get("missing_teams", [])) or "no aplica"
        print(f"- {match['match']} | razon: {match.get('reason')} | faltantes: {missing}")
    print("")

    for match in active:
        recommendation = _build_friendly_recommendation(
            match,
            teams,
            snapshots_data,
            simulation_mode,
            simulations,
        )
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
