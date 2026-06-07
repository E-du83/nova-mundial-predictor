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
  lesiones, alineaciones, cuotas, xG real y tabla por jornada.
- Regla operativa: cuando un dato no existe, el motor debe marcarlo como
  `pending_real_data` o `pre_tournament_context`; no debe inventarlo.
