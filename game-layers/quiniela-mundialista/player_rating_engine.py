import json
import re
import unicodedata
from pathlib import Path


PENDING_RATING = "pending_real_rating"
MISSING_EVIDENCE = "missing_rating_required"
REPLACEMENT_EVIDENCE = "replacement_level_estimate"
LINE_KEYS = ("goalkeeper", "defense", "midfield", "attack")


POSITION_REPLACEMENT_RATINGS = {
    "goalkeeper": 70.0,
    "defense": 70.5,
    "midfield": 71.0,
    "attack": 71.5,
    "unknown": 69.0,
}

SOURCE_CONFIDENCE_WEIGHTS = {
    "high": 1.0,
    "medium": 0.85,
    "low": 0.35,
}


def normalize_player_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(name))
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", ascii_name.lower()).strip()


def load_player_ratings(path: str | Path) -> dict:
    ratings_path = Path(path)
    if not ratings_path.exists():
        return {
            "data_status": "player_ratings_seed_missing",
            "players": [],
            "message": "player_ratings_seed.json not found.",
        }
    try:
        return json.loads(ratings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "data_status": "invalid_json",
            "players": [],
            "message": str(exc),
        }


def _is_numeric_rating(value) -> bool:
    return isinstance(value, (int, float)) and 0 <= float(value) <= 100


def _normalize_position(position: str) -> str:
    position = str(position).strip().lower()
    primary = re.split(r"[/,\s]+", position)[0]
    if position in LINE_KEYS:
        return position
    if primary in ("gk", "keeper", "goalkeeper"):
        return "goalkeeper"
    if primary in ("rb", "rwb", "lb", "lwb", "cb", "defender", "fullback", "centerback", "centreback"):
        return "defense"
    if primary in ("cm", "cdm", "cam", "dm", "am", "midfielder"):
        return "midfield"
    if primary in ("st", "cf", "lw", "rw", "rm", "lm", "lf", "rf", "forward", "winger", "striker"):
        return "attack"
    return "midfield"


def source_confidence_weight(source_confidence: str) -> float:
    return SOURCE_CONFIDENCE_WEIGHTS.get(str(source_confidence).strip().lower(), 0.35)


def _replacement_rating(position: str, is_worldcup_team: bool, appears_in_lineup: bool, is_key_player: bool) -> float:
    normalized_position = _normalize_position(position) if position != "unknown" else "unknown"
    rating = POSITION_REPLACEMENT_RATINGS.get(normalized_position, POSITION_REPLACEMENT_RATINGS["unknown"])
    if is_worldcup_team:
        rating += 1.5
    if appears_in_lineup:
        rating += 1.0
    if is_key_player:
        rating += 0.5
    return round(min(rating, 74.0), 2)


def normalize_rating_record(
    player: dict,
    *,
    is_worldcup_team: bool = True,
    appears_in_lineup: bool = False,
    is_key_player: bool = False,
) -> dict:
    normalized = dict(player)
    normalized["position"] = _normalize_position(normalized.get("position", "midfield"))
    real_rating = normalized.get("overall_rating")
    has_real_rating = _is_numeric_rating(real_rating)
    source_confidence = normalized.get(
        "source_confidence",
        "high" if normalized.get("evidence_level") == "official_public_rating" else "low",
    )
    normalized["source_confidence"] = source_confidence
    normalized["source_confidence_weight"] = source_confidence_weight(source_confidence)
    normalized["rating_scale"] = normalized.get("rating_scale", "0-100")
    normalized["has_real_rating"] = has_real_rating
    normalized["is_replacement_rating"] = not has_real_rating
    normalized["real_rating"] = real_rating if has_real_rating else PENDING_RATING
    normalized["appears_in_lineup"] = appears_in_lineup
    normalized["is_key_player"] = is_key_player
    normalized["is_worldcup_team"] = is_worldcup_team

    if has_real_rating:
        normalized["rating_status"] = "rating_available"
        normalized["rating_type"] = "real"
        normalized["has_numeric_rating"] = True
        return normalized

    normalized["overall_rating"] = _replacement_rating(
        normalized["position"],
        is_worldcup_team=is_worldcup_team,
        appears_in_lineup=appears_in_lineup,
        is_key_player=is_key_player,
    )
    normalized["replacement_rating"] = normalized["overall_rating"]
    normalized["evidence_level"] = REPLACEMENT_EVIDENCE
    normalized["source_confidence"] = "low"
    normalized["source_confidence_weight"] = source_confidence_weight("low")
    normalized["rating_status"] = REPLACEMENT_EVIDENCE
    normalized["rating_type"] = "replacement"
    normalized["has_numeric_rating"] = True
    normalized["notes"] = (
        f"{normalized.get('notes', '')} Replacement conservador usado porque no hay rating real local."
    ).strip()
    return normalized


