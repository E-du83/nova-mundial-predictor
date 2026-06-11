from __future__ import annotations

from worldcup_2026_bracket_guard import evaluate_bracket_readiness
from worldcup_2026_third_place_selector import rank_third_placed_teams


def _synthetic_third_place_table() -> list[dict]:
    rows = []
    points = [6, 5, 5, 4, 4, 4, 3, 3, 2, 2, 1, 1]
    goal_diff = [4, 3, 2, 2, 1, 0, 1, 0, -1, -2, -3, -4]
    goals_for = [7, 6, 5, 5, 4, 3, 4, 3, 2, 2, 1, 1]
    for index, group in enumerate("ABCDEFGHIJKL"):
        rows.append(
            {
                "group": group,
                "team": f"Synthetic Third {group}",
                "position": 3,
                "points": points[index],
                "goal_difference": goal_diff[index],
                "goals_for": goals_for[index],
                "fair_play_points": 10 - index,
                "fifa_ranking": index + 20,
            }
        )
    return rows


def _unresolved_tie_table() -> list[dict]:
    rows = _synthetic_third_place_table()
    for index in (7, 8):
        rows[index]["points"] = 3
        rows[index]["goal_difference"] = 0
        rows[index]["goals_for"] = 3
        rows[index].pop("fair_play_points", None)
        rows[index].pop("fifa_ranking", None)
    return rows


def main() -> None:
    current_selector = rank_third_placed_teams([])
    current_guard = evaluate_bracket_readiness()
    synthetic_selector = rank_third_placed_teams(_synthetic_third_place_table())
    unresolved_selector = rank_third_placed_teams(_unresolved_tie_table())
    validation_ok = (
        current_selector["selector_status"] == "blocked"
        and current_guard["bracket_guard_status"] == "blocked_pending_group_results"
        and len(synthetic_selector["qualified_third_placed"]) == 8
        and unresolved_selector["unresolved_tiebreaks"]
    )

    print("NOVA WORLD CUP 2026 THIRD PLACE DEMO")
    print("")
    print("Escenario actual:")
    print(f"- selector status: {current_selector['selector_status']}")
    print(f"- bracket guard: {current_guard['bracket_guard_status']}")
    print("")
    print("Escenario sintetico:")
    print(f"- qualified third placed count: {len(synthetic_selector['qualified_third_placed'])}")
    print(f"- selector status: {synthetic_selector['selector_status']}")
    print(f"- unresolved tiebreaks: {len(unresolved_selector['unresolved_tiebreaks'])}")
    print("- validation: " + ("OK" if validation_ok else "partial"))
    print("Warnings:")
    for warning in synthetic_selector["warnings"]:
        print(f"- {warning}")


if __name__ == "__main__":
    main()
