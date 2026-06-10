from worldcup_2022_blind_test_engine import build_worldcup_2022_blind_test_report
from worldcup_2022_dataset_loader import QUINIGOL_TIMING_REPORT_PATH


def main() -> None:
    report = build_worldcup_2022_blind_test_report(write_report=True)
    timing = report["quinigol_timing_analysis"]

    print("NOVA QUINIGOL TIMING CALIBRATION")
    print(f"- total matches: {timing['total_matches']}")
    print(f"- matches with first goal data: {timing['matches_with_first_goal_data']}")
    print(f"- team hit rate: {timing['quinigol_team_hit_rate']}")
    print(f"- average minute error: {timing['average_minute_error']}")
    print(f"- median minute error: {timing['median_minute_error']}")
    print(f"- early bias count: {timing['early_bias_count']}")
    print(f"- late bias count: {timing['late_bias_count']}")
    print(f"- range hit rate: {timing['range_hit_rate']}")
    print(f"- recommendation: {timing['recommendation']}")
    print("- warning: no automatic recalibration")
    if timing["total_matches"] < 30:
        print("- Sample size too small; do not recalibrate.")
    print(f"- reporte JSON: {QUINIGOL_TIMING_REPORT_PATH}")


if __name__ == "__main__":
    main()
