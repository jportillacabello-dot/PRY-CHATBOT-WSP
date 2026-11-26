---
name: harness-creator
description: >-
  Harness engineering: crea, audita y mejora el harness que vuelve fiables a los agentes de
  programación (AGENTS.md/CLAUDE.md, feature_list.json, init.sh, progress.md, session-handoff.md):
  instrucciones, estado, verificación, alcance, traspaso entre sesiones, memoria, presupuesto de
  contexto, seguridad de herramientas y coordinación multiagente. Úsala cuando un agente no es
  fiable entre sesiones (olvida el contexto, se sale del alcance, dice "terminado" antes de que
  pasen los tests o arranca cada sesión de forma distinta) o al crear o revisar esos archivos,
  aunque el usuario nunca diga la palabra "harness".
license: MIT
---

# Harness Creator

Usa esta skill para que un repositorio sea más fácil de usar para agentes de programación: que sepan cómo arrancar, se mantengan en el alcance, verifiquen su trabajo y puedan retomarlo en otra sesión. Mantén el harness lo bastante pequeño como para que los agentes lo sigan de verdad.

No sirve para elegir modelos, ajustar prompts de forma aislada, diseñar interfaces de chat ni para la arquitectura general de una aplicación.

## Ubicación de esta skill

Todas las rutas de abajo son relativas a **la carpeta de esta skill**, la que contiene este `SKILL.md`. Instalaciones típicas:

