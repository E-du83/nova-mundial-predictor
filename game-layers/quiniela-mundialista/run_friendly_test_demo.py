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


DATA_PATH = Path(__file__).resolve().parent / "data" / "friendly_test_matches.json"


def load_friendly_matches(path: Path = DATA_PATH) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["matches"]


def _missing_team_response(match: dict, missing_teams: list[str]) -> dict:
    context = build_friendly_context(match)
    return {
        "match": match["match"],
        "match_type": context["match_type"],
        "final_recommendation": "pending_real_data",
        "recommended_score": "pending_real_data",
        "quinigol": "pending_real_data",
        "quinigol_range": "pending_real_data",
        "adjusted_confidence": "pending_real_data",
        "friendly_risk": "alto",
        "odds_visible": match["odds_1x2"],
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
    }


def _build_friendly_recommendation(match: dict, teams: dict) -> dict:
    context = build_friendly_context(match)
    missing_teams = [
        team
        for team in (match["team_a"], match["team_b"])
        if team not in teams
    ]
    if missing_teams:
        return _missing_team_response(match, missing_teams)

    final_pick = build_final_pick(
        match["team_a"],
        match["team_b"],
        teams,
        fixtures_data=None,
        climate_profiles=None,
        simulations=20_000,
        seed=2026,
    )

    return {
        "match": match["match"],
        "match_type": context["match_type"],
        "final_recommendation": final_pick["final_quiniela_recommendation"],
        "recommended_score": final_pick["final_score"],
        "quinigol": final_pick["final_quinigol"],
        "quinigol_range": final_pick["quinigol_range"],
        "adjusted_confidence": adjusted_confidence(final_pick["confidence"]),
        "friendly_risk": friendly_risk(final_pick["risk"]),
        "odds_visible": match["odds_1x2"],
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
        "note": "Esto es prueba amistosa, no partido oficial del Mundial. Confianza ajustada por rotacion, pruebas tacticas e intensidad menor.",
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
        f"Confianza ajustada: {recommendation['adjusted_confidence']}",
        f"Riesgo amistoso: {recommendation['friendly_risk']}",
        f"Cuotas visibles si existen: {recommendation['odds_visible']}",
        f"Lectura del mercado: {recommendation['market_reading']}",
        "Datos usados: " + "; ".join(recommendation["data_used"]),
        "Datos faltantes: " + "; ".join(recommendation["missing_data"]),
        f"Nota: {recommendation['note']}",
    ]
    return "\n".join(lines)


def main() -> None:
    teams, _, _ = load_default_final_pick_inputs()
    matches = load_friendly_matches()

    print("NOVA FRIENDLY TEST DEMO - DOMINGO")
    print("Esto es una prueba amistosa, no una prediccion oficial del Mundial.")
    print("")

    for match in matches:
        recommendation = _build_friendly_recommendation(match, teams)
        print(format_friendly_recommendation(recommendation))
        print("")
        print("-" * 72)
        print("")


if __name__ == "__main__":
    main()
