from pathlib import Path

from manual_snapshot_engine import (
    find_manual_snapshot,
    load_manual_snapshots,
)
from player_rating_engine import (
    PENDING_RATING,
    build_player_index,
    find_player_rating,
    load_player_ratings,
    normalize_player_name,
    source_confidence_weight,
    summarize_player_ratings,
)


LAYER_ROOT = Path(__file__).resolve().parent
DEFAULT_SNAPSHOTS_PATH = LAYER_ROOT / "data" / "manual_match_snapshots.json"
DEFAULT_RATINGS_PATH = LAYER_ROOT / "data" / "player_ratings_seed.json"
LINE_KEYS = ("goalkeeper", "defense", "midfield", "attack")


def _is_pending(value) -> bool:
    return value in (None, "", "pending_manual_input", "pending_real_rating")


def _text_blob(values: list) -> str:
    parts = []
    for value in values:
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif isinstance(value, dict):
            parts.extend(str(item) for item in value.values())
        elif not _is_pending(value):
            parts.append(str(value))
    return " ".join(parts)


def _snapshot_key_players(snapshot: dict, team: str) -> list[str]:
    key_players = snapshot.get("key_players", {})
    if isinstance(key_players, dict):
        value = key_players.get(team, [])
        if isinstance(value, list):
            return value
        if not _is_pending(value):
            return [str(value)]
    return []


def detect_players_for_team(snapshot: dict, ratings_data: dict, team: str) -> list[dict]:
    lineups = snapshot.get("probable_lineups", {})
    team_prefix = "team_a" if snapshot.get("team_a") == team else "team_b"
    key_players = _snapshot_key_players(snapshot, team)
    lineup_text = _text_blob(
        [
            lineups.get(f"{team_prefix}_players"),
            lineups.get(f"{team_prefix}_players_text"),
        ]
    )
    text = _text_blob(
        [
            lineup_text,
            key_players,
        ]
    )
    normalized_text = normalize_player_name(text)
    normalized_lineup_text = normalize_player_name(lineup_text)
    normalized_key_players = {normalize_player_name(player) for player in key_players}
    index = build_player_index(ratings_data)
    detected = []

    for player in index.values():
        if player.get("team") != team:
            continue
        normalized_name = player["normalized_name"]
        tokens = normalized_name.split()
        token_hit = any(token and token in normalized_text.split() for token in tokens)
        if normalized_name and (normalized_name in normalized_text or token_hit):
            appears_in_lineup = normalized_name in normalized_lineup_text
            is_key_player = normalized_name in normalized_key_players
            detected.append(
                find_player_rating(
                    ratings_data,
                    player["player_name"],
                    team,
                    is_worldcup_team=True,
                    appears_in_lineup=appears_in_lineup,
                    is_key_player=is_key_player,
                )
            )

    if not detected and key_players:
        for player_name in key_players:
            detected.append(
                find_player_rating(
                    ratings_data,
                    player_name,
                    team,
                    is_worldcup_team=True,
                    appears_in_lineup=False,
                    is_key_player=True,
                )
            )

    return detected


def _line_strength(players: list[dict]) -> str | float:
    weighted = [
        (
            float(player["overall_rating"]),
            source_confidence_weight(player.get("source_confidence", "low")),
        )
        for player in players
        if isinstance(player.get("overall_rating"), (int, float))
    ]
    if not weighted:
        return PENDING_RATING
    total_weight = sum(weight for _, weight in weighted)
    if total_weight <= 0:
        return PENDING_RATING
    return round(sum(rating * weight for rating, weight in weighted) / total_weight, 2)


def _line_strengths(players: list[dict]) -> dict:
    strengths = {}
    for line in LINE_KEYS:
        line_players = [player for player in players if player.get("position") == line]
        strengths[f"{line}_strength"] = _line_strength(line_players)
    return strengths


def _lineup_adjustments(quality: float, strengths: dict) -> dict:
    if quality <= 0:
        return {
            "attack_xg_adjustment": 0.0,
            "defense_xg_adjustment": 0.0,
            "quinigol_adjustment": 0.0,
            "confidence_adjustment": 0.0,
            "risk_adjustment": "warning_only",
            "adjustment_status": "blocked_by_missing_ratings",
        }

    attack = strengths["attack_strength"]
    defense = strengths["defense_strength"]
    attack_delta = (float(attack) - 75.0) / 100 if isinstance(attack, (int, float)) else 0.0
    defense_delta = (float(defense) - 75.0) / 100 if isinstance(defense, (int, float)) else 0.0
    evidence_multiplier = 0.35 if quality < 60 else 1.0
    status = "conservative_replacement" if quality < 60 else "active"
    return {
        "attack_xg_adjustment": round(max(-0.05, min(0.05, attack_delta * evidence_multiplier)), 3),
        "defense_xg_adjustment": round(max(-0.04, min(0.04, defense_delta * evidence_multiplier)), 3),
        "quinigol_adjustment": round(max(-0.03, min(0.03, attack_delta * evidence_multiplier / 2)), 3),
        "confidence_adjustment": round(max(-1.5, min(1.5, (quality - 35) / 25)), 2),
        "risk_adjustment": "replacement_numeric" if quality < 60 else "numeric",
        "adjustment_status": status,
    }


