# Quiniela Mundialista v1.2

Esta carpeta agrega una capa especializada de juego para una quiniela real del
Mundial 2026. No reemplaza ni duplica el Core principal del proyecto.

La quiniela real se llena una sola vez. Por eso v1.2 agrega un motor de
`Final Pick`: evalua internamente los escenarios conservador, balanceado y
agresivo, pero entrega una sola recomendacion final clara para jugar.

Tambien incluye el bloque **Datos Open Source + Friendly Test Domingo v1** para
registrar fuentes gratis y correr una prueba real con amistosos internacionales
sin pagar APIs y sin inventar datos.

El bloque **Real Data Activation + Manual Match Snapshot v1** agrega filtros
para usar solo amistosos con ambos equipos en baseline mundialista, snapshots
manuales de paginas como 365Scores, sedes semilla y modos de simulacion.

El bloque **Research Snapshot v1** permite guardar investigacion publica manual
para partidos amistosos, incluyendo fuentes usadas, cuotas americanas,
referencias decimales, over/under, probabilidades externas y advertencias de
mercado. Estos datos solo ajustan lectura de riesgo/confianza; no reemplazan el
pick generado desde el Core.

El bloque **Player Rating + Lineup Weighting v1** convierte jugadores y
alineaciones en variables medibles. Si un jugador no tiene rating real en la
base local, se marca como `missing_rating_required` y no recibe peso matematico
fuerte.

El bloque **Match Intelligence Final Test v1** agrega descanso/final, robustez
del pick, alerta de empate y revision contra resultado real. Los resultados
reales se usan para evaluacion y aprendizaje manual, no para entrenamiento
automatico.

El bloque **Decision Weighting + Critical Alternative Layer v1** separa pick
principal, alternativa critica y opcion tentadora. Tambien clasifica las senales
por peso para decidir que sirve para quiniela y que sirve para apuesta
prepartido.

El bloque **Research Refresh + Match Alarm Layer v1** audita si un partido
activo necesita refresco manual antes del pick final y calcula la ventana de
kickoff con `kickoff_time_utc`. No usa APIs pagadas, no hace scraping y no
inventa datos: si faltan cuotas, alineaciones, formaciones, ratings o resultado
real, los deja como pendientes explicitos.

El bloque **Friendly Results Calibration + Data Completion Foundation v1**
cierra la prueba amistosa inicial con Morocco vs Norway, Colombia vs Jordan y
Netherlands vs Uzbekistan. Guarda metricas, patrones y notas evaluativas para
backtesting futuro. No entrena automaticamente, no toca el Core y no recalibra
fuerte porque tres partidos son una muestra demasiado pequena.

El bloque **Data Completion + Backtesting Foundation v1** prepara la entrada de
datos reales para fase de grupos, reportes por partido y backtesting futuro.
Los clientes de datos son offline-first: cargan snapshots locales o construyen
URLs, pero no hacen scraping agresivo ni dependen de APIs pagadas. Si falta un
dato, queda como `pending_real_data`, `manual_snapshot_required`,
`pending_manual_input` o `not_available_free`.

El bloque **Hardening Foundation v1** agrega limpieza de Git, tests minimos,
politica fuerte de Quinigol y trazabilidad basica para metricas futuras. No
recalibra pesos, no reemplaza el Core y no cambia picks salvo correcciones de
coherencia Quinigol.

El bloque **Tactical Input Bridge v1** conecta datos confiables de lineup,
ratings, formacion tactica, forma y ausencias con el calculo real de simulacion.
Antes de llamar a `simulate_match()`, crea copias temporales de los dos equipos,
aplica ajustes pequenos y auditables, y pasa esas copias al Core. El baseline
mundialista no se modifica y el Core no se recalibra. Si faltan datos confiables,
el bridge no fuerza ningun ajuste numerico y solo reporta el motivo en
`adjustment_report`.

El bloque **World Cup 2022 Historical Blind Test v1** crea una base historica
auditable para probar comportamiento del sistema con Mundial 2022 sin mezclar
datos futuros. El modo inicial es `behavioral_backtest`: como se genera despues
del torneo, no mide precision predictiva real previa. Separa dataset prematch,
dataset de resultados, configuracion, reporte y auditoria de data leakage.

El bloque **Verified 2022 Prematch Profiles + Quinigol Timing Calibration v1**
agrega perfiles prematch 2022 minimos para los equipos de la muestra historica.
Cuando no hay fuentes verificadas suficientes, usa defaults neutrales
declarados y auditados para que los 8 partidos existentes sean evaluables como
backtest de comportamiento. Esto no convierte el resultado en precision
predictiva real, no recalibra pesos y no usa el baseline 2026 como proxy 2022.

El bloque **Fixture Real 2026 + Group Stage Loader v1** prepara la estructura
oficial del Mundial 2026: 48 selecciones, 12 grupos, 72 partidos de fase de
grupos y 104 partidos totales. Mientras no exista sorteo/fixture oficial local
verificado, genera solo slots estructurales `WG-A-01` a `WG-L-06` con
`pending_group_draw` y `pending_official_fixture`. No inventa cruces, horarios
ni sedes.

El bloque **Official Fixture Snapshot Importer + Fixture Validation Guard v1**
prepara la importacion segura de un snapshot oficial/verificado del fixture
2026. El importador corre por defecto en `dry_run`, valida el snapshot y no
modifica el fixture activo si faltan equipos, horarios UTC, sedes, fuente o
verificacion. La guardia bloquea picks completos mientras el fixture siga como
placeholder o no verificado. El Full Group Stage Picks Runner queda para el
siguiente bloque.

El bloque **Full Group Stage Picks Runner v1** crea el runner oficial para los
72 picks de fase de grupos, pero respeta obligatoriamente
`worldcup_2026_fixture_guard.py`. Con el fixture actual queda bloqueado:
`guard_status=blocked_placeholder`, `simulated_matches=0` y `picks=[]`. No
genera predicciones reales hasta que el fixture oficial verificado este cargado
y la guardia devuelva `ready`.

## Relacion con el Core

El Core formal sigue viviendo en `src/`:

- `src/match_simulator.py`
- `src/group_simulator.py`
- `src/tournament_simulator.py`
- `src/knockout_simulator.py`
- `src/odds_engine.py`
- `src/odds_history_engine.py`

Esta capa reutiliza `simulate_match()` y `load_teams()` desde
`src/match_simulator.py`. El Core calcula probabilidades, goles esperados y
marcadores probables. La capa de quiniela traduce esos datos en picks de juego,
alternativas, estrategia, contexto y lenguaje de riesgo.

## Que hace la capa

