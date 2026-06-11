from __future__ import annotations

from pathlib import Path

from phase_freeze_engine import freeze_phase_predictions


LAYER_ROOT = Path(__file__).resolve().parent
DATA_ROOT = LAYER_ROOT / "data"


def main() -> None:
    summary = freeze_phase_predictions(
        "group_stage",
        str(DATA_ROOT / "prediction_history.json"),
        str(DATA_ROOT / "worldcup_2026_phase_freeze_log.json"),
        dry_run=True,
    )
    print("NOVA PHASE FREEZE DEMO")
    print(f"- phase: {summary['phase']}")
    print(f"- dry run: {str(summary['dry_run']).lower()}")
    print(f"- predictions found: {summary['predictions_found']}")
    print(f"- predictions frozen: {summary['predictions_frozen']}")
    print(f"- placeholders ignored: {summary['placeholders_ignored']}")
    print(f"- freeze status: {summary['freeze_status']}")
    print("Warnings:")
    if summary["warnings"]:
        for warning in summary["warnings"]:
            print(f"- {warning}")
    else:
        print("- none")


if __name__ == "__main__":
    main()
