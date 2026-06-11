from __future__ import annotations

from inter_phase_update_engine import run_inter_phase_update


def main() -> None:
    report = run_inter_phase_update(
        from_phase="group_stage",
        to_phase="round_of_32",
        dry_run=True,
        write_report=True,
    )
    print("NOVA INTER PHASE UPDATE DEMO")
    print(f"- from phase: {report['from_phase']}")
    print(f"- to phase: {report['to_phase']}")
    print(f"- dry run: {str(report['dry_run']).lower()}")
    print(f"- update status: {report['update_status']}")
    print(f"- freeze status: {report['freeze_summary']['freeze_status']}")
    print(f"- results status: {report['results_summary']['validation_status']}")
    print(f"- standings status: {report['standings_summary']['standings_status']}")
    print(f"- transition status: {report['transition_guard']['transition_status']}")
    print(f"- recalibration applied: {str(report['recalibration_applied']).lower()}")
    print(f"- baseline modified: {str(report['baseline_modified']).lower()}")
    print(f"- prediction history modified: {str(report['prediction_history_modified']).lower()}")
    print("Warnings:")
    if report["warnings"]:
        for warning in report["warnings"]:
            print(f"- {warning}")
    else:
        print("- none")
    print("Next steps:")
    for step in report["next_steps"]:
        print(f"- {step}")


if __name__ == "__main__":
    main()
