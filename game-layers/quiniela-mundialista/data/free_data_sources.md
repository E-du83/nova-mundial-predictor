# Free Data Sources - Quiniela Mundialista

Este bloque prioriza fuentes gratis, verificables y documentadas. La regla es
simple: si un dato no esta disponible gratis o no esta verificado, se marca como
`pending_real_data`, `pending_manual_snapshot` o `not_available_free`.

## Fuentes principales

| Fuente | Que aporta | Estado | Limitaciones |
| --- | --- | --- | --- |
| FIFA oficial | calendario, sedes, grupos, fixtures, fase y horarios | official | Puede requerir captura manual; no hacer scraping agresivo |
| openfootball/worldcup.json | datos open source de World Cup en JSON | open_data | Depende de actualizacion del repo y verificacion de licencia |
| World Football Elo Ratings | rating de selecciones y fuerza relativa | open_web_data | Necesita snapshot verificado para evitar scraping |
| JGravier/soccer-elo | historico Elo para backtesting | open_source_repo | Puede no estar actualizado a 2026 final |
| Open-Meteo | clima historico por sede sin API key | free_api | Requiere coordenadas, fechas y validacion del periodo |
| The Odds API | cuotas si existe plan/API key | optional_limited_api | No es dependencia obligatoria; puede requerir pago |
| GitHub football datasets | descubrimiento de datasets | reference_registry | Calidad y licencia variable |
| 365Scores snapshot manual | cuotas visibles, alineaciones, stats si el usuario las copia | manual_snapshot | No scraping; algunos datos pueden venir de proveedores premium |
| Backtesting open datasets | openfootball historico, international_results, StatsBomb Open Data, Football-Data.co.uk, soccer-elo | mixed_open_sources | Requieren validacion de licencia, cobertura y cutoff para evitar leakage |

## Lectura API key

- `requires_api_key: false` significa que la fuente no requiere llave. Es un
  punto positivo para pruebas gratis.
- `requires_api_key: true` significa fuente opcional. Si implica pago o limite
  estricto, no se usa como dependencia obligatoria.

## Como evitan humo

- No se inventan temperaturas, cuotas, sedes ni horarios.
- Los snapshots manuales quedan marcados como `pending_manual_snapshot` hasta
  verificar fuente, fecha y campos.
- Las APIs pagadas o limitadas no bloquean el flujo principal.
- El clima usa perfil historico o normal de sede, no clima del dia para demos.
- Cada fuente tiene tipo, costo, confiabilidad, limitaciones y uso previsto.
- 365Scores se usa solo como snapshot manual verificado por el usuario, nunca
  como scraping automatico.

## Que falta todavia

- Calendario FIFA final completo.
- Sedes reales por partido.
- Coordenadas de sedes.
- Clima historico normal por sede y mes.
- Snapshots Elo completos y actualizados.
- Fixture oficial completo de fase de grupos en snapshot local.
- Dataset historico blind para Mundial 2022 con corte temporal por partido.
- Cuotas 1X2 verificadas si el usuario decide aportarlas manualmente.
- Alineaciones, lesiones, sanciones y contexto tactico real.
- Resultado real de amistosos cuando se jueguen para comparar contra el pick.
