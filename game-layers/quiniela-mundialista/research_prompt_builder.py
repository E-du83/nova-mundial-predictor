from __future__ import annotations


WARNING_TEXT = (
    "Si un dato no esta disponible o no esta verificado, marcar pending_verification "
    "o not_available. No inventar."
)


def build_research_prompt(
    match,
    team_a,
    team_b,
    kickoff_utc=None,
    competition="FIFA World Cup 2026",
    language="es",
    output_format="json",
) -> str:
    kickoff = kickoff_utc or "pending_verification"
    if language != "es":
        language_note = "Answer in the requested language, but keep JSON keys unchanged."
    else:
        language_note = "Responder en espanol, manteniendo las llaves JSON en ingles."
    return f"""NOVA Research Snapshot Request

Partido: {match}
Equipo A: {team_a}
Equipo B: {team_b}
Competicion: {competition}
Kickoff UTC: {kickoff}
Formato de salida: {output_format}

Objetivo:
Preparar un snapshot investigativo previo al partido para revision manual. No
hagas picks ni modifiques probabilidades del modelo.

Investigar solo con fuentes oficiales o deportivas reconocidas:
- fuentes oficiales de competicion, federaciones, clubes o selecciones;
- medios deportivos reconocidos;
- casas o agregadores visibles si las cuotas estan publicamente visibles;
- reportes de lesiones, sanciones y disponibilidad con fuente.

Recopilar:
- alineaciones probables;
- formaciones probables;
- lesiones o ausencias relevantes, con impacto si existe;
- jugadores clave;
- cuotas visibles 1X2 si existen;
- over/under visible si existe;
- forma reciente;
- tendencias BTTS, over 2.5 y clean sheet si estan visibles;
- notas tacticas de cada equipo y del matchup;
- incertidumbres y datos pendientes;
- fecha/hora de captura;
- fuente, source_status y confidence por cada dato relevante.

Reglas:
- No inventar datos.
- No usar resultados futuros.
- No asumir alineaciones confirmadas si solo son probables.
- No usar fuentes sin fecha o sin trazabilidad.
- {WARNING_TEXT}

Devolver JSON siguiendo esta estructura:
{{
  "snapshot_id": "",
  "match": "{match}",
  "team_a": "{team_a}",
  "team_b": "{team_b}",
  "competition": "{competition}",
  "phase": "pending_verification",
  "kickoff_utc": "{kickoff}",
  "captured_at": "",
  "captured_by": "ai_assisted_research_pending_manual_review",
  "snapshot_type": "ai_assisted_research",
  "source_status": "pending_verification",
  "overall_confidence": "insufficient",
  "sources": [],
  "odds_1x2": {{"home": "", "draw": "", "away": "", "source": "", "captured_at": "", "confidence": ""}},
  "over_under": {{}},
  "probable_lineups": {{"team_a": [], "team_b": [], "source": "", "confidence": ""}},
  "formations": {{"team_a": "", "team_b": "", "source": "", "confidence": ""}},
  "injuries_or_absences": {{"team_a": [], "team_b": []}},
  "key_players": {{"team_a": [], "team_b": []}},
  "player_ratings": {{"team_a": {{}}, "team_b": {{}}, "source": "", "confidence": ""}},
  "form_snapshot": {{"team_a": {{}}, "team_b": {{}}}},
  "stats_snapshot": {{"btts": "", "over_2_5": "", "clean_sheet": "", "h2h": "", "corners": "", "cards": ""}},
  "tactical_notes": {{"team_a": "", "team_b": "", "matchup": ""}},
  "data_quality_flags": [],
  "missing_data": [],
  "warnings": [],
  "valid_for_tactical_bridge": false,
  "valid_for_market_weighting": false,
  "valid_for_prediction_context": false
}}

{language_note}
"""
