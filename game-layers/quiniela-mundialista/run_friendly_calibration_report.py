from pathlib import Path

from friendly_calibration_engine import build_and_save_calibration_outputs
from prediction_history_engine import normalize_prediction_history_file


LAYER_ROOT = Path(__file__).resolve().parent
RESULTS_PATH = LAYER_ROOT / "data" / "friendly_test_results.json"
HISTORY_PATH = LAYER_ROOT / "data" / "prediction_history.json"
REPORT_PATH = LAYER_ROOT / "data" / "friendly_calibration_report.json"
NOTES_PATH = LAYER_ROOT / "data" / "calibration_notes.json"


def _yes_no(value: bool) -> str:
    return "si" if value else "no"


def _main_error(review: dict) -> str:
    if review["exact_score_hit"]:
        return "Acierto exacto."
    if review["real_result"] in ("draw", "Empate") and not review["result_hit"]:
        return "Subestimo empate."
    if review["btts_real"] and not review["btts_predicted"]:
        return "Subestimo BTTS/gol rival."
    if review["patterns"].get("quinigol_timing_miscalibration"):
        return "Minuto Quinigol fuera del rango probable."
    return "Ganador o marcador parcialmente desviados."


def _pattern_names(patterns: dict) -> list[str]:
    names = []
    labels = {
        "draw_underestimation_pattern": "empate subestimado",
        "late_opponent_goal_pattern": "gol tardio rival / BTTS subestimado",
        "quinigol_timing_miscalibration": "minuto Quinigol demasiado temprano",
        "fragility_warning_validated": "advertencia de fragilidad validada",
        "clean_sheet_risk_warning": "riesgo de porteria a cero",
    }
    for key, label in labels.items():
        if patterns.get(key):
            names.append(label)
    return names


def main() -> None:
    normalize_prediction_history_file(HISTORY_PATH)
    report, notes = build_and_save_calibration_outputs(
        RESULTS_PATH,
        HISTORY_PATH,
        REPORT_PATH,
        NOTES_PATH,
    )
    metrics = report["metrics"]
    patterns = report["patterns"]

    print("NOVA FRIENDLY CALIBRATION REPORT")
    print("")
    print("Partidos revisados:")
    for review in report["matches_reviewed"]:
        print(f"- {review['match']}")
    print("")

    for review in report["matches_reviewed"]:
        print(f"Partido: {review['match']}")
        print(f"- prediccion: {review['predicted_result']} {review['predicted_score']}")
        print(f"- resultado real: {review['real_result']} {review['real_score']}")
        print(f"- acierto ganador: {_yes_no(review['result_hit'])}")
        print(f"- acierto marcador exacto: {_yes_no(review['exact_score_hit'])}")
        print(f"- error principal: {_main_error(review)}")
        print(f"- aprendizaje: {review['learning_note']}")
        detected = _pattern_names(review["patterns"])
        print("- patrones: " + ("; ".join(detected) if detected else "none"))
        print("")

    print("Resumen:")
    print(f"- acierto ganador: {round(metrics['result_hit_rate'] * 100, 2)}%")
    print(f"- acierto marcador exacto: {round(metrics['exact_score_hit_rate'] * 100, 2)}%")
    print(
        "- patrones detectados: "
        + "; ".join(
            f"{key}={value}"
            for key, value in patterns.items()
            if key != "sample_size_warning"
        )
    )
    print("- mejoras recomendadas: " + "; ".join(report["recommended_adjustments"]))
    print("- que NO cambiar todavia: " + "; ".join(report["do_not_change_yet"]))
    print(f"- advertencia muestra: {notes['sample_size_warning']}")
    print(f"- reporte JSON: {REPORT_PATH}")
    print(f"- notas JSON: {NOTES_PATH}")


if __name__ == "__main__":
    main()
