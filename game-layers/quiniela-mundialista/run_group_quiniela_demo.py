import json
from pathlib import Path

from quiniela_engine import (
    ROOT,
    format_quiniela_recommendation,
    load_teams,
    recommend_match,
)
from simulation_config import resolve_simulation_mode


STRATEGIES = ("conservador", "balanceado", "agresivo")

# Seleccion corta y documentada: no genera todo el calendario de grupos.
# Toma partidos existentes dentro de data/worldcup_2026_real_groups.json.
SELECTED_GROUP_MATCHES = [
    ("A", "Mexico", "South Africa"),
    ("C", "Brazil", "Morocco"),
    ("J", "Argentina", "Austria"),
    ("L", "England", "Croatia"),
]


def load_groups(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_selected_matches(groups: dict) -> None:
    for group_name, team_a, team_b in SELECTED_GROUP_MATCHES:
        group_teams = groups.get(group_name, [])
        if team_a not in group_teams or team_b not in group_teams:
            raise ValueError(
                f"Partido no valido para grupo {group_name}: {team_a} vs {team_b}"
            )


def main() -> None:
    teams_path = ROOT / "data" / "worldcup_2026_real_teams_baseline_v1.json"
    groups_path = ROOT / "data" / "worldcup_2026_real_groups.json"
    teams = load_teams(teams_path)
    groups = load_groups(groups_path)
    validate_selected_matches(groups)
    simulation_mode, simulations = resolve_simulation_mode("quick")

    print("NOVA QUINIELA MUNDIALISTA - DEMO GRUPOS 2026")
    print("Seleccion parcial de partidos reales por grupo.")
    print("No genera todavia la fase de grupos completa.")
    print("")

    seed = 2026
    for group_name, team_a, team_b in SELECTED_GROUP_MATCHES:
        print(f"GRUPO {group_name}: {team_a} vs {team_b}")
        print("=" * 72)
        for strategy in STRATEGIES:
            recommendation = recommend_match(
                team_a,
                team_b,
                teams,
                strategy=strategy,
                simulations=simulations,
                simulation_mode=simulation_mode,
                seed=seed,
            )
            print(format_quiniela_recommendation(recommendation))
            print("")
            print("-" * 72)
            print("")
            seed += 1

    print(f"Datos de equipos: {Path(teams_path).relative_to(ROOT)}")
    print(f"Datos de grupos: {Path(groups_path).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
