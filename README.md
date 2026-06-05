# NOVA Mundial Predictor

Versión actual: **v1.5.0**

Este proyecto es un motor probabilístico para analizar el Mundial 2026 con simulación de partidos, grupos, mejores terceros, cuotas, comparación entre casas, movimiento de cuotas y CLV.

> Nota: internamente se desarrolló por fases, pero esta es la primera versión limpia para subir a GitHub.


Esta versión consolida el proyecto como paquete maestro.

## Nueva fase agregada: histórico de cuotas / CLV

Archivos nuevos:

```txt
src/odds_history_engine.py
src/run_odds_history_demo.py
data/sample_odds_history.json
docs/PROJECT_STATUS.md
docs/ROADMAP.md
docs/GITHUB_NEXT_STEPS.md
docs/MODULES_PENDING.md
```

Ejecutar:

```bash
python src/run_odds_history_demo.py
```

## Qué hace CLV

CLV significa Closing Line Value.

Sirve para saber si agarraste una cuota mejor que la cuota final de cierre.

Ejemplo:
- agarraste cuota 1.95
- cerró en 1.80
- buena señal: tomaste mejor precio que el mercado final

Esto no garantiza ganar un partido, pero sí ayuda a medir si el sistema detecta precios buenos.

# NOVA Mundial Predictor — MVP Inicial

Este es el primer MVP funcional del motor NOVA para análisis probabilístico de partidos, quinielas y apuestas deportivas con enfoque responsable.

## Qué hace esta versión

Esta primera versión permite:

- Cargar dos equipos.
- Calcular goles esperados.
- Simular un partido muchas veces mediante Monte Carlo.
- Estimar probabilidad de victoria, empate y derrota.
- Detectar marcadores más probables.
- Comparar probabilidades contra cuotas.
- Decir claramente qué hacer:
  - Sí jugar
  - No jugar
  - Solo quiniela
  - Esperar mejor cuota
  - Evitar
- Generar una explicación simple para el usuario.

## Qué NO hace todavía

Todavía no incluye:

- Simulación completa de grupos.
- Mejores terceros.
- Mundial completo.
- Alineaciones reales.
- API automática de cuotas.
- Datos tácticos avanzados reales.
- Backtesting histórico.

Eso se agrega en las siguientes fases.

## Estructura

```txt
nova_mundial_predictor_mvp/
├── README.md
├── blueprint.md
├── requirements.txt
├── data/
│   └── sample_teams.json
└── src/
    ├── match_simulator.py
    └── run_demo.py
```

## Cómo usarlo

1. Instalar Python.
2. Abrir la carpeta del proyecto.
3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Ejecutar demo:

```bash
python src/run_demo.py
```

## Filosofía NOVA

Este sistema no promete apuestas seguras. Su objetivo es mejorar decisiones con:

- datos cruzados
- probabilidad
- simulación
- cuotas
- control de riesgo
- salida accionable

La frase base:

> No buscamos certeza absoluta. Buscamos ventaja probabilística responsable.
## Fase 2 agregada: simulador de grupos

Ahora el MVP también puede simular un grupo de 4 equipos.

Ejecutar:

```bash
python src/run_group_demo.py
```

Salida:

- orden recomendado para quiniela
- probabilidad de quedar 1.º
- probabilidad de quedar 2.º
- probabilidad de quedar 3.º
- probabilidad de quedar 4.º
- probabilidad de clasificar directo
- puntos esperados
- diferencia de gol esperada
- órdenes de grupo más repetidos

Nota:
La clasificación como mejor tercero todavía no está cerrada en esta fase, porque para eso hay que simular los 12 grupos juntos y comparar todos los terceros.


## Fase 3 agregada: mejores terceros entre 12 grupos

Ahora el MVP puede simular 12 grupos juntos y calcular:

- 1.º del grupo
- 2.º del grupo
- 3.º clasificado como mejor tercero
- 3.º eliminado
- 4.º eliminado
- clasificación total
- candidatos fuertes a mejores terceros

