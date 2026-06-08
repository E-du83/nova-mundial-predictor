import json
from pathlib import Path


PENDING = "pending_real_result"


def load_prediction_history(path: str | Path) -> dict:
    history_path = Path(path)
    if not history_path.exists():
        return {
            "data_status": "prediction_history_evidence_only",
            "source_status": "local_demo_history",
            "notes": (
                "Historial auditable para backtesting y calibracion futura. "
                "No se usa para entrenamiento automatico ni para cambiar picks."
            ),
            "entries": [],
        }
    return json.loads(history_path.read_text(encoding="utf-8"))


def _digits(value) -> int | None:
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    return int(digits) if digits else None


def _result_team_label(value: str, team_a: str, team_b: str) -> str:
    text = str(value).lower()
    if "empate" in text or text == "draw":
        return "Empate"
    if team_a.lower() in text:
        return team_a
    if team_b.lower() in text:
        return team_b
    return PENDING


def _predicted_quinigol_team(recommendation: dict) -> str:
    text = str(recommendation.get("quinigol", ""))
    if "No hay" in text:
        return "No hay"
    for team in recommendation["match"].split(" vs ", 1):
        if team in text:
            return team
    return PENDING


def _goals_for_team(real_result: dict, team: str) -> list[dict]:
    goals = real_result.get("goals", PENDING)
    if not isinstance(goals, dict):
        return []
    value = goals.get(team, [])
    return value if isinstance(value, list) else []


def _first_goal_minute(goals: list[dict]) -> int | None:
    minutes = []
    for goal in goals:
        minute = _digits(goal.get("minute"))
        if minute is not None:
            minutes.append(minute)
    return min(minutes) if minutes else None


def _goal_scorers(real_result: dict) -> list[str]:
    goals = real_result.get("goals", PENDING)
    if not isinstance(goals, dict):
        return []
    scorers = []
    for team, team_goals in goals.items():
        if not isinstance(team_goals, list):
            continue
        for goal in team_goals:
            player = goal.get("player", PENDING)
            minute = goal.get("minute", PENDING)
            scorers.append(f"{team}: {player} {minute}")
    return scorers


def _halftime_fulltime_hit(recommendation: dict, real_result: dict) -> bool | str:
    if real_result.get("status") != "final":
        return PENDING
    team_a, team_b = recommendation["match"].split(" vs ", 1)
    real_ht = _result_team_label(real_result.get("halftime_result", PENDING), team_a, team_b)
    real_ft = _result_team_label(real_result.get("real_result", PENDING), team_a, team_b)
    if PENDING in (real_ht, real_ft):
        return PENDING
    return recommendation["half_time"]["half_time_full_time"] == f"{real_ht}/{real_ft}"


def _quinigol_review(recommendation: dict, real_result: dict) -> dict:
    if real_result.get("status") != "final":
        return {
            "predicted_team": _predicted_quinigol_team(recommendation),
            "team_hit": PENDING,
            "minute_error": PENDING,
            "real_first_goal_minute": PENDING,
            "goal_scorers": [],
        }
    predicted_team = _predicted_quinigol_team(recommendation)
    if predicted_team in (PENDING, "No hay"):
        return {
            "predicted_team": predicted_team,
            "team_hit": predicted_team == "No hay" and not _goal_scorers(real_result),
            "minute_error": PENDING,
            "real_first_goal_minute": PENDING,
            "goal_scorers": _goal_scorers(real_result),
        }
    goals = _goals_for_team(real_result, predicted_team)
    first_minute = _first_goal_minute(goals)
    predicted_minute = _digits(recommendation.get("reference_minute"))
    minute_error = (
        abs(predicted_minute - first_minute)
        if predicted_minute is not None and first_minute is not None
        else PENDING
    )
    return {
        "predicted_team": predicted_team,
        "team_hit": bool(goals),
        "minute_error": minute_error,
        "real_first_goal_minute": first_minute if first_minute is not None else PENDING,
        "goal_scorers": _goal_scorers(real_result),
    }


def _history_status(recommendation: dict) -> str:
    review = recommendation["result_review"]
    if review.get("review_available"):
        return "reviewed"
    if recommendation["real_result"].get("status") == "final":
        return "final_result_recorded"
    return "pre_match_prediction"


def _signature(entry: dict) -> str:
    return "|".join(
        str(entry.get(key, ""))
        for key in (
            "match",
            "history_status",
            "simulation_mode",
            "simulations_used",
            "pick_principal",
            "marcador_recomendado",
            "research_refresh_recommended_action",
            "real_score",
        )
    )


