# Fase 4 — Eliminatorias y campeón probable

## Estado

Implementado MVP en:

```txt
src/knockout_simulator.py
src/run_knockout_demo.py
```

## Qué hace

- Simula fase de grupos.
- Clasifica 1.º, 2.º y mejores terceros.
- Construye una ronda de 32 genérica por seeding.
- Simula:
  - ronda de 32
  - octavos
  - cuartos
  - semifinal
  - final
  - campeón
- Calcula probabilidades por fase.

## Importante

Esta versión usa un bracket genérico:

```txt
1 vs 32
2 vs 31
3 vs 30
...
```

Esto permite probar el motor, pero todavía NO es el bracket oficial FIFA 2026.

## Próxima mejora

Crear:

```txt
src/official_bracket_2026.py
```

Para integrar:

- matriz oficial de terceros
- cruces reales de ronda de 32
- ruta oficial hasta la final