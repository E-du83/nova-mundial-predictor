from pathlib import Path

from lineup_strength_engine import (
    DEFAULT_RATINGS_PATH,
    DEFAULT_SNAPSHOTS_PATH,
    build_match_lineup_strength,
)
from manual_snapshot_engine import find_manual_snapshot, load_manual_snapshots


PENDING = "pending_manual_input"


def _is_numeric(value) -> bool:
    return isinstance(value, (int, float))


def _strength(value, fallback: float = 75.0) -> float:
    return float(value) if _is_numeric(value) else fallback


def _clamp(value: float, low: float = -0.35, high: float = 0.35) -> float:
    return round(max(low, min(high, value)), 3)


def _formation_for(snapshot: dict, team_key: str) -> str:
    lineups = snapshot.get("probable_lineups", {})
    return lineups.get(f"{team_key}_formation", PENDING)


def _has_formation(formation: str) -> bool:
    return formation not in (None, "", PENDING)


def _formation_parts(formation: str) -> tuple[int, int, int] | None:
    if not _has_formation(formation):
        return None
    parts = []
    for part in str(formation).replace(" ", "").split("-"):
        if part.isdigit():
            parts.append(int(part))
    if len(parts) < 3:
        return None
    defense = parts[0]
    midfield = sum(parts[1:-1])
    attack = parts[-1]
    return defense, midfield, attack


def _detected_role_hints(team_strength: dict) -> dict:
    names = " ".join(team_strength.get("players_detected", [])).lower()
    return {
        "aerial_threat": int("haaland" in names or "sorloth" in names or "mina" in names),
        "transition_threat": int("diaz" in names or "nusa" in names or "bobb" in names or "tamari" in names),
        "central_control": int("odegaard" in names or "james" in names or "lerma" in names or "ounahi" in names),
        "set_piece_threat": int("haaland" in names or "sorloth" in names or "mina" in names or "aguerd" in names),
        "width": int("hakimi" in names or "munoz" in names or "diaz" in names or "nusa" in names),
        "pressing": int("lerma" in names or "ounahi" in names or "berge" in names or "arias" in names),
    }


def _hint_edge(a_hints: dict, b_hints: dict, key: str, weight: float) -> float:
    return (a_hints.get(key, 0) - b_hints.get(key, 0)) * weight


def _team_average(team_strength: dict) -> float:
    values = [
        _strength(team_strength.get("goalkeeper_strength")),
        _strength(team_strength.get("defense_strength")),
        _strength(team_strength.get("midfield_strength")),
        _strength(team_strength.get("attack_strength")),
    ]
    return sum(values) / len(values)


def _formation_matchup_edge(team_a_formation: str, team_b_formation: str) -> float:
    a_parts = _formation_parts(team_a_formation)
    b_parts = _formation_parts(team_b_formation)
    if not a_parts or not b_parts:
        return 0.0
    a_def, a_mid, a_att = a_parts
    b_def, b_mid, b_att = b_parts
    edge = 0.0
    edge += (a_mid - b_mid) * 0.04
    edge += (a_att - b_def) * 0.025
    edge -= (b_att - a_def) * 0.025
    return _clamp(edge, -0.25, 0.25)


def _impact_level(tactical_score: float) -> str:
    if tactical_score >= 0.20:
        return "high_tactical_advantage"
    if tactical_score >= 0.05:
        return "moderate_tactical_advantage"
    if tactical_score <= -0.05:
        return "tactical_risk"
    return "neutral"


def _score_impact(level: str) -> str:
    if level == "high_tactical_advantage":
        return "puede subir confianza del favorito y favorecer margen de 2 goles si top_scores lo permite"
    if level == "moderate_tactical_advantage":
        return "usar solo como desempate entre marcadores cercanos, por ejemplo 1-0 vs 2-0"
    if level == "tactical_risk":
        return "activar riesgo tactico; puede subir draw_warning, BTTS risk o reducir confianza"
    return "ventaja tactica neutra; no cambiar pick"


def _half_time_impact(level: str) -> str:
    if level == "high_tactical_advantage":
        return "puede apoyar descanso/final favorable al equipo con ventaja si xG y top_scores acompanan"
    if level == "moderate_tactical_advantage":
        return "puede desempatar descanso/final cercano, sin cambiarlo por si solo"
    if level == "tactical_risk":
        return "favorece descanso prudente o alerta de empate si el partido ya es fragil"
    return "sin impacto numerico en descanso/final"


def _quinigol_impact(level: str) -> str:
    if level == "high_tactical_advantage":
        return "puede adelantar rango/minuto de Quinigol si el ataque favorecido ya era el recomendado"
    if level == "moderate_tactical_advantage":
        return "puede reforzar el equipo recomendado para Quinigol, sin cambiarlo solo"
    if level == "tactical_risk":
        return "puede ensanchar rango de Quinigol o elevar BTTS risk"
    return "sin impacto numerico en Quinigol"