- Genera recomendaciones de quiniela por partido.
- Calcula Quinigol como gol recomendado del juego, no como cronologia de goles.
- Compara escenarios conservador, balanceado y agresivo.
- Entrega un Final Pick unico para llenar la quiniela.
- Agrega contexto de fase, grupo, jornada y presion estimada.
- Agrega estructura para sede y clima historico sin usar clima del dia.
- Marca datos faltantes con `pending_real_data` o `pre_tournament_context`.
- Registra fuentes open source/gratis para fixtures, Elo, clima y snapshots
  manuales.
- Permite probar amistosos internacionales como contexto separado, no como
  partidos oficiales del Mundial.
- Permite snapshots manuales de cuotas, alineaciones y stats sin scraping.
- Expone modos de simulacion `quick`, `standard` y `final`.
- Muestra research snapshots manuales como contexto de mercado y noticias.
- Convierte jugadores clave, alineaciones, tactica y mercado en capas de
  weighting auditables.
- Registra resultado real de amistosos y revisa acierto/error sin modificar el
  Core.
- Distingue datos de peso alto, medio y bajo para evitar humo o notas
  decorativas.
- Audita `research_refresh_required`, `recommended_action`, estado de alarma
  del partido y datos criticos faltantes antes de correr un pick final.
- Conecta datos tacticos confiables con la simulacion mediante
  `tactical_input_bridge.py`, siempre sobre copias temporales y con caps de
  seguridad.
- Agrega blind test historico 2022 con `data_leakage_guard.py`, datasets
  prematch/resultados separados y reporte behavioral, sin usar baseline 2026
  como proxy 2022.
- Agrega perfiles prematch 2022 auditados con defaults neutrales para pruebas
  de comportamiento cuando faltan datos historicos verificables.
- Calcula Quinigol Timing para el backtest 2022: equipo del primer gol, error
  de minuto, sesgo temprano/tardio y acierto de rango, sin recalibracion
  automatica.
- Genera reporte de calibracion amistosa con aciertos, errores, BTTS, Quinigol,
  alternativas criticas y patrones de fragilidad sin cambiar picks.
- Prepara fixtures de fase de grupos, reportes estructurados, manifiesto de
  backtesting y auditoria critica del sistema sin inventar datos.
- Crea 72 slots estructurales para fase de grupos 2026 y permite reemplazar la
  asignacion cuando exista fixture oficial, manteniendo separados
  `slot_structure`, `fixture_assignment` y `match_result`.
- Agrega template de snapshot oficial, importador en `dry_run` y guardia para
  impedir simulaciones completas con fixture placeholder/no verificado.
- Agrega runner de picks completos de fase de grupos, actualmente bloqueado por
  Fixture Guard hasta que exista fixture oficial confirmado.

## Final Pick

El Final Pick combina:

- probabilidad del marcador;
- puntos potenciales segun reglas de quiniela;
- consistencia con resultado 1X2;
- consistencia con xG;
- riesgo del marcador agresivo;
- contexto de fase, grupo y jornada;
- datos disponibles de sede y clima;
- datos faltantes marcados explicitamente.

Las alternativas segura y agresiva siguen apareciendo, pero son informacion
secundaria. La salida principal es una sola recomendacion final.

## Que es Quinigol

Quinigol es una seleccion de gol recomendado para un partido especifico.
No intenta crear una cronologia de todos los goles del partido.

La salida puede recomendar:

- un equipo que probablemente anote el gol recomendado;
- un minuto de referencia;
- un rango probable;
- la opcion `No hay` cuando el perfil de gol es bajo.

El minuto de referencia es una estimacion probabilistica. El rango probable es
mas importante que el minuto exacto.

Politica definitiva:

- Si el marcador recomendado es `0-0`, Quinigol queda como `No hay gol`,
  `minute=None`, `minute_label=No hay gol`, `minute_range=No aplica` y
  `policy_applied=score_0_0_no_goal`.
- Si el marcador recomendado tiene al menos un gol, el minuto es obligatorio y
  nunca debe quedar en `None`.
- Si ambos equipos tienen goles, el equipo Quinigol se elige por mayor xG/lambda;
  si hay empate, se usa probabilidad de primer gol si existe, luego favorito
  1X2 y finalmente `team_a`.
- El rango probable es contexto; el minuto especifico es el pick registrado.
- Si el engine proponia `No hay` pero el marcador tiene goles, la policy corrige
  el pick y marca `policy_applied=minute_forced_by_predicted_goals`.
- Si no hubo correccion, marca `policy_applied=normal`.

## Tests

Los tests minimos de scoring viven en:

```txt
tests/test_scoring_rules.py
```

Ejecucion directa sin pytest:

```bash
python -B tests/test_scoring_rules.py
```

Si pytest esta disponible, el mismo archivo tambien puede descubrirse como test.

## Trazabilidad prediction_history

`prediction_history.json` guarda evidencia para backtesting y metricas futuras.
Cuando la recomendacion trae esos datos, se persisten:

- `probabilities_1x2` con `home_win`, `draw`, `away_win`;
- `top_scores`;
- `expected_goals`;
- `simulation_mode` y `simulations`;
- `quinigol_policy_applied`, `quinigol_team`, `quinigol_minute`,
  `quinigol_range`;
- `data_quality_score`, `research_refresh_status` y `tactical_score`.

El historial conserva dedupe por firma y no entrena automaticamente el modelo.
SQLite local es runtime y no debe versionarse; la persistencia completa en tabla
queda compatible mediante columnas opcionales no destructivas.

## Marcador recomendado vs Quinigol

El marcador recomendado responde: "cual resultado exacto conviene jugar en la
quiniela".

Quinigol responde: "que gol puntual conviene asociar al partido". Puede coincidir
con el equipo favorecido por el marcador, pero no son lo mismo:

- marcador recomendado: busca puntos por resultado y goles exactos;
- Quinigol: busca una jugada adicional de gol o `No hay`;
- alternativa segura: reduce riesgo;
- alternativa agresiva: acepta mas riesgo por potencial.

## Motores

- `strategy_engine.py`: genera escenarios conservador, balanceado y agresivo.
- `quinigol_engine.py`: recomienda Quinigol sin crear cronologia completa.
- `quinigol_minute_policy.py`: fuerza coherencia entre marcador recomendado,
  equipo Quinigol, minuto y rango registrado.
- `tactical_input_bridge.py`: construye inputs ajustados para `simulate_match()`
  cuando existen lineups, ratings, formaciones, forma o ausencias confiables.
  Distingue contexto explicativo de ajuste real de simulacion y registra
  `adjustment_report`.
