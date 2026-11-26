# Trampas: modos de fallo del harness engineering

Principios poco obvios que provocan errores si no los respetas.

---

## 1. Los límites del índice de memoria saltan sin avisar

**Síntoma**: los recuerdos recientes "desaparecen" sin ningún error.

**Causa**: el índice tiene límites estrictos (p. ej., 200 líneas / 25 KB) que se aplican al leerlo. Las entradas largas (resúmenes de varias frases) llegan al límite de bytes aunque no lleguen al de líneas.

**Solución**: deja cada entrada del índice en una sola línea. Pon el detalle en los archivos de tema.

```markdown
✓ Bien: "Usar bun, no npm - preferencia del usuario 2024-01-15"
✗ Mal: "El usuario prefiere bun antes que npm porque es más rápido. Se habló el 2024-01-15, cuando el usuario dijo 'usa bun, no npm' y actualicé el package.json en consecuencia..."
```

---

## 2. El orden de prioridad es contraintuitivo

**Síntoma**: una regla global queda anulada sin aviso por un archivo local.

**Causa**: las anulaciones locales ganan a las reglas del proyecto, que ganan a las del usuario, que ganan a las de la organización. Si inyectas una regla a nivel de usuario esperando que domine, un archivo de anulación local en la raíz del proyecto le gana.

**Solución**: prueba con toda la pila de archivos de instrucciones presente:

```bash
# Probar el orden de prioridad
cat ~/.claude/CLAUDE.md          # Nivel de usuario
cat ./CLAUDE.md                   # Nivel de proyecto
cat ./CLAUDE.local.md             # Anulación local (GANA)
```

---

## 3. El momento de la extracción crea una ventana de carrera

**Síntoma**: el extractor en segundo plano escribe en memoria, pero el usuario empieza el siguiente turno antes de que termine.

**Causa**: la extracción se lanza al final de la respuesta, y el usuario puede enviar un mensaje antes de que acabe.

**Solución**: junta las peticiones de extracción concurrentes. Avanza el cursor solo después de una ejecución exitosa. Si una extracción falla, esos mensajes se vuelven a considerar la próxima vez.

---

## 4. Lo que se puede deducir no va en la memoria

**Síntoma**: el índice de memoria se llena de detalles de arquitectura que quedan obsoletos rápido.

**Causa**: el agente guarda lo que ya se puede deducir del código (arquitectura, patrones de código, historial de versiones).

**Solución**: excluye por diseño lo que se puede deducir. La taxonomía de tipos debe prohibir guardar lo que ya está en el repositorio.

---

## 5. La concurrencia se clasifica por llamada, no por herramienta

**Síntoma**: una herramienta marcada como "segura en concurrencia" provoca condiciones de carrera.

**Causa**: la misma herramienta puede ser segura con unas entradas e insegura con otras. No supongas que su comportamiento ante la concurrencia es fijo.

**Solución**: clasifica cada llamada en tiempo de ejecución:

```typescript
// No hagas esto:
toolRegistry.register('shell', { concurrentSafe: false });

// Haz esto:
function isCallConcurrentSafe(call: ToolCall): boolean {
  if (call.args.command.startsWith('rm -rf')) return false;
  if (call.args.command.startsWith('cat')) return true;
  // ...clasificación en tiempo de ejecución
}
```

---

## 6. Evaluar permisos tiene efectos secundarios

**Síntoma**: un chequeo de permisos cambia el comportamiento de las llamadas siguientes.

**Causa**: el evaluador de permisos registra denegaciones, cambia de modo y actualiza el estado como efecto secundario. No es una simple consulta.

**Solución**: no guardes en caché los resultados de permisos entre llamadas. Evalúa cada llamada desde cero.

---

## 7. Casi todo el trabajo asíncrono se salta el estado "pendiente"

**Síntoma**: la interfaz muestra "pendiente", pero la unidad de trabajo nunca pasa por ese estado.

**Causa**: en la práctica, las unidades de trabajo se registran directamente como "en ejecución". El estado "pendiente" existe en la máquina de estados, pero casi no se usa.

**Solución**: no construyas una interfaz que suponga que toda unidad de trabajo empieza en "pendiente".

---

## 8. Los hijos de un fork no deben hacer fork

**Síntoma**: el costo de contexto se dispara de forma exponencial.

