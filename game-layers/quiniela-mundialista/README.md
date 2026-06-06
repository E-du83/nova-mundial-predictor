# Quiniela Mundialista

Esta carpeta agrega una capa especializada de juego para una quiniela real del
Mundial 2026. No reemplaza ni duplica el Core del proyecto.

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
marcadores probables. La capa de quiniela convierte esa salida en picks de
juego, alternativas y lenguaje de riesgo.

## Archivos

```txt
game-layers/quiniela-mundialista/
├── README.md
├── scoring_rules.py
├── quiniela_engine.py
├── quinigol_engine.py
├── strategy_engine.py
└── run_quiniela_demo.py
```

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

## Modos de estrategia

El sistema soporta tres modos:

- `conservador`: favorece marcadores de menor total de goles dentro de los
  escenarios probables del Core.
- `balanceado`: usa el marcador exacto mas probable segun el Core.
- `agresivo`: mantiene el resultado mas probable, pero busca una variante de
  marcador mas alta en goles.

## Salida por partido

Cada recomendacion incluye:

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
- Justificacion breve.

## Ejecutar demo

Desde la raiz del repositorio:

```bash
python game-layers/quiniela-mundialista/run_quiniela_demo.py
```

El demo usa `data/worldcup_2026_real_teams_baseline_v1.json`, corre tres
partidos de muestra y ejecuta una validacion simple de reglas de puntuacion.

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
