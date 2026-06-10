# Data Requirements - Quiniela Mundialista v1.2

El Bloque Quiniela Mundialista v1.2 puede funcionar con el baseline actual,
pero su maxima precision depende de datos reales adicionales. Esta tabla separa
que esta disponible hoy, que usa el baseline, que queda pendiente y cual seria
el impacto esperado.

| Dato | Disponible actualmente | Baseline actual | Pendiente de API/dato real | Impacto esperado en la prediccion |
| --- | --- | --- | --- | --- |
| FIFA schedule | Parcial | Grupos reales cargados, sin calendario final | Calendario FIFA oficial con fecha, hora y orden | Define jornada, presion, descanso y sede |
| Sedes | No | `pending_real_venue` | Sede oficial por partido | Activa capa clima/adaptacion |
| Clima historico | No | `pending_real_data` | Normales historicas por ciudad/sede/mes | Ajusta riesgo de calor, humedad y ritmo |
| Elo | Parcial | Elo/NOVA en baseline v1 | Elo completo y actualizado | Mejora fuerza relativa |
| Ranking FIFA | Si | Ranking FIFA en baseline v1 | Actualizaciones oficiales | Ajusta fortaleza base |
| Rating NOVA | Si | `nova_strength_rating_v1` | Calibracion continua | Mejora comparacion de equipos |
| Forma reciente | Parcial | Valor neutral `form=1.0` | Partidos recientes ponderados | Ajusta dinamica real prepartido |
| xG a favor | No | xG estimado por formula Core | xG real por seleccion | Mejora goles esperados |
| xG en contra | No | Defensa proxy del baseline | xGA real por seleccion | Mejora riesgo defensivo |
| Goles reales | Parcial | No integrado al pick final | Historial reciente competitivo | Calibra ataque/defensa |
| Calidad de rivales | No | No integrada | Fuerza de rivales recientes | Evita sobrevalorar rachas faciles |
| Formaciones | No | No integrada | Formacion probable/confirmada | Ajusta estilo y volumen ofensivo |
| Alineaciones | No | No integrada | XI probable y XI confirmado | Alto impacto en goles y riesgo |
| Ratings jugadores | Parcial | Seed local con ratings reales y `replacement_level_estimate` | Rating real verificado por jugador clave faltante | Activa fuerza por linea y ajustes xG/Quinigol |
| Roles jugadores | Parcial | `player_ratings_seed.json` con roles manuales | Confirmacion de rol/posicion actual | Mejora lectura tactica y set pieces |
| Lesiones | No | No integrada | Lesiones verificadas | Ajusta disponibilidad y riesgo |
| Sanciones | No | No integrada | Suspendidos oficiales | Ajusta disponibilidad |
| Estilo tactico | Parcial | `style_note` descriptivo baseline | Modelo tactico real por equipo | Mejora matchup de estilos |
| Presion | Parcial | `pre_tournament_context` | Tabla y necesidad real de puntos | Ajusta agresividad y rotacion |
| Bloque defensivo | No | Defensa proxy | Datos tacticos defensivos | Ajusta under/over y Quinigol |
| Transiciones | No | No integrada | Datos de ataque/defensa en transicion | Mejora matchups contra estilos directos |
| Balon parado | No | No integrada | xG y goles de pelota parada | Mejora picks de partidos cerrados |
| Rendimiento vs estilos similares | No | No integrada | Historial segmentado por estilo rival | Mejora comparacion contextual |
| Cuotas de mercado | No en esta capa | Pendiente | Odds 1X2 y marcadores | Contrasta modelo vs mercado |
| Movimiento de cuotas | No | Pendiente | Historial de line movement | Detecta cambios por noticias |
| Over/under | Parcial | Core calcula under 2.5/3.5 | Mercado real over/under | Mejora riesgo de goles |
| Ambos anotan | Parcial | Core calcula BTTS yes | Mercado real BTTS | Mejora Quinigol y marcador |
| Historico de goles por minuto | No | Estimacion probabilistica por xG | Distribucion real por equipo | Mejora minuto/rango Quinigol |
| Contexto de grupo | Parcial | Grupo real + pre_tournament_context | Tabla, calendario y escenarios | Ajusta presion, rotacion y diferencia de goles |
| Necesidad de puntos | No | No se inventa | Standings reales por jornada | Alto impacto en jornada 2/3 |
| Descanso | No | Pendiente calendario | Dias de descanso por equipo | Ajusta fatiga y rotacion |
| Backtesting y calibracion | Parcial | Validaciones simples | Backtesting historico por competicion | Ajusta pesos del motor final |

## Estado actual

