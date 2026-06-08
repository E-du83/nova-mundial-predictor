from pathlib import Path

from group_stage_runner import run_group_stage
from report_builder import build_prediction_report, save_prediction_report


LAYER_ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = LAYER_ROOT / "data" / "group_stage_prediction_report.json"


def main() -> None:
    result = run_group_stage(mode="quick")
    report = build_prediction_report(
        result["matches"],
        metadata={
            "scope": "group_stage",
            "simulation_mode": result["simulation_mode"],
            "simulations": result["simulations"],
            "fixture_warning": result["fixture_warning"],
        },
    )
    save_prediction_report(report, OUTPUT_PATH)

    print("NOVA GROUP STAGE REPORT DEMO")
    print(f"- partidos disponibles: {result['total_matches']}")
    print(f"- partidos simulables: {result['simulable_matches']}")
    print(f"- partidos pendientes por datos: {result['pending_matches']}")
    print(f"- advertencia fixture: {result['fixture_warning']}")
    if result["simulable_matches"]:
        first = next(item for item in result["matches"] if item["simulation_status"] == "simulated")
        print(f"- ejemplo: {first['match']} | pick {first['pick_principal']} | marcador {first['marcador']}")
    else:
        print("- ejemplo: no hay partidos simulables hasta cargar fixture oficial completo")
    print(f"- reporte JSON: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
