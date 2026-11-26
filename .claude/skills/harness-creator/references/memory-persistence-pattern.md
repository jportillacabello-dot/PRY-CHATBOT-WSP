# Patrón de memoria y persistencia

## Problema

Sin memoria persistente, un agente pierde todas las preferencias del usuario, el contexto del proyecto y las correcciones recibidas en cuanto termina la sesión. El usuario tiene que repetir las mismas correcciones en cada sesión ("usa bun, no npm") y el agente no puede acumular el conocimiento de trabajo que lo vuelve realmente útil con el tiempo.

## Reglas de oro

### Separa las capas por alcance y duración

- **Memoria de instrucciones** (curada por humanos, versionada): AGENTS.md, CLAUDE.md, convenciones del proyecto
- **Auto-memoria** (escrita por el agente, persistente): bitácoras de progreso, traspasos de sesión, patrones descubiertos
- **Extracción de sesión** (derivada en segundo plano): análisis automático de la conversación al cerrar la sesión

### Invariante de guardado en dos pasos

Toda escritura en memoria es una operación de dos pasos:
1. Escribir el contenido completo en un archivo de tema dedicado
2. Añadir una línea que apunte a ese archivo en el índice

Si el proceso se cae entre los dos pasos, lo peor que pasa es que queda un archivo de tema huérfano; el índice sigue siendo coherente.

### Las anulaciones locales ganan, siempre

Cuando el mismo tema aparece en varios niveles, manda la instrucción más local:

```
Organización → Usuario → Proyecto → Anulación local
     ↓            ↓          ↓              ↓
 pone el piso  lo acota  lo acota más  última palabra
```

### El índice es contexto acotado y siempre presente; los archivos de tema son detalle bajo demanda

- **Índice**: límite estricto de ~200 líneas / 25 KB, una línea por entrada
- **Archivos de tema**: detalle ilimitado, se cargan cuando hacen falta

## Cuándo usarlo

- Tu agente trabaja a lo largo de varias sesiones y debe recordar preferencias o contexto del proyecto
- Conviven instrucciones de varios niveles y necesitan un orden de prioridad claro
- El agente debe aprender de las sesiones sin curación manual
- Necesitas una extracción en segundo plano que no bloquee al usuario

## Compromisos

| Decisión | Beneficio | Costo |
|---|---|---|
| Memoria en capas | Cada nivel se puede compartir, auditar y anular por separado | Más archivos que descubrir al arrancar |
| Prioridad "gana lo local" | El usuario puede anular sin tocar archivos compartidos | Una regla global puede quedar anulada sin aviso |
| Índice acotado con temas bajo demanda | Costo de contexto constante sin importar cuánta memoria haya | El agente necesita un paso extra de búsqueda |
| Extracción en segundo plano | No añade latencia a las respuestas | Ventana de carrera entre la extracción y el siguiente turno |

## Patrones de implementación

1. **Define el directorio de memoria** de forma idempotente al arrancar (p. ej., `.claude/memory/`)
2. **Crea el archivo índice** con límites estrictos aplicados al leerlo
3. **Implementa el guardado en dos pasos**: primero el archivo de tema, luego el índice
4. **Lanza la extracción en segundo plano** solo después de la respuesta final y sin llamadas a herramientas pendientes
5. **Aplica exclusión mutua**: si el agente principal ya escribió en memoria, omite la extracción en ese turno
6. **Construye un mecanismo de revisión** para las propuestas de mover algo de una capa a otra

## Trampas

1. **El truncado del índice es silencioso hasta que ocurre**: mantén las entradas cortas
2. **El orden de prioridad es contraintuitivo**: lo local gana al proyecto, que gana al usuario, que gana a la organización
3. **El momento de la extracción crea una ventana de carrera**: el usuario puede empezar el siguiente turno antes de que termine
4. **Lo que se puede deducir no va en la memoria**: la arquitectura y los patrones de código se pueden volver a deducir del código
5. **Los archivos de tema huérfanos se acumulan**: conviene limpiarlos cada cierto tiempo

## Patrones relacionados

- [Ingeniería de contexto](context-engineering-pattern.md): cómo gestionar el presupuesto de contexto entre capas
- [Ciclo de vida y arranque](lifecycle-bootstrap-pattern.md): cómo se carga la memoria al inicializar

## Plantilla: estructura de la bitácora de progreso

```markdown
# Bitácora de progreso de sesión

## Estado actual (Última actualización: AAAA-MM-DD HH:MM)

**Funcionalidad activa:** feat-003 - Preguntas y respuestas con citas
**Estado:** En curso (60 % completado)

### Qué está hecho
- [x] Pipeline de troceado de documentos
- [x] Estructura de datos del índice
- [ ] Handler de preguntas y respuestas (en curso)

### Qué está en curso
- Implementando el handler IPC de preguntas y respuestas
- Falta decidir: respuesta en streaming o por lotes

### Bloqueos
- Esperando decisión: formato de citas (notas al pie o en línea)

### La siguiente sesión debería
1. Completar el handler de preguntas y respuestas
2. Añadir el formato de las citas
3. Probar el flujo de principio a fin
```

## Evidencia

Este patrón se basa en entornos de agentes en producción, entre ellos el sistema de memoria de Claude Code, que implementa:
- Jerarquía de instrucciones en cuatro niveles (organización/usuario/proyecto/local)
- Taxonomía de auto-memoria en cuatro tipos (usuario/feedback/proyecto/referencia)
- Extracción de sesión en segundo plano con exclusión mutua
- Memoria compartida por el equipo como capa adicional
