# Fase 3.4 — Comparación de varias casas

## Qué hace

Compara varias casas de apuestas para un mismo partido y escoge la mejor cuota disponible por mercado:

- local
- empate
- visitante

## Por qué importa

Una apuesta puede no valer en una casa, pero sí valer en otra si la cuota es más alta.

Ejemplo:

```txt
Casa A: España gana 1.78
Casa B: España gana 1.82
Casa C: España gana 1.88
```

Si la cuota mínima del modelo es 1.77, la mejor opción sería Casa C.

## Estado actual

`sample_odds_multi_bookmaker.json` contiene cuotas demo manuales.

## Próxima mejora

Conectar API real y guardar:

- casa
- mercado
- cuota
- timestamp
- apertura
- cierre
- movimiento
- CLV