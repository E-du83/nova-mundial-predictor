# Quiniela Mundialista v1.1

Esta carpeta agrega una capa especializada de juego para una quiniela real del
Mundial 2026. No reemplaza ni duplica el Core principal del proyecto.

La capa toma la salida de `src/match_simulator.py` y la convierte en:

- prediccion quiniela;
- marcador recomendado;
- alternativas segura y agresiva;
- riesgo en lenguaje simple;
- Quinigol recomendado;
- explicacion breve para el usuario.

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
marcadores probables. La capa de quiniela solo traduce esos datos en picks de
juego, alternativas, estrategia y lenguaje de riesgo.

## Que es Quinigol

Quinigol es una seleccion de gol recomendado para un partido especifico.
No intenta crear una cronologia de todos los goles del partido.

La salida puede recomendar:

- un equipo que probablemente anote el gol recomendado;
- un minuto estimado;
- un rango probable;
- la opcion `No hay` cuando el perfil de gol es bajo.

El minuto probable es una estimacion probabilistica. El rango probable es mas
importante que el minuto exacto.

## Marcador recomendado vs Quinigol

El marcador recomendado responde: "cual resultado exacto conviene jugar en la
quiniela".

Quinigol responde: "que gol puntual conviene asociar al partido". Puede coincidir
con el equipo favorecido por el marcador, pero no son lo mismo:

- marcador recomendado: busca puntos por resultado y goles exactos;
- Quinigol: busca una jugada adicional de gol o `No hay`;
- alternativa segura: reduce riesgo;
- alternativa agresiva: acepta mas riesgo por potencial.

## Modos de estrategia

El sistema soporta tres modos:

- `conservador`: favorece marcadores mas probables, evita goleadas y recomienda
  opciones de menor riesgo cuando el Core ofrece alternativas cercanas.
- `balanceado`: combina marcador probable con puntos potenciales sin alejarse
  demasiado del resultado principal.
- `agresivo`: puede elegir un marcador de mayor puntaje potencial y acepta mas
  riesgo. La salida explica cuando la seleccion es menos estable.

## Salida por partido

Cada recomendacion muestra:

- Partido.
- Prediccion quiniela.
- Marcador recomendado.
- Confianza.
- Riesgo.
- Estrategia.
- Quinigol recomendado.
- Minuto probable.
- Alternativa segura.
- Alternativa agresiva.
- Detalle Quinigol.
- Justificacion breve.

El detalle de Quinigol incluye rango probable, riesgo, opcion `No hay` y una
explicacion simple del minuto.

## Archivos

```txt
game-layers/quiniela-mundialista/
|-- README.md
|-- scoring_rules.py
|-- quiniela_engine.py
|-- quinigol_engine.py
|-- strategy_engine.py
|-- run_quiniela_demo.py
`-- run_group_quiniela_demo.py
```

## Ejecutar demos

Desde la raiz del repositorio:

```bash
python game-layers/quiniela-mundialista/run_quiniela_demo.py
```

Demo con seleccion parcial de partidos reales de fase de grupos:

```bash
python game-layers/quiniela-mundialista/run_group_quiniela_demo.py
```

El demo grupal usa `data/worldcup_2026_real_groups.json`, toma una seleccion
documentada de partidos reales y genera recomendaciones en modo conservador,
balanceado y agresivo. Todavia no intenta construir todo el calendario de fase
de grupos.

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

## Uso desde codigo

```python
from quiniela_engine import load_teams, recommend_match

teams = load_teams("data/worldcup_2026_real_teams_baseline_v1.json")
pick = recommend_match(
    "Argentina",
    "Austria",
    teams,
    strategy="balanceado",
    simulations=50_000,
    seed=2026,
)
```

## Advertencia de datos

Esta version usa baseline v1. Todavia no integra datos finales de lesiones,
alineaciones confirmadas, xG real calibrado, plantillas definitivas, tacticas
detalladas ni cuotas reales de mercado. Las recomendaciones son una capa de
juego basada en el modelo disponible, no una garantia de resultado.
