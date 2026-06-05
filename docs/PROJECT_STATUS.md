# NOVA Mundial Predictor — Estado del Proyecto

## Versión maestra actual

`nova_mundial_predictor_master_v8_clv_consolidated`

Esta versión consolida todo lo construido hasta ahora.

## Módulos implementados

### 1. Simulador de partido
Archivo:
`src/match_simulator.py`

Hace:
- goles esperados
- Monte Carlo por partido
- probabilidad 1X2
- marcadores probables

### 2. Simulador de grupo
Archivo:
`src/group_simulator.py`

Hace:
- tabla de grupo
- posición probable
- clasificación directa
- puntos esperados

### 3. Simulador de 12 grupos + mejores terceros
Archivo:
`src/tournament_simulator.py`

Hace:
- 12 grupos
- terceros clasificados
- terceros eliminados
- clasificación total

### 4. Grupos reales Mundial 2026
Archivo:
`data/worldcup_2026_real_groups.json`

Hace:
- sustituye demos ficticios por grupos reales

### 5. Baseline real v1
Archivo:
`data/worldcup_2026_real_teams_baseline_v1.json`

Hace:
- ranking FIFA
- puntos FIFA cuando disponibles
- Elo top 5 cuando disponible
- calidad de datos por equipo

### 6. Capa de cuotas
Archivo:
`src/odds_engine.py`

Hace:
- cuota justa
- probabilidad implícita
- margen casa
- valor esperado
- Kelly fraccional
- decisión accionable

### 7. Comparación multi-casa
Archivo:
`src/odds_engine.py`
Funciones:
- `best_odds_by_market`
- `evaluate_1x2_multi_bookmaker`
- `format_multi_bookmaker_report`

Hace:
- mejor cuota por casa
- mejor casa para apostar
- comparación de márgenes

### 8. Histórico de cuotas / CLV
Archivo:
`src/odds_history_engine.py`

Hace:
- apertura
- actual
- cierre
- movimiento
- Closing Line Value
- decisión: jugar ahora / se pasó la oportunidad / no jugar

## Módulos pendientes

### Prioridad alta

1. Conexión real a API de cuotas.
2. Histórico en SQLite.
3. Backtesting.
4. Ronda de 32 / eliminatorias / campeón.
5. Elo completo automatizado.
6. Ranking FIFA automatizado.

### Prioridad media

7. xG y estadísticas avanzadas.
8. plantillas oficiales FIFA.
9. lesiones.
10. alineaciones probables/confirmadas.
11. tácticas y estilos.

### Prioridad producto

12. Dashboard visual.
13. Exportar PDF/Excel.
14. App web.
15. Versión quiniela empresa.

## Regla de trabajo

A partir de esta versión, ya no conviene crear ZIPs sueltos infinitos.
Lo correcto es subir este master a GitHub y continuar con commits.