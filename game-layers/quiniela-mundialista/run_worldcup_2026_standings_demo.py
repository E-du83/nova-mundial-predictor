from __future__ import annotations

from worldcup_2026_results_loader import ensure_results_template
from worldcup_2026_standings_engine import build_group_standings


def _synthetic_results() -> dict:
    matches = [
        ("SYN-A-01", "Synthetic A1", "Synthetic A2", 2, 0),
        ("SYN-A-02", "Synthetic A3", "Synthetic A4", 1, 1),
        ("SYN-A-03", "Synthetic A1", "Synthetic A3", 1, 0),
        ("SYN-A-04", "Synthetic A2", "Synthetic A4", 0, 0),
        ("SYN-A-05", "Synthetic A1", "Synthetic A4", 3, 1),
        ("SYN-A-06", "Synthetic A2", "Synthetic A3", 2, 1),
    ]
    return {
        "dataset_name": "synthetic_group_results",
        "source_status": "synthetic_test_data",
        "matches": [
            {
                "match_id": match_id,
                "phase": "group_stage",
                "group": "Synthetic A",
                "team_a": team_a,
                "team_b": team_b,
                "goals_a_90": goals_a,
                "goals_b_90": goals_b,
                "winner_90": "synthetic",
                "source_status": "synthetic_test_data",
                "captured_at": "2026-06-10T00:00:00Z",
                "review_status": "final",
            }
            for match_id, team_a, team_b, goals_a, goals_b in matches
        ],
    }


def main() -> None:
    template = ensure_results_template()
    current = build_group_standings(template, write=False)
    synthetic_fixture = {"fixture_type": "synthetic_fixture", "structural_placeholder": False}
    synthetic = build_group_standings(_synthetic_results(), fixture=synthetic_fixture, write=False)
    validation_ok = (
        current["standings_status"] == "blocked_placeholder_fixture"
        and synthetic["standings_status"] == "partial"
        and synthetic["groups_calculated"] == 1
    )
    print("NOVA WORLD CUP 2026 STANDINGS DEMO")
    print("Escenario actual:")
    print(f"- standings_status: {current['standings_status']}")
    print(f"- groups calculated: {current['groups_calculated']}")
    print("Escenario sintetico:")
    print(f"- standings_status: {synthetic['standings_status']}")
    print(f"- groups calculated: {synthetic['groups_calculated']}")
    print("- validation: " + ("OK" if validation_ok else "partial"))
    print("- synthetic saved to real data: no")


if __name__ == "__main__":
    main()