- Disponible actualmente: equipos baseline v1, grupos reales, ranking FIFA,
  rating NOVA, probabilidades Core, top scores y xG estimado por formula.
- Baseline actual: suficiente para demos y recomendaciones iniciales.
- Pendiente de API/dato real: calendario completo, sedes, clima historico,
  lesiones, alineaciones, ratings reales de jugadores, cuotas, xG real y tabla
  por jornada.
- Regla operativa: cuando un dato no existe, el motor debe marcarlo como
  `pending_real_data` o `pre_tournament_context`; no debe inventarlo.

## Fuentes sugeridas v1 - open source y amistosos

| Dato | Fuente sugerida | Gratis | Estado | Impacto en prediccion |
| --- | --- | --- | --- | --- |
| Calendario FIFA | FIFA oficial | Si | official / pendiente snapshot | Define fecha, fase, jornada y horarios |
| Sedes | FIFA oficial | Si | pending_real_data | Permite clima y adaptacion |
| Grupos | FIFA oficial + `data/worldcup_2026_real_groups.json` | Si | disponible baseline | Contexto de fase de grupos |
| Fixtures World Cup JSON | openfootball/worldcup.json | Si | pending_manual_snapshot | Fuente abierta alternativa para fixtures |
| Rating selecciones | World Football Elo Ratings | Si | open_web_data / snapshot parcial | Mejora fuerza relativa |
| Historico Elo | JGravier/soccer-elo | Si | open_source_repo | Backtesting y calibracion historica |
| Clima historico | Open-Meteo | Si | free_api / pending coordinates | Ajusta calor, humedad y ritmo |
| Cuotas 1X2 | The Odds API o snapshot manual | Parcial | optional_limited_api / pending_manual_snapshot | Contrasta mercado vs modelo |
| Datasets football | GitHub football datasets | Si | reference_registry | Descubrimiento de fuentes complementarias |
| Amistosos del domingo | 365Scores screenshot/manual del usuario | Si, manual | manually_verified_from_user_screenshot | Permite prueba real sin API pagada |
| Horario amistoso | Snapshot manual o fuente oficial del partido | Si, manual | pending_or_manual | Evita confundir partidos ya jugados |
| Odds amistoso | Snapshot manual visible | Si, manual | pending_manual_snapshot | Lectura de mercado si el usuario aporta cuotas |
| Alineaciones amistoso | Fuente oficial / manual verificada | Si, manual | pending_real_data | Alto impacto por rotacion |
| Lesiones amistoso | Fuente oficial / manual verificada | Si, manual | pending_real_data | Ajusta riesgo y disponibilidad |
| Sede amistoso | Fuente oficial / manual verificada | Si, manual | pending_real_data | Necesaria para clima historico |
| Snapshot manual 365Scores | Usuario copia datos visibles | Si, manual | manual_snapshot_required | Permite cuotas, lineups y stats sin scraping |
| Ratings jugadores clave | Snapshot manual verificado/local | Si, manual | parcial | Rating real pesa mas; replacement estimate pesa menos |
| Formaciones amistoso | Fuente oficial / manual verificada | Si, manual | pending_manual_input | Permite tactical weighting numerico |
| Tactical score | Derivado local de formacion, roles y fuerza por linea | Si | activo con advertencia si falta formacion | Ajusta confianza/riesgo y sirve como desempate conservador |
| Tactical Input Bridge v1 | Lineups, ratings reales, formaciones, forma y ausencias verificadas | Si | activo si hay datos confiables suficientes | Ajusta copias temporales del team dict antes de `simulate_match()` |
| World Cup 2022 prematch dataset | Fixture/contexto historico antes del kickoff | Si | partial_prematch_dataset | Base para behavioral_backtest sin resultados mezclados |
| World Cup 2022 prematch profiles | Perfil historico por equipo antes del kickoff | Si | neutral_defaults_behavioral_only | Permite evaluar comportamiento de la muestra sin usar baseline 2026 |
| World Cup 2022 profile audit | Auditoria de fuentes, defaults y bloqueos | Si | warning_neutral_defaults | Evita ocultar perfiles no verificados y separa behavioral de accuracy real |
| World Cup 2022 results dataset | Resultados historicos separados | Si | partial_results_dataset | Solo evaluacion posterior, nunca input prematch |
| Data leakage guard 2022 | Auditoria local del dataset prematch | Si | cleared si no hay leakage critico | Bloquea si aparecen resultados, futuro o baseline 2026 |
| Quinigol timing report 2022 | Equipo/minuto/rango del primer gol | Si | small_sample_behavioral_only | Detecta sesgo temprano/tardio sin recalibrar automaticamente |
| Resultado real amistoso | Fuente oficial post-partido | Si | pending_real_result | Permite comparar pick vs resultado |
| Historial predicciones | `prediction_history.json` | Si | evidencia local | Guarda prediccion, resultado, revision y aprendizaje para backtesting futuro |
| Reporte calibracion amistosos | `friendly_calibration_report.json` | Si | evidencia local | Resume aciertos, errores, BTTS, Quinigol y patrones para backtesting futuro |
| Notas calibracion | `calibration_notes.json` | Si | evidencia local | Guarda patrones acumulativos y advertencia de muestra pequena |
| Research refresh | Auditoria local de snapshots manuales | Si | activo | Marca si faltan 3+ datos criticos y recomienda refresco antes del pick final |
| Match alarm | `kickoff_time_utc` del snapshot manual | Si | activo si hay hora UTC | Detecta ventana de 60 minutos, near kickoff, live/final o kickoff pendiente |
| Descanso/final | Derivado de Core + Quinigol | Si | parcial | Agrega lectura HT/FT sin nuevo motor Core |
| Robustez pick | Derivado de top_scores Core | Si | disponible si hay top_scores | Detecta pick fragil y alerta de empate |
| Alternativa critica | Derivado de top_scores Core | Si | disponible si hay top_scores | Advierte cuando el pick #2 esta muy cerca |
| Opcion tentadora | Derivado de top_scores y reglas de puntos | Si | disponible si hay top_scores | Marca opcion de mas recompensa con mayor riesgo |
| Lesiones de impacto | Fuente oficial / manual verificada | No | pending_real_data | Solo impactan si injury_impact es medium/high/critical |
| Coordenadas sedes | FIFA/venue official/manual verificado | Si | pending_real_data | Activa Open-Meteo historico |
| Modo simulacion final | Configuracion local | Si | disponible | Permite quick, standard o final 1M |
| Group stage fixture context | `group_stage_fixture_context.json` | Si | manual_snapshot_required | Permite fase de grupos completa cuando exista fixture oficial local |
| World Cup 2026 group structure | `worldcup_2026_group_structure.json` | Si | pending_group_draw | Define 48 equipos, 12 grupos, 72 partidos de grupos y 104 totales sin inventar sorteo |
| World Cup 2026 match slots | `worldcup_2026_match_slots.json` | Si | structural_placeholder | Crea 72 slots estables `WG-A-01` a `WG-L-06` |
| World Cup 2026 group fixture | `worldcup_2026_group_stage_fixture.json` | Si | pending_official_fixture | Guarda fixture placeholder/parcial/confirmado separado de resultados |
| World Cup 2026 fixture validation | `worldcup_2026_fixture_validation_report.json` | Si | cleared_placeholder | Valida conteos, grupos A-L, IDs, UTC/sedes pendientes y no cruces ficticios oficiales |
| Backtesting manifest | `backtesting_manifest.json` | Si | foundation_ready | Lista datasets, leakage risk e integracion pendiente |
| Report builder | `report_builder.py` | Si | foundation_ready | Genera reportes por partido sin modificar picks |
| System self audit | `system_self_audit.py` | Si | foundation_ready | Evalua readiness, riesgos, sesgo y sobreajuste |