def build_prediction_history_entry(recommendation: dict) -> dict:
    review = recommendation["result_review"]
    real_result = recommendation["real_result"]
    alternatives = recommendation["critical_alternatives"]
    quinigol_review = _quinigol_review(recommendation, real_result)
    critical = alternatives["critical_alternative"]
    tempting = alternatives["tempting_option"]
    refresh = recommendation.get("research_refresh", {})
    alarm = recommendation.get("match_alarm", {})
    entry = {
        "match": recommendation["match"],
        "history_status": _history_status(recommendation),
        "prediction_previous": recommendation["final_recommendation"],
        "simulation_mode": recommendation["simulation_mode"],
        "simulations_used": recommendation["simulations_used"],
        "pick_principal": alternatives["principal_pick"]["score"],
        "marcador_recomendado": recommendation["recommended_score"],
        "alternativa_critica": critical["score"] if critical else "none",
        "opcion_tentadora": tempting["score"] if tempting else "none",
        "quinigol": recommendation["quinigol"],
        "minuto_referencia": recommendation["reference_minute"],
        "rango_probable": recommendation["quinigol_range"],
        "descanso_final": recommendation["half_time"]["half_time_full_time"],
        "tactical_score": recommendation["research_weighting"]["tactical_weighting"]["tactical_score"],
        "confidence": recommendation["adjusted_confidence"],
        "risk": recommendation["friendly_risk"],
        "data_quality_score": recommendation["research_weighting"]["data_quality_score"],
        "research_refresh_status": {
            "required": refresh.get("research_refresh_required", "not_available"),
            "recommended_action": refresh.get("recommended_action", "not_available"),
            "missing_critical_fields": refresh.get("missing_critical_fields", []),
            "missing_optional_fields": refresh.get("missing_optional_fields", []),
            "partial_snapshot_ok_for_final_pick": refresh.get("partial_snapshot_ok_for_final_pick", "not_available"),
            "match_alarm_status": alarm.get("alarm_status", "not_available"),
            "match_status": alarm.get("match_status", "not_available"),
            "minutes_to_kickoff": alarm.get("minutes_to_kickoff", "not_available"),
            "final_refresh_due": alarm.get("final_refresh_due", "not_available"),
        },
        "research_refresh_recommended_action": refresh.get("recommended_action", "not_available"),
        "datos_usados": recommendation["data_used"],
        "datos_faltantes": recommendation["missing_data"],
        "real_score": real_result.get("real_score", PENDING),
        "real_result": real_result.get("real_result", PENDING),
        "real_status": real_result.get("status", "pending"),
        "post_match_review": review.get("summary", PENDING),
        "acierto_ganador": review.get("winner_hit", PENDING),
        "acierto_marcador_exacto": review.get("exact_score_hit", PENDING),
        "acierto_descanso_final": _halftime_fulltime_hit(recommendation, real_result),
        "acierto_quinigol_equipo": quinigol_review["team_hit"],
        "error_minuto_quinigol": quinigol_review["minute_error"],
        "quinigol_real_first_goal_minute": quinigol_review["real_first_goal_minute"],
        "goleadores_reales": quinigol_review["goal_scorers"],
        "learning_note": review.get("learning_note", real_result.get("learning_note", PENDING)),
        "history_note": "Evidencia guardada para backtesting/calibracion futura; no se usa para entrenamiento automatico.",
    }
    entry["signature"] = _signature(entry)
    return entry


def record_prediction_history(recommendations: list[dict], path: str | Path) -> dict:
    history_path = Path(path)
    history = load_prediction_history(history_path)
    entries = history.setdefault("entries", [])
    existing = {entry.get("signature") for entry in entries}
    added = 0
    for recommendation in recommendations:
        entry = build_prediction_history_entry(recommendation)
        if entry["signature"] in existing:
            continue
        entries.append(entry)
        existing.add(entry["signature"])
        added += 1
    history["entry_count"] = len(entries)
    history["last_update_status"] = f"added {added} entries"
    history_path.write_text(json.dumps(history, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return history


def summarize_prediction_history(history: dict) -> dict:
    entries = history.get("entries", [])
    matches = {entry.get("match") for entry in entries}
    real_result_matches = {
        entry.get("match")
        for entry in entries
        if entry.get("real_status") == "final"
    }
    reviewed_matches = {
        entry.get("match")
        for entry in entries
        if entry.get("history_status") == "reviewed"
    }
    pending_matches = {
        entry.get("match")
        for entry in entries
        if entry.get("real_status") != "final"
    }
    learning_matches = {
        entry.get("match")
        for entry in entries
        if entry.get("learning_note") not in (None, "", PENDING, "pending_manual_input")
    }
    return {
        "prediction_saved_count": len(matches),
        "real_result_count": len(real_result_matches),
        "reviewed_count": len(reviewed_matches),
        "pending_result_count": len(pending_matches),
        "learning_count": len(learning_matches),
        "history_entry_count": len(entries),
    }
