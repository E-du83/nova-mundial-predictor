# NOVA Research Snapshot Prompt

Usa `research_prompt_builder.build_research_prompt(...)` para generar una
version por partido.

Reglas:

- No inventar datos.
- No usar resultados futuros.
- No asumir alineaciones confirmadas si solo son probables.
- Si un dato no esta disponible o no esta verificado, marcar
  `pending_verification` o `not_available`.
- Cada dato relevante debe incluir fuente, fecha/hora de captura y confianza.
- Devolver JSON compatible con `research_snapshot_schema.py`.

Campos requeridos:

- alineaciones probables;
- formaciones probables;
- lesiones o ausencias relevantes;
- jugadores clave;
- cuotas visibles 1X2 si existen;
- over/under si existe;
- forma reciente;
- tendencias BTTS, over 2.5 y clean sheet si estan visibles;
- notas tacticas;
- incertidumbres.