## Reglas de activacion real

- `requires_api_key: false` significa que la fuente no requiere llave y es
  preferible para pruebas gratis.
- `requires_api_key: true` significa que la fuente puede ser opcional, pero no
  se usara como dependencia obligatoria si implica pago.
- Para friendly test solo se simulan partidos con ambos equipos clasificados al
  Mundial 2026 y presentes en `worldcup_2026_real_teams_baseline_v1.json`.
- Open-Meteo se usara para clima historico por sede, no clima del dia.
- openfootball y FIFA se usaran para calendario, sedes y fixtures cuando exista
  snapshot/verificacion.
- World Elo se usara para fuerza solo si hay CSV local verificado.
- 365Scores se usara solo como snapshot manual verificado, no scraping
  automatico. Algunos datos visibles pueden venir de proveedores premium, asi
  que no se asume API gratis.
- Los ratings de jugadores deben venir de una fuente local verificada o de
  snapshot manual trazable. Si quedan como `replacement_level_estimate`, el
  motor aplica peso conservador y mantiene advertencia de dato faltante.
- El weighting de alineacion queda `incomplete` cuando faltan demasiados ratings
  o no hay XI/formacion probable. En ese estado el pick del Core no cambia.
- `friendly_test_results.json` registra resultados reales solo para revision
  post-partido. No entrena ni recalibra automaticamente el Core.
