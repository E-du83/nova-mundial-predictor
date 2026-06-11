from __future__ import annotations


REQUIRED_FIELDS = ("group", "team", "points", "goal_difference", "goals_for")


def _missing_required(row: dict) -> list[str]:
    return [field for field in REQUIRED_FIELDS if field not in row or row[field] in (None, "pending_real_data")]


def _sort_key(row: dict) -> tuple:
    fair_play = row.get("fair_play_points")
    fifa_ranking = row.get("fifa_ranking")
    fair_play_key = -fair_play if isinstance(fair_play, (int, float)) else -1_000_000
    ranking_key = -fifa_ranking if isinstance(fifa_ranking, int) else -1_000_000
    return (
        row["points"],
        row["goal_difference"],
        row["goals_for"],
        fair_play_key,
        ranking_key,
    )


def _comparable_key(row: dict) -> tuple:
    return (
        row["points"],
        row["goal_difference"],
        row["goals_for"],
        row.get("fair_play_points"),
        row.get("fifa_ranking"),
    )


def _unresolved_boundary_tiebreaks(ordered: list[dict], cutoff: int) -> list[dict]:
    if len(ordered) <= cutoff:
        return []
    boundary = ordered[cutoff - 1]
    next_row = ordered[cutoff]
    if _comparable_key(boundary) != _comparable_key(next_row):
        return []
    tied = [
        row
        for row in ordered
        if _comparable_key(row) == _comparable_key(boundary)
    ]
    return [
        {
            "status": "unresolved_tiebreak_pending_official_rule",
            "affected_cutoff": cutoff,
            "teams": [row["team"] for row in tied],
            "groups": [row["group"] for row in tied],
            "reason": "Tie at qualification cutoff cannot be resolved with available criteria.",
        }
    ]


def rank_third_placed_teams(third_place_table: list[dict]) -> dict:
    if not third_place_table:
        return {
            "selector_status": "blocked",
            "qualified_third_placed": [],
            "blocked_reason": ["third_place_table missing"],
            "warnings": ["Final group standings are required before selecting best third-placed teams."],
            "unresolved_tiebreaks": [],
        }
    blocked_reason = []
    for index, row in enumerate(third_place_table, start=1):
        missing = _missing_required(row)
        if missing:
            blocked_reason.append(f"row {index} missing required fields: {', '.join(missing)}")
    if blocked_reason:
        return {
            "selector_status": "blocked",
            "qualified_third_placed": [],
            "blocked_reason": blocked_reason,
            "warnings": ["Cannot rank third-placed teams with incomplete points/goals data."],
            "unresolved_tiebreaks": [],
        }
    if len(third_place_table) != 12:
        blocked_reason.append(f"expected 12 third-place candidates, found {len(third_place_table)}")
    ordered = sorted(third_place_table, key=_sort_key, reverse=True)
    unresolved = _unresolved_boundary_tiebreaks(ordered, 8)
    if unresolved:
        return {
            "selector_status": "partial",
            "qualified_third_placed": [],
            "ranked_third_placed": ordered,
            "blocked_reason": ["unresolved_tiebreak_pending_official_rule"],
            "warnings": [
                "Do not select best third-placed teams until official tie-break rule resolves the cutoff."
            ],
            "unresolved_tiebreaks": unresolved,
        }
    if blocked_reason:
        return {
            "selector_status": "blocked",
            "qualified_third_placed": [],
            "ranked_third_placed": ordered,
            "blocked_reason": blocked_reason,
            "warnings": ["Third-place candidate count is not valid for World Cup 2026."],
            "unresolved_tiebreaks": [],
        }
    return {
        "selector_status": "ready",
        "qualified_third_placed": ordered[:8],
        "ranked_third_placed": ordered,
        "blocked_reason": [],
        "warnings": [
            "Synthetic or projected standings are not official bracket inputs.",
            "Official competition regulations must still verify final tie-break handling.",
        ],
        "unresolved_tiebreaks": [],
    }
