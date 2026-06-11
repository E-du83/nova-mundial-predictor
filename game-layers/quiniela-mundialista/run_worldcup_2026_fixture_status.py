from worldcup_2026_fixture_loader import load_worldcup_2026_fixture


def main() -> None:
    data = load_worldcup_2026_fixture()
    structure = data["group_structure"]
    validation = data["validation_report"]

    print("NOVA WORLD CUP 2026 FIXTURE STATUS")
    print(f"- tournament: {structure.get('tournament', 'FIFA World Cup 2026')}")
    print(f"- tournament structure: {structure.get('teams_total', 48)} teams / {structure.get('groups_total', 12)} groups")
    print(f"- groups: {data['groups_loaded']}")
    print(f"- slots: {data['slots_loaded']}")
    print(f"- total group stage matches: {structure.get('total_group_stage_matches', 72)}")
    print(f"- total tournament matches: {structure.get('total_tournament_matches', 104)}")
    print(f"- confirmed matches: {data['confirmed_matches']}")
    print(f"- pending matches: {data['pending_matches']}")
    print(f"- fixture type: {data['fixture_type']}")
    print(f"- fixture status: {data['official_status']}")
    print(f"- validation status: {data['validation_status']}")
    print(f"- fixture guard status: {data['fixture_guard_status']}")
    print(f"- ready for partial simulation: {str(data['ready_for_partial_simulation']).lower()}")
    print(f"- groups detected: {validation.get('groups_detected', 0)}")
    print(f"- slots detected: {validation.get('slots_detected', 0)}")
    print(f"- ready for full group simulation: {str(data['ready_for_full_group_simulation']).lower()}")
    print(f"- import report status: {data['import_report'].get('import_status', 'missing')}")
    print("- guard report path: game-layers/quiniela-mundialista/data/worldcup_2026_fixture_guard_report.json")
    print("Warnings:")
    for warning in data["warnings"]:
        print(f"- {warning}")
    print("Next steps:")
    print("- Import verified official fixture snapshot in dry_run first.")
    print("- Replace fixture_assignment fields while keeping stable slot IDs.")
    print("- Keep kickoff times in UTC and venues pending until verified.")


if __name__ == "__main__":
    main()