- `data_leakage_guard.py`: revisa datasets prematch historicos y bloquea si
  detecta resultados, narrativa posterior, caminos futuros o baseline 2026.
- `worldcup_2022_dataset_loader.py`: carga y valida prematch, resultados,
  config y auditoria del blind test 2022.
- `worldcup_2022_blind_test_engine.py`: construye el reporte behavioral 2022,
  separa readiness estructural, leakage y metricas Quinigol Timing.
- `worldcup_2022_profile_builder.py`: construye perfiles prematch 2022
  conservadores para la muestra historica; si falta dato verificado, usa
  defaults neutrales marcados explicitamente.
- `worldcup_2022_profile_validator.py`: valida que los perfiles 2022 no
  contengan resultados, narrativa posterior ni proxies del baseline 2026.
- `quinigol_timing_calibration_engine.py`: resume metricas de Quinigol Timing
  sobre evaluaciones historicas y recomienda no recalibrar si la muestra es
  insuficiente.
- `worldcup_2026_match_slot_engine.py`: genera estructura A-L y 72 slots
  estables sin cruces ficticios.
- `worldcup_2026_fixture_validator.py`: valida grupos, slots, IDs, UTC,
  sedes, duplicados, estado pendiente/confirmado y separacion group stage.
- `worldcup_2026_fixture_loader.py`: carga estructura, fixture, slots y reporte
  de validacion; expone si el fixture es placeholder, parcial o confirmado.
- `worldcup_2026_fixture_snapshot_importer.py`: valida un snapshot manual
  verificado y actualiza solo `fixture_assignment` si `dry_run=false` y la
  validacion pasa.
- `worldcup_2026_fixture_guard.py`: decide si puede haber simulacion parcial o
  completa; bloquea el Full Group Stage Picks Runner futuro si el fixture no
  esta confirmado.
- `full_group_stage_picks_runner.py`: runner oficial de picks de fase de grupos;
  no genera picks si la guardia no esta `ready`.
- `tournament_context_engine.py`: prepara fase, grupo, jornada, orden, presion,
  riesgo de rotacion e importancia de diferencia de goles.
- `venue_climate_engine.py`: prepara perfil historico de sede/clima.
- `final_pick_engine.py`: combina escenarios y contexto para elegir un pick final.
- `friendly_context_engine.py`: ajusta partidos amistosos por rotacion,
  intensidad menor, pruebas tacticas y mayor riesgo de sorpresa.
- `manual_snapshot_engine.py`: lee snapshots manuales tolerando datos
  incompletos.
- `research_intelligence_engine.py`: convierte investigacion publica manual en
  ajustes contextuales de riesgo/confianza sin sustituir el Core.
- `research_refresh_engine.py`: revisa venue, kickoff UTC, mercado,
  alineaciones, formaciones, ratings, tactica y resultado real para decidir si
  hace falta refresh manual.
- `match_alarm_engine.py`: calcula estado `upcoming`, `near_kickoff`, `live`,
  `final` o `unknown` desde `kickoff_time_utc` y marca `final_refresh_due`.
- `player_rating_engine.py`: lee ratings seed, busca nombres flexibles, agrupa
  por linea y reporta ratings faltantes.
- `lineup_strength_engine.py`: detecta jugadores desde snapshots manuales y
  calcula fuerza por linea solo con ratings numericos disponibles.
- `formation_tactical_engine.py`: convierte fuerza por linea, roles detectados
  y formacion en `tactical_score` numerico conservador.
- `tactical_weighting_engine.py`: expone senales tacticas compatibles con el
  weighting y mantiene advertencias cuando la formacion esta pendiente.
- `research_weighting_engine.py`: combina seis capas de informacion en ajustes,
  alineacion con mercado, fragilidad y calidad de datos.
- `half_time_engine.py`: estima marcador al descanso y descanso/final desde
  xG, marcador final recomendado y Quinigol.
- `pick_robustness_engine.py`: muestra top scores, estabilidad del pick y
  alerta de empate; tambien puede advertir riesgo de porteria a cero en
  amistosos fragiles con datos criticos faltantes.
- `result_review_engine.py`: compara prediccion vs resultado real registrado e
  incluye BTTS, gol tardio, roja, alternativa critica y aprendizaje
  estructurado.
- `calibration_rules_engine.py`: detecta patrones evaluativos como empate
  subestimado, gol tardio rival, desajuste de minuto Quinigol y fragilidad
  validada.
- `friendly_calibration_engine.py`: consolida resultados amistosos finalizados,
  calcula metricas globales y guarda reportes JSON para backtesting.
- `decision_weighting_engine.py`: clasifica senales por peso alto, medio y bajo
  y recomienda uso para quiniela o apuesta prepartido.
- `critical_alternative_engine.py`: identifica pick principal, alternativa
  critica y opcion tentadora.
- `simulation_config.py`: define modos `quick=10000`, `standard=100000` y
  `final=1000000`.
- `group_stage_runner.py`: recorre fixtures de fase de grupos, simula solo
  partidos confirmados con equipos concretos y baseline suficiente, y marca
  pendientes si el fixture sigue como placeholder/parcial.
- `report_builder.py`: construye reportes JSON por partido con pick, marcador,
  Quinigol, HT/FT, robustez, tactical score, calidad de datos y faltantes.
- `backtesting_engine.py`: prepara comparaciones prediccion vs resultado real
  con campos listos para Brier/log-loss cuando existan probabilidades.
- `system_self_audit.py`: audita fortalezas, debilidades, riesgos, leakage,
  sobreajuste y readiness para quiniela completa o venta.
- `src/data_ingestion/free_sources_registry.py`: registro estructurado de
  fuentes gratis u opcionales.
- `src/data_ingestion/openfootball_client.py`: scaffold offline para snapshots
  de openfootball.
- `src/data_ingestion/world_elo_client.py`: loader offline para CSV Elo manual.
- `src/data_ingestion/open_meteo_client.py`: constructor offline de parametros
  Open-Meteo.
- `src/data_ingestion/data_source_validator.py`: validadores de fuente y campos.

## Datos Open Source + Friendly Test Domingo

Fuentes registradas:

- FIFA oficial.
- openfootball/worldcup.json.
- World Football Elo Ratings.
- JGravier/soccer-elo.
- Open-Meteo.
- The Odds API como fuente opcional, no obligatoria.
- GitHub football datasets como registro de referencia.

Partidos amistosos cargados para prueba:

- Morocco vs Norway.
- Colombia vs Jordan.
- Croatia vs Slovenia.
- Ecuador vs Guatemala.
- Netherlands vs Uzbekistan.

