"""
Scoring rules for the Quiniela Mundialista layer.

The game is defined over 90 minutes, including the two regular halves.
Extra time and penalties are intentionally outside this layer.
"""

MAX_POINTS_PER_GAME = 9
QUINIGOL_POINTS = 2
RESULT_POINTS = 3
WINNER_AND_ONE_TEAM_GOALS_POINTS = 5
EXACT_SCORE_POINTS = 7


def parse_score(score: str | tuple[int, int]) -> tuple[int, int]:
    """Normalize a score expressed as '2-1' or (2, 1)."""
    if isinstance(score, tuple):
        if len(score) != 2:
            raise ValueError("El marcador debe tener dos valores.")
        return int(score[0]), int(score[1])

    if not isinstance(score, str) or "-" not in score:
        raise ValueError("El marcador debe venir como 'goles_a-goles_b'.")

    left, right = score.split("-", maxsplit=1)
    return int(left.strip()), int(right.strip())


def result_key(goals_a: int, goals_b: int) -> str:
    if goals_a > goals_b:
        return "team_a_win"
    if goals_a < goals_b:
        return "team_b_win"
    return "draw"


def result_label(score: str | tuple[int, int], team_a: str, team_b: str) -> str:
    goals_a, goals_b = parse_score(score)
    key = result_key(goals_a, goals_b)
    if key == "team_a_win":
        return f"{team_a} gana"
    if key == "team_b_win":
        return f"{team_b} gana"
    return "Empate"


def score_match_prediction(
    predicted_score: str | tuple[int, int],
    actual_score: str | tuple[int, int],
) -> int:
    """
    Score the match prediction without Quinigol.

    Rules:
    - 7 points: exact result and both teams' goals.
    - 5 points: correct non-draw winner and one team's goals.
    - 3 points: correct result only.
    - 0 points: incorrect result.
    """
    pred_a, pred_b = parse_score(predicted_score)
    real_a, real_b = parse_score(actual_score)

    predicted_result = result_key(pred_a, pred_b)
    actual_result = result_key(real_a, real_b)

    if (pred_a, pred_b) == (real_a, real_b):
        return EXACT_SCORE_POINTS

    if predicted_result != actual_result:
        return 0

    if actual_result != "draw" and (pred_a == real_a or pred_b == real_b):
        return WINNER_AND_ONE_TEAM_GOALS_POINTS

    return RESULT_POINTS


def score_quinigol_prediction(predicted: str, actual: str) -> int:
    """Score Quinigol as a binary hit: team/no hay matches the real event."""
    if predicted.strip().lower() == actual.strip().lower():
        return QUINIGOL_POINTS
    return 0


def score_game(
    predicted_score: str | tuple[int, int],
    actual_score: str | tuple[int, int],
    predicted_quinigol: str | None = None,
    actual_quinigol: str | None = None,
) -> dict:
    """Score a complete game and cap it at 9 total points."""
    match_points = score_match_prediction(predicted_score, actual_score)
    quinigol_points = 0

    if predicted_quinigol is not None and actual_quinigol is not None:
        quinigol_points = score_quinigol_prediction(predicted_quinigol, actual_quinigol)

    total_points = min(MAX_POINTS_PER_GAME, match_points + quinigol_points)

    return {
        "match_points": match_points,
        "quinigol_points": quinigol_points,
        "total_points": total_points,
        "max_points_per_game": MAX_POINTS_PER_GAME,
        "game_definition": "90 minutos, incluye dos tiempos regulares.",
    }
