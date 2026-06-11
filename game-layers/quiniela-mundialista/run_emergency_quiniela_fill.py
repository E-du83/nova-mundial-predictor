import argparse

from emergency_quiniela_fill_engine import run_emergency_quiniela_fill


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate World Cup 2026 emergency quiniela fill.")
    parser.add_argument("--mode", choices=("quick", "standard", "final"), default="standard")
    parser.add_argument("--write", action="store_true")
    return parser


def main() -> None:
    args = _parser().parse_args()
    report = run_emergency_quiniela_fill(mode=args.mode, write=args.write)
    print("NOVA EMERGENCY QUINIELA FILL")
    print(f"- fixture status: {report['fixture_status']}")
    print(f"- guard status: {report['guard_status']}")
    print(f"- research package status: {report['research_package_status']}")
    print(f"- matches detected: {report['matches_detected']}")
    print(f"- picks generated: {report['picks_generated']}")
    print(f"- blocked matches: {report['blocked_matches']}")
    print(f"- report JSON: {report['report_paths']['json']}")
    print(f"- report CSV: {report['report_paths']['csv']}")
    print(f"- printable MD: {report['report_paths']['printable_md']}")
    print(f"- ready for user quiniela: {str(report['ready_for_user_quiniela']).lower()}")
    print("Warnings:")
    if report["warnings"]:
        for warning in report["warnings"]:
            print(f"- {warning}")
    else:
        print("- none")
    print("Next steps:")
    for item in report["next_steps"]:
        print(f"- {item}")


if __name__ == "__main__":
    main()