- `prediction_history.json` registra ciclos completos de prediccion y revision.
  No entrena automaticamente ni corrige picks actuales; conserva evidencia para
  calibracion futura y backtesting manual.
- Desde Hardening Foundation v1, `prediction_history.json` debe guardar, cuando
  este disponible, `probabilities_1x2`, `top_scores`, `expected_goals`,
  `simulation_mode`, `simulations`, `quinigol_policy_applied`,
  `quinigol_team`, `quinigol_minute`, `quinigol_range`, `data_quality_score`,
  `research_refresh_status` y `tactical_score`.
- Desde Tactical Input Bridge v1, `prediction_history.json` tambien puede
  guardar `tactical_input_bridge_status`, flags de ajustes aplicados,
  `adjustment_report_summary`, `adjusted_expected_goals` y
  `baseline_mutated=false`.
- `friendly_calibration_report.json` y `calibration_notes.json` guardan
  aprendizaje evaluativo: empate subestimado, gol tardio rival/BTTS
  subestimado, minuto Quinigol fuera de rango, fragilidad validada y validacion
  de modo final vs standard. No entrenan automaticamente ni cambian picks.
- Tres amistosos son una muestra muy pequena. Sirven para detectar warnings y
  preparar backtesting, no para recalibrar agresivamente pesos del Core.
- `group_stage_fixture_context.json` no debe inventar cruces, sedes, fechas ni
  horarios. Si no existe fixture oficial completo local, debe quedar como
  `manual_snapshot_required`.
- `worldcup_2026_match_slots.json` debe mantener exactamente 72 slots de fase
  de grupos. Mientras no exista fixture oficial local, los equipos quedan como
  `pending_group_draw`, y `kickoff_utc` / `venue` quedan como
  `pending_official_fixture`.
- El fixture 2026 puede estar en tres estados: `structural_placeholder`,
  `partial_fixture` o `confirmed_fixture`. Solo los partidos con
  `status=confirmed_fixture`, equipos concretos, UTC valido y sede verificada
  pueden simularse como partidos reales.
- El loader 2026 debe separar `fixture_structure`, `confirmed_fixture` y
  `generated_placeholder_fixture`. Los resultados futuros nunca deben mezclarse
  dentro del fixture prematch.
- World Elo solo pesa fuerte si existe snapshot local con `team`, `elo`, `rank`,
  `source`, `date_collected` y `notes`.
- Open-Meteo solo construye consultas historicas gratis sin API key; si faltan
  coordenadas o clima real, el dato queda pendiente.
- El Mundial 2022 debe usarse solo con blind test separado y guardas de data
  leakage. No mezclarlo con datos posteriores al partido.
- Los perfiles prematch 2022 solo pueden usar datos disponibles antes del
  kickoff. Si no hay fuente historica verificable, deben quedar como
  `uses_neutral_defaults=true` y `valid_for_true_prediction_accuracy=false`.
- Los perfiles 2022 con defaults neutrales pueden habilitar un
  `behavioral_backtest`, pero no claims de precision del modelo ni
  recalibracion automatica.
- Quinigol Timing 2022 debe reportar muestra, equipo del primer gol, error de
  minuto, sesgo temprano/tardio y acierto de rango. Con 8 partidos debe quedar
  como muestra insuficiente para recalibrar.
- `research_refresh_engine.py` no busca datos por su cuenta. Solo audita el
  snapshot manual y marca `research_refresh_required`, faltantes criticos,
  faltantes opcionales y `recommended_action`.
- `match_alarm_engine.py` solo usa `kickoff_time_utc`; si falta ese dato,
  devuelve `match_status: unknown` y `needs_kickoff_time`.
- Las senales de peso alto pueden ajustar pick, confianza o riesgo. Las de peso
  medio ajustan confianza/riesgo o warnings. Las de peso bajo solo son nota y no
  pueden cambiar el pick.
- Lesiones solo pesan si tienen `injury_impact` igual a `medium`, `high` o
  `critical`; lesiones sin impacto definido quedan como dato pendiente.

## Tactical Input Bridge v1

El bridge separa dos usos de datos:

- contexto explicativo: notas de research, riesgo, confianza, fragilidad y
  advertencias;
- ajuste real de simulacion: modificadores pequenos aplicados a copias
  temporales del team dict antes de llamar al Core.

Para activar ajustes numericos se necesita evidencia confiable:

- lineups probables para ambos equipos;
- al menos 7 jugadores con ratings reales por equipo;
- formaciones probables de ambos equipos;
- forma confiable entre `0.80` y `1.20`;
- ausencias relevantes con jugador clave, impacto y rol claros.