Estos partidos tienen `competition_type: international_friendly`. El motor los
trata como amistosos: baja la confianza, sube el riesgo por rotacion y pruebas
tacticas, y aclara que no son partidos oficiales del Mundial.

Para la prueba actual solo quedan activos:

- Morocco vs Norway.
- Colombia vs Jordan.
- Netherlands vs Uzbekistan.

Se excluyen partidos donde no ambos equipos estan en baseline mundialista, o
partidos ya jugados. Los excluidos se informan con razon en el demo.

Worldcup Friendly Test v2 mantiene alcance `worldcup_only`: no crea Open
Friendly Lab, no agrega equipos fuera del baseline mundialista y no contamina
`worldcup_2026_real_teams_baseline_v1.json`. France vs Northern Ireland y Peru
vs Spain quedan fuera de esta capa; si aparecen en notas futuras deben marcarse
como `excluded_for_worldcup_only_scope`.

## Research Snapshot manual

`manual_match_snapshots.json` permite cargar datos visibles copiados por el
usuario:

- cuotas 1X2;
- odds americanas y referencias decimales;
- lineas over/under;
- probabilidades externas si existen;
- fuentes usadas y notas de mercado;
- impacto investigativo en riesgo/confianza;
- formaciones y jugadores probables;
- BTTS, over 2.5, promedios de goles, H2H y tendencias.

No hay scraping automatico. Las fuentes externas pueden cambiar sus cuotas o
lecturas, por eso cada snapshot debe conservar `captured_at`, `captured_by`,
`source_status` y `data_status`.

Si un dato no esta cargado, queda como `pending_manual_input`.

Regla principal: ninguna prediccion externa sustituye el Core. Sports Mole,
SportyTrader, FOX Sports, TalkSport, Reuters, FotMob, ESPN, Ticketmaster,
365Scores o cualquier otra fuente solo agregan contexto manual investigado.

## Player Rating + Lineup Weighting

`player_ratings_seed.json` define jugadores clave por seleccion con:

- nombre;
- equipo;
- posicion;
- rol;
- rating general;
- atributos tecnicos/fisicos;
- fuente;
- escala `0-100`;
- nivel de evidencia;
- confianza de fuente;
- notas.

Si el rating real no esta en la base local, el valor queda como
`replacement_level_estimate` y `source_confidence: low`. En ese caso la capa
detecta al jugador y aplica un replacement conservador con peso reducido:

- `official_public_rating`: confianza alta;
- `manual_researched_rating`: confianza media;
- `replacement_level_estimate`: confianza baja.

Los ratings por si solos no reemplazan el Core. Solo ajustan de forma
conservadora xG, Quinigol, confianza, riesgo y fragilidad.

## Tactical Input Bridge v1

`tactical_input_bridge.py` existe para evitar que las capas de lineup, tactica y
research queden solo como explicacion decorativa. Cuando hay datos suficientes,
el bridge traduce esa informacion a multiplicadores pequenos sobre `attack`,
`defense`, `form`, `tactical_attack_adjustment` y
`tactical_defense_adjustment` de copias temporales del dict de equipos.

Datos que pueden activar el bridge:

- lineups probables con al menos 7 jugadores con rating real por equipo;
- ratings reales verificados, no `replacement_level_estimate`;
- formaciones probables de ambos equipos;
- `form_score` confiable entre `0.80` y `1.20`;
- lesiones o ausencias de jugadores clave con rol e impacto claro.

Diferencia clave:

- contexto explicativo: notas, warnings, fragilidad, confianza y riesgo;
- ajuste real de simulacion: cambios capeados en copias temporales antes de
  `simulate_match()`.

El bridge no usa scraping, no usa APIs pagadas, no inventa datos, no cambia
`src/match_simulator.py`, no modifica
`data/worldcup_2026_real_teams_baseline_v1.json` y no recalibra pesos globales.
Si faltan datos, devuelve `bridge_status=not_applied` y las probabilidades se
mantienen equivalentes al flujo anterior.

## World Cup 2022 Historical Blind Test

`historical_blind_tests/worldcup_2022/` contiene la base del blind test historico
del Mundial 2022:

- `worldcup_2022_prematch_dataset.json`: fixtures y contexto permitido antes del
  partido, con `cutoff_datetime`, `source_status` y datos faltantes explicitos.
- `worldcup_2022_results_dataset.json`: resultados reales separados, solo para
  evaluacion posterior.
- `worldcup_2022_blind_test_config.json`: modo `behavioral_backtest`,
  `generated_after_event=true` y guardas contra leakage.
- `worldcup_2022_data_leakage_audit.json`: salida del guard.
- `worldcup_2022_blind_test_report.json`: reporte auditable.
- `worldcup_2022_team_profiles_prematch.json`: perfiles prematch 2022 para los
  equipos incluidos en la muestra. Los perfiles actuales usan defaults
  neutrales cuando no hay fuentes historicas verificadas.
- `worldcup_2022_profile_sources_audit.json`: auditoria de fuentes, defaults
  neutrales y bloqueos de perfiles.
- `worldcup_2022_quinigol_timing_report.json`: resumen de equipo/minuto/rango
  de primer gol para Quinigol Timing.

`true prediction` significa una prediccion creada antes del partido, con timestamp
y datos disponibles antes del cutoff. Este bloque todavia no tiene eso.
`behavioral_backtest` significa estudiar como se comportaria el sistema con una
estructura historica, sabiendo que la ejecucion se genera despues del evento.

Data leakage es cualquier filtracion de informacion futura en el input: marcador
real, campeon, finalistas, posiciones finales, narrativa posterior, camino de
eliminatorias o datos actuales usados como si fueran prepartido. Por eso el
baseline 2026 no puede usarse para simular 2022: sus ratings reflejan otro
momento historico y contaminarian la evaluacion.

Quinigol Timing Metrics mide, cuando existan predicciones historicas validas:
acierto del equipo del primer gol, error del minuto, sesgo temprano/tardio y
acierto de rango. No recalibra automaticamente; solo detecta patrones como:
`Quinigol team selection may be stronger than minute precision.`

Estado actual del bloque D:

- perfiles creados para los 10 equipos presentes en los 8 partidos de muestra;
- perfiles verificados con fuente fuerte: 0;
- perfiles con defaults neutrales auditados: 10;
- partidos evaluables como behavioral backtest: 8;
- partidos evaluados con defaults neutrales: 8;
- precision predictiva real: no valida;
- reclamos de accuracy del modelo: no permitidos.

Falta para convertirlo en backtest fuerte:

