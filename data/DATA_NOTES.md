# Notas de datos — NOVA Mundial Predictor

## Qué datos son reales en esta versión

`worldcup_2026_real_groups.json` contiene los grupos reales publicados para el Mundial 2026.

## Qué datos son provisionales

`worldcup_2026_real_teams_baseline_v0.json` contiene ratings iniciales aproximados para que el motor pueda correr.

Estos ratings NO son todavía el modelo final.

## Próxima mejora obligatoria

Sustituir o calibrar estos ratings con:

- Elo actual por selección.
- Ranking FIFA actual.
- xG a favor y en contra.
- últimos 10/20 partidos.
- plantillas finales.
- titulares probables.
- lesiones.
- estilo táctico.
- cuotas de mercado.
- movimiento de cuotas.
- backtesting.

## Regla NOVA

El sistema nunca debe presentar un rating provisional como dato oficial.
La simulación puede usar grupos reales, pero debe declarar cuándo los ratings son baseline v0.