from __future__ import annotations

import copy
import re
from typing import Any


PENDING_VALUES = {
    None,
    "",
    "pending_manual_input",
    "pending_real_data",
    "pending_real_rating",
    "replacement_level_estimate",
    "missing_rating_required",
    "not_available",
}

TACTICAL_RANGE = (0.94, 1.06)
LINEUP_RANGE = (0.82, 1.18)


def _is_pending(value: Any) -> bool:
    if value is None:
        return True
    return isinstance(value, str) and value.strip().lower() in PENDING_VALUES


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _cap_adjustment(value: float, min_value: float, max_value: float) -> float:
    return round(max(min_value, min(max_value, value)), 4)


def _append_cap(report: dict, label: str, original: float, capped: float) -> None:
    if round(original, 4) != round(capped, 4):
        report["safety_caps_applied"].append(
            {
                "field": label,
                "original": round(original, 4),
                "capped": capped,
            }
        )


def _snapshot_team_key(snapshot: dict, team_name: str) -> str | None:
    if snapshot.get("team_a") == team_name:
        return "team_a"
    if snapshot.get("team_b") == team_name:
        return "team_b"
    return None


def _as_list(value: Any) -> list:
    if _is_pending(value):
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [item.strip() for item in re.split(r"[,;\n]+", value) if item.strip()]
    return []