El bridge no modifica `src/match_simulator.py`, no toca
`data/worldcup_2026_real_teams_baseline_v1.json`, no usa APIs pagadas, no hace
scraping y no inventa datos faltantes. Los multiplicadores estan capeados para
evitar distorsiones: lineup maximo `0.82` a `1.18`, tactica `0.94` a `1.06`, y
ausencias relevantes se mantienen en impactos pequenos. Si faltan datos, el
resultado debe quedar en `bridge_status=not_applied` o `partial` y el reporte
debe explicar que no se aplico ajuste numerico.

## World Cup 2022 Historical Blind Test v1

El blind test 2022 usa archivos separados bajo
`historical_blind_tests/worldcup_2022/`:

- `worldcup_2022_prematch_dataset.json`: solo informacion permitida antes del
  partido, con `cutoff_datetime`, `source_status`, `allowed_context` y
  `unavailable_context`.
- `worldcup_2022_results_dataset.json`: marcador real, ganador, BTTS, primer
  gol y timeline, solo para evaluacion posterior.
- `worldcup_2022_blind_test_config.json`: declara `mode=behavioral_backtest`,
  `generated_after_event=true` y que no sirve para precision predictiva real.
- `worldcup_2022_data_leakage_audit.json`: salida del guard.
- `worldcup_2022_team_profiles_prematch.json`: perfiles 2022 para los equipos
  de la muestra. Los perfiles actuales son minimos y usan defaults neutrales
  auditados cuando falta dato historico verificable.
- `worldcup_2022_profile_sources_audit.json`: resume perfiles creados,
  verificados, pendientes de verificacion, defaults neutrales y bloqueos.
- `worldcup_2022_blind_test_report.json`: reporte de readiness y metricas.
- `worldcup_2022_quinigol_timing_report.json`: metricas de equipo/minuto/rango
  para primer gol en modo behavioral.

`generated_after_event=true` significa que las corridas actuales ocurren despues
del Mundial 2022. Por eso cualquier metrica queda como behavioral/backtest de
comportamiento, no como prediccion historica real previa.

Data leakage incluye mezclar en prematch el resultado, marcador, campeon,
finalistas, posiciones finales, narrativa posterior, camino real de
eliminatorias o informacion de partidos futuros. Tambien incluye usar
`data/worldcup_2026_real_teams_baseline_v1.json` como si representara perfiles
2022. Ese baseline es de otro momento historico y contaminaria la evaluacion.

Quinigol Timing Metrics debe calcularse solo cuando haya predicciones validas y
datos de primer gol: acierto de equipo, error promedio/mediano de minuto, sesgo
temprano o tardio y acierto de rango. No recalibra pesos automaticamente.

Estado actual del bloque D:

- equipos perfilados en la muestra 2022: 10;
- perfiles con fuente fuerte verificada: 0;
- perfiles con defaults neutrales auditados: 10;
- partidos evaluables como behavioral backtest: 8;
- partidos evaluados con defaults neutrales: 8;
- estado de precision predictiva real: no valido;
- recomendacion Quinigol Timing: muestra insuficiente, no recalibrar.

Falta para un backtest fuerte:

- verificar el fixture completo 2022 y todos los resultados;
- cargar perfiles prematch 2022 reales con fuentes y cutoff;
- tener predicciones o simulaciones generadas solo con esos perfiles;
- mantener el leakage guard en `cleared`;
- evaluar por fase antes de ampliar a otros torneos.

## Hardening Foundation v1

- SQLite local (`*.sqlite3`, `*.sqlite`, `*.db`) es artefacto runtime y no debe
  versionarse. Si `nova_mundial_predictor.sqlite3` aparece trackeado, usar
  `git rm --cached nova_mundial_predictor.sqlite3` para quitarlo del indice sin
  borrar el archivo local.
- Caches Python (`__pycache__/`, `*.pyc`, `*.pyo`), logs, `.env`, llaves y
  respaldos temporales deben quedar fuera de Git.
- Los tests minimos de scoring se ejecutan con
  `python -B tests/test_scoring_rules.py`.
- Quinigol tiene politica definitiva: `0-0` implica `No hay gol`; marcador con
  goles implica equipo y minuto obligatorios; el rango es contexto y el minuto
  es el pick registrado.
- Los reportes JSON no deben reescribirse si solo cambia `generated_at`.
- Persistencia SQLite completa queda pendiente para siguientes bloques, pero el
  schema ya admite columnas opcionales compatibles para probabilidades 1X2,
  Quinigol, fase, modo, simulaciones y calidad de datos.
- Este bloque no recalibra pesos, no toca el baseline mundialista y no cambia
  el Core predictivo salvo migracion compatible de almacenamiento.
