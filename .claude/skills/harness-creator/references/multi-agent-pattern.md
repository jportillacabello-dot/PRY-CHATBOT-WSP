# Patrón de coordinación multiagente

## Problema

Un solo agente choca con límites:
- **Límites de contexto**: no puede sostener toda la investigación y la implementación en una sola sesión
- **Especialización**: hacen falta investigadores, implementadores y revisores separados
- **Paralelismo**: se quiere explorar varios enfoques a la vez

Pero los sistemas multiagente traen caos:
- Los trabajadores repiten la investigación de los demás
- Los coordinadores delegan la comprensión en lugar de sintetizar
- La herencia de contexto crece de forma exponencial

## Reglas de oro

### El coordinador debe sintetizar, no delegar la comprensión

**Antipatrón:**
> "Según lo que encontraste, arregla el sistema de autenticación."

**Patrón:**
> "La investigación identificó 3 flujos de autenticación: login, logout y renovación de token. Implementa SOLO el handler de renovación de token usando la estrategia JWT documentada en [resultado de la investigación]. Devuelve: diff de la implementación + resultados de los tests."

El coordinador (orquestador) aporta valor digiriendo los resultados de los trabajadores y convirtiéndolos en especificaciones precisas antes de mandar a implementar.

### Tres patrones de delegación

| Patrón | Contexto compartido | Ideal para | Restricciones |
|---------|----------------|----------|-------------|
| **Coordinador** | Ninguno: los trabajadores empiezan de cero | Tareas complejas de varias fases (investigar → sintetizar → implementar → verificar) | El más lento pero el más seguro |
| **Fork** | Completo: el hijo hereda el historial del padre | Divisiones rápidas en paralelo que comparten el contexto ya cargado | **Solo un nivel**: los forks recursivos multiplican el costo de contexto |
| **Enjambre (Swarm)** | Entre pares, mediante una lista de tareas compartida | Líneas de trabajo largas e independientes | **Plantilla plana**: un compañero no puede crear otros compañeros |

### Los resultados llegan de forma asíncrona; el registro "lanzar y olvidar" devuelve el ID de inmediato

```typescript
// Ejemplo: lanzar un trabajador y recibir su ID al instante
const taskId = await coordinator.spawn({
  type: 'research',
  prompt: 'Analiza los flujos de autenticación...',
  toolFilter: ['read', 'search'], // Restringe las herramientas
});

// El padre puede seguir trabajando mientras el trabajador corre
// Los resultados llegan por callback o consultando el estado
```

## Cuándo usarlo

- La tarea es demasiado grande para una sola sesión de agente
- Se necesita explorar en paralelo (p. ej., prototipar varios enfoques)
- Se quieren compañeros especializados persistentes (investigador, implementador, revisor)
- Flujos complejos de varias fases

## Compromisos

| Patrón | Velocidad | Seguridad | Costo de contexto |
|---------|-------|--------|--------------|
| **Coordinador** | El más lento | El más seguro | El más bajo (sin herencia) |
| **Fork** | El más rápido | Medio | El más alto (herencia completa) |
| **Enjambre** | Medio | Medio | Medio (solo estado compartido) |

## Patrones de implementación

### Patrón coordinador (recomendado para tareas complejas)

Flujo por fases:

```
Fase 1: Investigar
  ↓ (sintetizar hallazgos)
Fase 2: Planificar
  ↓ (especificaciones precisas)
Fase 3: Implementar
  ↓ (verificar)
Fase 4: Revisar
```

```typescript
// Ejemplo: flujo del coordinador
const research = await coordinator.spawn({
  role: 'researcher',
  prompt: `Analiza la autenticación existente en ${authDir}.
  Busca: flujo de login, flujo de logout, manejo de tokens.
  Devuelve: solo hallazgos estructurados. SIN sugerencias de implementación.`,
  toolFilter: ['read', 'search', 'glob'], // No puede escribir
});

await coordinator.synthesize(research.results);

const implement = await coordinator.spawn({
  role: 'implementer',
  prompt: `Implementa el handler de renovación de token con la estrategia JWT
  de [hallazgos de la fase 2].
  Restricciones: usa los patrones existentes de AuthService, añade tests.`,
  toolFilter: ['read', 'search', 'edit', 'test'], // Puede escribir
});
```