- Por proyecto: `<proyecto>/.claude/skills/harness-creator/`
- Global: `~/.claude/skills/harness-creator/` (en Windows: `C:\Users\<usuario>\.claude\skills\harness-creator\`)

En los comandos, `<skill>` significa esa carpeta. Si no sabes dónde está, búscala antes de ejecutar nada.

## Modelo central

Todo harness útil para un agente de programación tiene cinco subsistemas:

| Subsistema | Artefacto mínimo | Propósito |
|---|---|---|
| Instrucciones | `AGENTS.md` o `CLAUDE.md` | Ruta de arranque, reglas de trabajo, definición de terminado |
| Estado | `feature_list.json`, `progress.md` | Funcionalidad actual, estado, evidencia, siguiente paso |
| Verificación | `init.sh` o comandos documentados | Tests y chequeos que el agente debe ejecutar antes de decir "terminado" |
| Alcance | Dependencias entre funcionalidades y criterios de terminado | Evita pasarse de la raya y dejar trabajo a medias |
| Ciclo de vida | `session-handoff.md`, rutina de fin de sesión | Permite que la siguiente sesión retome el trabajo |

## Primer paso

1. Revisa lo que ya existe: archivos de instrucciones, archivos de estado, comandos de verificación, documentación y manifiestos de paquetes (`package.json`, `pyproject.toml`, etc.).
2. Pregunta solo por el contexto que falte y no se pueda deducir con seguridad: qué agente se usará, qué nombre de archivo quiere (AGENTS.md o CLAUDE.md), cuánta estructura tolera y si se pueden sobrescribir archivos.
3. Empieza con un harness mínimo. Añade memoria, seguridad de herramientas, multiagente o benchmark solo cuando el problema del usuario lo pida.

## Tareas comunes

Los scripts necesitan **Node.js 18 o superior** y no requieren `npm install`. Si Node no está disponible, usa el [modo sin Node](#modo-sin-node).

### Crear un harness

```bash
node <skill>/scripts/create-harness.mjs --target /ruta/al/proyecto
```

Opciones:

- `--agent-file CLAUDE.md` para proyectos orientados a Claude (por defecto crea `AGENTS.md`).
- `--package-manager npm|pnpm|yarn|bun` si la detección automática se equivoca.
- `--commands "comando uno,comando dos"` para una verificación personalizada.
- `--force` solo después de confirmar con el usuario que se pueden sobrescribir archivos. Sin `--force`, los archivos existentes se respetan.

Después, explica qué se creó y cómo reemplazar las funcionalidades de ejemplo de `feature_list.json` por las reales del proyecto.

### Auditar un harness existente

```bash
node <skill>/scripts/validate-harness.mjs --target /ruta/al/proyecto
```

Informa las puntuaciones de los cinco subsistemas, el área más débil y los 2 o 3 primeros cambios que mejorarían la fiabilidad. Trata la puntuación más baja como un posible cuello de botella; confírmalo con fallos, logs o resultados de tareas antes de afirmar que esa es la causa.

### Generar un informe

Cuando el usuario quiera una evaluación para compartir:

```bash
node <skill>/scripts/render-assessment-html.mjs --target /ruta/al/proyecto
node <skill>/scripts/run-benchmark.mjs --target /ruta/al/proyecto --html /ruta/al/informe.html
```

Deja claro que es un benchmark **estructural**. Primero hace un autochequeo: genera un harness desechable y lo valida, lo que demuestra que los scripts funcionan de principio a fin. Luego puntúa el proyecto y la cobertura de `evals/`. La eficacia real solo se mide comparando sesiones del agente antes y después, con tareas representativas.

### Modo sin Node

Si no se pueden ejecutar los scripts:

- **Crear**: copia las plantillas de `<skill>/templates/` al proyecto (`agents.md` → `AGENTS.md` o `CLAUDE.md`, `feature-list.json` → `feature_list.json`, `progress.md`, `session-handoff.md`, `init.sh`). Reemplaza los marcadores `{{...}}` y ajusta los comandos de verificación al stack del proyecto.
- **Auditar**: revisa a mano cada subsistema con estas preguntas:
  - **Instrucciones**: ¿hay flujo de arranque, definición de terminado, comandos de verificación y enlaces a `feature_list.json` y `progress.md`?
  - **Estado**: ¿`feature_list.json` es JSON válido con `id`, `name`, `description` y `status`? ¿`progress.md` dice estado actual, qué está hecho y qué sigue?
  - **Verificación**: ¿existe `init.sh` con `set -e`, y ejecuta tests y un chequeo de build/tipos/lint? ¿Se registra la evidencia?
  - **Alcance**: ¿hay regla de una funcionalidad a la vez, dependencias en `feature_list.json` y límites de alcance?
  - **Ciclo de vida**: ¿hay rutina de fin de sesión, `session-handoff.md` y una forma limpia de retomar?

### Idioma del harness

Las plantillas están en español. Los títulos clave llevan su nombre en inglés entre paréntesis (p. ej., `## Definición de terminado (Definition of Done)`) porque `validate-harness.mjs` puntúa buscando esas frases en inglés. **No los quites**, o la auditoría bajará la puntuación aunque el contenido sea correcto.

## Cuándo leer las referencias

Carga solo la referencia que necesite el problema del usuario:

- Memoria entre sesiones: [Memoria y persistencia](references/memory-persistence-pattern.md)
- Flujos reutilizables empaquetados como skills: [Skills](references/skill-runtime-pattern.md)
- Permisos, herramientas, concurrencia: [Registro y seguridad de herramientas](references/tool-registry-pattern.md)
- Presupuesto de contexto y revelación progresiva: [Ingeniería de contexto](references/context-engineering-pattern.md)
- Delegación y agentes en paralelo: [Coordinación multiagente](references/multi-agent-pattern.md)
- Hooks, arranque, trabajo largo: [Ciclo de vida y arranque](references/lifecycle-bootstrap-pattern.md)
- Modos de fallo poco obvios: [Trampas](references/gotchas.md)

## Reglas de diseño

- Mantén corto el archivo de instrucciones raíz: rutas e invariantes, no un manual completo.
- Pon los datos del proyecto en la documentación del proyecto, no en la skill.
- Haz que los comandos de verificación sean explícitos y ejecutables.
- Exige evidencia antes de marcar una funcionalidad como terminada.
- Trabaja en una sola funcionalidad activa, salvo que el harness defina límites claros de propiedad para varios agentes.
- Prefiere añadir y actualizar archivos de estado antes que depender del historial del chat.
- Nunca escondas comportamiento destructivo en los scripts; sobrescribir requiere aprobación explícita del usuario.

## Checklist de entrega

Para un harness mínimo usable, deja en el proyecto:

- [ ] `AGENTS.md` o `CLAUDE.md`
- [ ] `feature_list.json`
- [ ] `progress.md`
- [ ] `init.sh`
- [ ] `session-handoff.md` (opcional, para trabajo de varias sesiones)
- [ ] Evidencia de verificación documentada o la siguiente acción

Si no puedes crear archivos, entrega el contenido exacto de cada archivo y los comandos a ejecutar.