def build_player_index(ratings_data: dict) -> dict:
    index = {}
    for player in ratings_data.get("players", []):
        key = normalize_player_name(player.get("player_name", ""))
        if key:
            normalized = dict(player)
            normalized["normalized_name"] = key
            normalized["position"] = _normalize_position(normalized.get("position", "midfield"))
            index[key] = normalized
    return index


def find_player_rating(
    ratings_data: dict,
    player_name: str,
    team: str | None = None,
    *,
    is_worldcup_team: bool = True,
    appears_in_lineup: bool = False,
    is_key_player: bool = False,
) -> dict:
    requested = normalize_player_name(player_name)
    team_key = str(team or "").strip().lower()
    candidates = []

    for player in ratings_data.get("players", []):
        current = normalize_player_name(player.get("player_name", ""))
        if not current:
            continue
        team_matches = not team_key or str(player.get("team", "")).strip().lower() == team_key
        name_matches = requested == current or requested in current or current in requested
        if team_matches and name_matches:
            candidates.append(player)

    if candidates:
        return normalize_rating_record(
            candidates[0],
            is_worldcup_team=is_worldcup_team,
            appears_in_lineup=appears_in_lineup,
            is_key_player=is_key_player,
        )

    return normalize_rating_record({
        "player_name": player_name,
        "team": team or "pending_team",
        "position": "unknown",
        "role": "unknown",
        "overall_rating": PENDING_RATING,
        "source": "not_found_in_player_ratings_seed",
        "evidence_level": MISSING_EVIDENCE,
        "notes": "Jugador detectado pero sin entrada en player_ratings_seed.json.",
    }, is_worldcup_team=is_worldcup_team, appears_in_lineup=appears_in_lineup, is_key_player=is_key_player)


def group_players_by_line(players: list[dict]) -> dict:
    grouped = {line: [] for line in LINE_KEYS}
    grouped["unknown"] = []
    for player in players:
        line = _normalize_position(player.get("position", "unknown"))
        if line not in grouped:
            line = "unknown"
        grouped[line].append(player)
    return grouped


def player_data_quality_score(players: list[dict]) -> float:
    if not players:
        return 0.0
    real_weight = sum(
        source_confidence_weight(player.get("source_confidence", "low"))
        for player in players
        if player.get("rating_type") == "real"
    )
    replacement_weight = sum(
        source_confidence_weight(player.get("source_confidence", "low"))
        for player in players
        if player.get("rating_type") == "replacement"
    )
    usable = real_weight + replacement_weight
    return round((usable / len(players)) * 100, 2)


def source_confidence_weighted_score(players: list[dict]) -> float:
    if not players:
        return 0.0
    weights = [source_confidence_weight(player.get("source_confidence", "low")) for player in players]
    return round((sum(weights) / len(weights)) * 100, 2)


def rating_warnings(players: list[dict]) -> list[str]:
    warnings = []
    for player in players:
        if player.get("rating_type") == "replacement":
            warnings.append(
                f"{player.get('player_name')}: {REPLACEMENT_EVIDENCE}; rating real faltante, ajuste conservador."
            )
        elif not _is_numeric_rating(player.get("overall_rating")):
            warnings.append(
                f"{player.get('player_name')}: {MISSING_EVIDENCE}; limita ajustes matematicos."
            )
    return warnings


def summarize_player_ratings(players: list[dict]) -> dict:
    real = [player for player in players if player.get("rating_type") == "real"]
    replacement = [player for player in players if player.get("rating_type") == "replacement"]
    missing = [player for player in players if player.get("rating_status") == MISSING_EVIDENCE]
    return {
        "players_detected": [player.get("player_name") for player in players],
        "ratings_found": [player.get("player_name") for player in real],
        "ratings_replacement": [player.get("player_name") for player in replacement],
        "ratings_missing": [player.get("player_name") for player in missing],
        "known_rating_count": len(real),
        "replacement_rating_count": len(replacement),
        "missing_rating_count": len(missing),
        "rating_coverage": (
            round(((len(real) + len(replacement)) / len(players)) * 100, 2)
            if players
            else 0.0
        ),
        "real_rating_coverage": (
            round((len(real) / len(players)) * 100, 2)
            if players
            else 0.0
        ),
        "source_confidence_weighted_score": source_confidence_weighted_score(players),
        "player_data_quality_score": player_data_quality_score(players),
        "warnings": rating_warnings(players),
        "grouped_by_line": group_players_by_line(players),
    }