**Causa**: los forks recursivos multiplican el contexto: padre + hijo1 + hijo2 + nietos...

**Solución**: aplica la regla de un solo nivel. Deja la herramienta de fork en el set del hijo (para compartir la caché del prompt) pero bloquéala en el momento de la llamada.

---

## 9. Los constructores de contexto se memoizan pero se invalidan a mano

**Síntoma**: el modelo ve datos obsoletos durante toda la sesión.

**Causa**: el constructor de contexto se guarda en caché al arrancar, pero los cambios no limpian esa caché.

**Solución**: cada punto de cambio debe limpiar de forma explícita su caché correspondiente:

```typescript
// Ejemplo: invalidar la caché en el punto de cambio
async function editFile(path: string, content: string) {
  await writeFile(path, content);
  context.cache.invalidate(`file:${path}`); // HAY que invalidar
}
```

---

## 10. La confianza en los hooks es todo o nada

**Síntoma**: todo el sistema de extensiones queda desactivado porque un hook no es confiable.

**Causa**: si el espacio de trabajo no es confiable, se omiten todos los hooks, no solo los sospechosos.

**Solución**: diseña los hooks con el control de confianza en el punto de despacho. No intentes evaluar la confianza hook por hook.

---

## 11. Liberar recursos exige avisar

**Síntoma**: el padre nunca consigue leer el resultado de una unidad de trabajo.

**Causa**: la unidad se liberó antes de avisar al padre de que había terminado. Condición de carrera: el padre intenta leer un resultado que ya se recolectó.

**Solución**: liberación en dos fases:
1. Limpiar la salida en disco al llegar al estado final (inmediato)
2. Limpiar el registro en memoria después de avisar al padre (diferido)

---

## 12. El espacio para listar skills es muy reducido

**Síntoma**: la descripción de la skill se corta y no se activa bien.

**Causa**: las descripciones de las skills se concatenan con un límite por entrada (~150 caracteres). Las palabras de activación que van al principio tienen prioridad.

**Solución**: pon al principio las palabras de activación más distintivas:

```markdown
✓ Bien: "harness-patterns: memoria, permisos, ingeniería de contexto, multiagente"
✗ Mal: "Una skill completa para entender e implementar diversos patrones relacionados con los harnesses de agentes de IA y los sistemas de ejecución..."
```

---

## 13. El permiso por defecto de una herramienta es "permitir"

**Síntoma**: una herramienta se salta un control que se esperaba.

**Causa**: las herramientas sin lógica de permisos propia delegan por completo en el sistema de reglas. El valor por defecto es "permitir" salvo que se configure otra cosa.

**Solución**: cambia el valor por defecto en las herramientas sensibles:

```typescript
registry.register('shell', {
  defaultPermission: 'ask', // NO 'allow'
  // ...
});
```

---

## 14. La memoria de equipo requiere la auto-memoria activada

**Síntoma**: la memoria compartida por el equipo no funciona aunque esté configurada.

**Causa**: la memoria de equipo usa la misma infraestructura de carpeta e índice que la auto-memoria. Si desactivas la auto-memoria (por variable de entorno o ajustes), también se desactiva la de equipo.

**Solución**: asegúrate de que la auto-memoria está activada antes de activar la memoria de equipo. Revisa tanto el interruptor de la funcionalidad como el chequeo de activación.

---

## 15. Los archivos de tema huérfanos se acumulan

**Síntoma**: el disco se llena de archivos en `.claude/memory/topics/`.

**Causa**: el guardado es en dos pasos (archivo de tema y luego índice). Una caída entre los dos pasos deja un archivo de tema huérfano.

**Solución**: un barrido periódico que borre los archivos de tema que el índice no referencia. Los huérfanos no corrompen el índice, pero ocupan espacio.

---

## Lecturas relacionadas

- [Patrón de memoria y persistencia](memory-persistence-pattern.md): trampas n.º 1, 3, 4 y 15
- [Patrón de registro de herramientas](tool-registry-pattern.md): trampas n.º 5, 6 y 13
- [Patrón multiagente](multi-agent-pattern.md): trampas n.º 8 y 11
- [Patrón de ingeniería de contexto](context-engineering-pattern.md): trampa n.º 9
- [Patrón de ciclo de vida](lifecycle-bootstrap-pattern.md): trampas n.º 10 y 14
