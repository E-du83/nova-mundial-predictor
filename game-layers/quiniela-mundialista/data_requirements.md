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
| Resultado real amistoso | Fuente oficial post-partido | Si | pending_real_result | Permite comparar pick vs resultado |
| Descanso/final | Derivado de Core + Quinigol | Si | parcial | Agrega lectura HT/FT sin nuevo motor Core |
| Robustez pick | Derivado de top_scores Core | Si | disponible si hay top_scores | Detecta pick fragil y alerta de empate |
| Coordenadas sedes | FIFA/venue official/manual verificado | Si | pending_real_data | Activa Open-Meteo historico |
| Modo simulacion final | Configuracion local | Si | disponible | Permite quick, standard o final 1M |

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