- verificar todos los fixtures/resultados 2022 contra fuente oficial;
- crear perfiles prematch 2022 con Elo/FIFA/rendimiento previos y cutoff;
- guardar predicciones historicas auditables o generar simulaciones solo con
  perfiles 2022 validados;
- mantener resultados fuera del dataset prematch;
- ampliar cobertura a todos los partidos de 2022 antes de mirar 2018/2014.

La secuencia obligatoria es:

```txt
dato -> variable -> peso -> ajuste -> impacto en prediccion
```

Cuando faltan datos, el impacto se informa como warning o ajuste cualitativo.
No se ocultan ratings faltantes.

## Seis capas de weighting

`research_weighting_engine.py` combina:

1. Fuerza real del Core.
2. Contexto del partido.
3. Informacion tactica.
4. Contexto externo.
5. Mercado.
6. Senales avanzadas.

La salida muestra `data_found`, `data_quality`, `evidence_level`,
`impact_type`, `numeric_adjustment`, `qualitative_adjustment` y `explanation`
por capa.

## Historial de predicciones

`prediction_history.json` guarda evidencia auditable de cada corrida amistosa:
prediccion previa, modo de simulacion, simulaciones usadas, pick, marcador,
alternativa critica, opcion tentadora, Quinigol, descanso/final,
`tactical_score`, confianza, riesgo, calidad de datos, estado de
research-refresh/match-alarm, resultado real cuando existe y revision
post-partido.

Este historial no entrena el modelo automaticamente y no cambia picks. Sirve
para backtesting, revision manual y calibracion futura. Las nuevas corridas se
deduplican por firma y no sobrescriben predicciones previas sin dejar rastro.

## Friendly Calibration v1

`run_friendly_calibration_report.py` genera:

- `data/friendly_calibration_report.json`
- `data/calibration_notes.json`

El reporte revisa solo amistosos finalizados y calcula acierto de ganador,
marcador exacto, BTTS, error de diferencia de goles, error de goles totales,
Quinigol por equipo, desviacion de minuto, descanso/final y relevancia de
alternativa critica.

Patrones detectados en la muestra inicial:

- empate subestimado cuando un amistoso cerrado tenia alternativa critica de
  empate;
- gol tardio rival / BTTS subestimado cuando un favorito con pick a cero gana
  por un gol y el rival anota despues del minuto 75;
- minuto Quinigol demasiado temprano cuando el equipo fue correcto pero el
  primer gol real salio del rango probable;
- fragilidad validada cuando un pick fragil/cauteloso no acierta marcador
  exacto.

Estos patrones se guardan como evidencia auditable, no como entrenamiento
automatico. La muestra de tres partidos no alcanza para recalibrar fuerte:
sirve para crear warnings, preparar backtesting y definir que datos faltan
antes de tocar pesos del modelo.

## Data Completion + Backtesting Foundation v1

Este bloque agrega estructura para completar datos reales sin contaminar el
Core:

- World Elo entra desde `world_elo_snapshot_template.csv` o un CSV local
  verificado con columnas `team, elo, rank, source, date_collected, notes`.
- Open-Meteo entra como URL historica construida desde lat/lon y rango de
  fechas. No requiere API key y no inventa clima.
- openfootball/worldcup.json entra solo como snapshot JSON local validado. Si
  no existe, el estado queda `manual_snapshot_required`.
- `group_stage_fixture_context.json` conserva la estructura de fase de grupos,
  pero no inventa cruces, sedes ni horarios.
- `backtesting_manifest.json` lista datasets posibles, costo, API key,
  estado, riesgo de leakage e integracion pendiente.

El Mundial 2022 debe correrse como blind test separado con data leakage guard:
cada prediccion historica debe usar solo datos disponibles antes del kickoff.
Hasta que exista ese dataset limpio, el sistema solo prepara la base y ejecuta
comparaciones demo con amistosos ya revisados.

## World Cup 2026 Fixture Structure v1

La estructura 2026 se separa en cuatro capas:

- `fixture_structure`: formato oficial esperado del torneo, 12 grupos y 72
  partidos de fase de grupos.
- `generated_placeholder_fixture`: slots estables cuando aun no hay sorteo ni
  fixture oficial cargado.
- `confirmed_fixture`: partidos reales cargados desde snapshot oficial
  verificado.
- `match_result`: resultado futuro del partido, separado del fixture prematch.

Estados permitidos:

- `structural_placeholder`: existen slots, pero no hay cruces oficiales.
- `partial_fixture`: hay algunos partidos confirmados y otros pendientes.
- `confirmed_fixture`: fixture completo verificado con equipos, UTC y sedes.
- `pending_official_fixture`: falta dato oficial.
- `pending_group_draw`: falta sorteo o asignacion de selecciones al grupo.

Archivos del bloque:

- `data/worldcup_2026_group_structure.json`
- `data/worldcup_2026_fixture_status.json`
- `data/worldcup_2026_group_stage_fixture.json`
- `data/worldcup_2026_match_slots.json`
- `data/worldcup_2026_fixture_validation_report.json`

El `group_stage_runner.py` usa el loader 2026. Si el fixture es placeholder,
devuelve 72 slots pendientes y no intenta simulacion real. Si luego existe
fixture parcial, corre solo partidos confirmados. Si el fixture completo queda
validado, habilita la simulacion completa de fase de grupos.

No se deben inventar ejemplos como partidos reales. Para reemplazar un slot,
mantener el `match_id` estable y actualizar solo `fixture_assignment`, equipos,
`kickoff_utc`, sede y estado con fuente oficial verificada.

## Official Fixture Snapshot Importer v1

El archivo `data/worldcup_2026_official_fixture_snapshot_template.json` es una
plantilla manual para cargar el fixture oficial cuando exista. Debe contener:

- 72 partidos de fase de grupos;
- `slot_id` estable `WG-A-01` a `WG-L-06`;
- grupo A-L;
- equipos concretos;
- `kickoff_utc` en UTC;
- sede, ciudad y pais;
- fuente oficial;
- `source_status=official_confirmed`;
- `verification_status=official_confirmed`.

El importador:

- corre por defecto con `dry_run=True`;
- valida antes de aplicar;
- bloquea snapshots pendientes o incompletos;
- no cambia el fixture activo si hay errores;
- conserva `slot_structure` y `match_result`;
- actualiza solo `fixture_assignment` y campos prematch cuando el snapshot es
  oficial/verificado.

La guardia (`worldcup_2026_fixture_guard.py`) revisa fixture type, status,
equipos, baseline, UTC, sedes, duplicados y reporte de validacion. Con el estado
actual debe quedar:

- `guard_status=blocked_placeholder`;
- `ready_for_partial_simulation=false`;
- `ready_for_full_group_simulation=false`.

