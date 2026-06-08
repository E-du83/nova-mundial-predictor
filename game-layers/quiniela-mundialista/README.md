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
- Genera reporte de calibracion amistosa con aciertos, errores, BTTS, Quinigol,
  alternativas criticas y patrones de fragilidad sin cambiar picks.
- Prepara fixtures de fase de grupos, reportes estructurados, manifiesto de
  backtesting y auditoria critica del sistema sin inventar datos.

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
  partidos con equipos concretos y baseline suficiente, y marca pendientes si
  faltan datos.
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
