import json
from pathlib import Path


DEFAULT_CONTEXT_STATUS = "pre_tournament_context"


def load_fixture_contexts(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _match_key(team_a: str, team_b: str) -> tuple[str, str]:
    return team_a.strip().lower(), team_b.strip().lower()


def _find_fixture(fixtures_data: dict, team_a: str, team_b: str) -> dict | None:
    requested = _match_key(team_a, team_b)
    requested_reverse = _match_key(team_b, team_a)

    for fixture in fixtures_data.get("fixtures", []):
        current = _match_key(fixture["team_a"], fixture["team_b"])
        if current in (requested, requested_reverse):
            return fixture
    return None


def _matchday_flags(matchday: str) -> dict:
    return {
        "is_first_group_match": matchday in ("jornada_1", "1", 1),
        "is_second_group_match": matchday in ("jornada_2", "2", 2),
        "is_third_group_match": matchday in ("jornada_3", "3", 3),
    }


def _pressure_estimate(matchday: str, context_status: str) -> str:
    if context_status == DEFAULT_CONTEXT_STATUS:
        return "media_pre_torneo"
    if matchday in ("jornada_3", "3", 3):
        return "alta"
    if matchday in ("jornada_2", "2", 2):
        return "media"
    return "normal"


def _rotation_risk(matchday: str, context_status: str) -> str:
    if context_status == DEFAULT_CONTEXT_STATUS:
        return "pendiente_tabla_real"
    if matchday in ("jornada_3", "3", 3):
        return "medio_alto"
    return "bajo_medio"


def _goal_difference_importance(matchday: str, context_status: str) -> str:
    if context_status == DEFAULT_CONTEXT_STATUS:
        return "media_pre_torneo"
    if matchday in ("jornada_2", "jornada_3", "2", "3", 2, 3):
        return "alta"
    return "media"


def build_tournament_context(
    team_a: str,
    team_b: str,
    fixtures_data: dict | None = None,
) -> dict:
    fixture = _find_fixture(fixtures_data or {}, team_a, team_b) if fixtures_data else None
    if fixture is None:
        fixture = {
            "match": f"{team_a} vs {team_b}",
            "team_a": team_a,
            "team_b": team_b,
            "phase": "fase de grupos",
            "group": "pending_real_data",
            "matchday": "pending_real_schedule",
            "match_order": "pending_real_schedule",
            "venue": "pending_real_venue",
            "context_status": DEFAULT_CONTEXT_STATUS,
        }

    matchday = fixture.get("matchday", "pending_real_schedule")
    context_status = fixture.get("context_status", DEFAULT_CONTEXT_STATUS)
    flags = _matchday_flags(matchday)

    notes = [
        "No se inventan standings ni necesidad real de puntos.",
        "El contexto usa estado pre_tournament_context hasta integrar calendario y tabla real.",
    ]

    return {
        "phase": fixture.get("phase", "fase de grupos"),
        "group": fixture.get("group", "pending_real_data"),
        "matchday": matchday,
        "match_order": fixture.get("match_order", "pending_real_schedule"),
        "venue": fixture.get("venue", "pending_real_venue"),
        "is_first_group_match": flags["is_first_group_match"],
        "is_second_group_match": flags["is_second_group_match"],
        "is_third_group_match": flags["is_third_group_match"],
        "pressure_estimate": _pressure_estimate(matchday, context_status),
        "rotation_risk": _rotation_risk(matchday, context_status),
        "goal_difference_importance": _goal_difference_importance(matchday, context_status),
        "context_status": context_status,
        "context_notes": notes,
        "missing_data": [
            "FIFA schedule final",
            "tabla de puntos real",
            "orden oficial del partido",
            "necesidad real de puntos por equipo",
        ],
    }
