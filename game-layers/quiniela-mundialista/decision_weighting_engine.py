PENDING = "pending_manual_input"


def _has_value(value) -> bool:
    return value not in (None, "", PENDING, "pending_real_data", "pending_real_result")


def _signal(name: str, value, impact: str, source: str, can_change_pick: bool) -> dict:
    return {
        "name": name,
        "value": value,
        "impact": impact,
        "source": source,
        "can_change_pick": can_change_pick,
    }


def _top_scores_text(robustness: dict) -> str:
    scores = robustness.get("top_scores", [])
    if not scores:
        return "pending_real_data"
    return "; ".join(
        f"{item['score']} ({round(item['probability'] * 100, 2)}%)"
        for item in scores[:5]
    )


def build_decision_weighting(recommendation: dict) -> dict:
    weighting = recommendation["research_weighting"]
    robustness = recommendation["robustness"]
    half_time = recommendation["half_time"]

    high = [
        _signal(
            "fuerza relativa / rating",
            (
                f"rating coverage {weighting['rating_coverage']}% | "
                f"real {weighting['real_rating_coverage']}%"
            ),
            "ajusta confianza/riesgo y fuerza por linea",
            "player_ratings_seed.json + lineup_strength_engine",
            True,
        ),
        _signal(
            "xG proyectado",
            f"team_a {weighting['xg_adjustment_team_a']} | team_b {weighting['xg_adjustment_team_b']}",
            "ajusta lectura de goles esperados",
            "Core + research_weighting_engine",
            True,
        ),
        _signal(
            "top marcadores simulados",
            _top_scores_text(robustness),
            "define alternativa critica, robustez y alerta de empate",
            "Core top_scores",
            True,
        ),
        _signal(
            "probabilidades 1X2 / mercado",
            recommendation.get("market_probabilities_visible", PENDING),
            "contrasta Core; puede ajustar confianza/riesgo",
            "manual_match_snapshots.json",
            True,
        ),
        _signal(
            "over/under",
            recommendation.get("over_under_visible", PENDING),
            "ajusta lectura de goles si existe",
            "manual_match_snapshots.json",
            True,
        ),
        _signal(
            "BTTS / goles promedio",
            recommendation.get("stats_visible", PENDING),
            "ajusta lectura de goles si existe; queda pendiente si no hay muestra clara",
            "manual_match_snapshots.json",
            True,
        ),
        _signal(
            "alineacion/formacion probable",
            recommendation.get("lineups_visible", PENDING),
            "ajusta fuerza por linea si existe; si esta pendiente solo queda como dato faltante",
            "manual_match_snapshots.json",
            True,
        ),
        _signal(
            "contexto del partido",
            recommendation["match_type"],
            "amistoso reduce certeza y sube riesgo",
            "friendly_context_engine",
            True,
        ),
    ]

    medium = [
        _signal(
            "H2H / stats snapshot",
            recommendation.get("stats_visible", PENDING),
            "activa advertencias si es relevante",
            "manual_match_snapshots.json",
            False,
        ),
        _signal(
            "rotacion / amistoso",
            recommendation.get("friendly_risk", PENDING),
            "ajusta riesgo y robustez",
            "friendly_context_engine",
            False,
        ),
        _signal(
            "descanso/final",
            half_time["half_time_full_time"],
            "sirve para apuesta prepartido o lectura de ritmo",
            "half_time_engine",
            False,
        ),
        _signal(
            "lesiones de impacto medio/alto/critico",
            recommendation["research"].get("injuries_visible", PENDING),
            "solo ajusta confianza/riesgo si injury_impact es medium, high o critical",
            "manual_match_snapshots.json",
            False,
        ),
    ]

    low = [
        _signal(
            "predicciones editoriales / notas externas",
            "; ".join(recommendation["research"].get("external_market_notes", [])) or PENDING,
            "solo nota; no cambia pick",
            "manual research snapshot",
            False,
        ),
        _signal(
            "comentarios generales",
            recommendation.get("market_reading", PENDING),
            "solo contexto salvo que este respaldado por mercado cuantificado",
            "research_intelligence_engine",
            False,
        ),
    ]

    missing_critical = list(weighting.get("missing_critical_data", []))
    if not _has_value(recommendation.get("lineups_visible")):
        missing_critical.append("alineaciones probables verificadas")

    pick_fragile = recommendation["robustness"]["pick_robustness"] in ("fragil", "cauteloso")
    draw_warning = recommendation["robustness"]["draw_warning"]
    market_alignment = weighting["market_alignment"]

    if pick_fragile or draw_warning or market_alignment == "market_weakens_core_pick":
        quiniela = (
            "Usar pick principal, pero revisar alternativa critica; evitar opcion tentadora salvo estrategia agresiva."
        )
    else:
        quiniela = "Usar pick principal como seleccion base de quiniela."

    if pick_fragile or draw_warning:
        apuesta = (
            "Preferir mercados conservadores: ganador/doble oportunidad, under/over o descanso/final; recalcular si cambian alineaciones."
        )
    else:
        apuesta = (
            "Pick principal viable prepartido si mercado y alineacion siguen favorables; recalcular ante cambios de ultimo momento."
        )

    return {
        "high_weight_signals": high,
        "medium_weight_signals": medium,
        "low_weight_signals": low,
        "missing_critical_data": sorted(set(missing_critical)),
        "recommended_use": {
            "quiniela": quiniela,
            "apuesta_prepartido": apuesta,
        },
        "decision_notes": [
            "Datos de peso bajo no pueden cambiar el pick final.",
            "Mercado y predicciones externas contrastan al Core, no lo reemplazan.",
            "Lesiones solo deben impactar si injury_impact es medium, high o critical.",
        ],
    }


def format_signal_group(title: str, signals: list[dict]) -> str:
    if not signals:
        return f"{title}: none"
    parts = [
        f"{signal['name']}={signal['value']} ({signal['impact']})"
        for signal in signals
    ]
    return f"{title}: " + "; ".join(parts)


def format_decision_weighting_lines(decision: dict) -> list[str]:
    return [
        format_signal_group("Senales de peso alto usadas", decision["high_weight_signals"]),
        format_signal_group("Senales de peso medio usadas", decision["medium_weight_signals"]),
        format_signal_group("Senales de peso bajo / solo nota", decision["low_weight_signals"]),
        "Datos faltantes criticos: "
        + (
            "; ".join(decision["missing_critical_data"])
            if decision["missing_critical_data"]
            else "none"
        ),
        f"Uso recomendado quiniela: {decision['recommended_use']['quiniela']}",
        f"Uso recomendado apuesta prepartido: {decision['recommended_use']['apuesta_prepartido']}",
        "Notas decision: " + "; ".join(decision["decision_notes"]),
    ]
