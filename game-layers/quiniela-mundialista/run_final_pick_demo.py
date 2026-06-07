from final_pick_engine import (
    build_final_pick,
    format_final_pick,
    load_default_final_pick_inputs,
)


DEMO_MATCHES = [
    ("Mexico", "South Africa"),
    ("Brazil", "Morocco"),
    ("Argentina", "Austria"),
    ("England", "Croatia"),
]


def main() -> None:
    teams, fixtures_data, climate_profiles = load_default_final_pick_inputs()

    print("NOVA QUINIELA MUNDIALISTA v1.2 - FINAL PICK DEMO")
    print("Salida: un pick final unico por partido.")
    print("Contexto: pre_tournament_context hasta integrar calendario, sedes y clima real.")
    print("")

    for index, (team_a, team_b) in enumerate(DEMO_MATCHES):
        final_pick = build_final_pick(
            team_a,
            team_b,
            teams,
            fixtures_data=fixtures_data,
            climate_profiles=climate_profiles,
            simulations=25_000,
            seed=2026 + index,
        )
        print(format_final_pick(final_pick))
        print("")
        print("-" * 72)
        print("")


if __name__ == "__main__":
    main()
