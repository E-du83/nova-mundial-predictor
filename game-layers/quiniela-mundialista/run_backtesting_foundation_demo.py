from pathlib import Path

from backtesting_engine import build_friendly_backtest_demo, load_backtesting_manifest


LAYER_ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = LAYER_ROOT / "data" / "backtesting_manifest.json"
HISTORY_PATH = LAYER_ROOT / "data" / "prediction_history.json"
RESULTS_PATH = LAYER_ROOT / "data" / "friendly_test_results.json"


def main() -> None:
    manifest = load_backtesting_manifest(MANIFEST_PATH)
    demo = build_friendly_backtest_demo(HISTORY_PATH, RESULTS_PATH)
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
    print("- Mundial 2022: no ejecutar todavia; requiere blind test y data leakage guard")
    print("- siguiente paso recomendado: Historical Blind Backtesting v1 with leakage guard")


if __name__ == "__main__":
    main()
