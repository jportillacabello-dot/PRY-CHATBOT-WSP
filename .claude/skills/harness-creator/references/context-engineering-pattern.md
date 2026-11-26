# Patrón de ingeniería de contexto

## Problema

Los agentes fallan cuando el contexto se gestiona mal:
- **Demasiado contexto** → el arranque es lento, el costo en tokens se dispara y el modelo se pierde en los detalles
- **Muy poco contexto** → el agente supone cosas equivocadas, reinventa lo que ya existe y rompe las convenciones
- **Contexto equivocado** → el agente se fija en detalles de bajo nivel y pasa por alto las restricciones de arquitectura

El contexto no es un vertedero. Es un presupuesto que se gestiona con operaciones explícitas.

## Reglas de oro

### Cuatro operaciones de contexto

Cada token de la ventana debe ganarse su lugar con una de estas cuatro operaciones:

1. **SELECCIONAR (SELECT)**: carga el contexto justo cuando hace falta, no todo de golpe
2. **ESCRIBIR (WRITE)**: el agente guarda en almacenamiento persistente (memoria, estado, reglas)
3. **COMPRIMIR (COMPRESS)**: compacta los turnos antiguos a mitad de sesión cuando hace falta
4. **AISLAR (ISOLATE)**: el trabajo delegado no debe contaminar el contexto del agente padre

### Revelación progresiva

Carga en tres niveles:

```
Nivel 1: Metadatos (siempre presentes, baratos)
  → Lista de funcionalidades, índice de memoria, estado de la sesión

Nivel 2: Instrucciones (se cargan al activarse)
  → AGENTS.md, cuerpo de las skills, guías de estilo

Nivel 3: Recursos (se cargan bajo demanda)
  → Documentos de arquitectura, referencias de API, ejemplos
```

### Memoiza los constructores costosos e invalídalos de forma explícita

Los constructores de contexto (p. ej., "cargar todos los commits recientes") deben memoizarse para no repetir trabajo, pero **tienen** que invalidarse en los puntos de cambio conocidos, no de forma reactiva. Cada punto de cambio debe limpiar su caché correspondiente.

## Cuándo usarlo

- El rendimiento del agente empeora en sesiones largas
- El arranque es lento porque se carga todo el contexto de entrada
- El trabajo delegado contamina el contexto del padre
- El costo en tokens es impredecible

## Compromisos

| Decisión | Beneficio | Costo |
|---|---|---|
| Carga justo a tiempo | Arranque rápido, poco costo en reposo | El agente no puede razonar sobre una skill hasta que se activa |
| Límites estrictos por bloque | Presupuesto de tokens predecible | Puede recortar contexto útil |
| Invalidación manual de caché | Sin datos obsoletos por reacción | Hay que añadir la invalidación en cada punto de cambio |
| Aislamiento al delegar | Contexto del padre limpio | El hijo no ve el contexto acumulado del padre |

## Patrones de implementación

### Patrón de selección

```markdown
## Contexto de arranque (se carga de inmediato)

- Ruta raíz del repositorio
- Stack tecnológico (una línea)
- ID de la funcionalidad activa en feature_list.json

## Contexto bajo demanda (se carga cuando se necesita)

- Skill: se lee cuando la skill se activa
- Docs de arquitectura: se leen al implementar una funcionalidad nueva
- Referencia de API: se lee al llamar a servicios externos
```

**Movimientos clave:**
- Mide cuánto contexto cuesta cada turno
- Pon límites estrictos a cada bloque de longitud variable
- Añade pistas para recuperar lo recortado ("llama a list_files para ver la salida completa")

### Patrón de compresión

Las sesiones largas agotan la ventana. Compactación reactiva:

1. **Disparador**: el uso de contexto supera un umbral (p. ej., 80 %)
2. **Resumir**: los turnos antiguos (el primer 50 % en tokens)
3. **Conservar**: el contexto reciente (el último 20 % de los turnos)
4. **Etiquetar**: marcar el resumen como "compactado en el turno N"

```markdown
## Resumen de sesión (turnos 1-15, compactado)

**Meta**: implementar preguntas y respuestas con citas
**Decisiones tomadas**:
- Usar respuesta en streaming por la experiencia de usuario
- Formato de cita: referencias en línea [doc:chunk]
**Archivos clave creados**:
- src/services/QaService.ts
- src/shared/types.ts (ampliado con QaResult)
```

### Patrón de aislamiento

El trabajo delegado no debe contaminar el contexto del padre:

| Patrón | Contexto compartido | Ideal para |
|---|---|---|
| **Coordinador** (sin herencia) | Ninguno: los trabajadores empiezan de cero | Tareas complejas de varias fases |
| **Fork** (herencia completa) | Completo, solo un nivel | Divisiones rápidas en paralelo |
| **Enjambre** (entre pares) | Lista de tareas compartida | Trabajo independiente y largo |

**Restricción clave**: el fork es de un solo nivel; los forks recursivos multiplican el costo de contexto de forma exponencial.

## Trampas

1. **Casi todo el trabajo asíncrono se salta el estado "pendiente"**: las unidades de trabajo se registran directamente como "en ejecución"
2. **Los constructores de contexto se memoizan pero se invalidan a mano**: añade la invalidación o tendrás datos obsoletos
3. **El truncado es silencioso hasta que ocurre**: los límites se aplican al leer
4. **El límite de aislamiento se aplica en el momento de la llamada**: no basta con quitar herramientas del prompt

## Patrones relacionados

- [Memoria y persistencia](memory-persistence-pattern.md): cómo interactúan las capas de memoria con el contexto
- [Coordinación multiagente](multi-agent-pattern.md): cómo se comparte el contexto entre agentes

## Plantilla: presupuesto de contexto

```markdown
## Presupuesto de contexto (sesión)

| Categoría | Presupuesto | Actual | Estado |
|----------|--------|---------|--------|
| Prompt de sistema | 2.000 | 1.850 | ✓ |
| Archivos de instrucciones | 3.000 | 2.400 | ✓ |
| Índice de memoria | 1.000 | 600 | ✓ |
| Historial de sesión | 10.000 | 4.200 | ✓ |
| Contexto de trabajo | 15.000 | 3.100 | ✓ |
| **Total** | **31.000** | **12.150** | 39 % usado |

**Disparador de compactación**: 80 % (24.800 tokens)
**Siguiente acción**: compactar al llegar a 24.800 tokens
```

## Evidencia

Estos patrones se observan en entornos de agentes en producción, donde:
- Los presupuestos de contexto son explícitos, no implícitos
- La revelación progresiva reduce la latencia de arranque entre un 60 y un 80 %
- La invalidación manual de caché evita errores sutiles por datos obsoletos
- Los patrones de aislamiento permiten coordinar varios agentes de forma fiable
