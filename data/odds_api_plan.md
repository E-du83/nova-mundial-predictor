# NOVA Market Intelligence Layer — Plan de cuotas

## Estado actual

Esta versión implementa el motor de cuotas con archivo manual:

```txt
data/sample_odds_manual.json
```

El archivo usa cuotas decimales.

## Qué calcula

- probabilidad implícita
- probabilidad del mercado sin margen
- margen de la casa
- cuota justa del modelo
- valor esperado
- decisión clara
- ejemplo con ₡10.000
- Kelly fraccional 25%

## Próxima integración

Crear `src/data_ingestion/odds_api_client.py` para consumir una API real, por ejemplo:

- The Odds API
- OddsPortal mediante scraping solo si es legal/técnicamente viable
- Oddschecker si hay acceso permitido
- Sportmonks / API-Football si el plan contratado incluye odds

## Reglas

1. No mezclar cuotas demo con cuotas reales.
2. Toda cuota debe tener fuente, fecha/hora, casa, mercado y formato decimal.
3. Toda recomendación debe decir: sí jugar, no jugar, esperar cuota o solo quiniela.
4. No prometer ganancias.