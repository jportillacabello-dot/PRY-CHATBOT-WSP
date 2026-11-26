# Patrón de ciclo de vida y arranque

## Problema

Los entornos de agentes necesitan poder extenderse sin perder seguridad:

- **Hooks**: extienden el comportamiento en momentos del ciclo de vida (antes/después de una herramienta, inicio/fin de sesión)
- **Tareas en segundo plano**: siguen el trabajo largo sin bloquear al agente principal
- **Arranque (bootstrap)**: ordena la inicialización para varios modos de entrada (CLI, servidor, SDK)

Pero una extensibilidad sin control crea:
- Agujeros de seguridad por hooks no confiables
- Fugas de recursos por tareas que nunca terminan
- Condiciones de carrera durante la inicialización

## Reglas de oro

### La confianza en los hooks es todo o nada

Si el espacio de trabajo no es confiable, **se omiten todos los hooks**, no solo los sospechosos. Los hooks de sesión son efímeros y se limpian al terminar la sesión.

```typescript
// Ejemplo: despacho de hooks con control de confianza
async function dispatchHook(
  hookType: HookType,
  context: HookContext
): Promise<HookResult[]> {

  // Control de confianza: si el espacio no es confiable, se omiten TODOS los hooks
  if (!context.trustBoundary.crossed) {
    logger.warn('Espacio de trabajo no confiable, se omiten los hooks');
    return [];
  }

  // Los hooks de sesión son efímeros: se limpian al terminar la sesión
  const sessionHooks = context.hooks.getByScope('session');
  const projectHooks = context.hooks.getByScope('project');

  return await Promise.all([
    ...sessionHooks.map(h => h.execute(context)),
    ...projectHooks.map(h => h.execute(context)),
  ]);
}
```

### Trabajo largo: máquinas de estado tipadas con liberación en dos fases

Cada unidad de trabajo recibe:
1. **Un ID tipado con prefijo** (p. ej., `extractor-001`, `benchmark-002`)
2. **Un ciclo de vida estricto** (en ejecución → completada | fallida | cancelada)
3. **Salida guardada en disco** (no solo en memoria)

La liberación se hace en dos fases:
1. **La salida en disco** se limpia en cuanto la tarea llega a un estado final
2. **El registro en memoria** se limpia más tarde, después de avisar al padre

### Arranque: etapas ordenadas por dependencias y memoizadas

Varios modos de entrada (CLI, servidor, SDK) comparten la misma ruta de arranque:

```
Etapa 1: Crear un contexto mínimo (no requiere confianza)
  ↓
Etapa 2: Cargar herramientas (solo las seguras de lectura)
  ↓
Etapa 3: Cruzar el límite de confianza (el usuario da su consentimiento)
  ↓
Etapa 4: Cargar subsistemas sensibles (telemetría, variables de entorno secretas)
```

**Punto crítico**: los subsistemas sensibles no deben activarse antes de establecer la confianza.

## Cuándo usarlo

- Necesitas extender el comportamiento del agente sin modificar el núcleo
- Necesitas seguir trabajo largo en segundo plano
- Necesitas una inicialización estructurada para varios modos de entrada
- Necesitas hooks en momentos del ciclo de vida (antes/después de una herramienta, inicio/fin de sesión)

## Compromisos

| Decisión | Beneficio | Costo |
|---|---|---|
| Confianza en hooks todo o nada | Límite de seguridad simple | Un hook no confiable desactiva todo el sistema de extensiones |
| Salida de tareas en disco | Memoria constante sin importar cuánto trabajo haya en paralelo | Latencia de E/S proporcional a las unidades de trabajo |
| Arranque ordenado por dependencias | Varios modos de entrada comparten ruta | El arranque inicial es secuencial (no se paralelizan las etapas) |
| Etapas memoizadas | Reinicializar es rápido | Hay que invalidar la memoización con cuidado al cambiar la configuración |

## Patrones de implementación

### Ciclo de vida de los hooks

Seis tipos de hooks que se disparan en momentos definidos:

```typescript
interface HookRegistry {
  // Ciclo de vida de la sesión
  onSessionStart: (context: SessionContext) => Promise<void>;
  onSessionEnd: (context: SessionContext) => Promise<void>;

  // Ejecución de herramientas
  preToolExecute: (context: ToolContext) => Promise<ToolContext>;
  postToolExecute: (context: ToolResult) => Promise<ToolResult>;

  // Envío del prompt
  prePromptSubmit: (context: PromptContext) => Promise<PromptContext>;
  postPromptSubmit: (context: ResponseContext) => Promise<ResponseContext>;
}

// Uso: registrar hooks mediante la configuración
// /update-config hooks.preToolExecute = "scripts/audit-tool-call.js"
```

### Seguimiento de tareas largas

