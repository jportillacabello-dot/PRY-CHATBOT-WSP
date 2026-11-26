# Patrón de registro y seguridad de herramientas

## Problema

Los agentes necesitan herramientas (shell, edición de archivos, búsqueda, etc.) para ser productivos. Pero un acceso sin límites trae riesgos:

- Operaciones destructivas (rm -rf, DROP TABLE, etc.)
- Condiciones de carrera por llamadas concurrentes
- Violaciones silenciosas de políticas por permisos mal configurados

La solución es un **registro que falla cerrado** (fail-closed), con clasificación explícita de concurrencia y una cadena de permisos que combina varias fuentes.

## Reglas de oro

### Por defecto, fallar cerrado

Las herramientas son **no concurrentes** y **no de solo lectura** salvo que se marquen explícitamente como seguras. Esto evita:
- Ejecutar en paralelo, por accidente, operaciones que cambian el estado
- Corrupción silenciosa de datos por escrituras concurrentes

### La concurrencia se decide por llamada, no por herramienta

La misma herramienta puede ser segura con unas entradas e insegura con otras:

```
✓ Seguras (pueden correr en paralelo):
  - cat file1.txt
  - grep "patron" src/
  - ls -la

✗ Inseguras (deben correr en serie):
  - rm -rf build/
  - npm install (red, cambios en el sistema de archivos)
  - sed -i 's/viejo/nuevo/g' *.ts
```

El entorno divide un lote de llamadas en grupos consecutivos: las seguras corren en paralelo y cualquier llamada insegura abre un tramo en serie.

### La cadena de permisos tiene efectos secundarios

El evaluador de permisos **tiene estado**:
- Registra las denegaciones (para auditoría y límite de frecuencia)
- Cambia de modo (p. ej., de automático a preguntar tras una denegación)
- Actualiza el estado de la sesión como efecto secundario

**Orden de prioridad estricto:**
```
Política (organización) → Ajustes del usuario → Reglas del proyecto → Anulaciones locales → Permisos de sesión
```

## Cuándo usarlo

- Tu entorno de agentes necesita registrar herramientas
- Necesitas controlar la concurrencia de llamadas en paralelo
- Necesitas filtrar permisos (aprobar automáticamente, preguntar antes, denegar)
- Necesitas registrar el uso de herramientas para auditoría

## Compromisos

| Decisión | Beneficio | Costo |
|---|---|---|
| Fallar cerrado por defecto | Las herramientas nuevas son seguras desde el principio | Hay que activar la concurrencia a propósito |
| Clasificación por llamada | Control fino del paralelismo | Exige analizar cada llamada, no solo el registro de la herramienta |
| Permisos en varias capas | Políticas flexibles y combinables | Difícil de depurar cuando las reglas chocan |
| Evaluador con estado | Puede adaptarse según el historial | No es una función pura: cuesta más probarlo |

## Patrones de implementación

### Registro de herramientas

```typescript
// Ejemplo: entrada del registro de herramientas
interface ToolDefinition {
  name: string;
  description: string;
  handler: (args: any) => Promise<any>;

  // Clasificación de seguridad
  isReadOnly: boolean;       // Por defecto: false
  isConcurrentSafe: boolean; // Por defecto: false

  // Lógica de permisos personalizada (opcional)
  permissionCheck?: (args: any, context: ToolContext) => PermissionResult;
}

// Registrar herramientas
registry.register('read_file', {
  name: 'read_file',
  description: 'Leer el contenido de un archivo',
  handler: readFile,
  isReadOnly: true,
  isConcurrentSafe: true,  // Se pueden leer varios archivos en paralelo sin riesgo
});

registry.register('write_file', {
  name: 'write_file',
  description: 'Escribir o sobrescribir un archivo',
  handler: writeFile,
  isReadOnly: false,
  isConcurrentSafe: false, // Debe correr en serie para evitar condiciones de carrera
});
```

### Cadena de permisos

```typescript
// Orden de evaluación de permisos
async function evaluatePermission(
  toolCall: ToolCall,
  context: PermissionContext
): Promise<PermissionResult> {

  // 1. Reglas de política (máxima prioridad, toda la organización)
  const policyResult = await policyEngine.check(toolCall, context);
  if (policyResult !== 'defer') return policyResult;

  // 2. Ajustes del usuario
  const userResult = await userSettings.check(toolCall, context);
  if (userResult !== 'defer') return userResult;

  // 3. Reglas del proyecto
  const projectResult = await projectRules.check(toolCall, context);
  if (projectResult !== 'defer') return projectResult;

  // 4. Anulaciones locales
  const localResult = await localOverrides.check(toolCall, context);
  if (localResult !== 'defer') return localResult;

  // 5. Permisos de sesión (mínima prioridad)
  return sessionGrants.check(toolCall, context);
}
```

### Reglas que no se pueden saltar

Hay rutas u operaciones que nunca deben aprobarse automáticamente:

```yaml
# Rutas protegidas (nunca aprobar automáticamente)
protected_paths:
  - /etc/**
  - /usr/**
  - node_modules/**
  - .git/**

# Comandos protegidos (preguntar siempre)
protected_commands:
  - "rm -rf*"
  - "DROP TABLE*"
  - "DELETE FROM*"
  - "mkfs*"
```

## Trampas

1. **Casi todo el trabajo asíncrono se salta el estado "pendiente"**: las unidades de trabajo se registran directamente como "en ejecución"
2. **Evaluar permisos tiene efectos secundarios**: no guardes en caché los resultados entre llamadas
3. **Clasificar la concurrencia exige analizar las entradas**, no solo el nombre de la herramienta
4. **El permiso por defecto de las herramientas es "permitir"**: las que no tienen lógica propia delegan en el sistema de reglas
5. **Liberar recursos exige avisar**: una unidad de trabajo terminada solo puede limpiarse después de notificar al padre

## Patrones relacionados

- [Ciclo de vida y arranque](lifecycle-bootstrap-pattern.md): cómo se registran las herramientas al inicializar y cómo se disparan los hooks antes y después de cada herramienta

## Plantilla: checklist de seguridad de una herramienta

Antes de habilitar una herramienta nueva:

```markdown
## Revisión de seguridad de la herramienta

**Nombre de la herramienta**: [p. ej., execute_shell]

### Clasificación
- [ ] Decidido si es de solo lectura (sí / no / depende de los argumentos)
- [ ] Decidido si es segura en concurrencia (sí / no / depende de los argumentos)
- [ ] Documentados los patrones de entrada inseguros

### Requisitos de permisos
- [ ] Modo por defecto en "preguntar" o "denegar"
- [ ] Definidas las rutas y comandos que no se pueden saltar
- [ ] Implementada la lógica de permisos propia (si hace falta)
- [ ] Activado el registro de auditoría

### Pruebas
- [ ] Probada con entradas seguras (debe aprobarse sola)
- [ ] Probada con entradas inseguras (debe preguntar o denegar)
- [ ] Probada la ejecución concurrente (debe serializarse si es insegura)
- [ ] Probado el manejo de errores (fallos registrados, estado coherente)
```

## Evidencia

Estos patrones se observan en entornos de agentes en producción, entre ellos:
- El registro de herramientas de Claude Code, con marcas de concurrencia explícitas
- Evaluación de permisos desde varias fuentes (ajustes → proyecto → sesión)
- Listas de rutas y comandos protegidos que ignoran los modos de aprobación automática
- Clasificación de concurrencia por llamada que divide los lotes de herramientas