def build_formation_tactical_score(
    team_a: str,
    team_b: str,
    snapshots_path: str | Path = DEFAULT_SNAPSHOTS_PATH,
    ratings_path: str | Path = DEFAULT_RATINGS_PATH,
) -> dict:
    snapshots_data = load_manual_snapshots(snapshots_path)
    snapshot = find_manual_snapshot(snapshots_data, team_a, team_b)
    lineup_strength = build_match_lineup_strength(team_a, team_b, snapshots_path, ratings_path)

    team_a_strength = lineup_strength["team_a"]
    team_b_strength = lineup_strength["team_b"]
    a_hints = _detected_role_hints(team_a_strength)
    b_hints = _detected_role_hints(team_b_strength)

    team_a_formation = _formation_for(snapshot, "team_a")
    team_b_formation = _formation_for(snapshot, "team_b")
    formation_missing = not (_has_formation(team_a_formation) and _has_formation(team_b_formation))

    a_avg = _team_average(team_a_strength)
    b_avg = _team_average(team_b_strength)
    line_strength_edge = _clamp((a_avg - b_avg) / 25)
    formation_matchup_edge = _formation_matchup_edge(team_a_formation, team_b_formation)
    midfield_control_edge = _clamp(
        (_strength(team_a_strength.get("midfield_strength")) - _strength(team_b_strength.get("midfield_strength")))
        / 20
        + _hint_edge(a_hints, b_hints, "central_control", 0.045),
        -0.3,
        0.3,
    )
    wide_attack_edge = _clamp(
        (
            _strength(team_a_strength.get("attack_strength"))
            - _strength(team_b_strength.get("defense_strength"))
        )
        / 35
        + _hint_edge(a_hints, b_hints, "width", 0.06),
        -0.3,
        0.3,
    )
    central_attack_edge = _clamp(
        (
            _strength(team_a_strength.get("attack_strength"))
            - _strength(team_b_strength.get("defense_strength"))
        )
        / 32
        + _hint_edge(a_hints, b_hints, "central_control", 0.04)
        + _hint_edge(a_hints, b_hints, "aerial_threat", 0.04),
        -0.3,
        0.3,
    )
    transition_risk_adjustment = _clamp(
        _hint_edge(a_hints, b_hints, "transition_threat", 0.08)
        + (
            (_strength(team_a_strength.get("attack_strength")) - _strength(team_b_strength.get("defense_strength")))
            - (_strength(team_b_strength.get("attack_strength")) - _strength(team_a_strength.get("defense_strength")))
        )
        / 60,
        -0.25,
        0.25,
    )
    defensive_security_edge = _clamp(
        (
            (
                _strength(team_a_strength.get("goalkeeper_strength"))
                + _strength(team_a_strength.get("defense_strength"))
            )
            - (
                _strength(team_b_strength.get("goalkeeper_strength"))
                + _strength(team_b_strength.get("defense_strength"))
            )
        )
        / 50
        - _hint_edge(a_hints, b_hints, "set_piece_threat", 0.035),
        -0.3,
        0.3,
    )
    pressing_advantage = _clamp(
        (
            _strength(team_a_strength.get("midfield_strength"))
            + _strength(team_a_strength.get("attack_strength"))
            - _strength(team_b_strength.get("midfield_strength"))
            - _strength(team_b_strength.get("attack_strength"))
        )
        / 45
        + _hint_edge(a_hints, b_hints, "pressing", 0.04),
        -0.25,
        0.25,
    )
    low_block_breakdown_score = _clamp(
        (wide_attack_edge * 0.45) + (central_attack_edge * 0.4) + (midfield_control_edge * 0.15),
        -0.3,
        0.3,
    )

    tactical_score = round(
        (line_strength_edge * 0.35)
        + (formation_matchup_edge * 0.25)
        + (midfield_control_edge * 0.15)
        + (wide_attack_edge * 0.10)
        + (transition_risk_adjustment * 0.10)
        + (defensive_security_edge * 0.05),
        3,
    )
    level = _impact_level(tactical_score)
    if lineup_strength["lineup_weighting_status"] == "active":
        data_status = "active_numeric"
    elif lineup_strength["lineup_weighting_status"] == "replacement_estimate":
        data_status = "replacement_numeric_conservative"
    else:
        data_status = "partial_numeric_warning"
    if formation_missing:
        data_status += "_formation_pending"

    return {
        "match": snapshot["match"],
        "team_a": team_a,
        "team_b": team_b,
        "team_a_formation": team_a_formation,
        "team_b_formation": team_b_formation,
        "formation_missing": formation_missing,
        "line_strength_edge": line_strength_edge,
        "formation_matchup_edge": formation_matchup_edge,
        "midfield_control_edge": midfield_control_edge,
        "wide_attack_edge": wide_attack_edge,
        "central_attack_edge": central_attack_edge,
        "transition_risk_adjustment": transition_risk_adjustment,
        "defensive_security_edge": defensive_security_edge,
        "pressing_advantage": pressing_advantage,
        "low_block_breakdown_score": low_block_breakdown_score,
        "tactical_score": tactical_score,
        "tactical_impact_level": level,
        "score_impact": _score_impact(level),
        "half_time_impact": _half_time_impact(level),
        "quinigol_impact": _quinigol_impact(level),
        "tactical_data_status": data_status,
        "lineup_strength_status": lineup_strength["lineup_weighting_status"],
    }


def format_formation_tactical_lines(tactical: dict) -> list[str]:
    return [
        f"Tactical score: {tactical['tactical_score']} ({tactical['tactical_impact_level']})",
        f"Line strength edge: {tactical['line_strength_edge']}",
        f"Formation matchup edge: {tactical['formation_matchup_edge']}",
        f"Midfield control: {tactical['midfield_control_edge']}",
        f"Wide attack: {tactical['wide_attack_edge']}",
        f"Central attack: {tactical['central_attack_edge']}",
        f"Transition risk: {tactical['transition_risk_adjustment']}",
        f"Defensive security: {tactical['defensive_security_edge']}",
        f"Pressing advantage: {tactical['pressing_advantage']}",
        f"Low block breakdown score: {tactical['low_block_breakdown_score']}",
        f"Impacto en marcador: {tactical['score_impact']}",
        f"Impacto en descanso/final: {tactical['half_time_impact']}",
        f"Impacto en Quinigol: {tactical['quinigol_impact']}",
        f"Estado de datos tacticos: {tactical['tactical_data_status']}",
    ]
