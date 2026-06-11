import argparse

from full_group_stage_picks_runner import run_full_group_stage_picks


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run World Cup 2026 full group-stage picks.")
    parser.add_argument("--mode", choices=("quick", "standard", "final"), default="standard")
    parser.add_argument("--write", action="store_true", help="Write JSON/CSV reports.")
    parser.add_argument("--allow-partial", action="store_true", help="Allow confirmed partial fixture simulation.")
    parser.add_argument("--force", action="store_true", help="Allow report rewrite only; never bypasses guard.")
    return parser


def main() -> None:
    args = _parser().parse_args()
    result = run_full_group_stage_picks(
        mode=args.mode,
        write_report=args.write,
        allow_partial=args.allow_partial,
        force=args.force,
    )

    print("NOVA FULL GROUP STAGE PICKS RUNNER")
    print(f"- mode: {result['mode']}")
    print(f"- guard status: {result['guard_status']}")
    print(f"- runner status: {result['runner_status']}")
    print(f"- total slots: {result['total_group_stage_slots']}")
    print(f"- confirmed matches: {result['confirmed_matches']}")
    print(f"- pending matches: {result['pending_matches']}")
    print(f"- simulated matches: {result['simulated_matches']}")
    print(f"- blocked matches: {result['blocked_matches']}")
    print(f"- ready for full simulation: {str(result['ready_for_full_group_simulation']).lower()}")
    print(f"- ready for partial simulation: {str(result['ready_for_partial_simulation']).lower()}")
    print("Block reasons:")
    if result["block_reasons"]:
        for reason in result["block_reasons"]:
            print(f"- {reason}")
    else:
        print("- none")
    print("Warnings:")
    if result["warnings"]:
        for warning in result["warnings"]:
            print(f"- {warning}")
    else:
        print("- none")
    if result["runner_status"] == "blocked":
        print(
            "Full Group Stage Picks Runner bloqueado: el fixture actual es "
            "estructural/placeholder y no contiene partidos oficiales confirmados."
        )
    else:
        print("Resumen por grupo:")
        for group, summary in result["summary"]["groups"].items():
            if summary["picks_generated"]:
                print(f"- {group}: {summary['picks_generated']} picks")
        print(f"- total picks generados: {result['summary']['picks_generated']}")
        print(f"- historial actualizado: {result['summary']['prediction_history_updated']}")
    print("Report paths:")
    for key, value in result["report_paths"].items():
        print(f"- {key}: {value}")
    print("Next steps:")
    print("- Import verified official fixture snapshot in dry_run first.")
    print("- Wait for Fixture Guard to return guard_status=ready.")
    print("- Run with --write only after the fixture is verified.")


if __name__ == "__main__":
    main()