### Patrón fork (solo un nivel)

```typescript
// El padre lanza hijos para trabajar en paralelo
const forks = await Promise.all([
  coordinator.fork({
    prompt: 'Implementa el handler de login',
    inheritContext: true, // Historial completo del padre
  }),
  coordinator.fork({
    prompt: 'Implementa el handler de logout',
    inheritContext: true,
  }),
]);

// CRÍTICO: los hijos no deben hacer fork a su vez
// Si se permite, el costo de contexto se multiplica: padre + hijo1 + hijo2 + ...
```

### Patrón enjambre (plantilla plana)

```typescript
// Enjambre: equipo persistente con lista de tareas compartida
const swarm = new Swarm([
  { id: 'researcher', specialty: 'research' },
  { id: 'implementer', specialty: 'implementation' },
  { id: 'reviewer', specialty: 'verification' },
]);

// Los agentes toman tareas de una cola compartida
// Los resultados se publican en el estado compartido
await swarm.dispatch({
  taskId: 'feat-001',
  pickedBy: 'implementer',
});
```

## Trampas

1. **Los hijos de un fork no deben hacer fork**: un guardia contra la recursión mantiene la regla de un solo nivel. Deja la herramienta de fork en el set del hijo (para compartir la caché del prompt) pero bloquéala en el momento de la llamada.
2. **Los trabajadores del coordinador empiezan sin contexto**: solo reciben el prompt explícito. No supongas que el hijo ve la investigación acumulada del padre.
3. **Los compañeros de un enjambre no pueden crear otros compañeros**: la plantilla es plana para evitar un crecimiento descontrolado.
4. **Escribe prompts autocontenidos**: "según lo que encontraste" es un antipatrón. El coordinador debe digerir primero.
5. **Filtra las herramientas de cada trabajador**: el investigador no necesita escribir; el implementador no necesita búsquedas amplias.

## Patrones relacionados

- [Ingeniería de contexto](context-engineering-pattern.md): patrones de aislamiento para delegar
- [Ciclo de vida y arranque](lifecycle-bootstrap-pattern.md): cómo se lanzan los agentes al inicializar

## Plantilla: estructura del prompt de un trabajador

```markdown
# Prompt autocontenido para un trabajador

## Contexto (copiado de la síntesis del coordinador)

**Tarea**: implementar el handler de renovación de token
**Antecedentes**: la investigación identificó autenticación con JWT y tokens de acceso de 24 h.
**Decisión**: usar rotación de refresh token (un refresh token nuevo en cada renovación).

## Tu rol

Eres un **implementador**. Tu trabajo es escribir código de producción siguiendo las especificaciones anteriores.

## Restricciones

- Usa los patrones existentes de `${authServicePath}`
- Añade tests para los casos de éxito y de fallo
- NO modifiques los handlers de login/logout (es otra tarea)

## Tus herramientas

- read, search, edit, test
- Shell: solo npm test y npm run check

## Entregable

Devuelve:
1. Diff de la implementación (archivos cambiados)
2. Resultados de los tests (pasa/falla)
3. Bloqueos o dudas que necesiten aclaración

**NO devuelvas**: hallazgos de investigación, debates de arquitectura ni diseños alternativos.
```

## Evidencia

Estos patrones de coordinación se observan en sistemas en producción donde:
- Los trabajadores del coordinador empiezan sin heredar contexto
- El fork se limita a un nivel para controlar la explosión de contexto
- Los agentes de un enjambre se comunican mediante listas de tareas compartidas, no con prompts directos
- Los resultados llegan de forma asíncrona con registro de "lanzar y olvidar"