Ejecutar:

```bash
python src/run_tournament_group_demo.py
```

Importante:
`sample_tournament_groups.json` usa equipos ficticios de prueba para validar el motor. Para usar el Mundial real, hay que sustituirlos por los grupos oficiales y datos reales de selecciones.


## Fase 3.1 agregada: grupos reales del Mundial 2026

Ahora el MVP incluye los grupos reales del Mundial 2026 en:

```txt
data/worldcup_2026_real_groups.json
```

Y un archivo de ratings iniciales v0 para correr el motor:

```txt
data/worldcup_2026_real_teams_baseline_v0.json
```

Ejecutar simulación real de grupos:

```bash
python src/run_worldcup_2026_real_groups.py
```

Importante:
Los grupos son reales; los ratings son una base inicial para correr el motor. La siguiente fase de calidad debe sustituir estos ratings con datos cruzados reales: Elo actual, FIFA ranking, xG, forma reciente, plantillas, lesiones, tácticas y cuotas.


## Fase 3.2 agregada: baseline v1 trazable

Se agregó:

```txt
data/worldcup_2026_real_teams_baseline_v1.json
data/source_manifest_v1.json
data/data_sources_plan.md
src/show_data_quality.py
```

Ahora cada equipo tiene:

- ranking FIFA
- puntos FIFA cuando están disponibles
- Elo externo exacto para top 5 cuando está disponible
- rating NOVA v1
- calidad de dato
- campos faltantes declarados

Ejecutar:

```bash
python src/show_data_quality.py
python src/run_worldcup_2026_real_groups.py
```

Importante:
Esta versión ya no usa ratings arbitrarios, pero sigue siendo baseline v1. Falta integrar APIs para xG, cuotas, jugadores, lesiones y tácticas.


## Fase 3.3 agregada: capa de cuotas

Se agregó:

```txt
src/odds_engine.py
src/run_odds_demo.py
data/sample_odds_manual.json
data/odds_api_plan.md
```

Ahora el sistema puede convertir cuota a probabilidad implícita, quitar margen aproximado de la casa, calcular cuota mínima justa, calcular valor esperado y decir claramente: Sí jugar, No jugar, Esperar cuota o Jugar solo bajo.

Ejecutar:

```bash
python src/run_odds_demo.py
```

Importante:
Las cuotas del archivo son de ejemplo manual. No son cuotas reales en vivo.


## Fase 3.4 agregada: comparación de varias casas

Se agregó:

```txt
src/run_multi_bookmaker_demo.py
data/sample_odds_multi_bookmaker.json
data/multi_bookmaker_plan.md
```

Y se amplió `src/odds_engine.py` con:

- `best_odds_by_market`
- `evaluate_1x2_multi_bookmaker`
- `format_multi_bookmaker_report`

Ejecutar:

```bash
python src/run_multi_bookmaker_demo.py
```

Ahora el sistema puede decir:

- cuál es la mejor cuota encontrada
- en qué casa conviene jugar
- cuándo no vale en ninguna
- cuánto se cobra con ₡10.000
- qué opción tiene mejor valor esperado


## Fase 4 agregada: eliminatorias y campeón probable

Archivos nuevos:

```txt
src/knockout_simulator.py
src/run_knockout_demo.py
docs/PHASE_4_KNOCKOUT.md
```

Ejecutar:

```bash
python src/run_knockout_demo.py
```

Nota:
Esta fase usa un bracket genérico por seeding. Todavía falta integrar el bracket oficial FIFA 2026 completo.


## Versión v1.5.0 — Core Complete

Esta versión agrega estructura completa para seguir el desarrollo sin crear más paquetes pequeños:

- SQLite.
- Backtesting scaffold.
- API de cuotas scaffold.
- Bracket oficial 2026 scaffold.
- Reality Check.
- Pipeline summary.
- Eliminatorias MVP.

Ejecutar resumen del core:

```bash
python src/pipelines/run_core_summary.py
```