Este bloque no genera picks, no simula los 72 partidos y no inventa fixture. El
siguiente bloque recomendado es **Full Group Stage Picks Runner v1**, solo
despues de importar un snapshot oficial y pasar la guardia.

## Full Group Stage Picks Runner v1

`run_full_group_stage_picks.py` prepara la ejecucion de los 72 picks de fase de
grupos. El flujo correcto para desbloquearlo es:

1. cargar `worldcup_2026_official_fixture_snapshot_template.json` con fixture
   oficial verificado;
2. correr importacion en `dry_run`;
3. aplicar import real solo si la validacion pasa;
4. confirmar `guard_status=ready`;
5. ejecutar el runner de picks.

Comando de estado:

```bash
python -B game-layers/quiniela-mundialista/run_full_group_stage_picks.py --mode standard
```

Comando para escribir reportes cuando corresponda:

```bash
python -B game-layers/quiniela-mundialista/run_full_group_stage_picks.py --mode final --write
```

`--force` no salta la guardia. Solo puede permitir reescritura de reportes; no
autoriza picks con fixture invalido o placeholder.

Mientras el fixture siga bloqueado, el runner devuelve `runner_status=blocked`,
`simulated_matches=0`, `picks=[]` y no escribe `prediction_history`.

## Decision Weighting

- Pick principal: marcador recomendado para jugar.
- Alternativa critica: marcador cercano que puede afectar la decision si el top
  #1 y top #2 estan separados por menos de 1.5 puntos porcentuales.
- Opcion tentadora: marcador de mayor recompensa/puntos potenciales, pero con
  menor probabilidad o mayor riesgo.
- Quiniela: usar el pick principal; considerar alternativa critica solo si hay
  fragilidad alta.
- Apuesta prepartido: usar mercados mas conservadores si el marcador exacto es
  fragil; recalcular si cambian alineaciones o mercado.

No todos los datos pesan igual. Ratings, xG, 1X2, top scores, mercado,
alineaciones y contexto son peso alto. Tendencias claras, H2H, sede, viaje,
rotacion y lesiones de impacto medio/alto/critico son peso medio. Predicciones
editoriales y comentarios generales son peso bajo y no pueden cambiar el pick.

## Salida Final Pick

Cada recomendacion final muestra:

- Partido.
- Fase.
- Grupo.
- Jornada.
- Sede.
- Recomendacion final quiniela.
- Marcador final recomendado.
- Quinigol final recomendado.
- Rango probable Quinigol.
- Minuto referencia.
- Confianza.
- Riesgo.
- Por que este marcador.
- Por que este Quinigol.
- Alternativa segura.
- Alternativa agresiva.
- No recomendado.
- Datos usados.
- Datos faltantes.
- Notas.

## Archivos

```txt
game-layers/quiniela-mundialista/
|-- README.md
|-- data_requirements.md
|-- scoring_rules.py
|-- quiniela_engine.py
|-- quinigol_engine.py
|-- strategy_engine.py
|-- tactical_input_bridge.py
|-- data_leakage_guard.py
|-- worldcup_2022_dataset_loader.py
|-- worldcup_2022_blind_test_engine.py
|-- worldcup_2022_profile_builder.py
|-- worldcup_2022_profile_validator.py
|-- quinigol_timing_calibration_engine.py
|-- worldcup_2026_match_slot_engine.py
|-- worldcup_2026_fixture_loader.py
|-- worldcup_2026_fixture_validator.py
|-- worldcup_2026_fixture_snapshot_importer.py
|-- worldcup_2026_fixture_guard.py
|-- full_group_stage_picks_runner.py
|-- tournament_context_engine.py
|-- venue_climate_engine.py
|-- final_pick_engine.py
|-- friendly_context_engine.py
|-- manual_snapshot_engine.py
|-- player_rating_engine.py
|-- lineup_strength_engine.py
|-- formation_tactical_engine.py
|-- tactical_weighting_engine.py
|-- research_intelligence_engine.py
|-- research_weighting_engine.py
|-- research_refresh_engine.py
|-- match_alarm_engine.py
|-- half_time_engine.py
|-- pick_robustness_engine.py
|-- result_review_engine.py
|-- calibration_rules_engine.py
|-- friendly_calibration_engine.py
|-- group_stage_runner.py
|-- report_builder.py
|-- backtesting_engine.py
|-- system_self_audit.py
|-- decision_weighting_engine.py
|-- critical_alternative_engine.py
|-- simulation_config.py
|-- run_quiniela_demo.py
|-- run_group_quiniela_demo.py
|-- run_final_pick_demo.py
|-- run_data_sources_demo.py
|-- run_lineup_weighting_demo.py
|-- run_tactical_input_bridge_demo.py
|-- run_worldcup_2022_blind_test.py
|-- run_worldcup_2022_profile_validation.py
|-- run_quinigol_timing_calibration.py
|-- run_worldcup_2026_fixture_status.py
|-- run_worldcup_2026_fixture_import_demo.py
|-- run_worldcup_2026_fixture_guard.py
|-- run_full_group_stage_picks.py
|-- run_group_context_demo.py
|-- run_decision_weighting_demo.py
|-- run_match_intelligence_demo.py
|-- run_friendly_test_demo.py
|-- run_research_snapshot_demo.py
|-- run_research_refresh_demo.py
|-- run_friendly_calibration_report.py
|-- run_group_stage_report_demo.py
|-- run_backtesting_foundation_demo.py
|-- run_system_self_audit.py
|-- run_project_status_report.py
`-- data/
    |-- fixtures_context.json
    |-- friendly_test_matches.json
    |-- free_data_sources.md
    |-- manual_match_snapshots.json
    |-- friendly_test_results.json
    |-- prediction_history.json
    |-- friendly_calibration_report.json
    |-- calibration_notes.json
    |-- group_stage_fixture_context.json
    |-- worldcup_2026_group_structure.json
    |-- worldcup_2026_fixture_status.json
    |-- worldcup_2026_group_stage_fixture.json
    |-- worldcup_2026_match_slots.json
    |-- worldcup_2026_fixture_validation_report.json
    |-- worldcup_2026_official_fixture_snapshot_template.json
    |-- worldcup_2026_fixture_import_report.json
    |-- worldcup_2026_fixture_guard_report.json
    |-- worldcup_2026_group_stage_picks_report.json
    |-- worldcup_2026_group_stage_picks_summary.csv
    |-- worldcup_2026_group_stage_picks_guard_report.json
    |-- backtesting_manifest.json
    |-- group_stage_prediction_report.json
    |-- player_ratings_seed.json
    |-- openfootball_snapshot_README.md
    |-- venue_climate_profiles.json
    |-- world_elo_snapshot_template.csv
    `-- worldcup_venues_seed.json
```

