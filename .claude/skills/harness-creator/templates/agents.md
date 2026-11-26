# {{AGENT_FILE_NAME}}

{{PROJECT_PURPOSE}}

## Flujo de inicio (Startup Workflow)

Antes de escribir código:

1. **Confirma el directorio de trabajo** con `pwd`
2. **Lee este archivo** completo
3. **Lee la documentación del proyecto si existe** (`docs/ARCHITECTURE.md`, `docs/PRODUCT.md`, README o equivalente)
4. **Ejecuta `./init.sh`** para verificar que el entorno está sano
5. **Lee `feature_list.json`** para ver el estado actual de las funcionalidades
6. **Revisa los commits recientes** con `git log --oneline -5`

Si la verificación base falla, arréglala primero antes de añadir alcance nuevo.

## Reglas de trabajo

- **Una funcionalidad a la vez (One feature at a time)**: elige exactamente una funcionalidad sin terminar de `feature_list.json`
- **Verificación obligatoria**: no digas "terminado" sin haber ejecutado los comandos de verificación
- **Actualiza los artefactos**: antes de cerrar la sesión, actualiza `progress.md` y `feature_list.json`
- **Mantente en el alcance (Stay in scope)**: no modifiques archivos ajenos a la funcionalidad actual
- **Deja el repo limpio (clean)**: la siguiente sesión debe poder ejecutar `./init.sh` de inmediato

## Artefactos requeridos

- `feature_list.json` — Registro del estado de las funcionalidades (fuente de verdad)
- `progress.md` — Bitácora de continuidad entre sesiones
- `init.sh` — Ruta estándar de arranque y verificación
- `session-handoff.md` — Opcional, para sesiones largas

## Definición de terminado (Definition of Done)

Una funcionalidad está terminada solo cuando se cumple TODO lo siguiente:

- [ ] El comportamiento objetivo está implementado
- [ ] La verificación requerida se ejecutó de verdad (tests / lint / type-check)
- [ ] La evidencia quedó registrada en `feature_list.json` o `progress.md`
- [ ] El repositorio sigue pudiendo arrancar desde la ruta estándar (restartable)

## Fin de sesión (End of Session)

Antes de terminar una sesión:

1. Actualiza `progress.md` con el estado actual
2. Actualiza `feature_list.json` con el nuevo estado de la funcionalidad
3. Registra riesgos o bloqueos sin resolver
4. Haz commit con un mensaje descriptivo cuando el trabajo esté en un estado seguro
5. Deja el repo lo bastante limpio para que la siguiente sesión ejecute `./init.sh` de inmediato

## Comandos de verificación (Verification Commands)

```bash
# Verificación completa (recomendada)
{{PRIMARY_VERIFICATION_COMMAND}}
```

Chequeos requeridos:
{{VERIFICATION_COMMANDS}}

## Escalamiento

Si te encuentras con:
- **Decisiones de arquitectura**: consulta la documentación de arquitectura si existe; si no, pregunta al usuario
- **Requisitos poco claros**: revisa la documentación de producto/requisitos si existe; si no, pregunta al usuario
- **Fallos de tests repetidos**: actualiza el progreso y márcalo para revisión humana
- **Alcance ambiguo**: vuelve a leer `feature_list.json` para ver la definición de terminado
