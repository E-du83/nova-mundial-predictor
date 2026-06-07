from pathlib import Path

from lineup_strength_engine import (
    DEFAULT_RATINGS_PATH,
    DEFAULT_SNAPSHOTS_PATH,
    build_match_lineup_strength,
)
from manual_snapshot_engine import find_manual_snapshot, load_manual_snapshots
from formation_tactical_engine import build_formation_tactical_score


PENDING = "pending_manual_input"


def _formation_for(snapshot: dict, team_key: str) -> str:
    lineups = snapshot.get("probable_lineups", {})
    return lineups.get(f"{team_key}_formation", PENDING)


def _has_formation(formation: str) -> bool:
    return formation not in (None, "", PENDING)


def _role_count(team_strength: dict, role_part: str) -> int:
    count = 0
    for line in ("ratings_found", "ratings_missing"):
        for player_name in team_strength.get(line, []):
            if role_part.lower() in str(player_name).lower():
                count += 1
    return count


def _detected_role_hints(team_strength: dict) -> dict:
    names = " ".join(team_strength.get("players_detected", [])).lower()
    return {
        "aerial_threat": int("haaland" in names or "sorloth" in names or "mina" in names),
        "transition_threat": int("diaz" in names or "nusa" in names or "bobb" in names or "tamari" in names),
        "central_control": int("odegaard" in names or "james" in names or "lerma" in names or "ounahi" in names),
        "set_piece_risk": int("haaland" in names or "sorloth" in names or "mina" in names or "aguerd" in names),
        "width": int("hakimi" in names or "munoz" in names or "diaz" in names or "nusa" in names),
    }


def _advantage(team_a_value: int, team_b_value: int) -> str:
    if team_a_value > team_b_value:
        return "team_a"
    if team_b_value > team_a_value:
        return "team_b"
    return "neutral_or_pending"


def build_tactical_weighting(
    team_a: str,
    team_b: str,
    snapshots_path: str | Path = DEFAULT_SNAPSHOTS_PATH,
    ratings_path: str | Path = DEFAULT_RATINGS_PATH,
) -> dict:
    snapshots_data = load_manual_snapshots(snapshots_path)
    snapshot = find_manual_snapshot(snapshots_data, team_a, team_b)
    lineup_strength = build_match_lineup_strength(team_a, team_b, snapshots_path, ratings_path)
    formation_tactical = build_formation_tactical_score(team_a, team_b, snapshots_path, ratings_path)
    team_a_formation = _formation_for(snapshot, "team_a")
    team_b_formation = _formation_for(snapshot, "team_b")
    formation_missing = not (_has_formation(team_a_formation) and _has_formation(team_b_formation))

    a_hints = _detected_role_hints(lineup_strength["team_a"])
    b_hints = _detected_role_hints(lineup_strength["team_b"])
    width_advantage = _advantage(a_hints["width"], b_hints["width"])
    central_control_advantage = _advantage(a_hints["central_control"], b_hints["central_control"])
    aerial_threat_advantage = _advantage(a_hints["aerial_threat"], b_hints["aerial_threat"])
    transition_threat_advantage = _advantage(a_hints["transition_threat"], b_hints["transition_threat"])
    set_piece_risk = _advantage(a_hints["set_piece_risk"], b_hints["set_piece_risk"])

    if formation_missing or lineup_strength["lineup_weighting_status"] != "active":
        adjustment_status = "qualitative_only"
        tactical_attack_adjustment = 0.0
        tactical_defense_adjustment = 0.0
        btts_adjustment = 0.0
        over_under_adjustment = 0.0
        risk_adjustment = "warning_only"
    else:
        adjustment_status = "active"
        tactical_attack_adjustment = 0.03 if transition_threat_advantage != "neutral_or_pending" else 0.0
        tactical_defense_adjustment = -0.02 if central_control_advantage != "neutral_or_pending" else 0.0
        btts_adjustment = 0.02 if aerial_threat_advantage != "neutral_or_pending" else 0.0
        over_under_adjustment = 0.02 if set_piece_risk != "neutral_or_pending" else 0.0
        risk_adjustment = "numeric"

    return {
        "match": snapshot["match"],
        "formation_missing": formation_missing,
        "team_a_formation": team_a_formation,
        "team_b_formation": team_b_formation,
        "width_advantage": width_advantage,
        "central_control_advantage": central_control_advantage,
        "aerial_threat_advantage": aerial_threat_advantage,
        "transition_threat_advantage": transition_threat_advantage,
        "defensive_block_risk": "pending_without_confirmed_shape",
        "set_piece_risk": set_piece_risk,
        "tactical_attack_adjustment": tactical_attack_adjustment,
        "tactical_defense_adjustment": tactical_defense_adjustment,
        "btts_adjustment": btts_adjustment,
        "over_under_adjustment": over_under_adjustment,
        "risk_adjustment": risk_adjustment,
        "adjustment_status": adjustment_status,
        **formation_tactical,
        "explanation": (
            "Formacion faltante o ratings insuficientes; se usan roles detectados como contexto."
            if adjustment_status == "qualitative_only"
            else "Formaciones y ratings suficientes para ajustes tacticos moderados."
        ),
    }
