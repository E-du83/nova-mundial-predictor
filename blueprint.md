# NOVA Mundial Predictor — Blueprint Técnico Inicial

## 1. Propósito

Crear un motor de análisis probabilístico para el Mundial que permita tomar mejores decisiones en quinielas y apuestas, usando datos deportivos, tácticos, mercado de cuotas y simulación Monte Carlo.

## 2. Principio central

Toda recomendación debe terminar en una decisión clara:

- Sí jugar
- No jugar
- Solo quiniela
- Esperar mejor cuota
- Jugar conservador
- Evitar
- Revisar una hora antes

## 3. Capas del sistema

### 3.1 NOVA Data Core

Recolecta y normaliza datos:

- FIFA: calendario, sedes, grupos, plantillas, resultados.
- Elo: fuerza relativa de selecciones.
- APIs deportivas: estadísticas, jugadores, lesiones, alineaciones.
- APIs de cuotas: cuotas de apertura, actuales y cierre.
- Datos tácticos: formación, presión, bloque, estilo, transiciones, balón parado.

### 3.2 NOVA Team Strength Index

Índice inicial propuesto:

- 30% Elo
- 20% xG diferencial
- 15% forma reciente
- 10% ataque
- 10% defensa
- 5% plantilla
- 5% contexto
- 5% mercado

Estos pesos deben calibrarse con backtesting.

### 3.3 NOVA Tactical Matchup Layer

Variables tácticas:

- formación base
- formación con balón
- formación sin balón
- presión alta
- bloque bajo/medio/alto
- salida de balón
- ataque por bandas
- ataque central
- transiciones
- balón parado
- rendimiento contra estilos similares

### 3.4 NOVA Market Intelligence Layer

Analiza cuotas:

- cuota actual
- cuota mínima para que valga
- probabilidad implícita
- margen de la casa
- diferencia contra modelo NOVA
- movimiento de mercado
- closing line value

### 3.5 NOVA Monte Carlo Engine

Simula:

- partido individual
- grupo
- mejores terceros
- eliminatorias
- torneo completo

El estándar recomendado:

- 10.000 simulaciones para prueba rápida
- 100.000 para análisis serio
- 1.000.000 para análisis avanzado

### 3.6 NOVA Betting Recommendation Engine

Entrega decisión clara:

- apuesta recomendada
- cuota mínima
- cuota actual
- sí/no jugar
- monto sugerido
- quiniela recomendada
- apuesta a evitar
- explicación simple

## 4. Horizonte temporal

El sistema debe distinguir:

### Pre-Mundial

Usa datos estructurales:

- Elo
- ranking
- plantilla
- grupo
- ruta
- sedes
- forma general

### Días antes del partido

Agrega:

- contexto del grupo
- lesiones
- alineaciones probables
- cuotas maduras
- clima aproximado
- necesidad de puntos

### 1 hora antes

Agrega:

- alineación confirmada
- formación real
- clima real
- cuotas finales
- rotaciones confirmadas

## 5. Salida recomendada por partido

```txt
PARTIDO:
Equipo A vs Equipo B

DECISIÓN:
Sí jugar / No jugar / Solo quiniela / Esperar cuota

JUGADA:
Nombre de la apuesta

CUOTA ACTUAL:
Número

CUOTA MÍNIMA PARA QUE VALGA:
Número

SI APOSTÁS ₡10.000:
Cobrás: ₡____
Ganancia limpia: ₡____

QUINIELA:
Marcador recomendado

SEGUNDA OPCIÓN:
Marcador alternativo

EVITAR:
Apuesta riesgosa

CONFIANZA:
Alta / Media-alta / Media / Baja

MONTO:
Bajo / Medio / Alto / No apostar

EXPLICACIÓN SIMPLE:
Texto claro.
```

## 6. Fórmulas base

### Probabilidad implícita

```txt
probabilidad_implicita = 1 / cuota_decimal
```

