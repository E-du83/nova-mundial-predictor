from pathlib import Path

from worldcup_2022_blind_test_engine import build_worldcup_2022_blind_test_report


def _yes_no(value: bool) -> str:
    return "true" if value else "false"


def main() -> None:
    report = build_worldcup_2022_blind_test_report(write_report=True)
    structural = report["structural_readiness_metrics"]
    leakage = report["leakage_audit_summary"]
    timing = report["quinigol_timing_analysis"]
    report_path = (
        Path(__file__).resolve().parent
        / "historical_blind_tests"
        / "worldcup_2022"
        / "worldcup_2022_blind_test_report.json"
    )

    print("NOVA WORLD CUP 2022 HISTORICAL BLIND TEST")
    print(f"- modo: {report['test_mode']}")
    print(f"- generated_after_event: {_yes_no(report['generated_after_event'])}")
    print(f"- prematch dataset status: {structural['prematch_count']} matches")
    print(f"- results dataset status: {structural['results_count']} results")
    print(f"- profile dataset status: {report['profiles_count']} profiles")
    print(f"- profile audit status: {report.get('profile_audit_summary', {}).get('audit_status', 'not_available')}")
    print(f"- profiles using neutral defaults: {report['profiles_using_neutral_defaults']}")
    print(f"- leakage audit status: {leakage['audit_status']}")
    print(f"- cleared_for_blind_test: {_yes_no(bool(leakage['cleared_for_blind_test']))}")
    print(f"- partidos cargados: {report['total_matches_in_prematch']}")
    print(f"- partidos evaluables: {structural['structural_ready_count']}")
    print(f"- partidos bloqueados: {report['matches_blocked_by_leakage']}")
    print(f"- partidos con perfil historico insuficiente: {report['matches_missing_historical_profiles']}")
    print(f"- matches evaluated: {report['matches_evaluated']}")
    print(f"- matches evaluated with neutral defaults: {report['matches_evaluable_with_neutral_defaults']}")
    print(f"- not valid for model accuracy claims: {_yes_no(report['not_valid_for_model_accuracy_claims'])}")
    print(f"- true prediction metrics: {report['true_prediction_metrics']['status']}")
    print(f"- behavioral metrics: {report['behavioral_backtest_metrics']['status']}")
    print("Quinigol timing analysis:")
    print(f"- total matches: {timing.get('total_matches', 'not_available')}")
    print(f"- total matches with first goal data: {timing.get('matches_with_first_goal_data', timing.get('total_matches_with_first_goal_data', 0))}")
    print(f"- team hit rate: {timing.get('quinigol_team_hit_rate')}")
    print(f"- average minute error: {timing['average_minute_error']}")
    print(f"- early bias count: {timing['early_bias_count']}")
    print(f"- late bias count: {timing['late_bias_count']}")
    print(f"- range hit rate: {timing.get('range_hit_rate')}")
    print(f"- recommendation: {timing['recommendation']}")
    print("Warnings:")
    for warning in report["warnings"]:
        print(f"- {warning}")
    print("Next steps:")
    for step in report["next_steps"]:
        print(f"- {step}")
    print(f"- reporte JSON: {report_path}")


if __name__ == "__main__":
    main()