```typescript
interface TaskRegistry {
  // IDs tipados con prefijo
  registerWork(
    type: 'extraction' | 'benchmark' | 'indexing',
    outputType: 'json' | 'text' | 'file'
  ): string; // Devuelve un ID tipado: `extraction-001`

  // Máquina de estados estricta
  updateState(
    taskId: string,
    state: 'running' | 'completed' | 'failed' | 'killed',
    output?: any
  ): void;

  // Liberación en dos fases
  evictTask(taskId: string): void;
  // 1. Limpia la salida en disco (inmediato, en el estado final)
  // 2. Limpia el registro en memoria (diferido, tras avisar al padre)
}
```

### Secuencia de arranque

```typescript
// Ejemplo: inicialización ordenada por dependencias
class AgentBootstrap {
  private stages = new Map<string, Stage>();
  private memoizedCallers = new Map<string, any>();

  async bootstrap(entryMode: 'cli' | 'server' | 'sdk'): Promise<AgentContext> {

    // Etapa 1: contexto mínimo (no requiere confianza)
    await this.runStage('minimal-context', async () => {
      return {
        cwd: process.cwd(),
        entryMode,
        trustBoundary: { crossed: false },
      };
    });

    // Etapa 2: cargar herramientas (solo las seguras de lectura)
    await this.runStage('load-tools', async (context) => {
      context.tools = await this.loadSafeTools();
      return context;
    });

    // Etapa 3: límite de confianza (el usuario da su consentimiento)
    await this.runStage('trust-boundary', async (context) => {
      const consent = await this.requestConsent();
      context.trustBoundary = { crossed: consent };
      return context;
    });

    // Etapa 4: subsistemas sensibles (requiere confianza)
    if (context.trustBoundary.crossed) {
      await this.runStage('load-sensitive', async (context) => {
        context.telemetry = await this.loadTelemetry();
        context.secretEnvVars = await this.loadSecrets();
        return context;
      });
    }

    return context;
  }

  private async runStage(
    name: string,
    fn: (context: AgentContext) => Promise<AgentContext>
  ): Promise<void> {
    // Memoizado: se omite si ya se ejecutó
    if (this.stages.has(name) && this.stages.get(name).complete) {
      return;
    }

    // Ejecutar la etapa
    const stage = { name, complete: false, running: true };
    this.stages.set(name, stage);

    try {
      await fn(this.context);
      stage.complete = true;
    } finally {
      stage.running = false;
    }
  }
}
```

## Trampas

1. **La confianza en los hooks es todo o nada**: un hook no confiable desactiva todo el sistema de extensiones
2. **Casi todo el trabajo asíncrono se salta el estado "pendiente"**: las unidades se registran directamente como "en ejecución"
3. **Liberar exige avisar**: una unidad de trabajo terminada solo puede limpiarse después de avisar al padre
4. **Ruta rápida de despacho**: los llamadores memoizados deben aguantar llamadas concurrentes sin volver a ejecutar etapas
5. **Los tipos de hooks deben ser disjuntos**: no crees ámbitos de hooks que se solapen

## Patrones relacionados

- [Registro de herramientas](tool-registry-pattern.md): cómo se registran las herramientas en el arranque
- [Memoria y persistencia](memory-persistence-pattern.md): cómo se carga la memoria al inicializar

## Plantilla: checklist de arranque

Antes de dar el arranque por completado:

```markdown
## Verificación del arranque

### Etapa 1: Contexto mínimo
- [ ] Directorio de trabajo confirmado
- [ ] Modo de entrada determinado (cli / server / sdk)
- [ ] Límite de confianza NO cruzado (sin secretos cargados)

### Etapa 2: Herramientas cargadas
- [ ] Herramientas de solo lectura registradas (read, search, glob)
- [ ] Herramientas de escritura TODAVÍA NO registradas (edit, shell)
- [ ] Permisos de herramientas en su valor por defecto (preguntar / denegar)

### Etapa 3: Límite de confianza
- [ ] Consentimiento del usuario pedido (interactivo o por configuración)
- [ ] Consentimiento guardado en el estado de la sesión
- [ ] Auditoría de seguridad registrada

### Etapa 4: Subsistemas sensibles
- [ ] Telemetría inicializada (si hubo consentimiento)
- [ ] Variables de entorno secretas cargadas (si hubo consentimiento)
- [ ] Herramientas de escritura registradas (edit, shell, exec)
- [ ] Sistema de hooks activado (si el espacio es confiable)

### Etapa 5: Tareas en segundo plano
- [ ] Registro de tareas inicializado
- [ ] Handlers de limpieza registrados
- [ ] Vaciado al apagar configurado

## Si falla alguna etapa

- El arranque se detiene de inmediato
- La sesión queda en modo seguro (solo lectura)
- El error se registra con el nombre de la etapa y el motivo del fallo
```

## Evidencia

Estos patrones se observan en entornos en producción donde:
- El despacho de hooks es todo o nada según la confianza del espacio de trabajo
- Las tareas largas usan IDs tipados con prefijo y salida en disco
- El arranque está ordenado por dependencias y sus etapas se memoizan
- El límite de confianza es el punto explícito a partir del cual se activan los subsistemas sensibles
