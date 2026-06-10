from pathlib import Path

from backtesting_engine import build_friendly_backtest_demo, load_backtesting_manifest
from worldcup_2022_dataset_loader import (
    PREMATCH_PATH as WC2022_PREMATCH_PATH,
    PROFILES_PATH as WC2022_PROFILES_PATH,
    QUINIGOL_TIMING_REPORT_PATH as WC2022_QUINIGOL_TIMING_REPORT_PATH,
    REPORT_PATH as WC2022_REPORT_PATH,
    RESULTS_PATH as WC2022_RESULTS_PATH,
    load_worldcup_2022_datasets,
)


LAYER_ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = LAYER_ROOT / "data" / "backtesting_manifest.json"
HISTORY_PATH = LAYER_ROOT / "data" / "prediction_history.json"
RESULTS_PATH = LAYER_ROOT / "data" / "friendly_test_results.json"


def main() -> None:
    manifest = load_backtesting_manifest(MANIFEST_PATH)
    demo = build_friendly_backtest_demo(HISTORY_PATH, RESULTS_PATH)
    worldcup_2022 = load_worldcup_2022_datasets()
    audit = worldcup_2022.get("audit", {})
    report = {}
    if WC2022_REPORT_PATH.exists():
        report = __import__("json").loads(WC2022_REPORT_PATH.read_text(encoding="utf-8"))
    quinigol_timing_report = {}
    if WC2022_QUINIGOL_TIMING_REPORT_PATH.exists():
        quinigol_timing_report = __import__("json").loads(
            WC2022_QUINIGOL_TIMING_REPORT_PATH.read_text(encoding="utf-8")
        )
    datasets = manifest.get("datasets", [])
    ready = [item for item in datasets if item.get("integration_status") == "foundation_ready"]
    pending = [item for item in datasets if item.get("integration_status") != "foundation_ready"]

    print("NOVA BACKTESTING FOUNDATION DEMO")
    print(f"- datasets listos: {', '.join(item['dataset'] for item in ready) or 'none'}")
    print(f"- datasets pendientes: {', '.join(item['dataset'] for item in pending) or 'none'}")
    print(
        "- leakage risks: "
        + "; ".join(f"{item['dataset']}={item['leakage_risk']}" for item in datasets)
    )
    print(f"- comparaciones demo amistosos: {demo['comparison_count']}")
    for comparison in demo["comparisons"]:
        print(
            f"- {comparison['match']}: pred {comparison['predicted_score']} real {comparison['real_score']} "
            f"| ganador {'si' if comparison['result_hit'] else 'no'} "
            f"| exacto {'si' if comparison['exact_score_hit'] else 'no'}"
        )
    print("World Cup 2022 Blind Test status")
    print(f"- prematch dataset: {'OK' if WC2022_PREMATCH_PATH.exists() else 'missing'}")
    print(f"- results dataset: {'OK' if WC2022_RESULTS_PATH.exists() else 'missing'}")
    print(f"- prematch profiles: {'OK' if WC2022_PROFILES_PATH.exists() else 'missing'}")
    print(f"- leakage guard status: {audit.get('audit_status', 'pending')}")
    print(f"- prematch dataset count: {worldcup_2022['prematch_count']}")
    print(f"- results dataset count: {worldcup_2022['results_count']}")
    print(f"- profiles count: {worldcup_2022.get('profiles_count', 0)}")
    print(f"- profiles using neutral defaults: {worldcup_2022.get('profiles_using_neutral_defaults', 0)}")
    print(f"- report status: {report.get('engine_status', 'missing')}")
    print(f"- matches evaluated: {report.get('matches_evaluated', 0)}")
    print(
        "- matches evaluated with neutral defaults: "
        f"{report.get('matches_evaluable_with_neutral_defaults', 0)}"
    )
    print(
        "- not valid for model accuracy claims: "
        f"{str(report.get('not_valid_for_model_accuracy_claims', True)).lower()}"
    )
    print(
        "- Quinigol timing sample: "
        f"{quinigol_timing_report.get('matches_with_first_goal_data', 0)}"
    )
    print(
        "- Quinigol timing recommendation: "
        f"{quinigol_timing_report.get('recommendation', 'needs_more_sample')}"
    )
    print("- next action: verify real 2022 prematch profiles before any recalibration")
    print("- siguiente paso recomendado: ampliar fuentes 2022 verificadas; no usar baseline 2026")


if __name__ == "__main__":
    main()
