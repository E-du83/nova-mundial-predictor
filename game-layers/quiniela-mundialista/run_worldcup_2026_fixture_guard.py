from worldcup_2026_fixture_guard import evaluate_group_stage_simulation_readiness


def main() -> None:
    report = evaluate_group_stage_simulation_readiness()
    print("NOVA WORLD CUP 2026 FIXTURE GUARD")
    print(f"- fixture type: {report['fixture_type']}")
    print(f"- official status: {report['official_status']}")
    print(f"- confirmed matches: {report['confirmed_matches']}")
    print(f"- pending matches: {report['pending_matches']}")
    print(f"- ready for full group simulation: {str(report['ready_for_full_group_simulation']).lower()}")
    print(f"- ready for partial simulation: {str(report['ready_for_partial_simulation']).lower()}")
    print(f"- guard status: {report['guard_status']}")
    print("Block reasons:")
    for reason in report["block_reason"]:
        print(f"- {reason}")
    print("Warnings:")
    for warning in report["warnings"]:
        print(f"- {warning}")
    print("Baseline missing teams:")
    if report["baseline_team_missing"]:
        for team in report["baseline_team_missing"]:
            print(f"- {team}")
    else:
        print("- none")
    print("Next steps:")
    print("- Import a verified official fixture snapshot in dry_run first.")
    print("- Keep full group picks blocked until guard_status=ready.")


if __name__ == "__main__":
    main()
