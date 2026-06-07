from pathlib import Path

from manual_snapshot_engine import (
    load_manual_snapshots,
    normalize_manual_snapshot,
    summarize_manual_snapshot,
)
from research_intelligence_engine import (
    build_research_intelligence,
    format_research_lines,
)
from research_weighting_engine import (
    build_research_weighting,
    format_research_weighting_lines,
)


SNAPSHOTS_PATH = Path(__file__).resolve().parent / "data" / "manual_match_snapshots.json"


def main() -> None:
    snapshots_data = load_manual_snapshots(SNAPSHOTS_PATH)
    print("NOVA RESEARCH SNAPSHOT DEMO")
    print("Datos manuales investigados; no scraping automatico, no APIs pagadas.")
    print(f"Estado archivo: {snapshots_data.get('data_status')}")
    print("")

    for raw_snapshot in snapshots_data.get("snapshots", []):
        snapshot = normalize_manual_snapshot(raw_snapshot)
        summary = summarize_manual_snapshot(snapshot)
        research = build_research_intelligence(
            snapshot=snapshot,
            snapshot_summary=summary,
            base_confidence=50.0,
            base_risk="medio",
        )

        print(f"Partido: {snapshot['match']}")
        print(f"Competencia: {snapshot['competition_type']}")
        print(f"Estado datos: {snapshot['data_status']}")
        print(f"Capturado: {snapshot['captured_at']} | por: {snapshot['captured_by']}")
        for line in format_research_lines(research):
            print(line)
        print("")
        weighting = build_research_weighting(snapshot["team_a"], snapshot["team_b"])
        for line in format_research_weighting_lines(weighting):
            print(line)
        print("")
        print("-" * 72)
        print("")


if __name__ == "__main__":
    main()
