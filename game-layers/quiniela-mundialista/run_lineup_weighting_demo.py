from pathlib import Path

from lineup_strength_engine import build_match_lineup_strength
from manual_snapshot_engine import load_manual_snapshots


SNAPSHOTS_PATH = Path(__file__).resolve().parent / "data" / "manual_match_snapshots.json"


def _print_team(team_strength: dict) -> None:
    print(f"Equipo: {team_strength['team']}")
    print("Jugadores detectados: " + ", ".join(team_strength["players_detected"]))
    print(
        "Ratings encontrados: "
        + (", ".join(team_strength["ratings_found"]) if team_strength["ratings_found"] else "none")
    )
    print(
        "Ratings estimados/replacement: "
        + (
            ", ".join(team_strength["ratings_replacement"])
            if team_strength["ratings_replacement"]
            else "none"
        )
    )
    print(
        "Ratings criticos faltantes: "
        + (
            ", ".join(team_strength["critical_missing_ratings"])
            if team_strength["critical_missing_ratings"]
            else "none"
        )
    )
    print(f"goalkeeper_strength: {team_strength['goalkeeper_strength']}")
    print(f"defense_strength: {team_strength['defense_strength']}")
    print(f"midfield_strength: {team_strength['midfield_strength']}")
    print(f"attack_strength: {team_strength['attack_strength']}")
    print(f"lineup_strength_total: {team_strength['lineup_strength_total']}")
    print(f"known_rating_count: {team_strength['known_rating_count']}")
    print(f"replacement_rating_count: {team_strength['replacement_rating_count']}")
    print(f"missing_rating_count: {team_strength['missing_rating_count']}")
    print(f"rating_coverage: {team_strength['rating_coverage']}%")
    print(f"real_rating_coverage: {team_strength['real_rating_coverage']}%")
    print(f"source_confidence_weighted_score: {team_strength['source_confidence_weighted_score']}%")
    print(f"lineup_data_quality: {team_strength['lineup_data_quality']}")
    print(f"lineup_weighting_status: {team_strength['lineup_weighting_status']}")
    print(
        "Ajustes aplicados: "
        f"attack_xg={team_strength['attack_xg_adjustment']} | "
        f"defense_xg={team_strength['defense_xg_adjustment']} | "
        f"quinigol={team_strength['quinigol_adjustment']} | "
        f"confidence={team_strength['confidence_adjustment']} | "
        f"risk={team_strength['risk_adjustment']}"
    )
    print(f"Estado ajustes: {team_strength['adjustment_status']}")
    if team_strength["warnings"]:
        print("Ajustes pendientes / warnings:")
        for warning in team_strength["warnings"]:
            print(f"- {warning}")


def main() -> None:
    snapshots_data = load_manual_snapshots(SNAPSHOTS_PATH)
    print("NOVA LINEUP WEIGHTING DEMO")
    print("Dato -> variable -> peso -> ajuste -> impacto en prediccion.")
    print("No se aplican pesos fuertes si faltan ratings reales.")
    print("")

    for snapshot in snapshots_data.get("snapshots", []):
        result = build_match_lineup_strength(snapshot["team_a"], snapshot["team_b"])
        print(f"Partido: {result['match']}")
        print(f"lineup_weighting_status: {result['lineup_weighting_status']}")
        print(f"lineup_data_quality: {result['lineup_data_quality']}")
        print(f"known_rating_count: {result['known_rating_count']}")
        print(f"replacement_rating_count: {result['replacement_rating_count']}")
        print(f"missing_rating_count: {result['missing_rating_count']}")
        print(f"rating_coverage: {result['rating_coverage']}%")
        print(f"real_rating_coverage: {result['real_rating_coverage']}%")
        print(f"source_confidence_weighted_score: {result['source_confidence_weighted_score']}%")
        print("")
        _print_team(result["team_a"])
        print("")
        _print_team(result["team_b"])
        print("")
        print("Limitaciones:")
        for limitation in result["limitations"]:
            print(f"- {limitation}")
        if not result["limitations"]:
            print("- none")
        print("")
        print("-" * 72)
        print("")


if __name__ == "__main__":
    main()
