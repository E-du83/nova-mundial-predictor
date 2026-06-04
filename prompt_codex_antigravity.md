# Prompt para Codex / Antigravity

Quiero continuar desarrollando este proyecto llamado NOVA Mundial Predictor.

Objetivo:
Crear un motor probabilístico para quinielas y apuestas del Mundial 2026, con simulación Monte Carlo, análisis de cuotas, recomendación clara y posteriormente simulación de grupos, mejores terceros, eliminatorias y torneo completo.

Reglas fundamentales:
1. No prometer certeza absoluta.
2. Toda salida debe ser accionable:
   - Sí jugar
   - No jugar
   - Solo quiniela
   - Esperar mejor cuota
   - Evitar
3. La respuesta debe explicar cuotas de forma simple.
4. El motor debe separar:
   - predicción pre-Mundial
   - predicción días antes del partido
   - predicción 1 hora antes
5. Debe permitir 10.000, 100.000 y 1.000.000 de simulaciones.
6. Debe tener arquitectura modular.
7. Primero mejorar el simulador de partido.
8. Luego agregar simulador de grupo.
9. Luego agregar mejores terceros.
10. Luego simular Mundial completo.

Tareas inmediatas:
- Revisar el código actual.
- Crear tests básicos.
- Separar cálculos de cuotas en un módulo odds.py.
- Separar simulación en montecarlo.py.
- Crear group_simulator.py para grupos de 4 equipos.
- Crear salida clara por grupo:
  - probabilidad de quedar 1.º
  - probabilidad de quedar 2.º
  - probabilidad de quedar 3.º clasificado
  - probabilidad de quedar 3.º eliminado
  - probabilidad de quedar 4.º
  - clasificación total
- Mantener README actualizado.
Actualización:
Ya existe `src/group_simulator.py` y `src/run_group_demo.py`.

Siguiente tarea:
Crear Fase 3:
- `src/tournament_simulator.py`
- función para simular múltiples grupos a la vez
- ranking de terceros
- probabilidad de 3.º clasificado
- probabilidad de 3.º eliminado
- salida clara:
  - "este equipo debe ponerse como mejor tercero"
  - "este tercero es débil, evitarlo en quiniela"


Actualización Fase 3:
Ya existe `src/tournament_simulator.py` y `src/run_tournament_group_demo.py`.

Siguiente tarea Fase 4:
- Implementar bracket de ronda de 32 del Mundial 2026.
- Crear `knockout_simulator.py`.
- Simular 90 minutos, tiempo extra y penales.
- Calcular:
  - probabilidad de llegar a ronda de 32
  - octavos
  - cuartos
  - semifinal
  - final
  - campeón
- Salida accionable:
  - campeón recomendado para quiniela
  - final más probable
  - semifinalistas probables
  - ruta más dura
  - equipo de valor


Actualización Fase 3.1:
Ya existe simulación con grupos reales del Mundial 2026:

- `data/worldcup_2026_real_groups.json`
- `data/worldcup_2026_real_teams_baseline_v0.json`
- `src/run_worldcup_2026_real_groups.py`

Prioridad:
Reemplazar ratings baseline v0 por datos reales cruzados:
- Elo actual
- ranking FIFA
- xG
- forma últimos 10/20 partidos
- plantillas finales
- lesiones
- tácticas
- cuotas


Actualización Fase 3.2:
Ya existe baseline v1 trazable.

Prioridad para Codex:
1. Crear módulo `data_ingestion/`.
2. Automatizar importación de ranking FIFA.
3. Automatizar importación completa de World Football Elo.
4. Crear `odds_ingestion.py` para cuotas.
5. Crear tests que fallen si un equipo no tiene `data_quality`.
6. Mantener la regla: no presentar dato estimado como oficial.


Actualización Fase 3.3:
Ya existe `src/odds_engine.py`.

Tareas para Codex:
1. Crear tests para `odds_engine.py`.
2. Crear `src/data_ingestion/odds_api_client.py`.
3. Soportar varias casas por partido.
4. Guardar odds en SQLite.
5. Agregar campo `timestamp`.
6. Calcular movement y closing line value.


Actualización Fase 3.4:
Ya existe comparación multi-casa.

Tareas para Codex:
1. Crear tests para multi-bookmaker.
2. Convertir odds manuales a esquema SQLite.
3. Guardar histórico por timestamp.
4. Agregar importador de API.
5. Crear tabla de mejor cuota por mercado.
6. Crear alertas de cuota mínima alcanzada.
