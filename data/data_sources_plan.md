# NOVA Mundial Predictor — Plan de datos reales

## Estado actual

Esta versión usa:

1. Grupos reales del Mundial 2026.
2. Ranking FIFA actualizado con puntos exactos cuando están disponibles.
3. Elo exacto de World Football Elo para el top 5 visible en la búsqueda.
4. Estimación por ranking para selecciones donde la página pública devolvió ranking pero no puntos.

## Qué mejora respecto a baseline v0

- Los ratings ya no son una lista arbitraria.
- Cada equipo tiene `fifa_rank`, `fifa_points`, `data_quality`.
- Los equipos top integran Elo exacto cuando está disponible.
- Los datos faltantes quedan marcados, no ocultos.

## Datos pendientes de integrar

### Prioridad 1

- Scraper/API de World Football Elo para los 48 equipos.
- Ranking FIFA oficial completo con puntos de los 48 equipos.
- Cuotas de campeón, grupo y partido desde The Odds API u otro agregador.
- Backtesting con torneos anteriores.

### Prioridad 2

- xG a favor/en contra.
- últimos 10/20 partidos.
- fuerza ofensiva/defensiva por rival.
- partidos oficiales vs amistosos.

### Prioridad 3

- plantillas finales FIFA.
- titulares probables.
- lesiones.
- minutos recientes por jugador.

### Prioridad 4

- estilo táctico:
  - presión
  - bloque
  - transiciones
  - balón parado
  - ataque por zonas
  - rendimiento contra estilos similares

## Regla NOVA

Toda simulación debe indicar:

- qué datos son reales
- qué datos son estimados
- qué datos faltan
- qué tan confiable es la recomendación