# Quiniela Mundialista v1.2

Esta carpeta agrega una capa especializada de juego para una quiniela real del
Mundial 2026. No reemplaza ni duplica el Core principal del proyecto.

La quiniela real se llena una sola vez. Por eso v1.2 agrega un motor de
`Final Pick`: evalua internamente los escenarios conservador, balanceado y
agresivo, pero entrega una sola recomendacion final clara para jugar.

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
|-- run_quiniela_demo.py
|-- run_group_quiniela_demo.py
|-- run_final_pick_demo.py
`-- data/
    |-- fixtures_context.json
    `-- venue_climate_profiles.json
```

## Ejecutar demos

Desde la raiz del repositorio:

```bash
python -B game-layers/quiniela-mundialista/run_final_pick_demo.py
python -B game-layers/quiniela-mundialista/run_quiniela_demo.py
python -B game-layers/quiniela-mundialista/run_group_quiniela_demo.py
```

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
`pre_tournament_context`. Las recomendaciones son una capa de juego basada en el
modelo disponible, no una garantia de resultado.
