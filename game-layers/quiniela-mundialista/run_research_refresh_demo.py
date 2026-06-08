import argparse
from pathlib import Path

from manual_snapshot_engine import load_manual_snapshots
from match_alarm_engine import build_match_alarm
from research_refresh_engine import build_research_refresh
from result_review_engine import load_friendly_results


LAYER_ROOT = Path(__file__).resolve().parent
SNAPSHOTS_PATH = LAYER_ROOT / "data" / "manual_match_snapshots.json"
RESULTS_PATH = LAYER_ROOT / "data" / "friendly_test_results.json"


def _yes_no(value: bool) -> str:
    return "si" if value else "no"


def run_research_refresh_demo(current_time_utc: str | None = None) -> None:
    snapshots = load_manual_snapshots(SNAPSHOTS_PATH)
    results = load_friendly_results(RESULTS_PATH)
    refresh = build_research_refresh(
        "Netherlands",
        "Uzbekistan",
        snapshots_data=snapshots,
        results_data=results,
    )
    alarm = build_match_alarm(refresh, current_time_utc=current_time_utc)
    can_run = refresh["recommended_action"] in {
        "final_pick_can_run",
        "final_pick_can_run_with_partial_snapshot_warning",
    }

    print("NOVA RESEARCH REFRESH + MATCH ALARM DEMO")
    print("Partido: Netherlands vs Uzbekistan")
    print(f"Kickoff UTC: {refresh['kickoff_time_utc']}")
    print(f"Venue: {refresh['venue']}")
    print(f"Match alarm status: {alarm['alarm_status']}")
    print(f"Match status: {alarm['match_status']}")
    print(f"Minutes to kickoff: {alarm['minutes_to_kickoff']}")
    print(f"Final refresh due: {_yes_no(alarm['final_refresh_due'])}")
    print(f"Research refresh required: {_yes_no(refresh['research_refresh_required'])}")
    print("Missing critical: " + "; ".join(refresh["missing_critical_fields"]))
    print("Missing optional: " + "; ".join(refresh["missing_optional_fields"]))
    print(f"Research priority: {refresh['research_priority']}")
    print(f"Recommended action: {refresh['recommended_action']}")
    print("Snapshot sources: " + "; ".join(refresh["snapshot_sources"]))
    print("Cross checked with: " + "; ".join(refresh["cross_checked_with"]))
    print(f"Final pick can run: {_yes_no(can_run)}")
    if refresh["partial_snapshot_ok_for_final_pick"]:
        print("Warning: final pick can run only as partial researched snapshot; market, lineups and formations remain pending.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audita faltantes de investigacion y alarma de kickoff para Netherlands vs Uzbekistan."
    )
    parser.add_argument(
        "--current-time-utc",
        default=None,
        help="Override opcional ISO UTC para validar ventanas de alarma.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_research_refresh_demo(args.current_time_utc)


if __name__ == "__main__":
    main()