def _normalize_position(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in ("gk", "keeper", "goalkeeper"):
        return "goalkeeper"
    if text in ("cb", "rb", "lb", "rwb", "lwb", "def", "defense", "defender"):
        return "defense"
    if text in ("cm", "dm", "cdm", "cam", "mid", "midfield", "midfielder"):
        return "midfield"
    if text in ("st", "cf", "lw", "rw", "fw", "att", "attack", "forward", "striker", "winger"):
        return "attack"
    return "midfield"


def _rating_is_real(player: dict) -> bool:
    rating = player.get("rating", player.get("overall_rating"))
    if not (_is_number(rating) and 0 <= float(rating) <= 100):
        return False
    status_blob = " ".join(
        str(player.get(key, ""))
        for key in ("rating_status", "rating_type", "evidence_level", "source_confidence", "data_status")
    ).lower()
    blocked = ("replacement_level_estimate", "pending_manual_input", "pending_real_rating")
    return not any(item in status_blob for item in blocked)


def _players_from_snapshot(snapshot: dict, team_name: str) -> list[dict]:
    players: list[dict] = []
    ratings = snapshot.get("player_ratings", {})
    if isinstance(ratings, dict):
        players.extend(item for item in _as_list(ratings.get(team_name)) if isinstance(item, dict))

    lineups = snapshot.get("probable_lineups", {})
    if isinstance(lineups, dict):
        team_key = _snapshot_team_key(snapshot, team_name)
        if team_key:
            direct = lineups.get(f"{team_key}_players")
            players.extend(item for item in _as_list(direct) if isinstance(item, dict))

    return players


def _players_from_team(team: dict) -> list[dict]:
    players = team.get("probable_lineup", [])
    return [item for item in _as_list(players) if isinstance(item, dict)]


def _valid_rated_players(team_name: str, team: dict, snapshot: dict | None) -> list[dict]:
    candidates = []
    if snapshot:
        candidates.extend(_players_from_snapshot(snapshot, team_name))
    candidates.extend(_players_from_team(team))
    return [player for player in candidates if _rating_is_real(player)]


def _lineup_multipliers(players: list[dict]) -> tuple[float, float, dict]:
    grouped = {
        "goalkeeper": [],
        "defense": [],
        "midfield": [],
        "attack": [],
    }
    for player in players:
        grouped[_normalize_position(player.get("position", player.get("role")))].append(
            float(player.get("rating", player.get("overall_rating")))
        )

    attack_values = grouped["attack"] + grouped["midfield"]
    defense_values = grouped["defense"] + grouped["goalkeeper"]
    attack_avg = sum(attack_values) / len(attack_values) if attack_values else 75.0
    defense_avg = sum(defense_values) / len(defense_values) if defense_values else 75.0
    attack_multiplier = 1 + ((attack_avg - 75.0) / 100.0 * 0.45)
    defense_multiplier = 1 - ((defense_avg - 75.0) / 100.0 * 0.38)
    return attack_multiplier, defense_multiplier, {
        "valid_player_count": len(players),
        "attack_rating_average": round(attack_avg, 2),
        "defense_rating_average": round(defense_avg, 2),
    }


def _module_lineup_multipliers(team_a_name: str, team_b_name: str) -> dict | None:
    try:
        from lineup_strength_engine import build_match_lineup_strength
    except Exception:
        return None
    try:
        strength = build_match_lineup_strength(team_a_name, team_b_name)
    except Exception:
        return None
    if strength.get("lineup_weighting_status") != "active":
        return None

    result = {}
    for key in ("team_a", "team_b"):
        team_strength = strength.get(key, {})
        if team_strength.get("known_rating_count", 0) < 7:
            return None
        attack = team_strength.get("attack_strength")
        midfield = team_strength.get("midfield_strength")
        defense = team_strength.get("defense_strength")
        goalkeeper = team_strength.get("goalkeeper_strength")
        values = (attack, midfield, defense, goalkeeper)
        if not all(_is_number(value) for value in values):
            return None
        attack_avg = (float(attack) + float(midfield)) / 2
        defense_avg = (float(defense) + float(goalkeeper)) / 2
        result[key] = (
            1 + ((attack_avg - 75.0) / 100.0 * 0.45),
            1 - ((defense_avg - 75.0) / 100.0 * 0.38),
            {
                "source": "lineup_strength_engine",
                "valid_player_count": team_strength.get("known_rating_count", 0),
                "attack_rating_average": round(attack_avg, 2),
                "defense_rating_average": round(defense_avg, 2),
            },
        )
    return result


def _formation_for(team_name: str, team: dict, snapshot: dict | None) -> str | None:
    if snapshot:
        formations = snapshot.get("formations", {})
        if isinstance(formations, dict) and not _is_pending(formations.get(team_name)):
            return str(formations[team_name])
        lineups = snapshot.get("probable_lineups", {})
        team_key = _snapshot_team_key(snapshot, team_name)
        if isinstance(lineups, dict) and team_key:
            formation = lineups.get(f"{team_key}_formation")
            if not _is_pending(formation):
                return str(formation)
    formation = team.get("formation")
    return None if _is_pending(formation) else str(formation)


def _module_formations(team_a_name: str, team_b_name: str) -> tuple[str | None, str | None]:
    try:
        from formation_tactical_engine import build_formation_tactical_score
    except Exception:
        return None, None
    try:
        tactical = build_formation_tactical_score(team_a_name, team_b_name)
    except Exception:
        return None, None
    if tactical.get("formation_missing"):
        return None, None
    return tactical.get("team_a_formation"), tactical.get("team_b_formation")


def _formation_profile(formation: str) -> tuple[float, float, str]:
    normalized = formation.strip().replace(" ", "")
    profiles = {
        "4-3-3": (1.035, 1.015, "4-3-3 favorece amplitud y ataque, con pequena exposicion defensiva."),
        "5-4-1": (0.975, 0.96, "5-4-1 prioriza bloque bajo y proteccion defensiva."),
        "4-2-3-1": (1.015, 0.99, "4-2-3-1 favorece balance y control."),
        "3-5-2": (1.02, 1.02, "3-5-2 suma mediocampo/amplitud, pero puede exponer bandas."),
        "4-4-2": (1.01, 0.995, "4-4-2 favorece estructura y centros."),
    }
    return profiles.get(normalized, (1.0, 1.0, f"{formation} sin regla tactica especifica; ajuste neutral."))


def _form_for(team_name: str, team: dict, snapshot: dict | None) -> tuple[float | None, str]:
    if snapshot:
        stats = snapshot.get("stats_snapshot", {})
        if isinstance(stats, dict):
            for key in (f"{team_name}_form_score", f"form_score_{team_name}", "form_score"):
                value = stats.get(key)
                if _is_number(value):
                    return float(value), "stats_snapshot"
        forms = snapshot.get("form", {})
        if isinstance(forms, dict) and _is_number(forms.get(team_name)):
            return float(forms[team_name]), "match_snapshot.form"
    value = team.get("form")
    if _is_number(value):
        return float(value), "team.form"
    return None, "not_available"


def _confidence_is_low(snapshot: dict | None) -> bool:
    if not snapshot:
        return False
    confidence = str(snapshot.get("research_confidence", "")).lower()
    data_status = str(snapshot.get("data_status", "")).lower()
    return confidence == "low" or "low_confidence" in data_status


def _absence_items(team_name: str, snapshot: dict | None) -> list[dict]:
    if not snapshot:
        return []
    raw = snapshot.get("injuries_or_absences", snapshot.get("injuries", {}))
    if isinstance(raw, dict):
        value = raw.get(team_name, [])
    else:
        value = raw
    items = _as_list(value)
    normalized = []
    for item in items:
        if isinstance(item, dict):
            normalized.append(item)
        elif not _is_pending(item):
            normalized.append({"player": str(item), "impact": "unknown", "role": "unknown"})
    return normalized


def _apply_absences(team: dict, team_name: str, snapshot: dict | None, report: dict) -> dict:
    applied = []
    for item in _absence_items(team_name, snapshot):
        impact = str(item.get("impact", "unknown")).lower()
        key_player = bool(item.get("key_player"))
        if not key_player and impact not in ("high", "medium"):
            continue
        role = _normalize_position(item.get("role", item.get("position", "unknown")))
        if str(item.get("role", item.get("position", "unknown"))).lower() in ("unknown", ""):
            report["warnings"].append(
                f"{team_name}: ausencia sin rol claro ({item.get('player', 'unknown')}); solo warning."
            )
            continue
        delta = 0.08 if impact == "high" else 0.05 if impact == "medium" else 0.03
        if role in ("attack", "midfield"):
            team["attack"] = round(float(team["attack"]) * (1 - delta), 4)
            applied.append({"player": item.get("player", "unknown"), "attack_delta": round(-delta, 3)})
        else:
            team["defense"] = round(float(team["defense"]) * (1 + delta), 4)
            applied.append({"player": item.get("player", "unknown"), "defense_delta": round(delta, 3)})
    return {"applied": bool(applied), "items": applied}


def _data_quality(report: dict) -> str:
    applied_count = sum(
        bool(report[key])
        for key in ("lineup_applied", "tactical_applied", "form_applied")
    )
    if applied_count >= 3 and report["player_ratings_applied"]:
        return "high"
    if applied_count >= 2:
        return "medium"
    if applied_count == 1:
        return "low"
    return "insufficient"


def _expected_direction(original: dict, adjusted: dict, team_a: str, team_b: str) -> str:
    a_delta = (
        adjusted["team_a_adjusted"]["attack"] / original[team_a]["attack"]
        * adjusted["team_b_adjusted"]["defense"] / original[team_b]["defense"]
    ) - 1
    b_delta = (
        adjusted["team_b_adjusted"]["attack"] / original[team_b]["attack"]
        * adjusted["team_a_adjusted"]["defense"] / original[team_a]["defense"]
    ) - 1
    if abs(a_delta - b_delta) < 0.01:
        return "neutral"
    return "team_a_up" if a_delta > b_delta else "team_b_up"


def build_adjusted_match_inputs(
    team_a_name: str,
    team_b_name: str,
    teams: dict,
    match_snapshot: dict | None = None,
    apply_lineup: bool = True,
    apply_tactical: bool = True,
    apply_form: bool = True,
    max_adjustment_delta: float = 0.18,
) -> dict:
    team_a_adjusted = copy.deepcopy(teams[team_a_name])
    team_b_adjusted = copy.deepcopy(teams[team_b_name])
    adjusted_teams = dict(teams)
    adjusted_teams[team_a_name] = team_a_adjusted
    adjusted_teams[team_b_name] = team_b_adjusted

    report = {
        "bridge_status": "not_applied",
        "baseline_mutated": False,
        "lineup_applied": False,
        "tactical_applied": False,
        "form_applied": False,
        "player_ratings_applied": False,
        "data_quality": "insufficient",
        "adjustments": {},
        "missing_data": [],
        "warnings": [],
        "safety_caps_applied": [],
        "original_attack_a": teams[team_a_name]["attack"],
        "original_defense_a": teams[team_a_name]["defense"],
        "original_attack_b": teams[team_b_name]["attack"],
        "original_defense_b": teams[team_b_name]["defense"],
    }

    max_min = 1 - max_adjustment_delta
    max_max = 1 + max_adjustment_delta

    if apply_lineup:
        players_a = _valid_rated_players(team_a_name, teams[team_a_name], match_snapshot)
        players_b = _valid_rated_players(team_b_name, teams[team_b_name], match_snapshot)
        module_lineup = None
        if not (len(players_a) >= 7 and len(players_b) >= 7):
            module_lineup = _module_lineup_multipliers(team_a_name, team_b_name)
        if len(players_a) >= 7 and len(players_b) >= 7:
            for team_name, team, players, suffix in (
                (team_a_name, team_a_adjusted, players_a, "a"),
                (team_b_name, team_b_adjusted, players_b, "b"),
            ):
                attack_mult, defense_mult, summary = _lineup_multipliers(players)
                attack_capped = _cap_adjustment(attack_mult, max(LINEUP_RANGE[0], max_min), min(LINEUP_RANGE[1], max_max))
                defense_capped = _cap_adjustment(defense_mult, max(LINEUP_RANGE[0], max_min), min(LINEUP_RANGE[1], max_max))
                _append_cap(report, f"lineup_attack_{suffix}", attack_mult, attack_capped)
                _append_cap(report, f"lineup_defense_{suffix}", defense_mult, defense_capped)
                team["attack"] = round(float(team["attack"]) * attack_capped, 4)
                team["defense"] = round(float(team["defense"]) * defense_capped, 4)
                report["adjustments"][f"{team_name}_lineup"] = {
                    **summary,
                    "attack_multiplier": attack_capped,
                    "defense_multiplier": defense_capped,
                }
            report["lineup_applied"] = True
            report["player_ratings_applied"] = True
        elif module_lineup:
            for team_name, team, module_key, suffix in (
                (team_a_name, team_a_adjusted, "team_a", "a"),
                (team_b_name, team_b_adjusted, "team_b", "b"),
            ):
                attack_mult, defense_mult, summary = module_lineup[module_key]
                attack_capped = _cap_adjustment(attack_mult, max(LINEUP_RANGE[0], max_min), min(LINEUP_RANGE[1], max_max))
                defense_capped = _cap_adjustment(defense_mult, max(LINEUP_RANGE[0], max_min), min(LINEUP_RANGE[1], max_max))
                _append_cap(report, f"lineup_attack_{suffix}", attack_mult, attack_capped)
                _append_cap(report, f"lineup_defense_{suffix}", defense_mult, defense_capped)
                team["attack"] = round(float(team["attack"]) * attack_capped, 4)
                team["defense"] = round(float(team["defense"]) * defense_capped, 4)
                report["adjustments"][f"{team_name}_lineup"] = {
                    **summary,
                    "attack_multiplier": attack_capped,
                    "defense_multiplier": defense_capped,
                }
            report["lineup_applied"] = True
            report["player_ratings_applied"] = True
        else:
            report["missing_data"].append(
                "lineup/player_ratings: se requieren al menos 7 jugadores con ratings reales por equipo"
            )

    if apply_tactical:
        formation_a = _formation_for(team_a_name, teams[team_a_name], match_snapshot)
        formation_b = _formation_for(team_b_name, teams[team_b_name], match_snapshot)
        if not (formation_a and formation_b):
            module_formation_a, module_formation_b = _module_formations(team_a_name, team_b_name)
            formation_a = formation_a or module_formation_a
            formation_b = formation_b or module_formation_b
        if formation_a and formation_b:
            for team_name, team, formation, suffix in (
                (team_a_name, team_a_adjusted, formation_a, "a"),
                (team_b_name, team_b_adjusted, formation_b, "b"),
            ):
                attack_mult, defense_mult, summary = _formation_profile(formation)
                attack_capped = _cap_adjustment(attack_mult, *TACTICAL_RANGE)
                defense_capped = _cap_adjustment(defense_mult, *TACTICAL_RANGE)
                team["tactical_attack_adjustment"] = round(
                    float(team.get("tactical_attack_adjustment", 1.0)) * attack_capped,
                    4,
                )
                team["tactical_defense_adjustment"] = round(
                    float(team.get("tactical_defense_adjustment", 1.0)) * defense_capped,
                    4,
                )
                report["adjustments"][f"{team_name}_tactical"] = {
                    "formation": formation,
                    "attack_multiplier": attack_capped,
                    "defense_multiplier": defense_capped,
                    "summary": summary,
                }
            report["adjustments"]["tactical_matchup_summary"] = (
                f"{team_a_name} {formation_a} vs {team_b_name} {formation_b}; "
                "ajustes conservadores aplicados a copias temporales."
            )
            report["tactical_applied"] = True
        else:
            report["missing_data"].append("formations: se requiere formacion probable de ambos equipos")

    if apply_form:
        if _confidence_is_low(match_snapshot):
            report["missing_data"].append("form: research_confidence low bloquea ajuste numerico")
        for team_name, team, suffix in (
            (team_a_name, team_a_adjusted, "a"),
            (team_b_name, team_b_adjusted, "b"),
        ):
            form_value, form_source = _form_for(team_name, teams[team_name], match_snapshot)
            if form_value is None or form_value == 1.0:
                continue
            if 0.80 <= form_value <= 1.20 and not _confidence_is_low(match_snapshot):
                team["form"] = round(float(team.get("form", 1.0)) * form_value, 4)
                report["adjustments"][f"{team_name}_form"] = {
                    "form_multiplier": form_value,
                    "form_source": form_source,
                }
                report["form_applied"] = True
            else:
                report["warnings"].append(f"{team_name}: form fuera de rango o baja confianza; no aplicado.")
        if not report["form_applied"]:
            report["missing_data"].append("form: no hay form_score confiable distinto de 1.0")

    injury_a = _apply_absences(team_a_adjusted, team_a_name, match_snapshot, report)
    injury_b = _apply_absences(team_b_adjusted, team_b_name, match_snapshot, report)
    if injury_a["applied"] or injury_b["applied"]:
        report["adjustments"]["injury_adjustments"] = {
            team_a_name: injury_a["items"],
            team_b_name: injury_b["items"],
        }

    report["adjusted_attack_a"] = team_a_adjusted["attack"]
    report["adjusted_defense_a"] = team_a_adjusted["defense"]
    report["adjusted_attack_b"] = team_b_adjusted["attack"]
    report["adjusted_defense_b"] = team_b_adjusted["defense"]
    report["xg_delta_expected_direction"] = _expected_direction(
        teams,
        {
            "team_a_adjusted": team_a_adjusted,
            "team_b_adjusted": team_b_adjusted,
        },
        team_a_name,
        team_b_name,
    )
    report["data_quality"] = _data_quality(report)

    applied_flags = [
        report["lineup_applied"],
        report["tactical_applied"],
        report["form_applied"],
        bool(report["adjustments"].get("injury_adjustments")),
    ]
    if any(applied_flags):
        expected_enabled = sum(bool(value) for value in (apply_lineup, apply_tactical, apply_form))
        actual_enabled = sum(bool(value) for value in applied_flags[:3])
        report["bridge_status"] = "applied" if actual_enabled >= expected_enabled else "partial"
    else:
        report["bridge_status"] = "not_applied"

    return {
        "team_a_adjusted": team_a_adjusted,
        "team_b_adjusted": team_b_adjusted,
        "adjusted_teams": adjusted_teams,
        "adjustment_report": report,
    }