def build_team_lineup_strength(snapshot: dict, ratings_data: dict, team: str) -> dict:
    players = detect_players_for_team(snapshot, ratings_data, team)
    rating_summary = summarize_player_ratings(players)
    strengths = _line_strengths(players)
    quality = rating_summary["player_data_quality_score"]
    if quality >= 60 and rating_summary["known_rating_count"] >= 4:
        status = "active"
    elif rating_summary["replacement_rating_count"] > 0:
        status = "replacement_estimate"
    else:
        status = "incomplete"
    adjustments = _lineup_adjustments(quality, strengths)
    if status == "incomplete":
        adjustments["confidence_adjustment"] = 0.0
        adjustments["risk_adjustment"] = "partial_lineup_warning"
        adjustments["adjustment_status"] = "partial_numeric"

    return {
        "team": team,
        "players_detected": rating_summary["players_detected"],
        "ratings_found": rating_summary["ratings_found"],
        "ratings_replacement": rating_summary["ratings_replacement"],
        "ratings_missing": rating_summary["ratings_missing"],
        "known_rating_count": rating_summary["known_rating_count"],
        "replacement_rating_count": rating_summary["replacement_rating_count"],
        "missing_rating_count": rating_summary["missing_rating_count"],
        "rating_coverage": rating_summary["rating_coverage"],
        "real_rating_coverage": rating_summary["real_rating_coverage"],
        "source_confidence_weighted_score": rating_summary["source_confidence_weighted_score"],
        "critical_missing_ratings": rating_summary["ratings_replacement"] + rating_summary["ratings_missing"],
        "player_data_quality_score": rating_summary["player_data_quality_score"],
        "lineup_data_quality": quality,
        "lineup_weighting_status": status,
        "warnings": rating_summary["warnings"],
        **strengths,
        "lineup_strength_total": _line_strength(players),
        **adjustments,
    }


def build_match_lineup_strength(
    team_a: str,
    team_b: str,
    snapshots_path: str | Path = DEFAULT_SNAPSHOTS_PATH,
    ratings_path: str | Path = DEFAULT_RATINGS_PATH,
) -> dict:
    snapshots_data = load_manual_snapshots(snapshots_path)
    snapshot = find_manual_snapshot(snapshots_data, team_a, team_b)
    ratings_data = load_player_ratings(ratings_path)
    team_a_strength = build_team_lineup_strength(snapshot, ratings_data, team_a)
    team_b_strength = build_team_lineup_strength(snapshot, ratings_data, team_b)
    total_detected = len(team_a_strength["players_detected"]) + len(team_b_strength["players_detected"])
    total_known = team_a_strength["known_rating_count"] + team_b_strength["known_rating_count"]
    total_replacement = (
        team_a_strength["replacement_rating_count"] + team_b_strength["replacement_rating_count"]
    )
    total_missing = team_a_strength["missing_rating_count"] + team_b_strength["missing_rating_count"]
    quality = (
        round(((total_known + (0.35 * total_replacement)) / total_detected) * 100, 2)
        if total_detected
        else 0.0
    )
    coverage = (
        round(((total_known + total_replacement) / total_detected) * 100, 2)
        if total_detected
        else 0.0
    )
    real_coverage = round((total_known / total_detected) * 100, 2) if total_detected else 0.0
    source_confidence_weighted_score = (
        round(
            (
                (
                    team_a_strength["source_confidence_weighted_score"]
                    * len(team_a_strength["players_detected"])
                )
                + (
                    team_b_strength["source_confidence_weighted_score"]
                    * len(team_b_strength["players_detected"])
                )
            )
            / total_detected,
            2,
        )
        if total_detected
        else 0.0
    )
    if quality >= 60 and total_known >= 8:
        status = "active"
    elif total_replacement > 0:
        status = "replacement_estimate"
    else:
        status = "incomplete"

    return {
        "match": snapshot["match"],
        "team_a": team_a_strength,
        "team_b": team_b_strength,
        "known_rating_count": total_known,
        "replacement_rating_count": total_replacement,
        "missing_rating_count": total_missing,
        "rating_coverage": coverage,
        "real_rating_coverage": real_coverage,
        "source_confidence_weighted_score": source_confidence_weighted_score,
        "lineup_data_quality": quality,
        "lineup_weighting_status": status,
        "critical_missing_ratings": (
            team_a_strength["critical_missing_ratings"]
            + team_b_strength["critical_missing_ratings"]
        ),
        "limitations": (
            ["No detected lineup/key-player names in manual snapshot."]
            if total_detected == 0
            else []
        )
        + team_a_strength["warnings"]
        + team_b_strength["warnings"],
    }
