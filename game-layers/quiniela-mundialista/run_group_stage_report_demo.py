from pathlib import Path

from group_stage_runner import run_group_stage
from report_builder import build_prediction_report, save_prediction_report
from worldcup_2026_fixture_loader import load_worldcup_2026_fixture


LAYER_ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = LAYER_ROOT / "data" / "group_stage_prediction_report.json"


def main() -> None:
    result = run_group_stage(mode="quick")
    fixture = load_worldcup_2026_fixture()
    report = build_prediction_report(
        result["matches"],
        metadata={
            "scope": "group_stage",
            "simulation_mode": result["simulation_mode"],
            "simulations": result["simulations"],
            "fixture_type": result["fixture_type"],
            "fixture_status": result["fixture_status"],
            "fixture_warning": result["fixture_warning"],
        },
    )
    save_prediction_report(report, OUTPUT_PATH)

    print("NOVA GROUP STAGE REPORT DEMO")
    print(f"- groups loaded: {fixture['groups_loaded']}")
    print(f"- slots loaded: {result['total_slots']}")
    print(f"- confirmed matches: {result['confirmed_matches']}")
    print(f"- pending matches: {result['pending_matches']}")
    print(f"- simulable matches: {result['simulable_matches']}")
    print(f"- fixture type: {result['fixture_type']}")
    print(f"- fixture status: {result['fixture_status']}")
    print(f"- warning: {result['fixture_warning']}")
    if result["simulable_matches"]:
        first = next(item for item in result["matches"] if item["simulation_status"] == "simulated")
        print(f"- ejemplo: {first['match']} | pick {first['pick_principal']} | marcador {first['marcador']}")
    else:
        print("- placeholder: sistema listo; espera sorteo/fixture oficial antes de simular partidos reales")
    print(f"- reporte JSON: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