## Ejecutar demos

Desde la raiz del repositorio:

```bash
python -B game-layers/quiniela-mundialista/run_final_pick_demo.py
python -B game-layers/quiniela-mundialista/run_data_sources_demo.py
python -B game-layers/quiniela-mundialista/run_lineup_weighting_demo.py
python -B game-layers/quiniela-mundialista/run_tactical_input_bridge_demo.py
python -B game-layers/quiniela-mundialista/run_worldcup_2022_profile_validation.py
python -B game-layers/quiniela-mundialista/run_worldcup_2022_blind_test.py
python -B game-layers/quiniela-mundialista/run_quinigol_timing_calibration.py
python -B game-layers/quiniela-mundialista/run_worldcup_2026_fixture_status.py
python -B game-layers/quiniela-mundialista/run_worldcup_2026_fixture_import_demo.py
python -B game-layers/quiniela-mundialista/run_worldcup_2026_fixture_guard.py
python -B game-layers/quiniela-mundialista/run_full_group_stage_picks.py --mode standard
python -B game-layers/quiniela-mundialista/run_group_context_demo.py
python -B game-layers/quiniela-mundialista/run_worldcup_2026_bracket_status.py
python -B game-layers/quiniela-mundialista/run_worldcup_2026_third_place_demo.py
python -B game-layers/quiniela-mundialista/run_research_prompt_builder_demo.py
python -B game-layers/quiniela-mundialista/run_research_snapshot_validation_demo.py
python -B game-layers/quiniela-mundialista/run_research_automation_demo.py
python -B game-layers/quiniela-mundialista/run_phase_freeze_demo.py
python -B game-layers/quiniela-mundialista/run_worldcup_2026_standings_demo.py
python -B game-layers/quiniela-mundialista/run_inter_phase_update_demo.py
python -B game-layers/quiniela-mundialista/run_decision_weighting_demo.py
python -B game-layers/quiniela-mundialista/run_match_intelligence_demo.py
python -B game-layers/quiniela-mundialista/run_research_snapshot_demo.py
python -B game-layers/quiniela-mundialista/run_research_refresh_demo.py
python -B game-layers/quiniela-mundialista/run_friendly_test_demo.py
python -B game-layers/quiniela-mundialista/run_friendly_calibration_report.py
python -B game-layers/quiniela-mundialista/run_group_stage_report_demo.py
python -B game-layers/quiniela-mundialista/run_backtesting_foundation_demo.py
python -B game-layers/quiniela-mundialista/run_system_self_audit.py
python -B game-layers/quiniela-mundialista/run_project_status_report.py
python -B game-layers/quiniela-mundialista/run_quiniela_demo.py
python -B game-layers/quiniela-mundialista/run_group_quiniela_demo.py
```

## Modos de simulacion

- `quick`: 10000 simulaciones, recomendado para demos rapidas.
- `standard`: 100000 simulaciones, recomendado para pruebas mas estables.
- `final`: 1000000 simulaciones, disponible para picks finales aunque no se
  ejecuta por defecto en demos si el runtime local puede tardar demasiado.

Toda salida principal imprime modo y simulaciones usadas.

El demo final usa:

- `data/worldcup_2026_real_teams_baseline_v1.json`;
- `game-layers/quiniela-mundialista/data/fixtures_context.json`;
- `game-layers/quiniela-mundialista/data/venue_climate_profiles.json`.

## Reglas de juego

Definicion del juego:

- 90 minutos.
- Incluye los dos tiempos regulares.
- No incluye tiempo extra ni penales.

Puntuacion:

- 2 puntos por acierto del Quinigol.
- 3 puntos por acertar resultado: gana equipo o empate.
- 5 puntos por acertar equipo ganador y goles de un equipo.
- 7 puntos por acertar resultado y goles de ambos equipos.
- Maximo 9 puntos por juego.

## Advertencia de datos

Esta version usa baseline v1. Todavia no integra datos finales de lesiones,
alineaciones confirmadas, xG real calibrado, plantillas definitivas, tacticas
detalladas, calendario FIFA completo, sedes reales, clima historico real ni
cuotas reales de mercado.

Cuando un dato no esta disponible, la capa lo marca como `pending_real_data` o
`pre_tournament_context`. Para snapshots manuales tambien puede usar
`pending_manual_snapshot`, `manual_snapshot_required`, `pending_manual_input` o
`not_available_free`. Las recomendaciones son una capa de juego basada en el
modelo disponible, no una garantia de resultado.

## Group Context Engine v1

`group_context_engine.py` agrega contexto de grupo para picks futuros del
Mundial 2026. La capa puede marcar:

- `death_group`
- `balanced_group`
- `clear_favorite_group`
- `surprise_candidate_in_group`
- `surprise_candidate_in_match`
- `jornada3_trap_pending`
- `jornada3_trap_confirmed`
- `mutual_draw_incentive`
- `must_win_pressure`
- `underdog_upset_spot`
- `insufficient_group_data`

Mientras el fixture oficial no exista, el engine queda bloqueado por
`worldcup_2026_fixture_guard.py`. Con el placeholder actual devuelve
`context_status=placeholder_blocked`, `allowed_for_prediction=false` y no
inventa flags reales.

Datos necesarios para activar contexto real:

- grupos oficiales;
- fixture oficial con equipos reales;
- ratings/rankings previos verificables;
- `standings_before_match` para analizar jornada 3.

Datos prohibidos para este modulo:

- resultados futuros;
- tabla final del grupo antes de un partido;
- narrativa posterior, campeon o finalistas.

`full_group_stage_picks_runner.py` queda preparado para incluir
`group_context`, `group_context_flags`, `group_strength_bucket`,
`surprise_candidate_context`, `jornada3_trap_context` y
`points_pressure_context` cuando Fixture Guard este en `ready` o
`partial_ready`. Si el contexto tiene datos insuficientes, no debe cambiar el
pick.

## Official Bracket 2026 v1

`worldcup_2026_bracket_structure.py` crea la estructura scaffold de
eliminatorias del Mundial 2026:

- Round of 32: 16 partidos.
- Round of 16: 8 partidos.
- Cuartos: 4 partidos.
- Semifinales: 2 partidos.
- Tercer lugar: 1 partido.
- Final: 1 partido.

El formato esperado clasifica a los dos primeros de cada uno de los 12 grupos
(24 equipos) y a 8 mejores terceros. La seleccion de terceros queda separada en
`worldcup_2026_third_place_selector.py`, con reglas pendientes de verificacion
oficial en `worldcup_2026_third_place_rules.json`.

