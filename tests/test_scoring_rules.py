from pathlib import Path
import sys


LAYER_ROOT = Path(__file__).resolve().parents[1] / "game-layers" / "quiniela-mundialista"
if str(LAYER_ROOT) not in sys.path:
    sys.path.insert(0, str(LAYER_ROOT))

from scoring_rules import (  # noqa: E402
    EXACT_SCORE_POINTS,
    MAX_POINTS_PER_GAME,
    QUINIGOL_POINTS,
    WINNER_AND_ONE_TEAM_GOALS_POINTS,
    parse_score,
    score_game,
    score_match_prediction,
)


def test_exact_score_scores_7_points() -> None:
    assert score_match_prediction("2-1", "2-1") == EXACT_SCORE_POINTS


def test_correct_winner_and_one_team_goals_scores_5_points() -> None:
    assert score_match_prediction("2-0", "2-1") == WINNER_AND_ONE_TEAM_GOALS_POINTS


def test_correct_result_only_scores_3_points() -> None:
    assert score_match_prediction("3-1", "2-0") == 3


def test_wrong_result_scores_0_points() -> None:
    assert score_match_prediction("1-0", "0-1") == 0


def test_exact_draw_scores_7_points() -> None:
    assert score_match_prediction("1-1", "1-1") == EXACT_SCORE_POINTS


def test_correct_quinigol_adds_2_points() -> None:
    result = score_game("1-0", "1-0", "Spain", "Spain")
    assert result["quinigol_points"] == QUINIGOL_POINTS


def test_wrong_quinigol_adds_no_points() -> None:
    result = score_game("1-0", "1-0", "Spain", "France")
    assert result["quinigol_points"] == 0


def test_total_points_are_capped_at_9() -> None:
    result = score_game("2-1", "2-1", "Spain", "Spain")
    assert result["total_points"] == MAX_POINTS_PER_GAME


def test_zero_zero_score() -> None:
    assert score_match_prediction("0-0", "0-0") == EXACT_SCORE_POINTS


def test_parse_score_from_string() -> None:
    assert parse_score(" 2 - 1 ") == (2, 1)


def test_parse_score_from_tuple() -> None:
    assert parse_score((2, 1)) == (2, 1)


def run_all() -> None:
    tests = [
        value
        for name, value in globals().items()
        if name.startswith("test_") and callable(value)
    ]
    for test in tests:
        test()
    print(f"OK - {len(tests)} scoring tests passed")


if __name__ == "__main__":
    run_all()