### Valor esperado

```txt
EV = probabilidad_modelo * cuota_decimal - 1
```

### Cuota justa

```txt
cuota_justa = 1 / probabilidad_modelo
```

### Goles esperados simplificados

```txt
lambda_A = ataque_A * defensa_B * fuerza_A * ajuste_tactico_A
lambda_B = ataque_B * defensa_A * fuerza_B * ajuste_tactico_B
```

## 7. Reglas de salida accionable

Nunca responder solo:

- riesgo alto
- valor positivo
- confianza media

Siempre traducirlo a:

- jugá esto
- no jugués esto
- esperá mejor cuota
- usalo solo en quiniela
- revisalo una hora antes
- evitá esta jugada

## 8. Roadmap

### Fase 1

Simulador de partido.

### Fase 2

Simulador de grupo.

### Fase 3

Mejores terceros.

### Fase 4

Eliminatorias.

### Fase 5

Mundial completo.

### Fase 6

Conexión con APIs reales.

### Fase 7

Dashboard en Antigravity / React / Astro.

### Fase 8

Versión comercial: quiniela inteligente para usuarios y empresas.
## 9. Fase 2 implementada

Se agregó `group_simulator.py` con simulación de grupos de 4 equipos.

Pendiente inmediato para Fase 3:

- crear `tournament_simulator.py`
- simular los 12 grupos juntos
- comparar los 12 terceros
- calcular probabilidad de 3.º clasificado y 3.º eliminado
- construir ruta de ronda de 32


## 10. Fase 3 implementada

Se agregó `tournament_simulator.py` con simulación de 12 grupos y comparación de mejores terceros.

Ya calcula:

- probabilidad de 1.º
- probabilidad de 2.º
- probabilidad de 3.º clasificado
- probabilidad de 3.º eliminado
- probabilidad de 4.º
- clasificación total
- ranking de candidatos a mejores terceros

Pendiente para Fase 4:

- crear bracket de ronda de 32
- mapear cruces oficiales del Mundial 2026
- simular eliminatorias
- calcular probabilidad de octavos, cuartos, semifinal, final y campeón


## 10.1 Fase 3.1 implementada

Se agregó simulación con grupos reales del Mundial 2026:

- `data/worldcup_2026_real_groups.json`
- `data/worldcup_2026_real_teams_baseline_v0.json`
- `src/run_worldcup_2026_real_groups.py`

Advertencia técnica:
Los grupos son reales, pero los ratings actuales son baseline v0. No deben presentarse como estadística oficial.

Siguiente mejora:
Crear `data_sources_plan.md` y conectar fuentes reales para reemplazar ratings manuales por datos vivos.


## 10.2 Fase 3.2 implementada

Se reemplazó baseline v0 por baseline v1 trazable:

- FIFA ranking actualizado como base.
- Elo exacto top 5 de World Football Elo cuando disponible.
- Data quality por equipo.
- Source manifest.
- Plan de datos reales.

Pendiente:

- scraping/API completa de Elo.
- API de cuotas.
- xG.
- plantillas finales.
- lesiones.
- tácticas.
- backtesting.


## 10.3 Fase 3.3 implementada

Se agregó NOVA Market Intelligence Layer:

- probabilidad implícita
- margen de casa
- no-vig probabilities
- valor esperado
- cuota justa
- decisión accionable
- Kelly fraccional 25%

Pendiente: conectar API real de cuotas, guardar hora/fuente/casa, comparar varias casas, calcular closing line value y alertas de movimiento de cuota.


## 10.4 Fase 3.4 implementada

Se agregó comparación multi-casa:

- mejor cuota por resultado
- mejor casa para la jugada recomendada
- margen estimado por casa
- decisión accionable con mejor cuota disponible

Pendiente:

- conectar API real
- guardar histórico de cuotas
- movimiento apertura/actual/cierre
- Closing Line Value