El bracket queda bloqueado porque todavia faltan:

- standings finales/proyectados de grupos con posiciones 1-4;
- matriz oficial de combinaciones de terceros, si aplica;
- fixture knockout oficial/verificado;
- sedes y horarios knockout verificados.

No se inventan clasificados, mejores terceros ni cruces. Los slots de
`worldcup_2026_bracket_slots.json` quedan con `team_a` y `team_b` en
`pending_group_results`. Este bloque no genera picks de eliminatorias.

## Research Automation v1

Research Automation prepara investigacion previa al partido sin llamar APIs por
defecto. La capa incluye:

- `research_prompt_builder.py`: genera prompts estructurados.
- `research_snapshot_schema.py`: define campos obligatorios.
- `research_snapshot_validator.py`: valida fuentes, confianza, cuotas,
  alineaciones, formaciones, lesiones y ratings.
- `research_snapshot_normalizer.py`: normaliza snapshots para el formato usado
  por `manual_snapshot_engine.py` y `tactical_input_bridge.py`.
- `research_snapshot_store.py`: guarda snapshots en
  `data/research_snapshots/`, con `dry_run=True` por defecto.
- `ai_research_client.py`: cliente seguro; `provider=manual` por defecto y sin
  llamadas externas.

Campos clave del snapshot:

- `match`, `team_a`, `team_b`, `competition`, `phase`, `kickoff_utc`;
- `captured_at`, `captured_by`, `snapshot_type`, `source_status`;
- `sources`, `overall_confidence`;
- `odds_1x2`, `over_under`;
- `probable_lineups`, `formations`, `injuries_or_absences`;
- `key_players`, `player_ratings`, `form_snapshot`, `stats_snapshot`;
- `tactical_notes`, `missing_data`, `warnings`.

Uso antes de un partido:

```bash
python -B game-layers/quiniela-mundialista/run_research_prompt_builder_demo.py
python -B game-layers/quiniela-mundialista/run_research_snapshot_validation_demo.py
python -B game-layers/quiniela-mundialista/run_research_automation_demo.py
```

El flujo no modifica `manual_match_snapshots.json`, no toca
`data/worldcup_2026_real_teams_baseline_v1.json` y no cambia picks
automaticamente. Si en el futuro se conecta a OpenAI o Anthropic, las claves
deben vivir fuera del repo como variables de entorno (`OPENAI_API_KEY` o
`ANTHROPIC_API_KEY`) y la llamada real debe implementarse de forma explicita.

## Inter Phase Updater v1

`inter_phase_update_engine.py` prepara el paso ordenado entre fases del Mundial
2026. No genera picks nuevos, no toca picks congelados, no modifica Core y no
recalibra pesos automaticamente.

Componentes:

- `phase_freeze_engine.py`: identifica predicciones de una fase y prepara el
  freeze auditado. En `dry_run=True` no modifica `prediction_history.json`.
- `worldcup_2026_results_loader.py`: crea/carga
  `worldcup_2026_results_template.json` con 72 slots de fase de grupos y valida
  resultados reales.
- `worldcup_2026_standings_engine.py`: calcula standings solo con resultados
  finales y equipos reales.
- `worldcup_2026_phase_transition_guard.py`: bloquea avances si faltan picks
  congelados, resultados completos, standings o bracket.
- `inter_phase_update_engine.py`: orquesta freeze, results, standings y guard.

Estados actuales esperados:

- `freeze_status=blocked_no_predictions`;
- `results_status=pending_results`;
- `standings_status=blocked_placeholder_fixture`;
- `transition_status=blocked`.

Uso:

```bash
python -B game-layers/quiniela-mundialista/run_phase_freeze_demo.py
python -B game-layers/quiniela-mundialista/run_worldcup_2026_standings_demo.py
python -B game-layers/quiniela-mundialista/run_inter_phase_update_demo.py
```

Congelar una fase significa guardar evidencia de que los picks previos quedan
cerrados antes de adjuntar resultados reales. No significa recalibrar el modelo
ni alterar predicciones historicas. La transicion a eliminatorias solo puede
prepararse cuando existan resultados finales verificados y standings calculados.

## ChatGPT Research Intake + Emergency Quiniela Fill v1

Este bloque convierte un paquete local generado por ChatGPT en datos operativos
para la quiniela de fase de grupos:

```text
ChatGPT research package -> intake -> fixture import -> guard -> quiniela fill
```

Archivos principales:

- `data/chatgpt_research_intake_package.json`: entrada que debe llenar ChatGPT.
- `chatgpt_research_intake_engine.py`: valida fixture, grupos y research.
- `data/worldcup_2026_official_fixture_snapshot_manual.json`: snapshot
  compatible con el importer.
- `data/worldcup_2026_research_snapshots_batch.json`: research contextual
  separado del baseline.
- `emergency_quiniela_fill_engine.py`: genera JSON, CSV y Markdown imprimible
  solo si Fixture Guard esta en `ready`.

Reglas de seguridad:

- no reemplaza Core;
- no modifica `src/match_simulator.py`;
- no modifica `data/worldcup_2026_real_teams_baseline_v1.json`;
- no hace scraping ni llamadas externas;
- no recalibra pesos;
- no escribe `prediction_history.json`;
- no modifica `manual_match_snapshots.json`;
- no genera picks si el fixture oficial no esta listo.

Uso:

```bash
python -B game-layers/quiniela-mundialista/run_chatgpt_research_intake.py --dry-run
python -B game-layers/quiniela-mundialista/run_chatgpt_research_intake.py --apply-fixture-import
python -B game-layers/quiniela-mundialista/run_emergency_quiniela_fill.py --mode final --write
```

Para que `fixture_ready=true`, el paquete debe tener
`fixture.source_status="official_verified"` y 72 partidos con `group`,
`matchday`, `team_a` y `team_b`. La investigacion puede ser parcial: si faltan
alineaciones confirmadas, cuotas, clima o lesiones de ultimo minuto, se permite
`pending_verification` o `not_available`. Esos faltantes no bloquean una
quiniela pre-torneo si el fixture oficial y los equipos estan correctos.

Salidas:

- `data/chatgpt_research_intake_validation_report.json`
- `data/worldcup_2026_quiniela_fill_report.json`
- `data/worldcup_2026_quiniela_fill_summary.csv`
- `data/worldcup_2026_quiniela_fill_printable.md`

`ready_for_user_quiniela=true` exige `guard_status=ready` y 72 picks generados.
Con el paquete de plantilla actual, el estado correcto es bloqueado y
`picks_generated=0`.
