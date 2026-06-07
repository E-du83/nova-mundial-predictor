# openfootball Snapshot

`openfootball/worldcup.json` puede servir como fuente open data sin API key para
fixtures, grupos y datos de Mundial cuando exista un snapshot verificable.

Reglas:

- No hacer scraping agresivo.
- Preferir un archivo JSON local copiado/verificado manualmente.
- Verificar licencia del repositorio antes de redistribuir datos.
- Si no hay snapshot local, marcar `pending_manual_snapshot`.
- No usar este dato como verdad final sin comparar contra FIFA oficial.

Estado actual:

- Snapshot local: `pending_manual_snapshot`.
- API key: `false`.
- Uso previsto: calendario, fixtures, grupos y validacion cruzada.
